"""Jaw eligibility, ownership, release and reset without Blender."""
import unittest
from lapsim_ai.simulator.grasp import GraspWorld


class GraspTests(unittest.TestCase):
    def test_threshold_distance_and_close_edge(self):
        world=GraspWorld({'bead':(0,0,0)})
        world.update({'LEFT':((.02,0,0),0)})
        self.assertIsNone(world.owners['bead'])
        world.update({'LEFT':((0,0,0),0)})
        self.assertIsNone(world.owners['bead']) # already closed, must reopen
        world.update({'LEFT':((.002,0,0),.8)})
        world.update({'LEFT':((.002,0,0),.25)})
        self.assertEqual(world.owners['bead'],'LEFT')
        self.assertEqual(world.positions['bead'],(0,0,0)) # no acquisition snap

    def test_follow_release_hold_and_reset(self):
        world=GraspWorld({'bead':(0,0,0)})
        world.update({'RIGHT':((.002,0,0),.2)})
        world.update({'RIGHT':((.012,0,0),.5)})
        self.assertAlmostEqual(world.positions['bead'][0],.01)
        self.assertEqual(world.owners['bead'],'RIGHT')
        held=dict(world.positions)
        world.update({})
        self.assertEqual(world.positions,held)
        world.update({'RIGHT':((.012,0,0),.65)})
        self.assertIsNone(world.owners['bead'])
        world.update({'RIGHT':((.1,0,0),1)})
        self.assertEqual(world.positions,held)
        world.reset()
        self.assertEqual(world.positions,{'bead':(0,0,0)})
        self.assertIsNone(world.owners['bead'])

    def test_deterministic_simultaneous_ownership(self):
        for order in (('LEFT','RIGHT'),('RIGHT','LEFT')):
            world=GraspWorld({'bead':(0,0,0)})
            world.update({side:((0,0,0),0) for side in order})
            self.assertEqual(world.owners['bead'],'LEFT')
        world=GraspWorld({'a':(-.02,0,0),'b':(.02,0,0)})
        world.update({'RIGHT':((.02,0,0),0),'LEFT':((-.02,0,0),0)})
        self.assertEqual(world.owners,{'a':'LEFT','b':'RIGHT'})
        world.update({'RIGHT':((-.02,0,0),0)})
        self.assertEqual(world.owners['a'],'LEFT')

    def test_invalid_input_holds(self):
        world=GraspWorld({'a':(0,0,0)})
        world.update({'LEFT':((float('nan'),0,0),0)})
        self.assertIsNone(world.owners['a'])
