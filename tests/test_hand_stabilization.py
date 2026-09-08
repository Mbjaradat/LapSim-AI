"""Pure Phase 2B checks: no webcam, MediaPipe runtime or Blender needed."""
import sys
from pathlib import Path
import unittest
from statistics import pvariance
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lapsim_ai.vision.hand_state import HandState, extract_hand_state
from lapsim_ai.vision.stabilization import HandStabilizer, Settings


def raw(side="Right", x=0.5, pinch=0.1):
    return HandState(side, (x, 0.5), (x, 0.4), (x, 0.4 + pinch), pinch)


class StabilizationTests(unittest.TestCase):
    def test_smoothing_all_components_and_independence(self):
        engine = HandStabilizer(Settings(dead_zone=0))
        outputs, inputs = [], []
        for i in range(120):
            jitter = 0.01 * (-1) ** i
            states = engine.update([raw(x=.5 + jitter, pinch=.1 + jitter), raw("Left")], i / 30)
            if i > 20:
                s = states["Right"]
                outputs.append((s.wrist[0], s.index_fingertip[0], s.thumb_tip[1], s.pinch_distance))
                inputs.append(jitter)
            self.assertEqual(states["Left"].wrist, (.5, .5))
        for component in zip(*outputs):
            self.assertLess(pvariance(component), pvariance(inputs) / 4)

    def test_deadband_and_deliberate_small_motion(self):
        engine = HandStabilizer(Settings(smoothing_seconds=0))
        engine.update([raw()], 0)
        self.assertEqual(engine.update([raw(x=.501)], .03)["Right"].wrist[0], .5)
        self.assertGreater(engine.update([raw(x=.506)], .06)["Right"].wrist[0], .5)

    def test_calibration_median_direction_clamp_and_reset(self):
        engine = HandStabilizer(Settings(smoothing_seconds=0, dead_zone=0,
                                         max_step=1, max_pinch_step=1, calibration_samples=3))
        t = 0
        for stage, pinch in (("neutral", .1), ("open", .25), ("closed", .02)):
            engine.calibrate("Right", stage)
            for x in (.5, .51, .99):
                t += .03
                state = engine.update([raw(x=x, pinch=pinch)], t)["Right"]
        self.assertEqual(state.calibration.neutral_wrist, (.51, .5))
        self.assertTrue(state.valid)
        self.assertEqual(state.normalized_pinch, 0)
        for pinch, expected in ((0, 0), (.135, .5), (.25, 1), (.5, 1)):
            t += .03
            self.assertAlmostEqual(engine.update([raw(pinch=pinch)], t)["Right"].normalized_pinch, expected)
        engine.calibrate("Right", "open")
        for _ in range(3):
            t += .03
            state = engine.update([raw(pinch=.01)], t)["Right"]
        self.assertIn("rejected", state.status)
        self.assertEqual(state.calibration.pinch_open, .25)
        engine.reset("Right")
        state = engine.update([], t + .03)["Right"]
        self.assertIsNone(state.wrist)
        self.assertFalse(state.valid)
        self.assertIsNone(state.normalized_pinch)

    def test_loss_reacquisition_and_independent_reset(self):
        engine = HandStabilizer()
        engine.update([raw(), raw("Left", x=.2)], 0)
        state = engine.update([raw("Left", x=.2)], .1)["Right"]
        self.assertFalse(state.tracked)
        self.assertFalse(state.valid)
        self.assertTrue(state.available)
        self.assertEqual(state.wrist, (.5, .5))
        self.assertFalse(engine.update([], .6)["Right"].available)
        state = engine.update([raw(x=.9)], 10)["Right"]
        self.assertTrue(state.tracked)
        self.assertLessEqual(state.wrist[0] - .5, .0300001)
        engine.reset("Right")
        states = engine.update([raw("Left", x=.2)], 10.1)
        self.assertEqual(states["Left"].wrist, (.2, .5))
        self.assertIsNone(states["Right"].wrist)

    def test_missing_duplicate_invalid_and_sampling_restart(self):
        engine = HandStabilizer(Settings(calibration_samples=3))
        engine.calibrate("Right", "neutral")
        engine.update([raw()], 0)
        engine.update([], .03)
        self.assertIn("1/3", engine.update([raw()], .06)["Right"].status)
        self.assertFalse(engine.update([raw(), raw()], .09)["Right"].tracked)
        self.assertFalse(engine.update([raw(x=float("nan"))], .12)["Right"].tracked)
        with self.assertRaises(ValueError):
            engine.update([], .12)

    def test_verified_mirrored_identity_preserved(self):
        landmarks = [SimpleNamespace(x=.5, y=.5) for _ in range(21)]
        for label, physical in (("Left", "Right"), ("Right", "Left")):
            state = extract_hand_state(landmarks, label, mirrored_input=True)
            self.assertEqual(state.handedness, physical)
            self.assertTrue(HandStabilizer().update([state], 0)[physical].tracked)


if __name__ == "__main__":
    unittest.main()
