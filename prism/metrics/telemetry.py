import json
import os
from datetime import datetime, timezone
from typing import Dict


class LocalMetricsLogger:
    """
    Writes structured observability events and aggregate counters to local files.
    """

    def __init__(self, base_path: str = "data/metrics"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        self.events_path = os.path.join(self.base_path, "events.jsonl")
        self.counters_path = os.path.join(self.base_path, "counters.json")

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _read_counters(self) -> Dict[str, int]:
        if not os.path.exists(self.counters_path):
            return {
                "injection_decisions": 0,
                "injection_applied": 0,
                "injection_abstained": 0,
                "user_corrections": 0,
            }
        with open(self.counters_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_counters(self, counters: Dict[str, int]):
        with open(self.counters_path, "w", encoding="utf-8") as f:
            json.dump(counters, f, indent=2)

    def log_event(self, event_type: str, payload: Dict[str, object]):
        record = {
            "timestamp": self._now_iso(),
            "event_type": event_type,
            "payload": payload,
        }
        with open(self.events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def record_injection_decision(
        self,
        user_id: str,
        confidence: float,
        signal_count: int,
        injected: bool,
        uiv: Dict[str, str],
    ):
        self.log_event(
            "injection_decision",
            {
                "user_id": user_id,
                "confidence": confidence,
                "signal_count": signal_count,
                "injected": injected,
                "uiv": uiv,
            },
        )
        counters = self._read_counters()
        counters["injection_decisions"] += 1
        if injected:
            counters["injection_applied"] += 1
        else:
            counters["injection_abstained"] += 1
        self._write_counters(counters)

    def record_user_feedback(self, user_id: str, message: str, is_correction: bool):
        self.log_event(
            "user_feedback",
            {
                "user_id": user_id,
                "is_correction": is_correction,
                "message": message,
            },
        )
        if is_correction:
            counters = self._read_counters()
            counters["user_corrections"] += 1
            self._write_counters(counters)

    def get_counters(self) -> Dict[str, int]:
        return self._read_counters()
