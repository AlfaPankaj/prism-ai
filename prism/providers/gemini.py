from typing import Dict, List, Optional

from prism.providers.utils import split_system_messages


def build_gemini_payload(
    messages: List[Dict[str, str]],
    model: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Dict[str, object]:
    system_text, non_system = split_system_messages(messages)
    contents = []
    for msg in non_system:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": str(msg.get("content", ""))}]})

    payload: Dict[str, object] = {"model": model, "contents": contents}
    if system_text:
        payload["systemInstruction"] = {"parts": [{"text": system_text}]}

    generation_config: Dict[str, object] = {}
    if temperature is not None:
        generation_config["temperature"] = float(temperature)
    if max_tokens is not None:
        generation_config["maxOutputTokens"] = int(max_tokens)
    if generation_config:
        payload["generationConfig"] = generation_config
    return payload
