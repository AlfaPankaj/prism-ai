from collections import defaultdict
from typing import Dict

from prism.extractor.uiv_builder import UIVBuilder
from prism.metrics.clarification import ClarificationDetector


def normalize_record(example: Dict[str, object]) -> Dict[str, str]:
    role = str(example.get("role") or example.get("speaker") or "unknown").lower()
    if role in {"prompter", "user", "human"}:
        role = "user"
    elif role in {"assistant", "bot", "model"}:
        role = "assistant"
    else:
        role = "unknown"

    text = str(
        example.get("text")
        or example.get("content")
        or example.get("message")
        or example.get("prompt")
        or ""
    )
    user_id = str(example.get("user_id") or example.get("author_id") or "unknown_user")
    session_id = str(
        example.get("session_id")
        or example.get("conversation_id")
        or example.get("thread_id")
        or f"session::{user_id}"
    )
    return {"role": role, "text": text, "user_id": user_id, "session_id": session_id}


class EvaluationTracker:
    """
    Tracks production-style metrics for intent personalization quality.
    """

    def __init__(self):
        self.detector = ClarificationDetector()
        self.builder = UIVBuilder()

        self.stats = {
            "total_records": 0,
            "user_turns": 0,
            "clarification_turns": 0,
            "preventable_clarifications": 0,
            "first_response_sessions": 0,
            "first_response_accepted_sessions": 0,
            "personalization_decisions": 0,
            "personalization_applied": 0,
            "wrong_personalization_events": 0,
            "injection_instruction_chars": 0,
            "clarification_chars": 0,
        }
        self.session_state = {}
        self.user_history = defaultdict(list)
        self.user_known_prefs = defaultdict(set)

    def _extract_pref_keywords(self, text: str) -> set:
        text_l = text.lower()
        prefs = set()
        if "bullet" in text_l or "list" in text_l:
            prefs.add("bullets")
        if "short" in text_l or "concise" in text_l or "brief" in text_l:
            prefs.add("concise")
        if "simple" in text_l or "beginner" in text_l or "layman" in text_l:
            prefs.add("simple")
        if "detail" in text_l or "expert" in text_l or "advanced" in text_l:
            prefs.add("detailed")
        return prefs

    def process(self, example: Dict[str, object]):
        rec = normalize_record(example)
        self.stats["total_records"] += 1

        user_id = rec["user_id"]
        session_id = rec["session_id"]
        role = rec["role"]
        text = rec["text"]

        if session_id not in self.session_state:
            self.session_state[session_id] = {"seen_user_turn": False, "had_clarification": False}

        if role != "user":
            return

        self.stats["user_turns"] += 1
        state = self.session_state[session_id]

        if not state["seen_user_turn"]:
            self.stats["first_response_sessions"] += 1
            state["seen_user_turn"] = True

        history = self.user_history[user_id] + [{"role": "user", "content": text}]
        profile = self.builder.extract_profile(history)
        should_inject = self.builder.should_inject(profile)
        instructions = self.builder.get_system_instructions(
            profile["uiv"], confidence=float(profile["confidence"])
        )

        self.stats["personalization_decisions"] += 1
        if should_inject and instructions:
            self.stats["personalization_applied"] += 1
            self.stats["injection_instruction_chars"] += len(instructions)

        is_clarification = self.detector.is_clarification(text)
        if is_clarification:
            self.stats["clarification_turns"] += 1
            self.stats["clarification_chars"] += len(text)
            state["had_clarification"] = True

            pref_keywords = self._extract_pref_keywords(text)
            if pref_keywords.intersection(self.user_known_prefs[user_id]):
                self.stats["preventable_clarifications"] += 1

            if should_inject:
                self.stats["wrong_personalization_events"] += 1

            self.user_known_prefs[user_id].update(pref_keywords)

        self.user_history[user_id].append({"role": "user", "content": text})

    def finalize(self) -> Dict[str, float]:
        accepted = 0
        for session_id in self.session_state:
            if not self.session_state[session_id]["had_clarification"]:
                accepted += 1
        self.stats["first_response_accepted_sessions"] = accepted

        user_turns = max(1, self.stats["user_turns"])
        clarifications = self.stats["clarification_turns"]
        decisions = max(1, self.stats["personalization_decisions"])
        injected = max(1, self.stats["personalization_applied"])
        first_sessions = max(1, self.stats["first_response_sessions"])

        return {
            "clarification_rate": clarifications / user_turns,
            "first_response_acceptance_rate": self.stats["first_response_accepted_sessions"] / first_sessions,
            "preventable_clarification_rate": self.stats["preventable_clarifications"] / max(1, clarifications),
            "wrong_personalization_rate": self.stats["wrong_personalization_events"] / injected,
            "token_savings_proxy": self.stats["clarification_chars"] / max(1, clarifications),
            "latency_overhead_proxy": self.stats["injection_instruction_chars"] / decisions,
            "total_user_turns": user_turns,
            "total_clarifications": clarifications,
        }
