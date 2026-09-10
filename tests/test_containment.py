"""Board/camera envelope, recovery and accepted-pose path checks; no GUI."""
import sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1]/'blender/scripts')]
import unittest
from unittest.mock import patch
from dataclasses import replace
from math import sqrt
from peg_config import BOARD_CENTER,BOARD_DIMENSIONS,BOARD_TOP,CAMERA_POSITION,CAMERA_TARGET,CAMERA_LENS,RING_RADIUS,RING_THICKNESS
from config import DEFAULTS,TROCARS,LIMITS,JAW_LENGTH
from lapsim_ai.simulator.containment import trainer_planes
from lapsim_ai.simulator.collision import CollisionConstraint,CollisionSettings,transform,proxies,add
from lapsim_ai.telemetry.session import SessionTelemetry
from lapsim_ai.simulator.tasks.peg_transfer import PegTransfer
from lapsim_ai.simulator.workspace import inverse_contact


def constraint():
    f=tuple(b-a for a,b in zip(CAMERA_POSITION,CAMERA_TARGET)); length=sqrt(sum(v*v for v in f)); f=tuple(v/length for v in f)
    ceiling=max(TROCARS[s][2]+transform(p,(0,0,-p.insertion))[2] for s,p in DEFAULTS.items())+2*JAW_LENGTH
    planes=trainer_planes(BOARD_CENTER,BOARD_DIMENSIONS,BOARD_TOP,ceiling,CAMERA_POSITION,f,(1,0,0),(0,-f[2],f[1]),36/(2*CAMERA_LENS),36/(2*CAMERA_LENS)*.75)
    return CollisionConstraint(TROCARS,LIMITS,CollisionSettings(workspace_planes=planes))


class ContainmentTests(unittest.TestCase):
    def test_six_boundaries_both_sides_jaws_and_held_ring(self):
        goals={'left':dict(yaw=35,insertion=.26),'right':dict(yaw=-35,insertion=.26),
               'front':dict(pitch=-25),'back':dict(pitch=25,insertion=.26),
               'floor':dict(insertion=.28),'upper':dict(insertion=.12)}
        for side in TROCARS:
            for name,changes in goals.items():
                with self.subTest(side=side,boundary=name):
                    c=constraint(); poses=dict(DEFAULTS); held={side:(.002,0,-.002)}
                    goal=replace(poses[side],**changes,jaw=1,rotation=45)
                    self.assertLess(c.workspace_gap(side,goal,held),0)
                    # Isolate the volume unit under test; pair collisions remain
                    # enabled in the full Blender trial and existing collision tests.
                    with patch.object(c,'_pair_clear',return_value=True):
                        for _ in range(4):
                            poses=c.resolve(poses,{**poses,side:goal},held)
                            self.assertGreaterEqual(c.workspace_gap(side,poses[side],held),-1e-9)
                    self.assertNotEqual(poses[side],goal)

    def test_parallel_inward_and_no_fake_path_at_contact(self):
        c=constraint(); poses=dict(DEFAULTS)
        goal=replace(poses['LEFT'],yaw=10,insertion=.24)
        for _ in range(5): poses=c.resolve(poses,{**poses,'LEFT':goal})
        before=poses['LEFT']
        self.assertLess(c.workspace_gap('LEFT',before,{}),1e-6)
        telemetry=SessionTelemetry('test',1)
        def observe():
            tips={s:add(TROCARS[s],transform(p,(0,0,-p.insertion))) for s,p in poses.items()}
            telemetry.observe(dt=.03,paused=False,task_state='RUNNING',owners={'ring':None},placements={'ring':'SOURCE'},completed=0,tips=tips)
        observe()
        for _ in range(12):
            poses=c.resolve(poses,{**poses,'LEFT':goal}); observe()
        self.assertEqual(telemetry.paths['LEFT'],0)
        self.assertAlmostEqual(poses['LEFT'].yaw,before.yaw,places=5)
        slid=c.resolve(poses,{**poses,'LEFT':replace(poses['LEFT'],pitch=poses['LEFT'].pitch+2)})
        self.assertGreater(slid['LEFT'].pitch,poses['LEFT'].pitch+1)
        inward=c.resolve(slid,{**slid,'LEFT':replace(slid['LEFT'],yaw=slid['LEFT'].yaw-3)})
        self.assertLess(inward['LEFT'].yaw,slid['LEFT'].yaw-2)
        self.assertGreaterEqual(c.workspace_gap('LEFT',inward['LEFT'],{}),-1e-9)
        c.reset(); self.assertFalse(c.contacts)

    def test_camera_planes_and_ring_extent_not_just_tip(self):
        c=constraint(); pose=DEFAULTS['LEFT']
        self.assertEqual(len(c.settings.workspace_planes),10)
        self.assertGreaterEqual(c.workspace_gap('LEFT',pose,{}),0)
        # Offset puts a carried ring outside despite a contained contact point.
        self.assertLess(c.workspace_gap('LEFT',pose,{'LEFT':(-.06,0,0)}),0)
        for name,n,_ in c.settings.workspace_planes:
            self.assertAlmostEqual(sum(v*v for v in n),1)

    def test_grasp_release_near_edge(self):
        c=constraint(); poses=dict(DEFAULTS)
        source=(-.044,.042,-.110)  # Outer ring edge 1.9 mm inside board footprint.
        target=(-.036,.042,-.110)
        task=PegTransfer({'ring':source},{'ring':target},seat_height=-.110)
        for point,jaw in ((source,1),(source,0),(target,0),(target,1)):
            offset=task.world.offsets.get('ring',(0,0,0))
            contact=tuple(p-o for p,o in zip(point,offset))
            goal=replace(inverse_contact(TROCARS['LEFT'],contact,.0126),jaw=jaw)
            for _ in range(4):
                held={owner:task.world.offsets[name] for name,owner in task.world.owners.items() if owner}
                poses=c.resolve(poses,{**poses,'LEFT':goal},held)
                hands={s:(proxies(TROCARS[s],p,c.settings)[1],p.jaw) for s,p in poses.items()}
                task.update(hands,.03)
            if jaw==0:
                self.assertEqual(task.world.owners['ring'],'LEFT')
                self.assertGreaterEqual(c.workspace_gap('LEFT',poses['LEFT'],{'LEFT':task.world.offsets['ring']}),-1e-9)
        self.assertEqual(task.placements['ring'],'CORRECT')


if __name__=='__main__': unittest.main()
