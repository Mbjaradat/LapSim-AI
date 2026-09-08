"""Depth-only synthetic checks. Ideal geometry is not real-camera validation."""
from dataclasses import replace
from math import cos, sin
from types import SimpleNamespace
import unittest
from test_hand_mapping import state
from lapsim_ai.vision.hand_state import extract_hand_state
from lapsim_ai.vision.stabilization import HandStabilizer, Settings
from lapsim_ai.control.hand_mapping import HandMapper


def landmarks(scale=1, tilt=0, shift=(0,0), finger_motion=False):
    points = {0:(0,0,0), 5:(-.05,-.10,0), 9:(0,-.12,0),
              13:(.03,-.11,0), 17:(.06,-.08,0)}
    result = []
    for i in range(21):
        x,y,z = points.get(i,(.02,-.2,.01))
        if finger_motion and i not in points:
            x,y,z = .08,-.04,.06
        result.append(SimpleNamespace(x=.5+shift[0]+scale*x,
                      y=.5+shift[1]+scale*(y*cos(tilt)-z*sin(tilt)),
                      z=scale*(y*sin(tilt)+z*cos(tilt))))
    return result


def raw(**kwargs):
    return extract_hand_state(landmarks(**kwargs),"Left",mirrored_input=True)


class PalmDepthTests(unittest.TestCase):
    def test_fingers_translation_and_tilt(self):
        baseline = raw().palm_depth_scale
        for kw in (dict(finger_motion=True),dict(shift=(.1,-.1)),dict(tilt=.45),dict(tilt=-.45)):
            self.assertAlmostEqual(raw(**kw).palm_depth_scale,baseline)
        # Common Z offsets are not whole-hand range information and must cancel.
        points = landmarks()
        for p in points:
            p.z += .2
        self.assertAlmostEqual(extract_hand_state(points,"Left",mirrored_input=True).palm_depth_scale,baseline)

    def test_forward_backward_and_unaffected_channels(self):
        baseline = raw().palm_depth_scale
        base_state = state()
        base_state = replace(base_state,palm_depth_scale=baseline,
                             calibration=replace(base_state.calibration,neutral_depth_scale=baseline))
        mapper = HandMapper()
        neutral = mapper.map(base_state)
        self.assertAlmostEqual(neutral.insertion,0)
        for factor,sign in ((1.10,-1),(.90,1),(2,-1),(.5,1)):
            sample = replace(base_state,palm_depth_scale=raw(scale=factor).palm_depth_scale)
            target = mapper.map(sample)
            self.assertGreater(sign*target.insertion,0)
            self.assertLessEqual(abs(target.insertion),1)
            for channel in ('yaw','pitch','rotation','jaw'):
                self.assertEqual(getattr(target,channel),getattr(neutral,channel))
        left = replace(base_state,handedness='Left')
        self.assertEqual(mapper.map(left).side,'LEFT')
        self.assertEqual(mapper.map(base_state).side,'RIGHT')
        self.assertFalse(mapper.map(replace(base_state,tracked=False)).valid)

    def test_calibration_smoothing_deadband_and_independence(self):
        engine = HandStabilizer(Settings(calibration_samples=3))
        t=0
        for stage,pinch in (('neutral',.1),('open',.2),('closed',.01)):
            engine.calibrate('Right',stage)
            for _ in range(3):
                t+=1/30
                engine.update([replace(raw(),pinch_distance=pinch)],t)
        baseline=engine.hands['Right'].calibration.neutral_depth_scale
        self.assertAlmostEqual(baseline,raw().palm_depth_scale)
        for i in range(30):
            t+=1/30
            output=engine.update([raw(scale=1+.003*(-1)**i)],t)['Right']
            self.assertAlmostEqual(HandMapper().map(output).insertion,0)
        t+=1/30
        output=engine.update([raw(scale=1.15),replace(raw(),handedness='Left')],t)
        self.assertLess(output['Right'].palm_depth_scale,baseline*1.15)
        self.assertLessEqual(output['Right'].palm_depth_scale-baseline,baseline*.030001)
        self.assertAlmostEqual(output['Left'].palm_depth_scale,baseline)
        for _ in range(30):
            t+=1/30
            output=engine.update([raw(scale=1.15)],t)['Right']
        self.assertLess(HandMapper().map(output).insertion,-.9)


if __name__ == '__main__':
    unittest.main()
