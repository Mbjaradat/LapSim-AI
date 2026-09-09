"""Deterministic workspace checks against the existing instrument parameters."""
from pathlib import Path
import sys
import unittest
from math import dist
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1]/'blender/scripts')]
from config import LIMITS, TROCARS, DEFAULTS
from phase3_config import CONTACT_OFFSET, TOKEN_OFFSETS, GB_OFFSET, shifted
from lapsim_ai.simulator.workspace import contact_point, inverse_contact, characterize, reachable, sample_workspace


class WorkspaceTests(unittest.TestCase):
    def test_deterministic_overlap_and_targets(self):
        first=characterize(TROCARS,DEFAULTS,LIMITS,CONTACT_OFFSET)
        self.assertEqual(first,characterize(TROCARS,DEFAULTS,LIMITS,CONTACT_OFFSET))
        self.assertGreater(len(first['shared']),100)
        for point in first['shared']:
            self.assertTrue(all(reachable(p,point,LIMITS,CONTACT_OFFSET,.1) for p in TROCARS.values()))
        for offset in (*TOKEN_OFFSETS.values(),GB_OFFSET):
            target=shifted(first['center'],offset)
            for pivot in TROCARS.values():
                self.assertTrue(reachable(pivot,target,LIMITS,CONTACT_OFFSET,.1))
                pose=inverse_contact(pivot,target,CONTACT_OFFSET)
                self.assertLess(dist(contact_point(pivot,pose,CONTACT_OFFSET),target),1e-12)

    def test_inverse_round_trip_and_unreachable(self):
        for pivot in TROCARS.values():
            cloud=sample_workspace(pivot,LIMITS,CONTACT_OFFSET,5)
            self.assertEqual(len(cloud),125)
            for point in cloud:
                recovered=inverse_contact(pivot,point,CONTACT_OFFSET)
                self.assertLess(dist(contact_point(pivot,recovered,CONTACT_OFFSET),point),1e-12)
            self.assertFalse(reachable(pivot,(1,1,1),LIMITS,CONTACT_OFFSET))
            self.assertFalse(reachable(pivot,pivot,LIMITS,CONTACT_OFFSET))
