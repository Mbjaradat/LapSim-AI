"""Temporary Blender UI registration: modal keyboard provider and replaceable HUD."""

import time
import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent
from lapsim_ai.control.keyboard import KeyboardInput, KEY_BINDINGS
from lapsim_ai.control.controller import NormalizedCommand
from lapsim_ai.control.settings import TIMER_INTERVAL, WHEEL_DT, KEY_TAP_DT
from live_rig import LiveSession

ACTIVE = None
REGISTERED = False


def hud_lines(session, selected):
    controller = session.controller
    lines = [f"LapSim-AI | Keyboard | {'PAUSED' if controller.paused else 'LIVE'} | {controller.profile[0]}"]
    for side, pose in controller.poses.items():
        lines.append(f"{'>' if side == selected else ' '} {side}: yaw {pose.yaw:+.1f}  pitch {pose.pitch:+.1f}  "
                     f"depth {pose.insertion * 100:.1f} cm  roll {pose.rotation:+.1f}  jaw {pose.jaw:.2f}")
    lines.extend(("Space pause | R reset | Tab sensitivity | 1/2 mouse target | Esc stop",
                  "L: WASD QE ZX FG   R: arrows PgUp/PgDn NM JK | wheel depth; Shift+wheel roll"))
    return lines


class LAPSIM_OT_live(bpy.types.Operator):
    bl_idname = "lapsim.live"
    bl_label = "LapSim: Start Keyboard Control"
    bl_description = "Reset to neutral and take exclusive live ownership of the Phase 1B rig"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == "VIEW_3D" and ACTIVE is None

    def invoke(self, context, event):
        global ACTIVE
        try:
            self.session = LiveSession()
        except ValueError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        self.provider = KeyboardInput()
        self.selected = "LEFT"
        self.mode = "Keyboard"
        self._closed = False
        self._wm, self._window, self._area = context.window_manager, context.window, context.area
        self._last = time.perf_counter()
        self._timer = self._wm.event_timer_add(TIMER_INTERVAL, window=self._window)
        self._draw = bpy.types.SpaceView3D.draw_handler_add(self.draw_hud, (), "WINDOW", "POST_PIXEL")
        ACTIVE = self
        self.select_instrument(context)
        self._wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def select_instrument(self, context):
        obj = bpy.data.objects.get(f"{self.selected}_INSTRUMENT")
        if obj:
            for selected in list(context.selected_objects):
                selected.select_set(False)
            obj.select_set(True)
            context.view_layer.objects.active = obj

    def draw_hud(self):
        if self._closed or bpy.context.area != self._area:
            return
        font = 0
        blf.size(font, 16)
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)
        self.provider = KeyboardInput()
        self.selected = "LEFT"
        self._area = context.area
        self._window = context.window
        self._wm = context.window_manager
        self._closed = False
        self._last = time.perf_counter()
        self._timer = self._wm.event_timer_add(TIMER_INTERVAL, window=self._window)
        self._draw = bpy.types.SpaceView3D.draw_handler_add(self.draw_hud, (), "WINDOW", "POST_PIXEL")
        ACTIVE = self
        self.select_instrument(context)
        self._wm.modal_handler_add(self)
        self._area.tag_redraw()
        return {"RUNNING_MODAL"}

    def select_instrument(self, context):
        for obj in context.selected_objects:
            obj.select_set(False)
        obj = bpy.data.objects[f"{self.selected}_INSTRUMENT"]
        obj.select_set(True)
        context.view_layer.objects.active = obj

    def draw_hud(self):
        if self._closed or bpy.context.area != self._area:
            return
        font = 0
        blf.size(font, 15)
        blf.enable(font, blf.SHADOW)
        blf.shadow(font, 5, 0, 0, 0, 1)
        blf.shadow_offset(font, 1, -1)
        # Bottom placement avoids Blender's tool settings and top-left overlays.
        # Wrap to the actual viewport width instead of painting under side panels.
        available = max(120, bpy.context.region.width - 56)
        rows = []
        for i, line in enumerate(hud_lines(self.session, self.selected)):
            row = ""
            for word in line.split():
                candidate = f"{row} {word}".strip()
                if row and blf.dimensions(font, candidate)[0] > available:
                    rows.append((i, row))
                    row = word
                else:
                    row = candidate
            rows.append((i, row))
        width = min(available + 24, max(blf.dimensions(font, line)[0] for _, line in rows) + 24)
        top = 24 + 23 * len(rows) + 20
        vertices = ((16, 24), (16 + width, 24), (16 + width, top),
                    (16, 24), (16 + width, top), (16, top))
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        batch = batch_for_shader(shader, "TRIS", {"pos": vertices})
        gpu.state.blend_set("ALPHA")
        shader.bind()
        shader.uniform_float("color", (.012, .018, .025, .88))
        batch.draw(shader)
        gpu.state.blend_set("NONE")
        y = top - 24
        for i, line in rows:
            color = (.2, .85, 1, 1) if i == 1 else (1, .65, .2, 1) if i == 2 else (.95, .95, .95, 1)
            blf.color(font, *color)
            blf.position(font, 28, y, 0)
            blf.draw(font, line)
            y -= 23
        blf.disable(font, blf.SHADOW)

    def pause(self):
        self.provider.clear()
        self.session.controller.paused = True

    def finish(self):
        global ACTIVE
        if self._closed:
            return
        self._closed = True
        self.provider.clear()
        self._wm.event_timer_remove(self._timer)
        bpy.types.SpaceView3D.draw_handler_remove(self._draw, "WINDOW")
        if ACTIVE is self:
            ACTIVE = None
        self._area.tag_redraw()

    def cancel(self, context):
        self.finish()

    def modal(self, context, event):
        if self._closed:
            return {"CANCELLED"}
        try:
            return self.handle_event(context, event)
        except Exception as error:
            self.finish()
            self.report({"ERROR"}, f"LapSim stopped: {error}")
            return {"CANCELLED"}

    def handle_event(self, context, event):
        if self._area not in list(self._window.screen.areas) or self._area.type != "VIEW_3D":
            self.finish()
            return {"CANCELLED"}
        if event.type == "ESC":
            self.finish()
            return {"CANCELLED"}
        if event.type == "WINDOW_DEACTIVATE":
            self.pause()
            return {"PASS_THROUGH"}
        if event.type == "TIMER":
            # Blender 5.2 Event exposes no timer identity. Use elapsed time so
            # other window timers cannot multiply the commanded movement rate.
            now = time.perf_counter()
            self.session.update(self.provider.commands(), now - self._last)
            self._last = now
            self._area.tag_redraw()
            return {"RUNNING_MODAL"}
        region = next(r for r in self._area.regions if r.type == "WINDOW")
        inside = region.x <= event.mouse_x < region.x + region.width and region.y <= event.mouse_y < region.y + region.height
        if not inside:
            self.pause()
            return {"PASS_THROUGH"}
        if event.type == "MIDDLEMOUSE":
            self.pause()
            return {"PASS_THROUGH"}
        if event.type in {"MOUSEMOVE", "INBETWEEN_MOUSEMOVE"}:
            return {"PASS_THROUGH"}
        if event.type in {"WHEELUPMOUSE", "WHEELDOWNMOUSE"}:
            sign = 1 if event.type == "WHEELUPMOUSE" else -1
            channel = "rotation" if event.shift else "insertion"
            self.session.update([NormalizedCommand(self.selected, **{channel: sign})], WHEEL_DT)
            self._area.tag_redraw()
            return {"RUNNING_MODAL"}
        if event.type.startswith("NUMPAD"):
            self.provider.clear()
            return {"PASS_THROUGH"}
        if event.ctrl or event.alt:
            self.provider.clear()
            return {"RUNNING_MODAL"}
        if event.type in KEY_BINDINGS:
            if event.value == "RELEASE":
                self.provider.key(event.type, False)
            elif event.value == "PRESS" and not self.session.controller.paused:
                if not event.is_repeat and event.type not in self.provider.held:
                    side, channel, direction = KEY_BINDINGS[event.type]
                    self.session.update([NormalizedCommand(side, **{channel: direction})], KEY_TAP_DT)
                self.provider.key(event.type, True)
            return {"RUNNING_MODAL"}
        if event.value == "PRESS" and not event.is_repeat:
            if event.type == "SPACE":
                self.provider.clear()
                self.session.controller.paused = not self.session.controller.paused
            elif event.type == "R":
                self.provider.clear()
                self.session.reset()
            elif event.type == "TAB":
                self.provider.clear()
                self.session.controller.cycle_sensitivity()
            elif event.type in {"ONE", "TWO"}:
                self.selected = "LEFT" if event.type == "ONE" else "RIGHT"
                self.select_instrument(context)
            self._area.tag_redraw()
        # Own keyboard input until Esc; avoid transforms, timeline playback, or deletion.
        return {"RUNNING_MODAL"}


