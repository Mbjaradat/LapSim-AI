"""Headless saved-scene/reach/full handoff trial/regeneration checks. No GUI."""
from pathlib import Path
import sys
import json
import hashlib
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'src'),str(Path(__file__).resolve().parent)]
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
from config import TROCARS, LIMITS
from peg_config import SOURCES,TARGETS,HANDOFF
from phase3_config import CONTACT_OFFSET
from lapsim_ai.simulator.workspace import reachable,inverse_contact
from live_rig import LiveSession
from verify_phase3 import digest,as_target
from verify_phase1b import check_jaws,check_modal_events
import verify_phase1a as baseline
from build_peg_transfer import build_peg_transfer


def fingerprint():
    scene=bpy.context.scene
    extra=(digest(),scene.camera.data.lens,
           [(o.name,o.data.body) for o in bpy.data.objects if o.type=='FONT'],
           [(m.name,tuple(m.diffuse_color)) for m in bpy.data.materials],
           scene['peg_transfer_config'],scene['peg_workspace'])
    return hashlib.sha256(json.dumps(extra).encode()).hexdigest()


def main():
    old = {p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'blender/scenes').glob('*.blend')
           if p.name != 'lapsim_ai_peg_transfer.blend'}
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/scenes/lapsim_ai_peg_transfer.blend'))
    scene=bpy.context.scene
    initial=fingerprint()
    assert len([o for o in bpy.data.objects if o.get('role')=='peg_transfer_object'])==6
    assert not any(o.name in ('LIVER','GALLBLADDER') for o in bpy.data.objects)
    targets=json.loads(scene['peg_workspace'])['critical']
    for name,point in targets.items():
        assert all(reachable(p,point,LIMITS,CONTACT_OFFSET,.10) for p in TROCARS.values()),name
        screen=world_to_camera_view(scene,scene.camera,Vector(point))
        assert .03<screen.x<.97 and .03<screen.y<.97 and screen.z>0,(name,tuple(screen))
    graph=bpy.context.evaluated_depsgraph_get()
    def tree(obj):
        evaluated=obj.evaluated_get(graph); mesh=evaluated.to_mesh()
        result=BVHTree.FromPolygons([evaluated.matrix_world@v.co for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons])
        evaluated.to_mesh_clear(); return result
    obstacles=[tree(o) for o in bpy.data.objects if o.type=='MESH' and
               (o.name in ('TRAINING_BOARD','TRAINING_SURFACE') or '_PEG_' in o.name or o.get('role')=='peg_transfer_object')]
    for side in TROCARS:
        for part in ('SHAFT','JAW_-1','JAW_1'):
            tool=tree(bpy.data.objects[f'{side}_{part}'])
            assert not any(tool.overlap(obstacle) for obstacle in obstacles),(side,part)
    session=LiveSession(); task=session.interaction.task
    assert task.state=='READY'
    ticks=0
    def move(side,point,jaw):
        nonlocal ticks
        pose=inverse_contact(TROCARS[side],point,CONTACT_OFFSET)
        from dataclasses import replace
        target=as_target(side,replace(pose,jaw=jaw))
        desired=target.to_control(session.controller.neutral[side],LIMITS)
        last=None
        for _ in range(160):
            session.update_targets([target],.05); ticks+=1
            actual=session.controller.poses[side]
            assert session.collision.pair_gap(session.controller.poses)>=-1e-9
            held={owner:task.world.offsets[n] for n,owner in task.world.owners.items() if owner}
            assert all(session.collision.board_gap(s,p,held)>=-1e-9 for s,p in session.controller.poses.items())
            if all(abs(getattr(actual,k)-getattr(desired,k))<1e-7 for k in ('yaw','pitch','insertion','rotation','jaw')):
                break
            if last==actual and any(contact.startswith(side) for contact in session.collision.contacts):
                break  # A requested below-board/intersecting pose must not converge.
            last=actual
        else: raise AssertionError('Controller failed to converge')
        # Validate actual evaluated jaw/shaft vertices, not just the analytic proxies.
        for s in TROCARS:
            for part in ('SHAFT','JAW_-1','JAW_1'):
                obj=bpy.data.objects[f'{s}_{part}'].evaluated_get(bpy.context.evaluated_depsgraph_get())
                mesh=obj.to_mesh()
                assert min((obj.matrix_world@v.co).z for v in mesh.vertices)>=session.collision.settings.board_height-1e-7,(s,part,'board penetration')
                obj.to_mesh_clear()
    def move_object(name,side,point,jaw):
        offset=task.world.offsets.get(name,(0,0,0))
        move(side,tuple(p-o for p,o in zip(point,offset)),jaw)
    for name,source in SOURCES.items():
        move('LEFT',source,1); move('LEFT',source,0)
        assert task.world.owners[name]=='LEFT',(name,'pickup',task.world.owners)
        move_object(name,'LEFT',(source[0],source[1],source[2]+.025),0)
        move_object(name,'LEFT',HANDOFF,0)
        point=tuple(task.world.positions[name])
        # Approach the near side of the ring, not through the donor jaw volume.
        receiver=(point[0],point[1]-.006,point[2]-.003)
        move('RIGHT',receiver,1); move('RIGHT',receiver,0)
        if name not in task.pending:
            from lapsim_ai.simulator.collision import proxies
            print('HANDOFF_DIAGNOSTIC',name,point,task.world.positions[name],
                  {s:(vars(p),proxies(TROCARS[s],p,session.collision.settings)[1]) for s,p in session.controller.poses.items()},
                  session.collision.contacts)
        assert task.world.owners[name]=='LEFT',(name,'premature handoff')
        move_object(name,'LEFT',HANDOFF,1)
        assert task.world.owners[name]=='RIGHT',(name,'handoff',task.pending)
        target=TARGETS[name]
        move_object(name,'RIGHT',(target[0],target[1],target[2]+.025),0)
        move_object(name,'RIGHT',target,0); move_object(name,'RIGHT',target,1)
        assert task.placements[name]=='CORRECT',(name,'placement',task.world.positions[name])
        for side in TROCARS: baseline.check_instrument(side); check_jaws(side)
    assert task.state=='COMPLETE' and task.completed==6
    session.controller.paused=True
    elapsed=task.elapsed
    session.update_targets([],.1)
    assert task.elapsed==elapsed
    session.reset()
    assert task.state=='READY' and task.completed==0 and task.elapsed==0 and not task.pending
    assert all(owner is None for owner in task.world.owners.values())
    assert task.world.positions==task.world.homes
    assert session.controller.poses==session.controller.neutral
    assert session.controller.paused
    assert not session.collision.contacts
    keys=check_modal_events()
    build_peg_transfer()
    assert fingerprint()==initial,'Regeneration differs'
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==value for p,value in old.items())
    polygons=sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH')
    report=dict(status='PASS',pure_tests='see unittest output',full_trial='6 pickups, lifts, donor/receiver handoffs, placements, COMPLETE, reset',
                controller_ticks=ticks,critical_reach_points=len(targets),joint_range_margin=.10,
                pivot_error_metres=baseline.maximum_pivot_error,pivot_tolerance_metres=baseline.PIVOT_TOLERANCE,
                initial_intersections='NONE',camera_framing='PASS',keyboard_bindings=keys,
                collision_checks='Every trial tick: capsules + held-ring board clearance; evaluated tool vertices at each move; reset clears contacts',
                deterministic_scene_sha256=initial,previous_scene_hashes_preserved={p.name:h for p,h in old.items()},base_mesh_polygons=polygons)
    out=ROOT/'outputs/peg_transfer';out.mkdir(parents=True,exist_ok=True)
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PEG_TRANSFER_VALIDATION',json.dumps(report))


if __name__=='__main__': main()
