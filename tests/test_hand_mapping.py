"""Synthetic mapping checks; no camera or Blender."""
import sys
from pathlib import Path
import unittest
from dataclasses import replace
from math import sin, cos, pi

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lapsim_ai.control.hand_mapping import HandMapper, MappingSettings
from lapsim_ai.vision.stabilization import Calibration, StableHandState, HandStabilizer, Settings
from lapsim_ai.vision.hand_state import HandState


def state(side="Right", x=.5, y=.5, scale=1, angle=0, pinch=.5):
    return StableHandState(side, True, True, True, (x,y), (.5,.2), (.6,.2),
                           .1, pinch, Calibration((.5,.5), .2,.01,(0,-.1)), "ready",
                           (x + .1*scale*sin(angle), y - .1*scale*cos(angle)))


class MappingTests(unittest.TestCase):
    def test_neutral_and_independence(self):
        mapper = HandMapper()
        right = mapper.map(state(x=.6))
        left = mapper.map(state("Left"))
        self.assertEqual((right.side, left.side), ("RIGHT", "LEFT"))
        for name in ("yaw", "pitch", "insertion", "rotation"):
            self.assertAlmostEqual(getattr(left,name), 0)
        self.assertGreater(right.yaw, 0)

    def test_translation_and_fulcrum_sign(self):
        mapper = HandMapper()
        for command, axis in ((mapper.map(state(x=.6)), "yaw"), (mapper.map(state(y=.6)), "pitch")):
            self.assertGreater(getattr(command, axis), 0)
            for other in {"yaw", "pitch", "insertion", "rotation"} - {axis}:
                self.assertAlmostEqual(getattr(command, other), 0)
        # Existing rig: Ry(yaw) Rx(pitch), handle +Z, internal tip -Z.
        yaw = mapper.map(state(x=.6)).to_control().yaw*pi/180
        self.assertGreater(sin(yaw), 0)  # external X right
        self.assertLess(-sin(yaw), 0)  # internal X left
        pitch = mapper.map(state(y=.6)).to_control().pitch*pi/180
        self.assertLess(-sin(pitch), 0)  # external Y down
        self.assertGreater(sin(pitch), 0)  # internal Y up

    def test_depth_roll_jaw_and_clamps(self):
        mapper = HandMapper()
        self.assertGreater(mapper.map(state(scale=.7)).insertion, 0)
        self.assertLess(mapper.map(state(scale=1.3)).insertion, 0)
        self.assertLess(mapper.map(state(angle=.4)).rotation, 0)
        self.assertGreater(mapper.map(state(angle=-.4)).rotation, 0)
        for value in (0, 1):
            self.assertEqual(mapper.map(state(pinch=value)).jaw, value)
        command = mapper.map(state(x=1,y=0,scale=3,angle=2,pinch=2))
        self.assertEqual((command.yaw,command.pitch,command.insertion,command.rotation,command.jaw), (1,-1,-1,-1,1))
        pose = command.to_control()
        self.assertEqual((pose.yaw,pose.pitch,pose.insertion,pose.rotation,pose.jaw), (35,-25,.12,-180,1))

    def test_invalid_and_degenerate(self):
        mapper = HandMapper()
        for sample in (replace(state(),valid=False), replace(state(),tracked=False),
                       replace(state(),middle_mcp=None), state(scale=0), state(x=float("nan"))):
            command = mapper.map(sample)
            self.assertFalse(command.valid)
            self.assertIsNone(command.yaw)
            self.assertIsNone(command.to_control())
        with self.assertRaises(ValueError):
            MappingSettings(scale_range=0)

    def test_neutral_capture_and_stabilized_palm(self):
        engine = HandStabilizer(Settings(calibration_samples=3))
        t = 0
        for stage,pinch in (("neutral",.1),("open",.2),("closed",.01)):
            engine.calibrate("Right",stage)
            for _ in range(3):
                t += .03
                sample = engine.update([HandState("Right",(.5,.5),(.5,.2),(.6,.2),pinch,(.5,.4))],t)["Right"]
        command = HandMapper().map(sample)
        self.assertTrue(command.valid)
        self.assertAlmostEqual(command.insertion, 0)
        self.assertAlmostEqual(command.rotation, 0)


if __name__ == "__main__":
    unittest.main()