class LAPSIM_OT_stop(bpy.types.Operator):
    bl_idname = "lapsim.stop"
    bl_label = "Stop LapSim Control"

    def execute(self, context):
        if ACTIVE:
            ACTIVE.finish()
        return {"FINISHED"}


class LAPSIM_PT_controls(bpy.types.Panel):
    bl_label = "LapSim-AI"
    bl_idname = "LAPSIM_PT_controls"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LapSim"

    def draw(self, context):
        layout = self.layout
        layout.operator("lapsim.stop" if ACTIVE else "lapsim.live")
        layout.label(text="Move pointer into the viewport")
        layout.label(text="Space: pause/resume | Esc: stop")
        layout.label(text="R: neutral | Tab: sensitivity")
        if ACTIVE:
            layout.label(text=f"{getattr(ACTIVE, 'mode', 'Keyboard')} / {'Paused' if ACTIVE.session.controller.paused else 'Live'}")
        for side in ("LEFT", "RIGHT"):
            box = layout.box()
            box.label(text=side)
            obj = bpy.data.objects.get(f"{side}_INSTRUMENT")
            if obj and "jaw" in obj:
                for name in ("yaw", "pitch", "insertion", "rotation", "jaw"):
                    row = box.row()
                    row.enabled = ACTIVE is None
                    row.prop(obj, f'["{name}"]', text=name.title())


@persistent
def stop_before_load(_):
    if ACTIVE:
        ACTIVE.finish()


CLASSES = (LAPSIM_OT_live, LAPSIM_OT_stop, LAPSIM_PT_controls)


def view_menu(self, context):
    self.layout.separator()
    self.layout.operator("lapsim.stop" if ACTIVE else "lapsim.live")


def register():
    global REGISTERED
    if REGISTERED:
        return
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_pre.append(stop_before_load)
    bpy.types.VIEW3D_MT_view.append(view_menu)
    REGISTERED = True


def unregister():
    global REGISTERED
    if ACTIVE:
        ACTIVE.finish()
    if not REGISTERED:
        return
    bpy.app.handlers.load_pre.remove(stop_before_load)
    bpy.types.VIEW3D_MT_view.remove(view_menu)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    REGISTERED = False
