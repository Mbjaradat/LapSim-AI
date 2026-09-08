"""Deterministic startup timing checks without a camera or Blender."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lapsim_ai.control.webcam_startup import WebcamStartup
from lapsim_ai.control.hand_mapping import InstrumentTarget

TARGETS = [InstrumentTarget(side, True, 0,0,0,0,.5) for side in ("LEFT","RIGHT")]
READY = {side: True for side in ("LEFT","RIGHT")}


class StartupTests(unittest.TestCase):
    def test_countdown_and_once_only_entry(self):
        gate = WebcamStartup()
        for tick in range(51):
            now = tick/10
            entered = gate.update(TARGETS,now,READY,now)
            self.assertEqual(entered,tick == 50)
            if tick in (0,10,20,30,40):
                self.assertIn(f"IN {5-tick//10}...",gate.label(True))
        self.assertEqual(gate.label(False),"LIVE")
        for tick in range(51,101):
            self.assertFalse(gate.update(TARGETS,tick/10,READY,tick/10))
            self.assertEqual(gate.label(True),"PAUSED")

    def test_missing_invalid_stale_prevent_start(self):
        for targets,stamp in ((TARGETS[:1],0),([TARGETS[0],InstrumentTarget('RIGHT')],0),
                              (TARGETS,-1),(TARGETS,None)):
            gate = WebcamStartup()
            self.assertFalse(gate.update(targets,stamp,READY,0))
            self.assertIsNone(gate.deadline)
            self.assertEqual(gate.label(True),'WAITING FOR BOTH HANDS')
        self.assertEqual(WebcamStartup().label(True),'WAITING FOR CALIBRATION')

    def test_loss_cancels_and_reacquisition_restarts_full_countdown(self):
        for targets,stamp in (([],1),([TARGETS[0],InstrumentTarget('RIGHT')],1),(TARGETS,0)):
            gate=WebcamStartup()
            for tick in range(10):
                gate.update(TARGETS,tick/10,READY,tick/10)
            gate.update(targets,stamp,READY,1)
            self.assertIsNone(gate.deadline)
            self.assertEqual(gate.label(True),'WAITING FOR BOTH HANDS')
            gate.update(TARGETS,1.1,READY,1.1)
            self.assertAlmostEqual(gate.deadline,6.1)
            self.assertIn('IN 5...',gate.label(True))

    def test_stalled_timer_cannot_skip_countdown(self):
        gate=WebcamStartup()
        gate.update(TARGETS,0,READY,0)
        self.assertFalse(gate.update(TARGETS,10,READY,10))
        self.assertEqual(gate.deadline,15)

    def test_stop_idempotence_and_new_session(self):
        gate=WebcamStartup()
        gate.update(TARGETS,0,READY,0)
        gate.stop()
        gate.stop()
        self.assertFalse(gate.update(TARGETS,10,READY,10))
        self.assertIsNone(gate.deadline)
        fresh=WebcamStartup()
        fresh.update(TARGETS,10,READY,10)
        self.assertEqual(fresh.deadline,15)


if __name__ == '__main__':
    unittest.main()
