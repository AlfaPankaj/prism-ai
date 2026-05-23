from typing import Dict, List, Tuple


def split_system_messages(messages: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
    system_parts = []
    non_system = []
    for msg in messages:
        if msg.get("role") == "system":
            content = str(msg.get("content", ""))
            if content:
                system_parts.append(content)
        else:
            non_system.append(msg)
    return "\n\n".join(system_parts), non_system
