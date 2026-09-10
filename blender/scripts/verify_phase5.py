"""Real Blender modal adapter with synthetic camera frames; no camera/GUI claims."""
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'blender/scripts')]
import bpy
from live_rig import LiveSession
from webcam_ui import LAPSIM_OT_webcam
from lapsim_ai.control.public_runtime import PublicRuntime
from lapsim_ai.control.public_setup import GuidedSetup
from lapsim_ai.vision.stabilization import HandStabilizer
from lapsim_ai.control.hand_mapping import HandMapper
from test_public_setup import pair, BOUNDS
from unittest.mock import patch
from dataclasses import asdict

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/scenes/lapsim_ai_peg_transfer.blend'))
session=LiveSession()
camera_before=tuple(v for row in bpy.context.scene.camera.matrix_world for v in row)
poses_before=session.controller.poses
positions_before=dict(session.interaction.world.positions)
setup,stabilizer=GuidedSetup(),HandStabilizer()
now=time.perf_counter()
for pinch in (.01,.2,.01):
    for _ in range(43):
        now+=.1
        status=setup.update(pair(pinch),BOUNDS,now,stabilizer)
        stable=stabilizer.update(pair(pinch),now)
assert setup.ready
calibrations={s:h.calibration for s,h in stabilizer.hands.items()}

area=SimpleNamespace(type='VIEW_3D',tag_redraw=lambda:None)
window=SimpleNamespace(screen=SimpleNamespace(areas=[area]))
runtime=PublicRuntime()
worker=SimpleNamespace(frame=None,setup={},calibrated=dict(LEFT=True,RIGHT=True),inform=Mock())
# Invoke the real modal method on a plain carrier; no UI event loop required.
op=SimpleNamespace(_closed=False,_area=area,_window=window,session=session,worker=worker,
    runtime=runtime,startup=runtime.startup,_last=now,_last_notice=None,report=Mock())
clock=now

def tick(hands=None):
    global clock
    clock+=.1
    hands=pair() if hands is None else hands
    status=setup.update(hands,BOUNDS,clock,stabilizer)
    stable=stabilizer.update(hands,clock)
    targets=[HandMapper().map(s) for s in stable.values()]
    worker.frame=(clock,targets,{})
    worker.setup=asdict(status)
    worker.poll=lambda *args:targets
    with patch('webcam_ui.time.perf_counter',return_value=clock):
        outcome=LAPSIM_OT_webcam.modal(op,None,SimpleNamespace(type='TIMER'))
    assert outcome=={'RUNNING_MODAL'}

def key(name):
    outcome=LAPSIM_OT_webcam.modal(op,None,SimpleNamespace(type=name,value='PRESS',is_repeat=False))
    assert outcome=={'RUNNING_MODAL'}

for _ in range(25):
    tick()
    assert session.controller.poses==poses_before
    assert session.interaction.world.positions==positions_before
    assert not session.interaction.telemetry.events
assert op.runtime.state=='LIVE_COUNTDOWN'
tick([])
assert op.startup.deadline is None
for _ in range(52): tick()
assert op.startup.started and not session.controller.paused
# Missing hand holds, returns via existing rate bounds, and never recalibrates.
held=session.controller.poses['RIGHT']
tick(pair()[:1])
assert op.runtime.state=='TRACKING_LOST'
assert session.controller.poses['RIGHT']==held
tick()
assert op.runtime.state=='LIVE'
assert calibrations=={s:h.calibration for s,h in stabilizer.hands.items()}
# Exercise paused timing after a session has begun (pure timing fixture).
session.interaction.task.state='RUNNING'
tick()
key('SPACE'); tick()
assert op.runtime.state=='PAUSED'
active_before=session.interaction.telemetry.active
def receive_notice(state,message,action=None):
    if action=='recenter':
        assert setup.recenter(paused=True,manipulating=False)
worker.inform.side_effect=receive_notice
key('BACK_SPACE')
assert worker.inform.call_args.args[-1]=='recenter'
assert not op.startup.started
for pinch in (.01,.2,.01):
    for _ in range(43):
        tick(pair(pinch))
        assert session.interaction.telemetry.active==active_before
for _ in range(80):
    if op.startup.started:
        break
    tick()
    assert session.interaction.telemetry.active==active_before
assert op.startup.started, 'Recenter did not return to LIVE within the expected gate duration'
tick()
assert session.interaction.telemetry.paused_seconds>10
assert session.interaction.telemetry.active-active_before<.11
# Reset/retry is separate from calibration and clears task/telemetry history.
key('R')
assert session.interaction.task.state=='READY'
assert session.controller.paused
assert not session.interaction.telemetry.events
assert 'peg_session_result' not in bpy.context.scene
assert calibrations=={s:h.calibration for s,h in stabilizer.hands.items()}
assert tuple(v for row in bpy.context.scene.camera.matrix_world for v in row)==camera_before
assert not op.report.called
print('PHASE5 PASS: guided pair capture -> modal countdown -> loss/restart -> LIVE; countdown task/telemetry isolation; recovery; pause; recenter hook; retry; unchanged camera matrix')
