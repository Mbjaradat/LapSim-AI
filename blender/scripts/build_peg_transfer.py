"""Original procedural peg trainer. Saves only lapsim_ai_peg_transfer.blend."""
from pathlib import Path
import sys
import json
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'src'), str(Path(__file__).resolve().parent)]
import bpy
from build_phase1b import build_live_scene
from build_phase3 import move_to
from scene import material, cube, cylinder, ring, aim
from config import TROCARS, DEFAULTS, LIMITS
from phase3_config import CONTACT_OFFSET
from peg_config import *
from lapsim_ai.simulator.workspace import characterize, reachable, inverse_contact


def label(name, body, location, size, mat, collection, parent=None):
    curve = bpy.data.curves.new(name+'_TEXT','FONT')
    curve.body = body; curve.size = size; curve.align_x = 'CENTER'
    obj = bpy.data.objects.new(name,curve); collection.objects.link(obj)
    obj.parent = parent; obj.location = location
    curve.materials.append(mat)
    return obj


def build_peg_transfer():
    workspace = characterize(TROCARS,DEFAULTS,LIMITS,CONTACT_OFFSET)
    critical = {**{'SOURCE_'+k:v for k,v in SOURCES.items()},
                **{'TARGET_'+k:v for k,v in TARGETS.items()}, 'HANDOFF':HANDOFF}
    for name,point in critical.items():
        for side,pivot in TROCARS.items():
            if not reachable(pivot,point,LIMITS,CONTACT_OFFSET,.10):
                raise ValueError(f'{name} outside comfortable {side} reach')
    scene = build_live_scene()
    collections = {}
    for name in ('LAPSIM_BOARD','LAPSIM_TRANSFER_OBJECTS','LAPSIM_INSTRUMENTS','LAPSIM_ENVIRONMENT'):
        col = bpy.data.collections.new(name); scene.collection.children.link(col); collections[name] = col
    for obj in list(bpy.data.objects):
        if obj.name.startswith(('WORKSPACE_','GRID_')):
            bpy.data.objects.remove(obj,do_unlink=True)
        else:
            move_to(obj,collections['LAPSIM_INSTRUMENTS' if obj.name.startswith(('LEFT_','RIGHT_')) else 'LAPSIM_ENVIRONMENT'])
    board_col = collections['LAPSIM_BOARD']; tokens = collections['LAPSIM_TRANSFER_OBJECTS']
    base_mat = material('Trainer ceramic slate',(.08,.12,.15),roughness=.52)
    top_mat = material('Trainer warm surface',(.085,.125,.15),roughness=.62)
    source_mat = material('Peg source',(.11,.26,.32),roughness=.45)
    target_mat = material('Peg target',(.55,.34,.12),roughness=.45)
    material('Peg complete',(.12,.46,.28),roughness=.4).use_fake_user = True
    peg_mat = material('Peg brushed titanium',(.32,.40,.43),metallic=.65,roughness=.3)
    ink = material('Trainer markings',(.045,.065,.075),roughness=.8)
    board_ink = material('Board lettering',(.65,.72,.74),roughness=.8)
    token_mat = material('Transfer ring ivory',(.82,.76,.55),roughness=.35)
    board = move_to(cube('TRAINING_BOARD',BOARD_CENTER,BOARD_DIMENSIONS,base_mat),board_col)
    surface = move_to(cube('TRAINING_SURFACE',(0,.042,BOARD_TOP-.0006),(.102,.082,.0012),top_mat),board_col)
    for obj in (board,surface): obj.modifiers[0].segments = 5
    for kind,positions,mat in (('SOURCE',SOURCES,source_mat),('TARGET',TARGETS,target_mat)):
        for name,(x,y,z) in positions.items():
            peg = move_to(cylinder(f'{kind}_PEG_{name}',(x,y,BOARD_TOP+PEG_HEIGHT/2),PEG_RADIUS,PEG_HEIGHT,peg_mat),board_col)
            bevel = peg.modifiers.new('Rounded peg cap','BEVEL'); bevel.width = .0007; bevel.segments = 3
            move_to(ring(f'{kind}_MARKER_{name}',(x,y,BOARD_TOP+.0003),.008,.00045,mat),board_col)
            label(f'{kind}_NUMBER_{name}',name[-1],(x,y-.011,BOARD_TOP+.0007),.0033,board_ink,board_col)
    for name,position in SOURCES.items():
        obj = move_to(ring(name,position,RING_RADIUS,RING_THICKNESS,token_mat),tokens)
        obj['role'] = 'peg_transfer_object'; obj['grasp_home'] = position
        obj['grasp_owner'] = ''; obj['placement'] = 'SOURCE'
        # A small integral number tab keeps the ring identity legible during handoff.
        move_to(cube(name+'_ID_TAB',(0,-.004,.0004),(.004,.003,.0012),token_mat,obj),tokens)
        label(name+'_ID',name[-1],(0,-.005,.0011),.0027,ink,tokens,obj)
    label('SOURCE_CAPTION','SOURCE',(-.025,.077,BOARD_TOP+.0007),.0032,board_ink,board_col)
    label('TARGET_CAPTION','TARGET',(.025,.077,BOARD_TOP+.0007),.0032,board_ink,board_col)
    label('TRAINER_TITLE','LAPSIM  /  PEG TRANSFER',(0,.003,BOARD_TOP+.0007),.0023,board_ink,board_col)
    # Subtle centre guide marks the handoff XY; actual transfer occurs above the pegs.
    move_to(ring('HANDOFF_GUIDE',(0,.042,BOARD_TOP+.0003),.004,.0003,source_mat),board_col)
    surround = material('Trainer surround',(.018,.026,.032),roughness=.8)
    move_to(cube('TRAINER_BACKDROP',(0,.045,BOARD_TOP-.014),(.26,.22,.012),surround),collections['LAPSIM_ENVIRONMENT'])
    scene.camera.location = CAMERA_POSITION; aim(scene.camera,CAMERA_TARGET)
    scene.camera.data.lens = CAMERA_LENS
    scene.camera.data.clip_start = .003
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            obj.location = (-.06,-.03,.08) if obj.name=='Scope light' else (.07,.07,.03)
            obj.data.energy = .9 if obj.name=='Scope light' else .5
            obj.data.size = .10; aim(obj,(0,.042,SEAT_HEIGHT))
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .15
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.shading.type = 'MATERIAL'; space.shading.use_scene_lights = True; space.shading.use_scene_world = True
                space.region_3d.view_camera_zoom = 0
    scene['peg_transfer_config'] = json.dumps(dict(sources=SOURCES,targets=TARGETS,seat_height=SEAT_HEIGHT),sort_keys=True)
    scene['prototype'] = 'LapSim-AI | Peg transfer educational engineering prototype | not clinically validated'
    scene['phase3_interactions'] = False
    from peg_interaction import PegInteraction
    PegInteraction()
    report = dict(critical=critical,workspace_center=workspace['center'],shared_points=len(workspace['shared']),
                  margin=.10,controls={name:{side:vars(inverse_contact(p,point,CONTACT_OFFSET)) for side,p in TROCARS.items()}
                                      for name,point in critical.items()})
    scene['peg_workspace'] = json.dumps(report,sort_keys=True)
    note = bpy.data.texts['START_HERE.txt']; note.clear()
    note.write('LAPSIM-AI / PEG TRANSFER\n'
               'Run blender/scripts/start_webcam.py, then hover the viewport: F3 > LapSim: Start Webcam Control.\n'
               'Calibrate each hand in preview (1/2, N/O/C); both ready hands start LIVE after 5 seconds.\n'
               'Close near a ring centre, lift above pegs, move to matching numbered target and open.\n'
               'Handoff: close the receiver near the held ring, then open donor.\n'
               'Blender R resets task + instruments and pauses webcam; Space resumes.\n'
               'Keyboard alternative: start_live.py; F3 > LapSim: Start Keyboard Control.\n'
               'Original procedural geometry. No scoring, anatomy, clinical validation or release packaging.\n')
    bpy.context.view_layer.update()
    return scene,report


if __name__ == '__main__':
    scene,report = build_peg_transfer()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/scenes/lapsim_ai_peg_transfer.blend'))
    out = ROOT/'outputs/peg_transfer'; out.mkdir(parents=True,exist_ok=True)
    (out/'workspace.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PEG_TRANSFER_BUILD',json.dumps(report))
    if '--render' in sys.argv:
        scene.render.filepath = str(out/'preview.png')
        bpy.ops.render.render(write_still=True)
