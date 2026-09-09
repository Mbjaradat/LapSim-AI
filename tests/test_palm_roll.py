"""Ideal 3D palm and pipeline tests; no camera/GUI, no physical accuracy claims."""
from dataclasses import replace
from math import cos, sin, pi
from random import Random
from types import SimpleNamespace
import unittest

from test_hand_mapping import state
from lapsim_ai.vision.hand_state import extract_hand_state
from lapsim_ai.vision.palm_orientation import palm_frame, relative_twist, TwistFilter, cross, dot
from lapsim_ai.vision.stabilization import HandStabilizer, Settings
from lapsim_ai.control.hand_mapping import HandMapper
from lapsim_ai.control.controller import InstrumentController
from lapsim_ai.control.instrument import InstrumentControl

PALM = [(0,0,0), (-.05,-.10,0), (0,-.12,0), (.03,-.11,0), (.06,-.08,0)]
BASE = palm_frame(PALM)


def rotate(point, axis, angle):
    perpendicular = cross(axis, point)
    projection = dot(axis, point)
    return tuple(p*cos(angle)+q*sin(angle)+a*projection*(1-cos(angle))
                 for p,q,a in zip(point,perpendicular,axis))


def raw(angle=0, side='Right', swing=0, scale=1, shift=(0,0), noise=0, seed=0, fingers=False):
    rng = Random(seed)
    points = dict(zip((0,5,9,13,17), PALM))
    result = []
    for i in range(21):
        p = points.get(i, (.02,-.18,.01) if not fingers else (.08,-.04,.05))
        p = rotate(rotate(p, BASE.longitudinal, angle), BASE.transverse, swing)
        x,y,z = (scale*v+rng.uniform(-noise,noise) for v in p)
        result.append(SimpleNamespace(x=.5+shift[0]+x, y=.5+shift[1]+y, z=z))
    return extract_hand_state(result,side,mirrored_input=False)


def calibrated():
    engine = HandStabilizer(Settings(calibration_samples=3))
    t = 0
    for stage, pinch in (('neutral',.1), ('open',.2), ('closed',.01)):
        for side in ('Left','Right'): engine.calibrate(side,stage)
        for _ in range(3):
            t += 1/30
            engine.update([replace(raw(side=side),pinch_distance=pinch) for side in ('Left','Right')],t)
    return engine,t


