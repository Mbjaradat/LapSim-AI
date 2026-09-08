"""Reproduce transport-to-startup calibration/visibility separation."""
import json
import unittest
from unittest.mock import Mock
from test_webcam_integration import packet
from test_webcam_startup import TARGETS
from lapsim_ai.control.webcam_bridge import WebcamProcess, decode_frame
from lapsim_ai.control.webcam_startup import WebcamStartup


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.worker = WebcamProcess.__new__(WebcamProcess)
        self.worker.closed, self.worker.frame, self.worker.token = False, None, 'secret'
        self.worker.state_time = float('-inf')
        self.worker.calibrated = dict(LEFT=False,RIGHT=False)
        self.worker.process = Mock()
        self.worker.process.poll.return_value = None
        self.worker.socket = Mock()
        self.gate = WebcamStartup()

    def tick(self, now, tracked=True, calibrated=True, stamp=None, malformed=False):
        frame=json.loads(packet(TARGETS[0],TARGETS[1],now if stamp is None else stamp))
        frame['state']={side:dict(calibrated=calibrated,tracked=tracked) for side in ('LEFT','RIGHT')}
        # Human-facing status is deliberately absent: never infer readiness from text.
        if malformed:
            frame['hands']['LEFT']['yaw']=float('nan')
        self.worker.socket.recvfrom.side_effect=[(json.dumps(frame).encode(),('127.0.0.1',123)),BlockingIOError()]
        targets=self.worker.poll(now)
        timestamp=self.worker.frame[0] if self.worker.frame else None
        return self.gate.update(targets,timestamp,self.worker.calibrated,now)

    def test_loss_reacquisition_full_five_seconds(self):
        self.tick(0,tracked=False)
        self.assertEqual(self.gate.label(True),'WAITING FOR BOTH HANDS')
        self.tick(.1)
        self.assertIn('IN 5...',self.gate.label(True))
        self.tick(.2,tracked=False)
        self.assertIsNone(self.gate.deadline)
        self.assertTrue(all(self.worker.calibrated.values()))
        self.assertEqual(self.gate.label(True),'WAITING FOR BOTH HANDS')
        self.tick(.3)
        self.assertAlmostEqual(self.gate.deadline,5.3)
        for i in range(4,53):
            self.assertFalse(self.tick(i/10))
        self.assertTrue(self.tick(5.3))
        self.assertEqual(self.gate.label(False),'LIVE')

    def test_stale_and_invalid_packets_keep_calibration(self):
        self.tick(2,stamp=1,tracked=False)
        self.assertTrue(all(self.worker.calibrated.values()))
        self.assertIsNone(self.worker.frame)
        self.assertEqual(self.gate.label(True),'WAITING FOR BOTH HANDS')
        self.tick(2.1,malformed=True)
        self.assertTrue(all(self.worker.calibrated.values()))
        self.assertEqual(self.gate.label(True),'WAITING FOR BOTH HANDS')
        self.tick(2.2)
        self.assertIn('IN 5...',self.gate.label(True))

    def test_explicit_reset_and_older_packets(self):
        self.tick(2)
        self.tick(2.1,calibrated=False)
        self.assertEqual(self.gate.label(True),'WAITING FOR CALIBRATION')
        self.tick(2.2,stamp=1.9,calibrated=True)
        self.assertFalse(any(self.worker.calibrated.values()))
        self.assertIsNone(self.gate.deadline)

    def test_old_clock_offset_reproduces_rejected_fresh_packet(self):
        self.assertIsNone(decode_frame(packet(TARGETS[0],TARGETS[1],10),'secret',11.07))
        self.assertIsNotNone(decode_frame(packet(TARGETS[0],TARGETS[1],11.05),'secret',11.07))


if __name__ == '__main__':
    unittest.main()
