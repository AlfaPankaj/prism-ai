from typing import Dict, List, Optional


def build_openai_payload(
    messages: List[Dict[str, str]],
    model: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Dict[str, object]:
    payload: Dict[str, object] = {"model": model, "messages": messages}
    if temperature is not None:
        payload["temperature"] = float(temperature)
    if max_tokens is not None:
        payload["max_tokens"] = int(max_tokens)
    return payload
