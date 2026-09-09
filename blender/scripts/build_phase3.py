"""Original procedural Phase 3 scene. No downloads, physics or Phase 1 saves."""
from pathlib import Path
import sys
import math
import json

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'src'),str(Path(__file__).resolve().parent)]
import bpy
from mathutils import Vector
from build_phase1b import build_live_scene
from scene import material, aim, empty
from config import TROCARS, DEFAULTS, LIMITS
from phase3_config import *
from lapsim_ai.simulator.workspace import characterize, reachable, inverse_contact


def move_to(obj, collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def sphere(name, location, radii, mat, collection):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=1,location=location)
    obj=bpy.context.object
    obj.name=name
    for vertex in obj.data.vertices:
        vertex.co=Vector(tuple(v*r for v,r in zip(vertex.co,radii)))
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth=True
    return move_to(obj,collection)


def gallbladder(location, mat, collection):
    # Original pear profile, lathed along +Y: rounded fundus, body, narrow neck.
    profile=((.04,.005),(.12,.009),(.25,.012),(.42,.011),(.60,.009),
             (.76,.006),(.88,.0035),(1,.0025))
    verts=[]
    segments=32
    for t,radius in profile:
        for i in range(segments):
            theta=2*math.pi*i/segments
            verts.append((radius*math.cos(theta),t*GB_LENGTH,
                          radius*.8*math.sin(theta)+.008*t))
    faces=[]
    pole=len(verts)
    verts.append((0,0,0))
    for i in range(segments):
        faces.append((pole,(i+1)%segments,i))
    for row in range(len(profile)-1):
        for i in range(segments):
            a=row*segments+i;b=row*segments+(i+1)%segments
            faces.append((a,b,b+segments,a+segments))
    faces.append(tuple(range((len(profile)-1)*segments,pole)))
    mesh=bpy.data.meshes.new('GALLBLADDER_PROCEDURAL_MESH')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new('GALLBLADDER',mesh)
    collection.objects.link(obj)
    obj.location=location
    mesh.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth=True
    return obj


def debug_cloud(name, points, color, collection):
    mesh=bpy.data.meshes.new(name+'_POINTS')
    # Tiny octahedra make the optional point cloud visible in ordinary object mode.
    vertices=[];faces=[]
    offsets=((.001,0,0),(-.001,0,0),(0,.001,0),(0,-.001,0),(0,0,.001),(0,0,-.001))
    triangles=((0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5))
    for point in points:
        start=len(vertices)
        vertices.extend(shifted(point,offset) for offset in offsets)
        faces.extend(tuple(start+i for i in face) for face in triangles)
    mesh.from_pydata(vertices,[],faces)
    mesh.materials.append(material(name+'_COLOR',color,emission=.2))
    obj=bpy.data.objects.new(name,mesh)
    collection.objects.link(obj)
    obj.color=(*color,1)
    obj.show_in_front=True
    obj.hide_render=True
    return obj


