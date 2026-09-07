"""Standard-library checks for the independent control contract."""

import unittest
from lapsim_ai.control.instrument import InstrumentControl, InstrumentLimits


class ControlTests(unittest.TestCase):
    def test_clamps_all_channels(self):
        self.assertEqual(InstrumentControl(-99, 99, 9, -999).limited(InstrumentLimits()),
                         InstrumentControl(-35, 25, .28, -180))

    def test_rejects_nonfinite_input(self):
        for field in ("yaw", "pitch", "insertion", "rotation"):
            for value in (float("nan"), float("inf"), -float("inf")):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    InstrumentControl(**{field: value}).limited(InstrumentLimits())

    def test_preserves_valid_input(self):
        control = InstrumentControl(12, -5, .19, 175)
        self.assertEqual(control.limited(InstrumentLimits()), control)

    def test_invalid_limits(self):
        with self.assertRaises(ValueError):
            InstrumentLimits(insertion=(-1, .2))
        with self.assertRaises(ValueError):
            InstrumentLimits(yaw=(35, -35))


if __name__ == "__main__":
    unittest.main()
