import os

import gradio as gr
import ollama

from prism import PrismAdapter, UIVBuilder
from prism.storage import JSONProfileStore
from prism.metrics.clarification import ClarificationDetector
from prism.metrics.telemetry import LocalMetricsLogger
from prism.metrics.drift import DriftMonitor

builder = UIVBuilder()
adapter = PrismAdapter()
store = JSONProfileStore()
detector = ClarificationDetector()
metrics_logger = LocalMetricsLogger()
drift_monitor = DriftMonitor()

MODEL_NAME = "llama3.2:3b"
PERSONALIZATION_ENABLED = os.getenv("PRISM_DISABLE_PERSONALIZATION", "0") != "1"


def process_chat(message, history, user_id):
    prism_history = []
    for msg_obj in history:
        content = msg_obj["content"]
        if isinstance(content, list):
            content = " ".join([item["text"] for item in content if "text" in item])
        prism_history.append({"role": msg_obj["role"], "content": str(content)})

    current_message_str = message
    if isinstance(message, list):
        current_message_str = " ".join([item["text"] for item in message if "text" in item])

    is_correction = detector.is_clarification(str(current_message_str))
    metrics_logger.record_user_feedback(user_id, str(current_message_str), is_correction=is_correction)

    full_history_for_uiv = prism_history + [{"role": "user", "content": str(current_message_str)}]
    previous_uiv = store.get_uiv(user_id, use_override=True) or builder.DEFAULT_UIV.copy()
    profile = builder.extract_profile(full_history_for_uiv, previous_uiv=previous_uiv, decay=0.7)
    uiv = profile["uiv"]
    should_inject = builder.should_inject(profile) and PERSONALIZATION_ENABLED

    store.save_profile(
        user_id,
        uiv=uiv,
        confidence=float(profile["confidence"]),
        axis_confidence=profile["axis_confidence"],
        source="inferred",
    )
    metrics_logger.record_injection_decision(
        user_id=user_id,
        confidence=float(profile["confidence"]),
        signal_count=int(profile["signal_count"]),
        injected=should_inject,
        uiv=uiv,
    )

    messages = (
        adapter.wrap_messages(full_history_for_uiv, profile=profile)
        if PERSONALIZATION_ENABLED
        else full_history_for_uiv
    )

    try:
        response = ollama.chat(model=MODEL_NAME, messages=messages)
        bot_message = response["message"]["content"]
    except Exception as e:
        bot_message = f"Error calling Ollama: {str(e)}\nMake sure Ollama is running and '{MODEL_NAME}' is pulled."

    optimized_prompt_str = ""
    for m in messages:
        optimized_prompt_str += f"[{m['role'].upper()}]: {m['content']}\n\n"

    return bot_message, str(uiv), optimized_prompt_str


def load_user_profile(user_id):
    profile = store.get_profile(user_id)
    if profile:
        effective_uiv = store.get_uiv(user_id, use_override=True)
        source = profile.get("metadata", {}).get("source", "unknown")
        confidence = profile.get("metadata", {}).get("confidence", 0.0)
        drift = drift_monitor.evaluate(metrics_logger.get_counters())
        return (
            f"Loaded profile for {user_id}: {effective_uiv} "
            f"(source={source}, confidence={confidence:.2f}, "
            f"drift_healthy={drift['healthy']}, personalization_enabled={PERSONALIZATION_ENABLED})"
        )
    return f"No profile found for {user_id}. Starting fresh."


with gr.Blocks() as demo:
    gr.Markdown("# 💎 PRISM: AI Recommendation Engine Demo")
    gr.Markdown("### *Big Data Meets AI Personalization*")

    with gr.Row():
        with gr.Column(scale=2):
            user_id_input = gr.Textbox(label="User ID", value="guest_user")
            load_btn = gr.Button("Load Profile from Store")
            status = gr.Markdown("Status: Ready")

            chatbot = gr.Chatbot(height=400)
            msg = gr.Textbox(label="Type your message (e.g., 'Explain AI' or 'Be more concise')")
            clear = gr.ClearButton([msg, chatbot])

        with gr.Column(scale=1):
            gr.Markdown("### 🧠 PRISM Brain (Real-time Analysis)")
            uiv_display = gr.Label(label="Current User Intent Vector (UIV)")
            adapted_prompt_display = gr.Textbox(label="The 'Adapted Prompt' sent to LLM", interactive=False, lines=10)

    def respond(message, chat_history, user_id):
        bot_message, uiv_str, optimized_prompt = process_chat(message, chat_history, user_id)
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": bot_message})
        return "", chat_history, uiv_str, optimized_prompt

    msg.submit(respond, [msg, chatbot, user_id_input], [msg, chatbot, uiv_display, adapted_prompt_display])
    load_btn.click(load_user_profile, [user_id_input], [status])


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
