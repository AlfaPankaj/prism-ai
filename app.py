import gradio as gr
import ollama
from prism import UIVBuilder, PrismAdapter
from prism.storage import JSONProfileStore

builder = UIVBuilder()
adapter = PrismAdapter()
store = JSONProfileStore()

MODEL_NAME = "llama3.2:3b"

def process_chat(message, history, user_id):
    # 1. Convert Gradio history to PRISM format
    # In newer Gradio, history is a list of dicts. 
    # Content can sometimes be a list (multimodal). We must ensure it is a string for Ollama.
    prism_history = []
    for msg_obj in history:
        content = msg_obj["content"]
        if isinstance(content, list):
            # Extract text from multimodal list if present
            content = " ".join([item["text"] for item in content if "text" in item])
        prism_history.append({"role": msg_obj["role"], "content": str(content)})
    
    # 2. Extract Intent Vector from history + current message
    current_message_str = message
    if isinstance(message, list):
        current_message_str = " ".join([item["text"] for item in message if "text" in item])
        
    full_history_for_uiv = prism_history + [{"role": "user", "content": str(current_message_str)}]
    uiv = builder.extract(full_history_for_uiv)
    
    # 3. Save to persistent store
    store.save_uiv(user_id, uiv)
    
    # 4. Get Optimized messages with PRISM instructions
    messages = adapter.wrap_messages(full_history_for_uiv)
    
    # 5. Call LOCAL Ollama Model
    try:
        response = ollama.chat(model=MODEL_NAME, messages=messages)
        bot_message = response['message']['content']
    except Exception as e:
        bot_message = f"Error calling Ollama: {str(e)}\nMake sure Ollama is running and '{MODEL_NAME}' is pulled."
        
    # Get the visual adapted prompt for the UI display
    optimized_prompt_str = ""
    for m in messages:
        optimized_prompt_str += f"[{m['role'].upper()}]: {m['content']}\n\n"
        
    return bot_message, str(uiv), optimized_prompt_str

def load_user_profile(user_id):
    uiv = store.get_uiv(user_id)
    if uiv:
        return f"Loaded existing profile for {user_id}: {uiv}"
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
