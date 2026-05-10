import unittest

from prism.metrics.drift import DriftMonitor


class TestDriftMonitor(unittest.TestCase):
    def test_healthy_state(self):
        monitor = DriftMonitor()
        result = monitor.evaluate(
            {
                "injection_decisions": 25,
                "injection_abstained": 5,
                "user_corrections": 3,
            }
        )
        self.assertTrue(result["healthy"])

    def test_alert_state(self):
        monitor = DriftMonitor()
        result = monitor.evaluate(
            {
                "injection_decisions": 30,
                "injection_abstained": 28,
                "user_corrections": 15,
            }
        )
        self.assertFalse(result["healthy"])
        self.assertGreater(len(result["alerts"]), 0)


if __name__ == "__main__":
    unittest.main()