class PalmRollTests(unittest.TestCase):
    def test_neutral_signed_twist_and_bounds(self):
        neutral = raw().palm_orientation
        for degrees in (0, -35, 35, -100, 100):
            angle = relative_twist(neutral,raw(degrees*pi/180).palm_orientation)
            self.assertAlmostEqual(angle,degrees*pi/180)
            command = HandMapper().map(replace(state(),roll_angle=angle))
            self.assertLessEqual(abs(command.rotation),1)
            if degrees: self.assertGreater(-degrees*command.rotation,0)
            else: self.assertEqual(command.rotation,0)
        # Same physical palm mirrored laterally still gives the same twist sign.
        left_points = [(-x,y,z) for x,y,z in PALM]
        left = palm_frame(left_points)
        rotated = palm_frame([rotate(p,left.longitudinal,.4) for p in left_points])
        self.assertAlmostEqual(relative_twist(left,rotated),.4)

    def test_swing_translation_scale_and_fingers_do_not_roll(self):
        neutral = raw().palm_orientation
        for kwargs in (dict(swing=.5),dict(swing=-.5),dict(shift=(.1,-.1)),dict(scale=.8),dict(scale=1.2),dict(fingers=True)):
            self.assertAlmostEqual(relative_twist(neutral,raw(**kwargs).palm_orientation),0)
            self.assertAlmostEqual(relative_twist(neutral,raw(.3,**kwargs).palm_orientation),.3)
        # Also swing around the palm normal (in-plane image rotation): no axial twist.
        normal = cross(BASE.longitudinal,BASE.transverse)
        frame = palm_frame([rotate(p,normal,.4) for p in PALM])
        self.assertAlmostEqual(relative_twist(BASE,frame),0)

    def test_wraparound(self):
        a = raw(179*pi/180).palm_orientation
        b = raw(-179*pi/180).palm_orientation
        self.assertAlmostEqual(relative_twist(a,b),2*pi/180)
        filt = TwistFilter()
        filt.update(179*pi/180,.03,.06)
        self.assertGreater(abs(filt.update(-179*pi/180,.03,.06)),178*pi/180)

    def test_deadzone_noise_response_and_return(self):
        engine,t = calibrated()
        mapper = HandMapper()
        for frame in range(60):
            t += 1/30
            sample = engine.update([raw(noise=.0004,seed=frame)],t)['Right']
            self.assertEqual(mapper.map(sample).rotation,0)
        for angle in (-1.9*pi/180,1.9*pi/180):
            self.assertEqual(mapper.map(replace(state(),roll_angle=angle)).rotation,0)
        values = []
        for _ in range(9):
            t += 1/30
            sample = engine.update([raw(35*pi/180)],t)['Right']
            values.append(mapper.map(sample).rotation)
        self.assertLess(abs(values[0]),.6)
        self.assertLess(values[5],-.95)  # Estimator >95% within 0.2 s; rig rate unchanged.
        for _ in range(15):
            t += 1/30
            sample = engine.update([raw()],t)['Right']
        self.assertEqual(mapper.map(sample).rotation,0)

    def test_loss_reset_independence_and_controller_hold(self):
        engine,t = calibrated(); mapper = HandMapper()
        controller = InstrumentController({side:InstrumentControl() for side in ('LEFT','RIGHT')})
        for _ in range(20):
            t += 1/30
            samples = engine.update([raw(.4),raw(side='Left')],t)
            commands = [mapper.map(s) for s in samples.values()]
            controller.update_targets(commands,1/30)
        self.assertLess(mapper.map(samples['Right']).rotation,0)
        self.assertEqual(mapper.map(samples['Left']).rotation,0)
        held = controller.poses
        t += .6
        lost = engine.update([],t)['Right']
        self.assertTrue(lost.calibration.ready)
        self.assertIsNone(lost.roll_angle)
        self.assertFalse(mapper.map(lost).valid)
        controller.update_targets([mapper.map(lost)],1/30)
        self.assertEqual(controller.poses,held)
        engine.reset('Right')
        t += 1/30
        states = engine.update([raw(),raw(side='Left')],t)
        self.assertIsNone(states['Right'].calibration.neutral_orientation)
        self.assertFalse(mapper.map(states['Right']).valid)
        self.assertTrue(mapper.map(states['Left']).valid)

    def test_recalibrate_twisted_neutral_and_other_channels_unchanged(self):
        engine,t = calibrated()
        original = engine.hands['Right'].calibration
        engine.calibrate('Right','neutral')
        for _ in range(3):
            t += 1/30
            output = engine.update([raw(.4)],t)['Right']
        self.assertAlmostEqual(output.roll_angle,0)
        self.assertEqual(output.calibration.pinch_open,original.pinch_open)
        self.assertEqual(output.calibration.pinch_closed,original.pinch_closed)
        base = state(x=.54,y=.46,depth_scale=.75,pinch=.3)
        a,b = (HandMapper().map(replace(base,roll_angle=angle)) for angle in (0,.4))
        for channel in ('yaw','pitch','insertion','jaw'):
            self.assertEqual(getattr(a,channel),getattr(b,channel))

    def test_degenerate_and_missing_z_no_fallback(self):
        self.assertIsNone(palm_frame([(0,0,0)]*5))
        self.assertIsNone(palm_frame([(float('nan'),0,0)]*5))
        reversed_frame = palm_frame([rotate(p,BASE.transverse,pi) for p in PALM])
        self.assertIsNone(relative_twist(BASE,reversed_frame))
        points = [SimpleNamespace(x=.5,y=.5) for _ in range(21)]
        self.assertIsNone(extract_hand_state(points,'Right',mirrored_input=False).palm_orientation)
        engine,t = calibrated()
        t += 1/30
        output = engine.update([replace(raw(),palm_orientation=None)],t)['Right']
        self.assertFalse(HandMapper().map(output).valid)


if __name__ == '__main__': unittest.main()
