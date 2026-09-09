"""Optional main-thread scene adapter, enabled only by the Phase 3 scene flag."""
import bpy
from mathutils import Vector
from lapsim_ai.simulator.grasp import GraspWorld
from phase3_config import CONTACT_OFFSET


class Phase3Interaction:
    def __init__(self):
        self.objects={obj.name:obj for obj in bpy.data.objects if obj.get('role')=='graspable_training_object'}
        self.world=GraspWorld({name:tuple(obj['grasp_home']) for name,obj in self.objects.items()})
        self.reset()

    def reset(self):
        self.world.reset()
        self.apply()

    def apply(self):
        for name,position in self.world.positions.items():
            obj=self.objects[name]
            obj.location=position
            obj['grasp_owner']=self.world.owners[name] or ''
        bpy.context.view_layer.update()

    def update(self, poses):
        depsgraph=bpy.context.evaluated_depsgraph_get()
        hands={}
        for side,pose in poses.items():
            tips=[bpy.data.objects[f'{side}_JAW_HINGE_{sign}'].evaluated_get(depsgraph).matrix_world
                  @ Vector((0,0,-CONTACT_OFFSET)) for sign in (-1,1)]
            hands[side]=(tuple((tips[0]+tips[1])/2),pose.jaw)
        self.world.update(hands)
        self.apply()
