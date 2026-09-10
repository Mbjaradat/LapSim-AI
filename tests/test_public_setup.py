"""Guided public UX tests using raw synthetic hands and real calibration sampler."""
import unittest
from dataclasses import replace
from test_palm_steering import raw
from lapsim_ai.control.public_setup import GuidedSetup, home_direction, HOME_RADIUS
from lapsim_ai.control.public_runtime import PublicRuntime
from lapsim_ai.control.hand_mapping import HandMapper
from lapsim_ai.vision.stabilization import HandStabilizer

BOUNDS = {s: (.15,.15,.85,.85) for s in ('Left','Right')}

def pair(pinch=.01, shift=(0,0)):
    return [raw(pinch, shift=shift, side=s) for s in ('Left','Right')]

class GuidedTests(unittest.TestCase):
    def setUp(self):
        self.setup, self.filter = GuidedSetup(), HandStabilizer()
        self.now = 0

    def tick(self, hands=None, bounds=None, gap=.1):
        self.now += gap
        hands = pair() if hands is None else hands
        status = self.setup.update(hands, BOUNDS if bounds is None else bounds, self.now, self.filter)
        self.stable = self.filter.update(hands, self.now)
        return status

    def hold(self, pinch=.01, count=42):
        history=[]
        for _ in range(count):
            history.append(self.tick(pair(pinch)).state)
        return history

    def calibrate(self):
        history = self.hold() + self.hold(.2) + self.hold(.01)
        self.assertTrue(self.setup.ready)
        return history

    def test_state_order_and_pair_calibration(self):
        states=self.calibrate()
        order=['CAMERA_SETUP','HOME_SETUP','HOME_COUNTDOWN','OPEN_SETUP','OPEN_COUNTDOWN',
               'PINCH_SETUP','PINCH_COUNTDOWN','CALIBRATION_COMPLETE']
        self.assertEqual(sorted(order,key=states.index),order)
        self.assertTrue(all(h.calibration.ready for h in self.filter.hands.values()))
        self.assertEqual(set(self.setup.home),{'Left','Right'})
        self.assertTrue(all(HandMapper().map(s).valid for s in self.stable.values()))

    def test_both_hands_and_duplicate_identity(self):
        for hands in ([],pair()[:1],pair()+pair()[:1]):
            for _ in range(60): self.tick(hands)
            self.assertFalse(self.setup.ready)
            self.assertIsNone(self.setup.since)
            self.assertTrue(all(h.calibration.neutral_wrist is None for h in self.filter.hands.values()))

    def test_neutral_countdown_movement_loss_and_stall_reset(self):
        self.hold(count=15)
        self.assertEqual(self.setup.state,'HOME_COUNTDOWN')
        self.tick(pair(shift=(.03,0)))
        self.assertIsNone(self.setup.remaining)
        self.hold(count=15)
        self.tick([])
        self.assertIsNone(self.setup.since)
        self.hold(count=15)
        self.tick(gap=1)
        self.assertIsNone(self.setup.remaining)
        self.assertEqual(self.setup.stage,'neutral')

    def test_open_closed_validation_and_stability(self):
        self.hold()
        self.hold(.01,60)
        self.assertEqual(self.setup.stage,'open')
        self.assertIn('OPEN MORE',self.setup.message)
        self.hold(.2,15)
        self.tick(pair(.2,shift=(.025,0)))
        self.assertIsNone(self.setup.remaining)
        self.hold(.2)
        self.hold(.2,60)
        self.assertEqual(self.setup.stage,'closed')
        self.assertIn('PINCH MORE',self.setup.message)
        self.hold(.01)
        self.assertTrue(self.setup.ready)

    def test_span_rejection_is_atomic(self):
        self.hold(); self.hold(.2)
        for h in self.filter.hands.values():
            h.calibration=replace(h.calibration,pinch_open=.02)
        before={s:h.calibration for s,h in self.filter.hands.items()}
        self.hold(.01)
        self.assertIn('TOO SIMILAR',self.setup.message)
        self.assertFalse(self.setup.ready)
        self.assertEqual(before,{s:h.calibration for s,h in self.filter.hands.items()})
        self.assertFalse(self.filter.capture_pair('closed',[pair(.019)]*30))
        self.assertEqual(before,{s:h.calibration for s,h in self.filter.hands.items()})

    def test_camera_margin_scale_invalid_geometry(self):
        self.tick()
        for hands,bounds,message in (
            (pair(),{'Left':(.01,.1,.8,.8),'Right':BOUNDS['Right']},'INSIDE FRAME'),
            ([replace(h,palm_depth_scale=.01) for h in pair()],BOUNDS,'MOVE CLOSER'),
            ([replace(h,palm_depth_scale=.4) for h in pair()],BOUNDS,'MOVE BACK'),
            ([replace(h,palm_depth_scale=float('nan')) for h in pair()],BOUNDS,'RETRY'),
            ([replace(h,palm_orientation=None) for h in pair()],BOUNDS,'RETRY')):
            status=self.tick(hands,bounds)
            self.assertIn(message,status.message)
            self.assertIsNone(self.setup.remaining)

    def test_home_direction_and_boundary(self):
        home=(.5,.5)
        for point,expected in (((.5,.5),'HOME'),((.3,.5),'RIGHT'),((.7,.5),'LEFT'),
                               ((.5,.3),'DOWN'),((.5,.7),'UP'),(None,'RETURN TO CAMERA')):
            self.assertEqual(home_direction(point,home),expected)
        self.assertEqual(home_direction((.5+HOME_RADIUS-.0001,.5),home),'HOME')
        self.assertEqual(home_direction((.5+HOME_RADIUS+.0001,.5),home),'LEFT')

    def test_open_and_closed_loss_reset_their_countdowns(self):
        self.hold()
        for pinch,stage in ((.2,'open'),(.01,'closed')):
            self.hold(pinch,15)
            self.assertIsNotNone(self.setup.remaining)
            self.tick(pair(pinch)[:1])
            self.assertIsNone(self.setup.remaining)
            self.assertEqual(self.setup.stage,stage)
            self.hold(pinch)
        self.assertTrue(self.setup.ready)

    def test_bad_second_hand_cannot_commit_first_hand(self):
        before={s:h.calibration for s,h in self.filter.hands.items()}
        hands=pair()
        hands[1]=replace(hands[1],palm_orientation=None)
        self.assertFalse(self.filter.capture_pair('neutral',[hands]*30))
        self.assertEqual(before,{s:h.calibration for s,h in self.filter.hands.items()})

    def test_runtime_stale_and_home_departure_cancel_live_countdown(self):
        from test_webcam_startup import TARGETS, READY
        runtime=PublicRuntime()
        status=dict(state='WAITING_FOR_LIVE',message='RETURN TO HOME',ready=True,near_home=True)
        runtime.update(TARGETS,0,READY,status,0,paused=True)
        self.assertIsNotNone(runtime.startup.deadline)
        runtime.update(TARGETS,.1,READY,dict(status,near_home=False),.1,paused=True)
        self.assertIsNone(runtime.startup.deadline)
        runtime.update(TARGETS,.2,READY,status,.2,paused=True)
        runtime.update(TARGETS,.2,READY,status,1,paused=True)
        self.assertIsNone(runtime.startup.deadline)

    def test_persistence_no_automatic_recalibration(self):
        self.calibrate()
        before={s:h.calibration for s,h in self.filter.hands.items()}
        homes=dict(self.setup.home)
        for hands in ([],pair(shift=(.2,0)),pair()):
            for _ in range(60): self.tick(hands)
        self.assertTrue(self.setup.ready)
        self.assertEqual(homes,self.setup.home)
        self.assertEqual(before,{s:h.calibration for s,h in self.filter.hands.items()})

    def test_open_must_be_near_home(self):
        self.hold()
        self.tick(pair(.2,shift=(.08,0)))
        self.assertEqual(self.setup.message,'MOVE TO HOME')
        self.assertIsNone(self.setup.remaining)

    def test_explicit_recenter_guard_and_new_setup_isolation(self):
        self.calibrate()
        self.assertFalse(self.setup.recenter(paused=False,manipulating=False))
        self.assertFalse(self.setup.recenter(paused=True,manipulating=True))
        self.assertTrue(self.setup.recenter(paused=True,manipulating=False))
        self.assertEqual(self.setup.stage,'neutral')
        self.assertFalse(GuidedSetup().home)
        self.assertIsNone(GuidedSetup().last)

    def test_runtime_uses_existing_countdown_and_preserves_loss_semantics(self):
        self.calibrate()
        runtime=PublicRuntime()
        calibration={s.upper():True for s in self.stable}
        def advance(hands=None,near=True,paused=False,complete=False):
            self.tick(hands)
            targets=[HandMapper().map(s) for s in self.stable.values()]
            status=dict(state='WAITING_FOR_LIVE',message='RETURN TO HOME',ready=True,near_home=near)
            return runtime.update(targets,self.now,calibration,status,self.now,paused=paused,complete=complete)
        advance(near=False)
        self.assertIsNone(runtime.startup.deadline)
        for _ in range(20): advance()
        self.assertEqual(runtime.state,'LIVE_COUNTDOWN')
        advance([])
        self.assertIsNone(runtime.startup.deadline)
        entered=[]
        for _ in range(52): entered.append(advance())
        self.assertEqual(sum(entered),1)
        self.assertEqual(runtime.state,'LIVE')
        before={s:h.calibration for s,h in self.filter.hands.items()}
        advance(pair()[:1]); self.assertEqual(runtime.state,'TRACKING_LOST')
        advance(near=False); self.assertEqual(runtime.state,'LIVE')
        self.assertEqual(before,{s:h.calibration for s,h in self.filter.hands.items()})
        advance(paused=True); self.assertEqual(runtime.state,'PAUSED')
        advance(complete=True); self.assertEqual(runtime.state,'COMPLETE')
        runtime.retry(); self.assertFalse(runtime.startup.started)
        self.assertIsNone(runtime.startup.deadline)
        self.assertEqual(before,{s:h.calibration for s,h in self.filter.hands.items()})

if __name__=='__main__': unittest.main()
