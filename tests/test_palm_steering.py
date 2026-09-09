"""Pinch isolation and palm steering tests; synthetic landmark errors, not webcam evidence."""
import unittest
from dataclasses import replace
from types import SimpleNamespace
from test_palm_roll import PALM
from lapsim_ai.vision.hand_state import extract_hand_state
from lapsim_ai.vision.stabilization import HandStabilizer,Settings
from lapsim_ai.control.hand_mapping import HandMapper,relative_command


def raw(pinch=.01, shift=(0,0), wrist_error=0, side='Right', jitter=0):
    palm=dict(zip((0,5,9,13,17),PALM))
    points=[]
    for i in range(21):
        x,y,z=palm.get(i,(0,-.18,0))
        if i==4: x+=pinch
        if i==0: x+=wrist_error
        points.append(SimpleNamespace(x=.5+x+shift[0]+jitter,y=.5+y+shift[1],z=z))
    return extract_hand_state(points,side,mirrored_input=False)


def engine():
    e=HandStabilizer(Settings(calibration_samples=3)); t=0
    for stage,pinch in (('neutral',.01),('open',.2),('closed',.01)):
        e.calibrate('Right',stage)
        for _ in range(3):
            t+=1/30; e.update([raw(pinch)],t)
    return e,t


class PalmSteeringTests(unittest.TestCase):
    def test_open_close_isolation_translation_and_other_channels(self):
        e,t=engine(); mapper=HandMapper(); targets=[]
        for pinch in (.2,.01):
            for _ in range(25):
                t+=1/30; target=mapper.map(e.update([raw(pinch)],t)['Right'])
                self.assertEqual((target.yaw,target.pitch,target.insertion,target.rotation),(0,0,0,0))
            targets.append(target.jaw)
        self.assertGreater(targets[0]-targets[1],.95)
        for _ in range(25):
            t+=1/30; output=e.update([raw(shift=(.04,-.04)),raw(side='Left')],t)
        moved=mapper.map(output['Right'])
        self.assertGreater(moved.yaw,.4); self.assertLess(moved.pitch,-.4)
        self.assertEqual(moved.insertion,0); self.assertEqual(moved.rotation,0)
        self.assertFalse(mapper.map(output['Left']).valid)
        e.reset('Right'); t+=1/30
        self.assertIsNone(e.update([],t)['Right'].calibration.neutral_palm_center)

    def test_wrist_error_reduction_jitter_and_loss(self):
        e,t=engine(); mapper=HandMapper()
        for _ in range(30):
            t+=1/30; sample=e.update([raw(.2,wrist_error=.012)],t)['Right']
        previous=relative_command(sample.wrist[0]-sample.calibration.neutral_wrist[0],.08,.003)
        current=mapper.map(sample).yaw
        self.assertLess(abs(current),abs(previous)*.1)
        print(f'Pinch synthetic wrist bias 0.012: old steering={previous:.6f}, palm steering={current:.6f}; geometry attenuates wrist error by 60%')
        e,t=engine()
        for i in range(60):
            t+=1/30
            self.assertEqual(mapper.map(e.update([raw(jitter=.001*(-1)**i)],t)['Right']).yaw,0)
        t+=.6; lost=e.update([],t)['Right']
        self.assertFalse(mapper.map(lost).valid)
        self.assertIsNotNone(lost.calibration.neutral_palm_center)


if __name__=='__main__': unittest.main()
