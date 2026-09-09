"""Analytic collision contracts, no Blender or physical simulation."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from dataclasses import replace
from lapsim_ai.simulator.collision import CollisionConstraint,proxies,segment_distance
from lapsim_ai.control.instrument import InstrumentControl,InstrumentLimits

PIVOTS={'LEFT':(-.085,0,.12),'RIGHT':(.085,0,.12)}
NEUTRAL={'LEFT':InstrumentControl(yaw=-18,pitch=12), 'RIGHT':InstrumentControl(yaw=18,pitch=12)}


class CollisionTests(unittest.TestCase):
    def test_segments(self):
        self.assertAlmostEqual(segment_distance((-1,0,0),(1,0,0),(0,-1,0),(0,1,0)),0)
        self.assertAlmostEqual(segment_distance((0,0,0),(1,0,0),(0,1,0),(1,1,0)),1)
        self.assertAlmostEqual(segment_distance((0,0,0),(0,0,0),(1,0,0),(1,0,0)),1)

    def test_board_jaws_ring_and_escape_sliding(self):
        c=CollisionConstraint(PIVOTS,InstrumentLimits()); poses=dict(NEUTRAL)
        held={'LEFT':(0,0,-.012)}
        for _ in range(10):
            poses=c.resolve(poses,{**poses,'LEFT':replace(poses['LEFT'],insertion=.28,jaw=1)},held)
        self.assertGreaterEqual(c.board_gap('LEFT',poses['LEFT'],held),-1e-9)
        self.assertIn('LEFT:board',c.contacts)
        before=poses['LEFT']
        slid=c.resolve(poses,{**poses,'LEFT':replace(before,pitch=before.pitch+2)},held)
        self.assertGreater(slid['LEFT'].pitch,before.pitch+1.5)
        self.assertGreaterEqual(c.board_gap('LEFT',slid['LEFT'],held),-1e-9)
        escaped=c.resolve(slid,{**slid,'LEFT':replace(slid['LEFT'],insertion=slid['LEFT'].insertion-.01)},held)
        self.assertLess(escaped['LEFT'].insertion,slid['LEFT'].insertion-.009)
        self.assertGreater(c.board_gap('LEFT',escaped['LEFT'],held),.008)
        c.reset(); self.assertFalse(c.contacts)

    def test_pair_crossing_bounded_sweep_and_escape(self):
        c=CollisionConstraint(PIVOTS,InstrumentLimits()); poses=dict(NEUTRAL)
        desired={'LEFT':replace(NEUTRAL['LEFT'],yaw=-35), 'RIGHT':replace(NEUTRAL['RIGHT'],yaw=35)}
        for _ in range(6):
            poses=c.resolve(poses,desired)
            self.assertGreaterEqual(c.pair_gap(poses),-1e-9)
        self.assertTrue(any('instrument' in contact for contact in c.contacts))
        escaped=c.resolve(poses,{side:replace(p,yaw=p.yaw+(5 if side=='LEFT' else -5)) for side,p in poses.items()})
        self.assertGreater(c.pair_gap(escaped),c.pair_gap(poses)+.005)

    def test_jaw_roll_and_proxy_board_clearance(self):
        c=CollisionConstraint(PIVOTS,InstrumentLimits()); poses=dict(NEUTRAL)
        for jaw in (0,1,0):
            for rotation in (-90,90):
                poses=c.resolve(poses,{**poses,'LEFT':replace(poses['LEFT'],insertion=.28,jaw=jaw,rotation=rotation)})
                self.assertGreaterEqual(c.board_gap('LEFT',poses['LEFT'],{}),-1e-9)
                for a,b,radius in proxies(PIVOTS['LEFT'],poses['LEFT'],c.settings)[0]:
                    self.assertGreaterEqual(min(a[2],b[2])-radius,c.settings.board_height-1e-9)


if __name__=='__main__': unittest.main()
