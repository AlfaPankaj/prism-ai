import re


class ClarificationDetector:
    """
    Detects if a user turn is a 'clarification' or 'reformulation' turn
    triggered by dissatisfaction with a previous response.
    """

    REFORMULATION_KEYWORDS = [
        r"too (long|short|wordy|brief|complex|simple)",
        r"make it (shorter|longer|simpler|more detailed|concise)",
        r"be (more|less) (concise|detailed|brief|verbose)",
        r"give me (bullet points|bullets|a summary|an example)",
        r"instead of",
        r"don't use",
        r"explain (it|that) (again|differently)",
        r"in (other|simple|layman's) terms",
        r"i (meant|wanted|asked for)",
        r"not what i (asked|wanted)",
    ]

    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.REFORMULATION_KEYWORDS]

    def is_clarification(self, text: str) -> bool:
        """Returns True if the text matches a reformulation pattern."""
        if not text:
            return False
        return any(pattern.search(text) for pattern in self.patterns)

    def detect_in_history(self, history):
        """
        Scans a conversation history and identifies turns where
        the user clarified their intent.
        """
        clarifications = []
        for i, turn in enumerate(history):
            if turn.get("role") == "user" and i > 0:
                if self.is_clarification(turn.get("content", "")):
                    clarifications.append(
                        {
                            "turn_index": i,
                            "content": turn.get("content"),
                            "previous_assistant_turn": history[i - 1].get("content") if i > 0 else None,
                        }
                    )
        return clarifications
