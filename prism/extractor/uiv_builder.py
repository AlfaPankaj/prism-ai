import re
from typing import Dict, List, Optional

from prism.metrics.clarification import ClarificationDetector

class UIVBuilder:
    """
    Builds and maintains a User Intent Vector (UIV) from conversation history.
    Uses a hybrid signal approach with confidence estimation and temporal decay.
    """

    DEFAULT_UIV = {
        "format": "default",
        "complexity": "default",
        "style": "default",
    }

    AXIS_LABELS = {
        "format": ("default", "bullets", "paragraph"),
        "complexity": ("default", "simple", "detailed"),
        "style": ("default", "concise", "detailed"),
    }

    SIGNAL_PATTERNS = [
        (re.compile(r"\b(bullet points?|bullets?|list|numbered)\b", re.IGNORECASE), {"format": ("bullets", 1.0)}),
        (re.compile(r"\b(paragraphs?|prose)\b", re.IGNORECASE), {"format": ("paragraph", 1.0)}),
        (re.compile(r"\b(simple|simpler|layman|beginner|plain language|explain like i[' ]?m 5)\b", re.IGNORECASE), {"complexity": ("simple", 1.0)}),
        (re.compile(r"\b(advanced|expert|detailed|more detail|deep dive|technical)\b", re.IGNORECASE), {"complexity": ("detailed", 1.0)}),
        (re.compile(r"\b(short|brief|concise|to the point|in a hurry|quickly)\b", re.IGNORECASE), {"style": ("concise", 1.0)}),
        (re.compile(r"\b(long|elaborate|thorough|in depth)\b", re.IGNORECASE), {"style": ("detailed", 1.0)}),
    ]

    def __init__(self):
        self.detector = ClarificationDetector()

    def _is_user_turn(self, turn: Dict[str, str]) -> bool:
        return turn.get("role") == "user" and bool(turn.get("content"))

    def _one_hot_distribution(self, axis: str, value: str) -> Dict[str, float]:
        dist = {label: 0.0 for label in self.AXIS_LABELS[axis]}
        if value in dist:
            dist[value] = 1.0
        else:
            dist["default"] = 1.0
        return dist

    def _normalize(self, scores: Dict[str, float]) -> Dict[str, float]:
        total = sum(scores.values())
        if total <= 0:
            return {k: 0.0 for k in scores}
        return {k: v / total for k, v in scores.items()}

    def _confidence_from_distribution(self, distribution: Dict[str, float]) -> float:
        ordered = sorted(distribution.values(), reverse=True)
        if not ordered:
            return 0.0
        if len(ordered) == 1:
            return 1.0
        return max(0.0, min(1.0, ordered[0] - ordered[1]))

    def extract_profile(
        self,
        history: List[Dict[str, str]],
        previous_uiv: Optional[Dict[str, str]] = None,
        decay: float = 0.7,
    ) -> Dict[str, object]:
        """
        Hybrid extraction with temporal decay against previous UIV.
        Returns UIV + confidence metadata for downstream gating.
        """
        bounded_decay = max(0.0, min(1.0, decay))
        axis_scores = {
            axis: {label: 0.1 for label in labels} for axis, labels in self.AXIS_LABELS.items()
        }

        clarifications = self.detector.detect_in_history(history)
        clarification_indexes = {item["turn_index"] for item in clarifications}

        signal_count = 0
        for index, turn in enumerate(history):
            if not self._is_user_turn(turn):
                continue

            content = str(turn.get("content", ""))
            turn_weight = 1.0 if index in clarification_indexes else 0.35

            for pattern, signal_map in self.SIGNAL_PATTERNS:
                if not pattern.search(content):
                    continue
                signal_count += 1
                for axis, (label, weight) in signal_map.items():
                    axis_scores[axis][label] += weight * turn_weight

        current_distribution = {
            axis: self._normalize(scores) for axis, scores in axis_scores.items()
        }

        blended_distribution = {}
        for axis in self.AXIS_LABELS:
            if previous_uiv:
                previous_value = previous_uiv.get(axis, "default")
                previous_dist = self._one_hot_distribution(axis, previous_value)
                prior_weight = bounded_decay if previous_value != "default" else (bounded_decay * 0.25)
                blended_distribution[axis] = {
                    label: (prior_weight * previous_dist[label]) + ((1 - prior_weight) * current_distribution[axis][label])
                    for label in self.AXIS_LABELS[axis]
                }
            else:
                blended_distribution[axis] = current_distribution[axis]

        uiv = {}
        axis_confidence = {}
        for axis, dist in blended_distribution.items():
            best_label = max(dist, key=dist.get)
            uiv[axis] = best_label
            axis_confidence[axis] = self._confidence_from_distribution(dist)

        overall_confidence = sum(axis_confidence.values()) / len(axis_confidence)

        return {
            "uiv": uiv,
            "axis_confidence": axis_confidence,
            "confidence": overall_confidence,
            "signal_count": signal_count,
        }

    def extract(
        self,
        history: List[Dict[str, str]],
        previous_uiv: Optional[Dict[str, str]] = None,
        decay: float = 0.7,
    ) -> Dict[str, str]:
        """
        Backward-compatible extractor that returns only the UIV dictionary.
        """
        return self.extract_profile(history, previous_uiv=previous_uiv, decay=decay)["uiv"]

    def should_inject(
        self,
        profile: Dict[str, object],
        min_confidence: float = 0.20,
        min_signal_count: int = 1,
    ) -> bool:
        confidence = float(profile.get("confidence", 0.0))
        signal_count = int(profile.get("signal_count", 0))
        return confidence >= min_confidence and signal_count >= min_signal_count

    def get_system_instructions(
        self,
        uiv: Dict[str, str],
        confidence: Optional[float] = None,
        min_confidence: float = 0.20,
    ) -> str:
        """Converts a UIV into a string of system instructions."""
        if confidence is not None and confidence < min_confidence:
            return ""

        instructions = []

        if uiv["format"] == "bullets":
            instructions.append("Use bullet points for lists and key information.")
        elif uiv["format"] == "paragraph":
            instructions.append("Use full, descriptive paragraphs.")

        if uiv["complexity"] == "simple":
            instructions.append("Explain concepts simply, as if to a beginner.")
        elif uiv["complexity"] == "detailed":
            instructions.append("Provide advanced, expert-level technical details.")

        if uiv["style"] == "concise":
            instructions.append("Be as brief and concise as possible.")
        elif uiv["style"] == "detailed":
            instructions.append("Provide thorough and elaborate explanations.")

        if not instructions:
            return ""

        return "ADAPTED USER PREFERENCES: " + " ".join(instructions)
