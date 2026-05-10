from typing import Dict, List


class DriftMonitor:
    """
    Lightweight drift/quality checks based on runtime counters.
    """

    def evaluate(
        self,
        counters: Dict[str, int],
        min_decisions: int = 20,
        max_correction_rate: float = 0.35,
        max_abstain_rate: float = 0.80,
    ) -> Dict[str, object]:
        decisions = max(1, counters.get("injection_decisions", 0))
        corrections = counters.get("user_corrections", 0)
        abstained = counters.get("injection_abstained", 0)

        correction_rate = corrections / decisions
        abstain_rate = abstained / decisions

        alerts: List[str] = []
        if counters.get("injection_decisions", 0) >= min_decisions:
            if correction_rate > max_correction_rate:
                alerts.append("high_correction_rate")
            if abstain_rate > max_abstain_rate:
                alerts.append("high_abstain_rate")

        return {
            "decisions": counters.get("injection_decisions", 0),
            "correction_rate": correction_rate,
            "abstain_rate": abstain_rate,
            "alerts": alerts,
            "healthy": len(alerts) == 0,
        }
