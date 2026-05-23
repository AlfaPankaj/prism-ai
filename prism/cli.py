import argparse
import json
import os
import sys
from typing import Dict, List, Optional

from prism import PrismAdapter, UIVBuilder
from prism.providers import (
    build_anthropic_payload,
    build_gemini_payload,
    build_openai_payload,
)
from prism.storage import JSONProfileStore


DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-latest",
    "gemini": "gemini-1.5-flash",
}


def _coerce_content(content: object) -> str:
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(str(item))
        return " ".join(parts)
    if content is None:
        return ""
    return str(content)


def _coerce_messages(raw_messages: List[Dict[str, object]]) -> List[Dict[str, str]]:
    messages = []
    for msg in raw_messages:
        if not isinstance(msg, dict):
            raise ValueError("Each message must be a JSON object with role/content fields.")
        role = str(msg.get("role") or msg.get("speaker") or "user").lower()
        if role not in {"user", "assistant", "system"}:
            role = "user"
        content = _coerce_content(
            msg.get("content")
            or msg.get("text")
            or msg.get("message")
            or msg.get("prompt")
        )
        messages.append({"role": role, "content": content})
    return messages


def _load_json_file(path: str) -> object:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_history(path: Optional[str]) -> List[Dict[str, str]]:
    if not path:
        return []
    data = _load_json_file(path)
    if not isinstance(data, list):
        raise ValueError("History file must contain a JSON array of message objects.")
    return _coerce_messages(data)


def _read_message(args: argparse.Namespace) -> Optional[str]:
    sources = [bool(args.message), bool(args.message_file), bool(args.stdin)]
    if sum(1 for s in sources if s) > 1:
        raise ValueError("Use only one of --message, --message-file, or --stdin.")
    if args.message:
        return args.message
    if args.message_file:
        with open(args.message_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    if args.stdin:
        return sys.stdin.read().strip()
    return None


def _build_profile_messages(
    history: List[Dict[str, str]],
    message: Optional[str],
) -> List[Dict[str, str]]:
    messages = list(history)
    if message:
        messages.append({"role": "user", "content": message})
    if not messages:
        raise ValueError("No messages provided. Use --message, --stdin, or --history.")
    return messages


def _build_payload(provider: str, messages: List[Dict[str, str]], args: argparse.Namespace) -> Dict[str, object]:
    model = args.model or DEFAULT_MODELS[provider]
    if provider == "openai":
        return build_openai_payload(messages, model, args.temperature, args.max_tokens)
    if provider == "anthropic":
        return build_anthropic_payload(messages, model, args.temperature, args.max_tokens)
    if provider == "gemini":
        return build_gemini_payload(messages, model, args.temperature, args.max_tokens)
    raise ValueError(f"Unsupported provider: {provider}")


def run_adapt(args: argparse.Namespace) -> int:
    history = _load_history(args.history)
    message = _read_message(args)
    messages = _build_profile_messages(history, message)

    builder = UIVBuilder()
    adapter = PrismAdapter()
    personalization_enabled = os.getenv("PRISM_DISABLE_PERSONALIZATION", "0") != "1"

    store = None if args.no_store else JSONProfileStore(base_path=args.profiles_path or "data/profiles")
    previous_uiv = store.get_uiv(args.user_id, use_override=True) if store else None

    profile = builder.extract_profile(messages, previous_uiv=previous_uiv, decay=0.7)
    if store:
        store.save_profile(
            args.user_id,
            uiv=profile["uiv"],
            confidence=float(profile["confidence"]),
            axis_confidence=profile["axis_confidence"],
            source="inferred",
        )

    adapted_messages = adapter.wrap_messages(messages, profile=profile) if personalization_enabled else messages
    payload = _build_payload(args.provider, adapted_messages, args)

    result = payload if args.payload_only else {
        "provider": args.provider,
        "uiv": profile["uiv"],
        "confidence": float(profile["confidence"]),
        "payload": payload,
    }
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prism", description="PRISM CLI plugin for LLM providers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    adapt = subparsers.add_parser("adapt", help="Generate provider payload with PRISM injection.")
    adapt.add_argument("--provider", choices=["openai", "anthropic", "gemini"], required=True)
    adapt.add_argument("--model", help="Override default provider model.")
    adapt.add_argument("--history", help="Path to JSON file containing message history.")
    adapt.add_argument("--message", help="User message to append to history.")
    adapt.add_argument("--message-file", help="Read the user message from a file.")
    adapt.add_argument("--stdin", action="store_true", help="Read the user message from STDIN.")
    adapt.add_argument("--user-id", default="cli_user", help="Profile user id for persistence.")
    adapt.add_argument("--profiles-path", help="Directory for profile storage.")
    adapt.add_argument("--no-store", action="store_true", help="Do not persist profile updates.")
    adapt.add_argument("--max-tokens", type=int, help="Max tokens / output tokens for provider.")
    adapt.add_argument("--temperature", type=float, help="Sampling temperature for provider.")
    adapt.add_argument("--payload-only", action="store_true", help="Output only provider payload JSON.")
    adapt.set_defaults(func=run_adapt)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
