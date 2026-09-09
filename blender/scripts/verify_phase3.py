"""Saved scene, workspace, jaw interaction and regeneration checks; no GUI."""
from pathlib import Path
import hashlib
import json
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(Path(__file__).resolve().parent)]
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
from config import DEFAULTS,LIMITS,TROCARS,SHAFT_RADIUS
from phase3_config import CONTACT_OFFSET
from lapsim_ai.simulator.workspace import inverse_contact,reachable
from lapsim_ai.control.hand_mapping import InstrumentTarget
from live_rig import LiveSession
from build_phase3 import build_phase3
import verify_phase1a as baseline
from verify_phase1b import check_jaws,check_modal_events


def scene_data():
    data=[]
    for obj in sorted(bpy.data.objects,key=lambda o:o.name):
        data.append((obj.name,obj.type,obj.parent.name if obj.parent else None,
                     (tuple(obj.location),tuple(obj.rotation_euler),tuple(obj.scale)),
                     [tuple(v.co) for v in obj.data.vertices] if obj.type=='MESH' else [],
                     sorted(tuple(p.vertices) for p in obj.data.polygons) if obj.type=='MESH' else [],
                     sorted(c.name for c in obj.users_collection)))
    return data


def digest():
    return hashlib.sha256(json.dumps(scene_data()).encode()).hexdigest()


def as_target(side,pose):
    values={}
    for channel in ('yaw','pitch','insertion','rotation'):
        base=getattr(DEFAULTS[side],channel);low,high=getattr(LIMITS,channel)
        delta=getattr(pose,channel)-base
        values[channel]=delta/(high-base if delta>=0 else base-low)
    return InstrumentTarget(side,True,**values,jaw=pose.jaw)


def main():
    old_paths=[ROOT/f'blender/scenes/lapsim_ai_{phase}.blend' for phase in ('phase1a','phase1b')]
    old_hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in old_paths]
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/scenes/lapsim_ai_phase3.blend'))
    initial=digest()
    initial_data=scene_data()
    workspace=json.loads(bpy.context.scene['phase3_workspace'])
    assert bpy.data.collections['LAPSIM_DEBUG'].hide_viewport
    assert bpy.data.collections['LAPSIM_DEBUG'].hide_render
    for name,point in workspace['targets'].items():
        for pivot in TROCARS.values():
            assert reachable(pivot,point,LIMITS,CONTACT_OFFSET,.1),name
        screen=world_to_camera_view(bpy.context.scene,bpy.context.scene.camera,Vector(point))
        assert .1<screen.x<.9 and .1<screen.y<.9 and screen.z>0,(name,screen)
        direction=Vector(point)-bpy.context.scene.camera.location
        hit,location,normal,index,obj,matrix=bpy.context.scene.ray_cast(
            bpy.context.evaluated_depsgraph_get(),bpy.context.scene.camera.location,direction.normalized(),distance=direction.length+.001)
        assert hit and obj.name in (name,'GALLBLADDER'),(name,obj.name if hit else 'no hit')
    depsgraph=bpy.context.evaluated_depsgraph_get()
    def tree(obj):
        evaluated=obj.evaluated_get(depsgraph)
        mesh=evaluated.to_mesh()
        result=BVHTree.FromPolygons([evaluated.matrix_world@v.co for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons])
        evaluated.to_mesh_clear()
        return result
    obstacles=[o for o in bpy.data.objects if o.type=='MESH' and
               (o.get('role') in ('static_anatomy','graspable_training_object') or o.name.startswith('WORKSPACE_'))]
    physical=[o for o in bpy.data.objects if o.type=='MESH' and any(o.name==f'{s}_{part}' for s in TROCARS for part in ('SHAFT','JAW_-1','JAW_1'))]
    for obstacle in obstacles:
        obstacle_tree=tree(obstacle)
        for pivot in TROCARS.values():
            nearest=obstacle_tree.find_nearest(Vector(pivot))
            assert nearest[3] is not None and nearest[3]>.018,(obstacle.name,'trocar clearance')
        for obj in physical:
            assert not obstacle_tree.overlap(tree(obj)),(obstacle.name,obj.name,'initial intersection')
    session=LiveSession()
    for side in TROCARS:
        baseline.check_instrument(side)
        check_jaws(side)
    for side in ('LEFT','RIGHT'):
        session.reset()
        name='TRAINING_BEAD_LEFT'
        point=tuple(bpy.data.objects[name].location)
        closed=inverse_contact(TROCARS[side],point,CONTACT_OFFSET)
        from dataclasses import replace
        opened=replace(closed,jaw=1)
        for _ in range(120):
            session.update_targets([as_target(side,opened)],.05)
        assert session.interaction.world.owners[name] is None
        for _ in range(20):
            session.update_targets([as_target(side,closed)],.05)
        assert session.interaction.world.owners[name]==side
        before=Vector(bpy.data.objects[name].location)
        moved=replace(closed,pitch=closed.pitch+3)
        for _ in range(40):
            session.update_targets([as_target(side,moved)],.05)
        assert (bpy.data.objects[name].location-before).length>.005
        baseline.check_instrument(side)
        check_jaws(side)
        for _ in range(20):
            session.update_targets([as_target(side,replace(moved,jaw=1))],.05)
        assert session.interaction.world.owners[name] is None
        session.reset()
        assert (bpy.data.objects[name].location-Vector(session.interaction.world.homes[name])).length<1e-7
    # Existing keyboard event checks also exercise Phase 3's optional adapter.
    keyboard_keys=check_modal_events()
    build_phase3()
    if digest()!=initial:
        for before,after in zip(initial_data,scene_data()):
            if before!=after:
                print('REPRO_DIFFERENCE',before[0],[(i,str(a)[:200],str(b)[:200]) for i,(a,b) in enumerate(zip(before,after)) if a!=b])
                break
    assert digest()==initial,'Procedural regeneration differs'
    assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in old_paths]==old_hashes
    vertices=sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH' and not o.hide_render)
    report=dict(status='PASS',manual_validation='PENDING',workspace_shared_points=workspace['shared_points'],
                maximum_pivot_error_metres=baseline.maximum_pivot_error,pivot_tolerance_metres=baseline.PIVOT_TOLERANCE,
                both_sides_grasp_follow_release_reset='PASS',initial_mesh_intersections='NONE',
                target_camera_visibility='PASS',keyboard_bindings=keyboard_keys,
                phase1_scene_hashes_preserved=True,reproducible_scene_sha256=initial,visible_base_vertices=vertices)
    out=ROOT/'outputs/phase3';out.mkdir(parents=True,exist_ok=True)
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PHASE3_VALIDATION',json.dumps(report))


if __name__=='__main__':
    main()
