"""Main-thread rig contact/task/scene adapter shared by keyboard and webcam."""
import json
import bpy
from mathutils import Vector
from lapsim_ai.simulator.tasks.peg_transfer import PegTransfer
from phase3_config import CONTACT_OFFSET


class PegInteraction:
    def __init__(self):
        config = json.loads(bpy.context.scene['peg_transfer_config'])
        self.task = PegTransfer(config['sources'],config['targets'],seat_height=config['seat_height'])
        self.world = self.task.world
        self.apply()

    def reset(self):
        self.task.reset()
        self.apply()

    def hud_lines(self):
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

    def update(self, poses, dt):
        graph = bpy.context.evaluated_depsgraph_get()
        hands = {}
        for side,pose in poses.items():
            tips = [bpy.data.objects[f'{side}_JAW_HINGE_{sign}'].evaluated_get(graph).matrix_world
                    @ Vector((0,0,-CONTACT_OFFSET)) for sign in (-1,1)]
            hands[side] = (tuple((tips[0]+tips[1])/2),pose.jaw)
        self.task.update(hands,dt)
        self.apply()
