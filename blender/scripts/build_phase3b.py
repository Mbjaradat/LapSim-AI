"""Rebuild the SPL-derived operative environment, without saving older scenes."""
from pathlib import Path
import hashlib
import json
import math
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'src'), str(Path(__file__).resolve().parent)]
import bpy
import bmesh
from mathutils import Matrix, Vector
from build_phase3 import build_phase3, move_to, sphere
from scene import material, aim, empty
from phase3b_config import *
from spl_assets import read_mesh


def collection(name, parent):
    result = bpy.data.collections.new(name)
    parent.children.link(result)
    return result


def mesh_object(name, vertices, faces, target, mat=None):
    mesh = bpy.data.meshes.new(name+'_MESH')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    if mat: mesh.materials.append(mat)
    for face in mesh.polygons: face.use_smooth = True
    obj['role'] = 'static_anatomy'
    return obj


def apply(obj, modifier):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def tissue(name, color, roughness, detail=900):
    mat = material(name, color, roughness=roughness)
    nodes = mat.node_tree.nodes; links = mat.node_tree.links
    shader = nodes['Principled BSDF']
    shader.inputs['Coat Weight'].default_value = .12
    shader.inputs['Coat Roughness'].default_value = .3
    tex = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = detail
    noise.inputs['Detail'].default_value = 2
    links.new(tex.outputs['Object'], noise.inputs['Vector'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .12
    bump.inputs['Distance'].default_value = .00025
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    return mat


def tube(name, points, radius, target, mat):
    curve = bpy.data.curves.new(name+'_CURVE', 'CURVE')
    curve.dimensions = '3D'; curve.resolution_u = 10
    curve.bevel_depth = radius; curve.bevel_resolution = 3; curve.use_fill_caps = True
    spline = curve.splines.new('BEZIER'); spline.bezier_points.add(len(points)-1)
    for bp, point in zip(spline.bezier_points, points):
        bp.co = point; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, curve); target.objects.link(obj)
    curve.materials.append(mat)
    obj['role'] = 'static_anatomy'; obj['provenance'] = 'original procedural approximation'
    return obj


def build_phase3b():
    scene, workspace = build_phase3()
    # Reuse the checkpoint builder in memory only; keep its saved file untouched.
    for obj in list(bpy.data.collections['LAPSIM_ANATOMY'].objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for obj in list(bpy.data.objects):
        if obj.name.startswith('WORKSPACE_') or obj.name == 'GALLBLADDER_TARGET':
            bpy.data.objects.remove(obj, do_unlink=True)
    training = bpy.data.collections['LAPSIM_INTERACTABLES']
    training.name = 'LAPSIM_TRAINING_OBJECTS'
    training.hide_render = training.hide_viewport = True
    # Retain the validated grasp implementation in Phase 3A; hidden beads cannot be grabbed here.
    scene['phase3_interactions'] = False
    anatomy = bpy.data.collections['LAPSIM_ANATOMY']
    liver_col = collection('LIVER', anatomy); gb_col = collection('GALLBLADDER', anatomy)
    biliary = collection('BILIARY', anatomy); arterial = collection('ARTERIAL', anatomy)
    interaction = collection('LAPSIM_INTERACTION', scene.collection)
    liver_mat = tissue('Liver capsule | procedural', (.19, .028, .018), .37)
    gb_mat = tissue('Gallbladder serosa | procedural', (.14, .19, .055), .32)
    duct_mat = tissue('Biliary ochre | procedural', (.46, .33, .12), .4)
    artery_mat = tissue('Arterial red | procedural', (.38, .018, .025), .34)
    cavity_mat = tissue('Peritoneal tan rose | procedural', (.24, .12, .095), .55, 180)
    neck = Vector(workspace['center']) + Vector(NECK_OFFSET)
    # One common proper rotation (180 degrees about Z), scale and translation.
    matrix = Matrix.Translation(neck) @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Scale(SOURCE_SCALE, 4) @ Matrix.Translation(-Vector(SOURCE_NECK))
    source = ROOT/ASSET_FOLDER
    manifest = json.loads((source/'SOURCE.json').read_text(encoding='utf-8'))
    liver_verts = []; liver_faces = []
    for entry in manifest['assets']:
        path = source/entry['local_source_filename']
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError(f'Asset checksum mismatch: {path.name}')
        verts, faces = read_mesh(path)
        verts = [matrix @ Vector(v) for v in verts]
        if 'Gallbladder' in path.name:
            gb = mesh_object('GALLBLADDER', verts, faces, gb_col, gb_mat)
        else:
            start = len(liver_verts)
            liver_verts.extend(verts)
            liver_faces.extend(tuple(i+start for i in face) for face in faces)
    liver = mesh_object('LIVER', liver_verts, liver_faces, liver_col, liver_mat)
    # Voxel union removes segmentation seams/internal faces; no anatomical claim for remeshed surface.
    bpy.context.view_layer.objects.active = liver
    liver.data.remesh_voxel_size = LIVER_VOXEL
    bpy.ops.object.voxel_remesh()
    smooth = liver.modifiers.new('Capsule smoothing', 'SMOOTH')
    smooth.factor = 1; smooth.iterations = LIVER_SMOOTH_ITERATIONS; apply(liver, smooth)
    for obj, ratio in ((liver, LIVER_DECIMATE), (gb, GB_DECIMATE)):
        if obj == gb:
            mod = obj.modifiers.new('Segmentation smoothing', 'SMOOTH')
            mod.factor = .7; mod.iterations = 3; apply(obj, mod)
        mod = obj.modifiers.new('Realtime simplification', 'DECIMATE'); mod.ratio = ratio; apply(obj, mod)
        for face in obj.data.polygons: face.use_smooth = True
        obj['provenance'] = ASSET_FOLDER+'/SOURCE.json'
        obj['source_to_world'] = json.dumps([list(row) for row in matrix])
        obj['modified_source'] = True
    def offset(point, delta): return tuple(Vector(point)+Vector(delta))
    # Original local topology: neck -> cystic duct -> CHD/CBD junction;
    # adjacent hepatic arterial branch supplies the cystic artery. No clinical fidelity claim.
    junction = offset(neck, (.027, -.004, -.012))
    duct_mid = offset(neck, (.013, -.009, -.008))
    tube('CYSTIC_DUCT', [neck, duct_mid, junction], .0021, biliary, duct_mat)
    tube('COMMON_HEPATIC_DUCT', [offset(junction, (0,.020,.030)), offset(junction, (0,.009,.016)), junction], .0028, biliary, duct_mat)
    tube('COMMON_BILE_DUCT', [junction, offset(junction, (.003,-.004,-.016)), offset(junction, (.010,.010,-.042))], .003, biliary, duct_mat)
    artery_origin = offset(junction, (.007,.002,.010))
    artery_mid = offset(neck, (.013,-.006,.006))
    tube('RIGHT_HEPATIC_ARTERY', [offset(artery_origin,(.015,.010,-.016)), artery_origin, offset(artery_origin,(-.008,.024,.014))], .0022, arterial, artery_mat)
    tube('CYSTIC_ARTERY', [artery_origin, artery_mid, offset(neck,(-.006,-.003,.003))], .0013, arterial, artery_mat)
    body = matrix @ Vector(SOURCE_BODY); fundus = matrix @ Vector(SOURCE_FUNDUS)
    # Narrow connective bed lies behind the source gallbladder, blending toward liver.
    bed_mat = tissue('Gallbladder bed | procedural', (.29,.12,.075), .46)
    tube('GALLBLADDER_BED', [offset(fundus,(.002,.007,.003)), offset(body,(.003,.008,.004)), offset(neck,(0,.005,.003))], .006, gb_col, bed_mat)
    targets = {'GALLBLADDER_NECK':tuple(neck), 'CYSTIC_DUCT_TARGET':duct_mid, 'CYSTIC_ARTERY_TARGET':artery_mid}
    for name, point in {'GALLBLADDER_ANCHOR':offset(body,(0,.008,.004)), 'GALLBLADDER_FUNDUS_GRASP_REGION':fundus,
                        'GALLBLADDER_BODY_GRASP_REGION':body, **targets}.items():
        obj = move_to(empty(name, location=point), interaction)
        obj.empty_display_size = .003; obj['role'] = 'future_region_only'
    # Curved inner shell, open on the scope side. No flat floor or rectangular walls.
    vertices = []; faces = []
    for row in range(CAVITY_RINGS+1):
        theta = .015 + (math.pi*.78-.015)*row/CAVITY_RINGS
        for col in range(CAVITY_SEGMENTS):
            phi = 2*math.pi*col/CAVITY_SEGMENTS
            x = CAVITY_RADII[0]*math.sin(theta)*math.cos(phi)
            y = CAVITY_RADII[1]*math.cos(theta)
            z = CAVITY_RADII[2]*math.sin(theta)*math.sin(phi)
            # Low-amplitude original folds, no texture imports.
            z += .003*math.sin(phi*7 + theta*3)*math.sin(theta)**2
            vertices.append(offset(CAVITY_CENTER, (x,y,z)))
    for row in range(CAVITY_RINGS):
        for col in range(CAVITY_SEGMENTS):
            a=row*CAVITY_SEGMENTS+col; b=row*CAVITY_SEGMENTS+(col+1)%CAVITY_SEGMENTS
            faces.append((a,b,b+CAVITY_SEGMENTS,a+CAVITY_SEGMENTS))
    cavity = mesh_object('PERITONEAL_CAVITY', vertices, faces, bpy.data.collections['LAPSIM_ENVIRONMENT'], cavity_mat)
    cavity['provenance'] = 'original procedural approximation'
    scene.camera.location = CAMERA_LOCATION; aim(scene.camera, CAMERA_AIM)
    scene.camera.data.lens = CAMERA_LENS
    scene.camera.data.clip_start = .003
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            if obj.name == 'Scope light':
                obj.location = offset(CAMERA_LOCATION,(-.025,.035,.025)); obj.data.energy = 5
            else:
                obj.location = offset(CAMERA_LOCATION,(.045,.065,.055)); obj.data.energy = 3
            obj.data.size = .085; aim(obj, neck)
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.12,.08,.065,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .12
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 24
    # Material preview with scene lighting uses Eevee; avoids progressive Cycles live rendering.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.shading.type = 'MATERIAL'; space.shading.use_scene_lights = True; space.shading.use_scene_world = True
                space.region_3d.view_camera_zoom = 0
    scene['prototype'] = 'LapSim-AI Phase 3B | SPL-derived + original approximations | unvalidated educational/research prototype'
    scene['phase3b_targets'] = json.dumps(targets, sort_keys=True)
    report = dict(source_to_world=[list(row) for row in matrix], targets=targets,
                  organ_polygons={o.name:len(o.data.polygons) for o in (liver,gb)},
                  source_triangles=sum(e['triangles'] for e in manifest['assets']),
                  liver_voxel_metres=LIVER_VOXEL, liver_decimate=LIVER_DECIMATE, gallbladder_decimate=GB_DECIMATE,
                  measured_workspace=workspace, camera_location=CAMERA_LOCATION, camera_aim=CAMERA_AIM, camera_lens_mm=CAMERA_LENS)
    scene['phase3b_build'] = json.dumps(report, sort_keys=True)
    note = bpy.data.texts['START_HERE.txt']; note.clear()
    note.write('LapSim-AI Phase 3B — visual review pending\n'
               'Run blender/scripts/start_webcam.py in Text Editor; hover 3D Viewport, F3 > LapSim: Start Webcam Control.\n'
               'Use the existing webcam bridge/calibration procedure; both ready/visible hands trigger the 5-second countdown.\n'
               'Keyboard alternative: start_live.py, F3 > LapSim: Start Keyboard Control.\n'
               'Anatomy is static; named gallbladder grasp regions are preparation only. Beads/grasp tests remain in Phase 3A.\n'
               'Material Preview uses scene lights/world. Numpad 0 restores camera. See docs/phase3b.md.\n')
    legal = bpy.data.texts.new('THIRD_PARTY_ANATOMY_LICENSE.txt')
    legal.write(manifest['attribution']+'\n\n'+manifest['required_preface']+'\n\n'+(source/'LICENSE.txt').read_text(encoding='utf-8'))
    bpy.context.view_layer.update()
    return scene, report


def main():
    scene, report = build_phase3b()
    output = ROOT/'blender/scenes/lapsim_ai_phase3b.blend'
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    out = ROOT/'outputs/phase3b'; out.mkdir(parents=True, exist_ok=True)
    (out/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PHASE3B_BUILD', json.dumps({k:v for k,v in report.items() if k!='measured_workspace'}))
    if '--render' in sys.argv:
        scene.render.filepath = str(out/'preview.png')
        bpy.ops.render.render(write_still=True)


if __name__ == '__main__': main()
