"""Synthetic ergonomics checks; no webcam, GUI or physical accuracy claims."""
import sys
from pathlib import Path
from dataclasses import replace
from math import cos, sin
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lapsim_ai.vision.hand_state import HandState, extract_hand_state
from lapsim_ai.vision.stabilization import HandStabilizer, Settings, Calibration
from lapsim_ai.control.controller import InstrumentController
from lapsim_ai.control.instrument import InstrumentControl
from lapsim_ai.control.hand_mapping import HandMapper, InstrumentTarget
from test_hand_mapping import state


class ErgonomicsTests(unittest.TestCase):
    def test_small_workspace_and_neutral_dead_zone(self):
        mapper = HandMapper()
        self.assertAlmostEqual(mapper.map(state(x=.58)).yaw, 1)
        self.assertAlmostEqual(mapper.map(state(y=.42)).pitch, -1)
        self.assertGreater(mapper.map(state(x=.54)).yaw, .45)
        tiny = mapper.map(state(x=.502,y=.498))
        self.assertEqual((tiny.yaw,tiny.pitch), (0,0))
        self.assertEqual(mapper.map(state("Left")).yaw, 0)

    def test_depth_geometry_scale_translation_and_moderate_tilt(self):
        points = [(0.,0.,0.) for _ in range(21)]
        points[5], points[9], points[13], points[17] = (-.05,-.1,0), (0,-.12,0), (.03,-.11,0), (.06,-.08,0)
        def extract(scale, tilt):
            landmarks = [SimpleNamespace(x=.5+scale*x, y=.5+scale*(y*cos(tilt)-z*sin(tilt)),
                                         z=scale*(y*sin(tilt)+z*cos(tilt))) for x,y,z in points]
            return extract_hand_state(landmarks,"Left",mirrored_input=True).palm_depth_scale
        baseline = extract(1,0)
        self.assertTrue(0 < baseline < 1)
        self.assertAlmostEqual(extract(.7,.4),baseline*.7)
        self.assertAlmostEqual(extract(1.2,-.4),baseline*1.2)
        mapper = HandMapper()
        self.assertGreater(mapper.map(state(depth_scale=.5)).insertion,0)
        self.assertLess(mapper.map(state(depth_scale=.9)).insertion,0)

    def test_roll_translation_independent_and_small_rotation(self):
        mapper = HandMapper()
        clockwise = mapper.map(state(angle=.2))
        moved = mapper.map(state(x=.55,y=.45,angle=.2))
        self.assertAlmostEqual(clockwise.rotation,moved.rotation)
        self.assertLess(clockwise.rotation,-.25)  # Phase 2.5: 35-degree span, 2-degree deadzone.
        self.assertAlmostEqual(clockwise.rotation,-mapper.map(state(angle=-.2)).rotation)
        self.assertFalse(mapper.map(replace(state(),valid=False)).valid)

    def test_jaw_response_and_stationary_noise(self):
        def response(settings, rate):
            engine = HandStabilizer(settings)
            engine.hands["Right"].calibration = Calibration((.5,.5),.2,0)
            controller = InstrumentController({side: InstrumentControl(jaw=0) for side in ("LEFT","RIGHT")})
            def raw(pinch):
                return HandState("Right",(.5,.5),(.5,.4),(.5,.4+pinch),pinch)
            engine.update([raw(0)],0)
            first = None
            with patch("lapsim_ai.control.controller.WEBCAM_JAW_RATE",rate):
                for frame in range(1,31):
                    stable = engine.update([raw(.2)],frame/30)["Right"]
                    target = InstrumentTarget("RIGHT",True,0,0,0,0,stable.normalized_pinch)
                    controller.update_targets([target],1/30)
                    if first is None and controller.poses["RIGHT"].jaw >= .9:
                        first = frame/30
            self.assertEqual(controller.poses["LEFT"].jaw,0)
            held = controller.poses
            controller.update_targets([InstrumentTarget("RIGHT")],1/30)
            self.assertEqual(controller.poses,held)
            return first
        fast = response(Settings(),8)
        previous = response(Settings(pinch_smoothing_seconds=.06,max_pinch_step=.1),1.5)
        self.assertLessEqual(fast,.2)
        self.assertLess(fast,previous/2)
        engine = HandStabilizer()
        engine.hands["Right"].calibration = Calibration((.5,.5),.2,0)
        values = []
        for i in range(60):
            raw = HandState("Right",(.5,.5),(.5,.4),(.6,.4),.1+.0005*(-1)**i)
            values.append(engine.update([raw],i/30)["Right"].normalized_pinch)
        self.assertLess(max(values[10:])-min(values[10:]),.01)
        print(f"Jaw synthetic 90% response: {fast:.3f}s tuned vs {previous:.3f}s previous rate/filter settings")


if __name__ == "__main__":
    unittest.main()
