"""Task semantics independent of Blender, camera, transport and wall clock."""
import unittest
from lapsim_ai.simulator.tasks.peg_transfer import PegTransfer


def task():
    return PegTransfer({str(i):(-.04,i*.025,0) for i in range(6)},
                       {str(i):(.04,i*.025,0) for i in range(6)},seat_height=0)


class PegTransferTests(unittest.TestCase):
    def test_initial_grasp_release_reset(self):
        t = task()
        self.assertEqual((t.state,t.elapsed,t.completed),('READY',0,0))
        t.update({'LEFT':((-.04,0,0),0)},.03)
        self.assertEqual(t.world.owners['0'],'LEFT')
        self.assertEqual(t.state,'RUNNING')
        t.update({'LEFT':((0,0,.03),0)},.03)
        self.assertEqual(t.world.positions['0'],(0,0,.03))
        t.update({'LEFT':((0,0,.03),1)},.03)
        self.assertEqual(t.placements['0'],'DROPPED')
        self.assertEqual(t.world.positions['0'],(0,0,0))
        t.reset()
        self.assertEqual((t.state,t.elapsed,t.completed),('READY',0,0))
        self.assertEqual(t.world.positions,t.world.homes)
        self.assertTrue(all(v is None for v in t.world.owners.values()))
        self.assertFalse(t.pending)

    def test_exclusive_handoff_no_snap(self):
        t = task(); p = (-.04,0,0)
        t.update({'LEFT':(p,0),'RIGHT':(p,1)},.03)
        t.update({'LEFT':((0,0,.03),0),'RIGHT':((.002,0,.03),0)},.03)
        self.assertEqual(t.world.owners['0'],'LEFT')
        before = t.world.positions['0']
        t.update({'LEFT':((0,0,.03),1),'RIGHT':((.002,0,.03),0)},.03)
        self.assertEqual(t.world.owners['0'],'RIGHT')
        self.assertEqual(t.world.positions['0'],before)
        t.update({'RIGHT':((.012,0,.03),0)},.03)
        self.assertAlmostEqual(t.world.positions['0'][0],.01)
        self.assertEqual(t.placements['0'],'HELD')

    def test_cancel_handoff_and_missing_data(self):
        t = task(); p = (-.04,0,0)
        t.update({'LEFT':(p,0)},.03)
        t.update({'LEFT':(p,0),'RIGHT':(p,0)},.03)
        t.update({'LEFT':(p,0)},.03)
        self.assertFalse(t.pending)
        held = dict(t.world.positions)
        t.update({},.03)
        self.assertEqual(t.world.positions,held)
        self.assertEqual(t.world.owners['0'],'LEFT')
        t.update({'LEFT':(p,1),'RIGHT':((.1,0,0),0)},.03)
        self.assertIsNone(t.world.owners['0'])

    def test_correct_incorrect_occupied_target_and_completion(self):
        t = task()
        def transfer(name, destination):
            t.update({'LEFT':(t.world.positions[name],1)},.03)
            t.update({'LEFT':(t.world.positions[name],0)},.03)
            t.update({'LEFT':(destination,0)},.03)
            t.update({'LEFT':(destination,1)},.03)
        transfer('0',t.targets['1'])
        self.assertEqual((t.placements['0'],t.completed),('INCORRECT',0))
        transfer('1',t.targets['1'])
        self.assertEqual(t.placements['1'],'DROPPED')
        transfer('0',t.targets['0'])
        for i in range(1,6): transfer(str(i),t.targets[str(i)])
        self.assertEqual((t.state,t.completed),('COMPLETE',6))
        elapsed = t.elapsed; positions = dict(t.world.positions)
        t.update({'LEFT':(t.targets['0'],0)},10)
        self.assertEqual((t.elapsed,t.world.positions),(elapsed,positions))

    def test_regrasp_removes_completion_and_height_matters(self):
        t = task(); p=t.world.homes['0']; q=t.targets['0']
        for point,jaw in ((p,0),(q,0),(q,1),(q,0)):
            t.update({'LEFT':(point,jaw)},.03)
        self.assertEqual(t.completed,0)
        t.update({'LEFT':((q[0],q[1],.05),1)},.03)
        self.assertEqual(t.placements['0'],'DROPPED')

    def test_deterministic_competing_capture(self):
        a,b=task(),task(); p=a.world.homes['0']
        a.update({'LEFT':(p,0),'RIGHT':(p,0)},.03)
        b.update({'RIGHT':(p,0),'LEFT':(p,0)},.03)
        self.assertEqual(a.world.owners,b.world.owners)
        self.assertEqual(a.world.owners['0'],'LEFT')
        with self.assertRaises(ValueError): a.update({},float('nan'))


if __name__ == '__main__': unittest.main()
