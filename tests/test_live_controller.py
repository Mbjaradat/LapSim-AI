"""Behavioral checks shared by keyboard and future input providers."""

import unittest
from lapsim_ai.control.instrument import InstrumentControl
from lapsim_ai.control.controller import InstrumentController, NormalizedCommand, CHANNELS
from lapsim_ai.control.keyboard import KeyboardInput, KEY_BINDINGS

NEUTRAL = {"LEFT": InstrumentControl(-18, 12), "RIGHT": InstrumentControl(18, 12)}


class LiveControllerTests(unittest.TestCase):
    def setUp(self):
        self.controller = InstrumentController(NEUTRAL)

    def test_rates_and_frame_partition(self):
        command = NormalizedCommand("LEFT", yaw=1, insertion=1, rotation=-1, jaw=1)
        self.controller.update([command], .04)
        other = InstrumentController(NEUTRAL)
        for _ in range(4):
            other.update([command], .01)
        for name in CHANNELS:
            self.assertAlmostEqual(getattr(self.controller.poses["LEFT"], name),
                                   getattr(other.poses["LEFT"], name))
        self.assertAlmostEqual(self.controller.poses["LEFT"].yaw, -18 + 22 * .04)

    def test_repeated_extremes_stay_bounded(self):
        for sign in (-1, 1):
            command = NormalizedCommand("LEFT", **{name: sign * 100 for name in CHANNELS})
            for _ in range(500):
                self.controller.update([command], .05)
            pose = self.controller.poses["LEFT"]
            for name in CHANNELS:
                self.assertEqual(getattr(pose, name), getattr(self.controller.limits, name)[sign == 1])

    def test_reset_all_channels_and_independence(self):
        for side, other in (("LEFT", "RIGHT"), ("RIGHT", "LEFT")):
            before = self.controller.poses[other]
            self.controller.update([NormalizedCommand(side, **{name: 1 for name in CHANNELS})], .05)
            self.assertEqual(self.controller.poses[other], before)
        self.controller.reset()
        self.assertEqual(self.controller.poses, NEUTRAL)

    def test_pause_and_stall_cap(self):
        self.controller.paused = True
        self.controller.update([NormalizedCommand("LEFT", yaw=1)], 50)
        self.assertEqual(self.controller.poses, NEUTRAL)
        self.controller.paused = False
        self.controller.update([NormalizedCommand("LEFT", yaw=1)], 50)
        self.assertAlmostEqual(self.controller.poses["LEFT"].yaw, -18 + 22 * .05)

    def test_invalid_batch_is_atomic(self):
        for bad in (NormalizedCommand("NO"), NormalizedCommand("RIGHT", jaw=float("nan"))):
            with self.assertRaises(ValueError):
                self.controller.update([NormalizedCommand("LEFT", yaw=1), bad], .05)
            self.assertEqual(self.controller.poses, NEUTRAL)
        with self.assertRaises(ValueError):
            self.controller.update([NormalizedCommand("LEFT"), NormalizedCommand("LEFT")], .05)
        for dt in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                self.controller.update([], dt)

    def test_sensitivity_cycle(self):
        names = []
        for _ in range(3):
            names.append(self.controller.profile[0])
            self.controller.cycle_sensitivity()
        self.assertEqual(names, ["Normal", "Fast", "Fine"])
        self.assertEqual(self.controller.profile[0], "Normal")

    def test_keyboard_repeat_release_and_opposites(self):
        provider = KeyboardInput()
        provider.key("W", True)
        provider.key("W", True)
        self.assertEqual(provider.commands()[0].pitch, 1)
        provider.key("S", True)
        self.assertEqual(provider.commands()[0].pitch, 0)
        provider.key("S", False)
        provider.key("UP_ARROW", True)
        self.assertEqual(provider.commands()[1].pitch, 1)
        provider.clear()
        self.assertTrue(all(getattr(cmd, name) == 0 for cmd in provider.commands() for name in CHANNELS))

    def test_all_keyboard_bindings(self):
        for key, (side, channel, sign) in KEY_BINDINGS.items():
            provider = KeyboardInput()
            self.assertTrue(provider.key(key, True))
            commands = {cmd.side: cmd for cmd in provider.commands()}
            self.assertEqual(getattr(commands[side], channel), sign)
            provider.key(key, False)
            self.assertTrue(all(getattr(cmd, name) == 0 for cmd in provider.commands() for name in CHANNELS))

    def test_jaw_finite_validation(self):
        for value in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                InstrumentControl(jaw=value).limited(self.controller.limits)


if __name__ == "__main__":
    unittest.main()
