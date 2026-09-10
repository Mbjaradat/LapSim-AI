"""Main-thread Blender adapter for the standalone webcam worker."""
import atexit
from pathlib import Path
import time
import bpy
import blf
import live_ui
from live_rig import LiveSession
from lapsim_ai.control.webcam_bridge import WebcamProcess
from lapsim_ai.control.public_runtime import PublicRuntime

ROOT = Path(__file__).resolve().parents[2]
REGISTERED = False


class LAPSIM_OT_webcam(bpy.types.Operator):
    bl_idname = "lapsim.webcam"
    bl_label = "LapSim: Start Webcam Control"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == "VIEW_3D" and live_ui.ACTIVE is None

    def invoke(self, context, event):
        self._closed = False
        self.runtime = PublicRuntime()
        self.startup = self.runtime.startup
        self._last_notice = None
        self.worker = None
        self._timer = self._draw = None
        self._wm, self._window, self._area = context.window_manager, context.window, context.area
        try:
            self.session = LiveSession()
            self.session.controller.paused = True
            self.worker = WebcamProcess(ROOT)
            atexit.register(self.worker.shutdown)
            self.mode = "Webcam"
            self._last = time.perf_counter()
            self.targets = []
            self._timer = self._wm.event_timer_add(1 / 30, window=self._window)
            self._draw = bpy.types.SpaceView3D.draw_handler_add(self.draw_hud, (), "WINDOW", "POST_PIXEL")
            live_ui.ACTIVE = self
            self._wm.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        except Exception as error:
            self.finish()
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

    def draw_hud(self):
        if self._closed or bpy.context.area != self._area:
            return
        lines = [self.runtime.message,
                 "Follow the Camera and HOME preview",
                 "Fallback: Space pause/resume | R retry | Backspace recenter | Esc stop"]
        if self.session.interaction and hasattr(self.session.interaction, 'hud_lines'):
            lines = self.session.interaction.hud_lines() + [
                lines[0], 'Handoff: close receiver, then open donor',
                'Fallback: Space pause/resume | R retry | Backspace recenter | Esc stop']
        rows = []
        blf.size(0, 15)
        width = max(100, bpy.context.region.width - 40)
        for line in lines:
            row = ""
            for word in line.split():
                candidate = (row + " " + word).strip()
                if row and blf.dimensions(0, candidate)[0] > width:
                    rows.append(row)
                    row = word
                else:
                    row = candidate
            rows.append(row)
        blf.enable(0, blf.SHADOW)
        blf.shadow(0, 5, 0, 0, 0, 1)
        blf.color(0, 1, 1, 1, 1)
        for i, line in enumerate(reversed(rows)):
            y = 32 + i * 22
            if bpy.context.scene.get('peg_transfer_config'):
                y = bpy.context.region.height - 48 - (len(rows)-1-i)*22
            blf.position(0, 20, y, 0)
            blf.draw(0, line)
        blf.disable(0, blf.SHADOW)

    def finish(self):
        if self._closed:
            return
        self._closed = True
        session=getattr(self,'session',None)
        if session and session.interaction and hasattr(session.interaction,'finish'):
            session.interaction.finish()
        self.startup.stop()
        if self.worker:
            self.worker.stop()
            worker = self.worker
            def reap():
                delay = worker.reap()
                if delay is None:
                    atexit.unregister(worker.shutdown)
                return delay
            bpy.app.timers.register(reap, first_interval=0.1, persistent=True)
        if self._timer:
            self._wm.event_timer_remove(self._timer)
        if self._draw:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw, "WINDOW")
        if live_ui.ACTIVE is self:
            live_ui.ACTIVE = None
        self._area.tag_redraw()

    def cancel(self, context):
        self.finish()

    def modal(self, context, event):
        if self._closed:
            return {"CANCELLED"}
        try:
            if self._area not in list(self._window.screen.areas) or self._area.type != "VIEW_3D" or event.type == "ESC":
                self.finish()
                return {"CANCELLED"}
            if event.type == "WINDOW_DEACTIVATE":
                if self.startup.started:
                    self.session.controller.paused = True
                return {"PASS_THROUGH"}
            if event.type == "TIMER":
                now = time.perf_counter()
                self.targets = self.worker.poll(now)
                frame = self.worker.frame
                if not self.startup.started:
                    self.session.controller.paused = True
                entered = self.runtime.update(self.targets, frame[0] if frame else None,
                    self.worker.calibrated, self.worker.setup, now,
                    paused=self.session.controller.paused,
                    complete=bpy.context.scene.get('peg_task_state') == 'COMPLETE')
                notice = (self.runtime.state, self.runtime.message)
                if notice != self._last_notice:
                    self.worker.inform(*notice)
                    self._last_notice = notice
                # Paused observation preserves telemetry timing during an explicit
                # mid-session recenter. It cannot move tools or update the task.
                if not self.startup.started or entered:
                    self.session.controller.paused = True
                    self.session.update_targets([], now - self._last)
                    if entered:
                        self.session.controller.paused = False
                else:
                    self.session.update_targets(self.targets, now - self._last)
                self._last = now
                self._area.tag_redraw()
            elif event.value == "PRESS" and not event.is_repeat:
                if event.type == "SPACE":
                    if not self.startup.started:
                        return {"RUNNING_MODAL"}
                    self.targets = self.worker.poll()
                    if self.session.controller.paused:
                        if len(self.targets) == 2 and all(t.valid for t in self.targets):
                            self.session.controller.paused = False
                        else:
                            self.report({"WARNING"}, "Calibrate and show both hands before entering LIVE")
                    else:
                        self.session.controller.paused = True
                elif event.type == "R":
                    self.session.controller.paused = True
                    self.session.reset()
                    self.runtime.retry()
                    self.startup = self.runtime.startup
                    self.worker.inform('WAITING_FOR_LIVE', 'RETURN TO HOME', 'retry')
                elif event.type == "BACK_SPACE":
                    world = getattr(self.session.interaction, 'world', None)
                    manipulating = world is not None and any(world.owners.values())
                    if self.session.controller.paused and not manipulating:
                        self.runtime.retry()
                        self.startup = self.runtime.startup
                        self.worker.setup = {}
                        self.worker.inform('HOME_SETUP', 'PLACE BOTH HANDS COMFORTABLY', 'recenter')
                    else:
                        self.report({'WARNING'}, 'Pause and release held objects before recentering')
            # Exclusive provider ownership; never pass transforms or playback keys.
            return {"RUNNING_MODAL"}
        except Exception as error:
            self.finish()
            self.report({"ERROR"}, f"Webcam stopped: {error}")
            return {"CANCELLED"}


def view_menu(self, context):
    # Normal F3 menu search discovers menu entries, not every registered operator.
    self.layout.operator_context = "INVOKE_REGION_WIN"
    self.layout.operator("lapsim.webcam", text="LapSim: Start Webcam Control")


def register():
    global REGISTERED
    live_ui.register()  # shared ownership lock and file-load cleanup
    if not REGISTERED:
        previous = bpy.types.Operator.bl_rna_get_subclass_py("LAPSIM_OT_webcam")
        if previous is not None and previous is not LAPSIM_OT_webcam:
            bpy.utils.unregister_class(previous)
        bpy.utils.register_class(LAPSIM_OT_webcam)
        bpy.types.VIEW3D_MT_view.append(view_menu)
        REGISTERED = True
