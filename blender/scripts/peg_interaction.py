"""Main-thread rig contact/task/scene adapter shared by keyboard and webcam."""
import json
import time
import bpy
from mathutils import Vector
from lapsim_ai.simulator.tasks.peg_transfer import PegTransfer
from phase3_config import CONTACT_OFFSET
from lapsim_ai.telemetry.session import SessionTelemetry


class PegInteraction:
    def __init__(self):
        config = json.loads(bpy.context.scene['peg_transfer_config'])
        self.task = PegTransfer(config['sources'],config['targets'],seat_height=config['seat_height'])
        self.world = self.task.world
        self.telemetry = SessionTelemetry('peg_transfer',len(self.task.targets))
        self._telemetry_time=time.perf_counter()
        bpy.context.scene.pop('peg_session_result',None)
        self.apply()

    def finish(self):
        self.telemetry.finish(self.task.completed)
        if self.telemetry.ended is not None:
            bpy.context.scene['peg_session_result']=json.dumps(self.telemetry.result,allow_nan=False)

    def reset(self):
        self.task.reset()
        self.telemetry.reset()
        self._telemetry_time=time.perf_counter()
        bpy.context.scene.pop('peg_session_result',None)
        self.apply()

    def hud_lines(self):
        result=self.telemetry.result
        if result:
            seconds=int(result['active_seconds'])
            c=result['counts']; p=result['path_metres']
            return ['PEG TRANSFER COMPLETE',f'Time {seconds//60:02d}:{seconds%60:02d} | Objects {result["objects_completed"]}/{result["objects_total"]}',
                    f'Grasps {c["grasps"]} | Drops {c["drops"]} | Handoffs {c["handoffs"]}',
                    f'Incorrect placements {c["incorrect_placements"]} | Successful placements {c["successful_placements"]}',
                    f'Left path {p["LEFT"]:.3f} m | Right path {p["RIGHT"]:.3f} m | Total {p["TOTAL"]:.3f} m']
        return ['PEG TRANSFER',f'Objects: {self.task.completed} / {len(self.task.targets)}',
                f'Task state: {self.task.state}']

    def apply(self):
        for name,position in self.world.positions.items():
            obj = bpy.data.objects[name]
            obj.location = position
            obj['grasp_owner'] = self.world.owners[name] or ''
            obj['placement'] = self.task.placements[name]
            indicator = bpy.data.objects['TARGET_MARKER_'+name]
            indicator.data.materials[0] = bpy.data.materials['Peg complete' if self.task.placements[name]=='CORRECT' else 'Peg target']
        scene = bpy.context.scene
        scene['peg_task_state'] = self.task.state
        scene['peg_objects_complete'] = self.task.completed
        scene['peg_elapsed_seconds'] = self.task.elapsed
        bpy.context.view_layer.update()

    def update(self, poses, dt, paused=False):
        graph = bpy.context.evaluated_depsgraph_get()
        hands = {}
        for side,pose in poses.items():
            tips = [bpy.data.objects[f'{side}_JAW_HINGE_{sign}'].evaluated_get(graph).matrix_world
                    @ Vector((0,0,-CONTACT_OFFSET)) for sign in (-1,1)]
            hands[side] = (tuple((tips[0]+tips[1])/2),pose.jaw)
        if not paused:
            self.task.update(hands,dt)
            self.apply()
        # Use the actual distal shaft reference: independent of jaw opening,
        # unlike the grasp-pad midpoint. Accepted rig motion only, after collisions.
        tips={side:tuple(bpy.data.objects[f'{side}_TIP_REFERENCE'].evaluated_get(graph).matrix_world.translation)
              for side in poses}
        now=time.perf_counter()
        elapsed=now-self._telemetry_time
        self._telemetry_time=now
        self.telemetry.observe(dt=elapsed,paused=paused,task_state=self.task.state,
            owners=self.world.owners,placements=self.task.placements,completed=self.task.completed,tips=tips)
        if self.telemetry.ended is not None and 'peg_session_result' not in bpy.context.scene:
            bpy.context.scene['peg_session_result']=json.dumps(self.telemetry.result,allow_nan=False)
