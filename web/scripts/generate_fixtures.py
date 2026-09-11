"""Read-only fixture generator. Run with native Python from repository root."""
from pathlib import Path
import sys,json,math
from dataclasses import asdict,replace
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'blender/scripts')]
from config import TROCARS,DEFAULTS,LIMITS
from peg_config import SOURCES,TARGETS,BOARD_CENTER,BOARD_DIMENSIONS,BOARD_TOP,CAMERA_POSITION,CAMERA_TARGET
from lapsim_ai.control.instrument import InstrumentControl
from lapsim_ai.control.hand_mapping import HandMapper
from lapsim_ai.simulator.collision import CollisionConstraint,CollisionSettings,proxies,transform
from lapsim_ai.simulator.containment import trainer_planes
from lapsim_ai.simulator.tasks.peg_transfer import PegTransfer
from lapsim_ai.telemetry.session import SessionTelemetry
from lapsim_ai.vision.hand_state import extract_hand_state
from lapsim_ai.vision.stabilization import HandStabilizer
from lapsim_ai.control.public_setup import GuidedSetup
from test_palm_roll import PALM
from types import SimpleNamespace

def unit(v):
    n=math.sqrt(sum(x*x for x in v));return tuple(x/n for x in v)
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
forward=unit(tuple(b-a for a,b in zip(CAMERA_POSITION,CAMERA_TARGET)));right=unit(cross(forward,(0,0,1)));up=cross(right,forward)
ceiling=max(TROCARS[s][2]+transform(p,(0,0,-p.insertion))[2] for s,p in DEFAULTS.items())+.036
planes=trainer_planes(BOARD_CENTER,BOARD_DIMENSIONS,BOARD_TOP,ceiling,CAMERA_POSITION,forward,right,up,36/96,36/96*.75)
cfg=CollisionSettings(workspace_planes=planes)
result={'reference':'922fdc0','planes':planes,'poses':[],'collisions':[],'task':[],'tracking':[]}
for side in TROCARS:
    for values in [(-18,12,.2,0,.5),(-30,20,.25,70,.9),(30,-20,.14,-130,.1),(0,0,.28,180,1)]:
        pose=InstrumentControl(*values);segs,contact=proxies(TROCARS[side],pose,cfg)
        result['poses'].append(dict(side=side,pose=asdict(pose),segments=segs,contact=contact,rotated=transform(pose,(.01,.02,-.03))))
for y,p,d,r,j in [(-35,25,.28,0,1),(35,-25,.28,90,0),(-20,15,.27,40,.2),(0,0,.12,0,.5)]:
    proposed={s:InstrumentControl(y if s=='LEFT' else -y,p,d,r,j) for s in TROCARS}
    held={'LEFT':(.001,-.002,.0005)}
    constraint=CollisionConstraint(TROCARS,LIMITS,cfg)
    accepted=constraint.resolve(DEFAULTS,proposed,held)
    result['collisions'].append(dict(previous={s:asdict(p) for s,p in DEFAULTS.items()},proposed={s:asdict(p) for s,p in proposed.items()},held=held,accepted={s:asdict(p) for s,p in accepted.items()},pair_gap=constraint.pair_gap(accepted),board={s:constraint.board_gap(s,p,held) for s,p in accepted.items()},workspace={s:constraint.workspace_gap(s,p,held) for s,p in accepted.items()}))
# Real deterministic task transitions: wrong/drop recovery and six handoffs.
task=PegTransfer(SOURCES,TARGETS,seat_height=-.110);tele=SessionTelemetry('peg_transfer',6)
def step(hands,paused=False,dt=.1):
    if not paused:task.update(hands,dt)
    tips={s:tuple(hands.get(s,((0,0,0),1))[0]) for s in TROCARS}
    tele.observe(dt=dt,paused=paused,task_state=task.state,owners=task.world.owners,placements=task.placements,completed=task.completed,tips=tips)
    result['task'].append(dict(hands=hands,paused=paused,dt=dt,positions=dict(task.world.positions),owners=dict(task.world.owners),placements=dict(task.placements),state=task.state,counts=dict(tele.counts),paths=dict(tele.paths),active=tele.active))
for name,source in SOURCES.items():
    step({'LEFT':(source,1)});step({'LEFT':(source,0)})
    if name=='RING_1':
        step({'LEFT':(TARGETS['RING_2'],0)});step({'LEFT':(TARGETS['RING_2'],1)})
        step({'LEFT':(TARGETS['RING_2'],0)})
        step({'LEFT':((0,.01,-.08),0)});step({'LEFT':((0,.01,-.08),1)})
        p=task.world.positions[name];step({'LEFT':(p,1)});step({'LEFT':(p,0)})
    point=(0,.042,-.08);step({'LEFT':(point,0),'RIGHT':(point,1)})
    step({'LEFT':(point,0),'RIGHT':(point,0)})
    step({'LEFT':(point,1),'RIGHT':(point,0)})
    if name=='RING_2':step({'RIGHT':(point,0)},paused=True,dt=2)
    step({'RIGHT':(TARGETS[name],0)});step({'RIGHT':(TARGETS[name],1)})
result['telemetry_result']=tele.result
# Extract exactly the native synthetic geometry, then run guided setup/filter.
def landmarks(side,pinch,shift=0):
    palm=dict(zip((0,5,9,13,17),PALM));points=[]
    for i in range(21):
        x,y,z=palm.get(i,(0,-.18,0))
        if i==4:x+=pinch
        points.append(dict(x=.5+x+(-.2 if side=='Left' else .2)+shift,y=.5+y,z=z))
    return points
engine=HandStabilizer();setup=GuidedSetup();now=0
for stage,pinch in [('neutral',.01),('open',.2),('closed',.01),('motion',.09)]:
    points={s:landmarks(s,pinch,.02 if stage=='motion' else 0) for s in ('Left','Right')}
    raw=[extract_hand_state([SimpleNamespace(**p) for p in points[s]],s,mirrored_input=False,image_aspect=1) for s in points]
    # Framing fixture independently specifies bounds to exercise native hold logic.
    bounds={s:(.1,.1,.9,.9) for s in points}
    snapshots=[]
    for i in range(42):
        now+=.1;status=setup.update(raw,bounds,now,engine);stable=engine.update(raw,now)
        if i in (0,8,18,28,38,41):snapshots.append(dict(tick=i,state=status.state,remaining=status.remaining,ready=status.ready,commands={s:asdict(HandMapper().map(h)) for s,h in stable.items()}))
    result['tracking'].append(dict(stage=stage,points=points,bounds=bounds,raw={h.handedness:asdict(h) for h in raw},snapshots=snapshots))
result['home']=setup.home
(ROOT/'web/fixtures/native.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print('Native fixtures generated:',len(result['poses']),'poses,',len(result['collisions']),'collision cases,',len(result['task']),'task/telemetry steps')