def build_phase3():
    # Characterize first, before creating or positioning anatomy.
    workspace=characterize(TROCARS,DEFAULTS,LIMITS,CONTACT_OFFSET,
                           WORKSPACE_SAMPLES,WORKSPACE_GRID,WORKSPACE_MARGIN)
    center=workspace['center']
    targets={name:shifted(center,offset) for name,offset in TOKEN_OFFSETS.items()}
    targets['GALLBLADDER_TARGET']=shifted(center,GB_OFFSET)
    for name,target in targets.items():
        if not all(reachable(p,target,LIMITS,CONTACT_OFFSET,WORKSPACE_MARGIN) for p in TROCARS.values()):
            raise ValueError(f'{name} outside useful bimanual workspace')
    scene=build_live_scene()
    collections={name:bpy.data.collections.new(name) for name in
                 ('LAPSIM_ENVIRONMENT','LAPSIM_ANATOMY','LAPSIM_INTERACTABLES','LAPSIM_INSTRUMENTS','LAPSIM_DEBUG')}
    for collection in collections.values():
        scene.collection.children.link(collection)
    for obj in list(bpy.data.objects):
        if obj.name.startswith('GRID_'):
            bpy.data.objects.remove(obj,do_unlink=True)
        else:
            move_to(obj,collections['LAPSIM_INSTRUMENTS'] if obj.name.startswith(('LEFT_','RIGHT_'))
                    else collections['LAPSIM_ENVIRONMENT'])
    liver_mat=material('Phase3 liver ochre red',(.29,.055,.035),roughness=.55)
    gall_mat=material('Phase3 gallbladder olive',(.18,.36,.07),roughness=.42)
    token_mat=material('Phase3 training beads ivory',(.9,.85,.48),roughness=.35)
    liver=sphere('LIVER',shifted(center,LIVER_OFFSET),LIVER_RADII,liver_mat,collections['LAPSIM_ANATOMY'])
    # Broad asymmetric lobe mass, original analytic deformation; not anatomical data.
    for vertex in liver.data.vertices:
        x,y,z=vertex.co
        vertex.co.y=y*(1+.22*x/LIVER_RADII[0])
        vertex.co.z=z*(.82+.18*(1-x/LIVER_RADII[0])/2)+.008*x/LIVER_RADII[0]
    liver['role']='static_anatomy'
    gb=gallbladder(targets['GALLBLADDER_TARGET'],gall_mat,collections['LAPSIM_ANATOMY'])
    gb['role']='static_anatomy'
    anchor=move_to(empty('GALLBLADDER_ANCHOR',location=shifted(gb.location,(0,GB_LENGTH,.008))),collections['LAPSIM_ANATOMY'])
    anchor.empty_display_size=.003
    # Short original continuation/attachment, not a full biliary tree.
    duct=sphere('CYSTIC_DUCT_APPROXIMATION',shifted(anchor.location,(0,.006,-.002)),(.003,.008,.003),gall_mat,collections['LAPSIM_ANATOMY'])
    duct['role']='static_anatomy'
    target=move_to(empty('GALLBLADDER_TARGET',location=targets['GALLBLADDER_TARGET']),collections['LAPSIM_DEBUG'])
    target.empty_display_size=.005
    for name in TOKEN_OFFSETS:
        obj=sphere(name,targets[name],(TOKEN_RADIUS,)*3,token_mat,collections['LAPSIM_INTERACTABLES'])
        obj['role']='graspable_training_object'
        obj['grasp_home']=list(targets[name])
        obj['grasp_owner']=''
    debug=collections['LAPSIM_DEBUG']
    for side,color in (('LEFT',(.1,.7,1)),('RIGHT',(1,.4,.1))):
        debug_cloud(side+'_REACH',workspace['clouds'][side],color,debug)
    debug_cloud('SHARED_COMFORTABLE_REACH',workspace['shared'],(.1,1,.2),debug)
    debug.hide_viewport=True
    debug.hide_render=True
    cavity=bpy.data.materials['Cavity charcoal']
    cavity.diffuse_color=(.045,.025,.028,1)
    cavity.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=cavity.diffuse_color
    aim(scene.camera,shifted(center,(0,.025,-.014)))
    # Retain the validated perspective/lens and instrument system; only aim at the field.
    for obj in collections['LAPSIM_ENVIRONMENT'].objects:
        if obj.type=='LIGHT':
            aim(obj,center)
    scene['prototype']='LapSim-AI Phase 3 | original procedural environment | awaiting manual validation'
    scene['phase3_interactions']=True
    scene['control_mode']='Keyboard or Webcam via existing entry scripts'
    report={key:value for key,value in workspace.items() if key not in ('clouds','shared')}
    report['shared_points']=len(workspace['shared'])
    report['targets']=targets
    report['target_controls']={name:{side:vars(inverse_contact(p,point,CONTACT_OFFSET)) for side,p in TROCARS.items()}
                               for name,point in targets.items()}
    scene['phase3_workspace']=json.dumps(report,sort_keys=True)
    note=bpy.data.texts['START_HERE.txt']
    note.clear()
    note.write('LapSim-AI Phase 3 — manual validation pending\n'
               'Run blender/scripts/start_webcam.py or start_live.py in the Text Editor.\n'
               'Start the chosen mode with F3 in a 3D Viewport. Webcam auto-starts after calibration and countdown.\n'
               'Close jaws near an ivory bead to grasp; open to release. R resets poses and beads.\n'
               'Liver/gallbladder are STATIC original approximations; no tissue physics or retraction.\n'
               'See docs/phase3.md for workspace, provenance, controls and manual checks.\n')
    bpy.context.view_layer.update()
    return scene,report


def main():
    scene,report=build_phase3()
    output=ROOT/'blender/scenes/lapsim_ai_phase3.blend'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    report_dir=ROOT/'outputs/phase3'
    report_dir.mkdir(parents=True,exist_ok=True)
    (report_dir/'workspace.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PHASE3_SCENE_SAVED',output)
    print('PHASE3_WORKSPACE',json.dumps(report))


if __name__=='__main__':
    main()
