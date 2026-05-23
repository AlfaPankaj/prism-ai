from typing import Dict, List, Optional

from prism.providers.utils import split_system_messages


def build_anthropic_payload(
    messages: List[Dict[str, str]],
    model: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Dict[str, object]:
    system_text, non_system = split_system_messages(messages)
    payload: Dict[str, object] = {
        "model": model,
        "messages": non_system,
        "max_tokens": int(max_tokens) if max_tokens is not None else 1024,
    }
    if system_text:
        payload["system"] = system_text
    if temperature is not None:
        payload["temperature"] = float(temperature)
    return payload
