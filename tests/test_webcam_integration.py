"""Transport and shared-controller checks without a physical webcam."""
from dataclasses import asdict
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lapsim_ai.control.controller import InstrumentController, NormalizedCommand, CHANNELS
from lapsim_ai.control.instrument import InstrumentControl
from lapsim_ai.control.hand_mapping import InstrumentTarget
from lapsim_ai.control.webcam_bridge import decode_frame, WebcamProcess


def packet(left=None, right=None, timestamp=10):
    return json.dumps(dict(token="secret", time=timestamp,
        state={side: dict(calibrated=True, tracked=True) for side in ("LEFT", "RIGHT")}, hands={
        "LEFT": asdict(left or InstrumentTarget("LEFT")),
        "RIGHT": asdict(right or InstrumentTarget("RIGHT"))})).encode()


class WebcamIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.neutral = {"LEFT": InstrumentControl(-18,12), "RIGHT": InstrumentControl(18,12)}
        self.controller = InstrumentController(self.neutral)

    def test_both_sides_all_fields_and_no_cross_routing(self):
        for side in ("LEFT", "RIGHT"):
            self.controller.reset()
            other = "LEFT" if side == "RIGHT" else "RIGHT"
            target = InstrumentTarget(side, True, .3, -.4, .5, -.2, .9)
            kwargs = {side.lower(): target}
            targets = decode_frame(packet(**kwargs), "secret", 10.1)[1]
            for _ in range(200):
                self.controller.update_targets(targets, .05)
            expected = target.to_control(self.neutral[side])
            for name in CHANNELS:
                self.assertAlmostEqual(getattr(self.controller.poses[side], name), getattr(expected, name))
            self.assertEqual(self.controller.poses[other], self.neutral[other])

    def test_invalid_loss_hold_and_reacquisition_speed(self):
        target = InstrumentTarget("RIGHT", True, 1,1,1,1,1)
        self.controller.update_targets([target], .05)
        before = self.controller.poses
        for targets in ([], [InstrumentTarget("RIGHT")]):
            self.controller.update_targets(targets, .05)
            self.assertEqual(self.controller.poses, before)
        self.controller.update_targets([target], 100)
        self.assertLessEqual(self.controller.poses["RIGHT"].yaw - before["RIGHT"].yaw, 1.100001)

    def test_pause_reset_and_keyboard_regression(self):
        self.controller.paused = True
        self.controller.update_targets([InstrumentTarget("LEFT",True,1,1,1,1,1)], .05)
        self.assertEqual(self.controller.poses, self.neutral)
        self.controller.paused = False
        self.controller.update([NormalizedCommand("LEFT",yaw=1)], .05)
        self.assertGreater(self.controller.poses["LEFT"].yaw, self.neutral["LEFT"].yaw)
        self.controller.reset()
        self.assertEqual(self.controller.poses, self.neutral)

    def test_protocol_stale_malformed_and_nonfinite(self):
        self.assertIsNotNone(decode_frame(packet(), "secret",10.1))
        for data,token,now in ((packet(),"bad",10.1), (packet(),"secret",10.6),
                               (packet(),"secret",9), (b"{}","secret",10),
                               (packet(right=InstrumentTarget("RIGHT",True,float("nan"),0,0,0,0)),"secret",10)):
            self.assertIsNone(decode_frame(data,token,now))

    def test_invalid_batch_atomic(self):
        with self.assertRaises(ValueError):
            self.controller.update_targets([InstrumentTarget("LEFT",True,1,1,1,1,1),
                                            InstrumentTarget("BOGUS")], .05)
        self.assertEqual(self.controller.poses,self.neutral)

    @patch("lapsim_ai.control.webcam_bridge.subprocess.Popen")
    @patch("lapsim_ai.control.webcam_bridge.socket.socket")
    @patch("lapsim_ai.control.webcam_bridge.Path.is_file", return_value=True)
    def test_worker_stop_idempotent_and_stuck_process_killed(self, exists, socket_type, popen):
        process = popen.return_value
        process.poll.return_value = None
        socket_type.return_value.getsockname.return_value = ("127.0.0.1",45678)
        worker = WebcamProcess(".")
        worker.stop()
        worker.stop()
        process.stdin.close.assert_called_once()
        socket_type.return_value.close.assert_called_once()
        self.assertEqual(worker.poll(), [])
        with patch("lapsim_ai.control.webcam_bridge.time.monotonic", return_value=worker.deadline+1):
            self.assertEqual(worker.reap(), .1)
        process.kill.assert_called_once()
        process.poll.return_value = 0
        self.assertIsNone(worker.reap())
        worker.shutdown()

    def test_out_of_order_and_stale_queue(self):
        worker = WebcamProcess.__new__(WebcamProcess)
        worker.closed, worker.frame, worker.token = False, None, "secret"
        worker.state_time = float("-inf")
        worker.calibrated = {side: False for side in ("LEFT", "RIGHT")}
        worker.process = Mock()
        worker.process.poll.return_value = None
        worker.socket = Mock()
        worker.socket.recvfrom.side_effect = [(packet(timestamp=10), ("127.0.0.1",123)),
                                             (packet(timestamp=9.9), ("127.0.0.1",123)), BlockingIOError()]
        self.assertEqual(len(worker.poll(10.1)),2)
        self.assertEqual(worker.frame[0],10)
        worker.socket.recvfrom.side_effect = BlockingIOError()
        self.assertEqual(worker.poll(10.6),[])


if __name__ == "__main__":
    unittest.main()
