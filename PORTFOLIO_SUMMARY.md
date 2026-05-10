# PRISM: Predicting Response Intent from Session Memory
### *The "Recommendation Engine" for Artificial Intelligence*

## 🌟 The Vision: "Big Data Meets AI"
In traditional e-commerce, companies like **Amazon** don't wait for you to search for a product if they already know your preferences from your search history. They anticipate your needs.

**PRISM** brings this "Big Data" philosophy to the world of Generative AI. Currently, AI models treat every session like a "cold start," forcing users to repeat instructions like *"be concise,"* *"use bullet points,"* or *"explain simply."* This is what I call the **"Intent Alignment Tax"**—a waste of human time and machine tokens.

PRISM is a model-agnostic framework that analyzes chat history to build a **User Intent Vector (UIV)**, ensuring the AI gets the response right on the **first try**.

---

## 🏗️ Technical Architecture

PRISM is built as a modular Python library with four core engineering layers:

### 1. The Metric Layer (Clarification Detector)
- **Problem**: How do we measure frustration?
- **Solution**: A regex and NLP-based engine that scans for "reformulation patterns" (e.g., *"not what I asked,"* *"make it shorter"*). It quantifies the "Tax" being paid in any dataset.

### 2. The Extraction Layer (UIV Builder)
- **Process**: Translates raw chat history into a mathematical **User Intent Vector**.
- **Dimensions**: Tracks **Format** (Bullets vs. Paragraphs), **Complexity** (Beginner vs. Expert), and **Style** (Concise vs. Detailed).

### 3. The Storage Layer (Big Data Persistence)
- **Architecture**: A JSON-based document store (inspired by **MongoDB**) that persists user profiles across sessions and days.
- **Persistence**: Even if a user returns after a month, PRISM retrieves their "Intent Profile" to calibrate the very first prompt of the new session.

### 4. The Adapter Layer (Model-Agnostic Integration)
- **Integration**: Integrated with **Llama 3.2:3b via Ollama** for a fully local, privacy-focused experience.
- **Action**: Dynamically injects "Hidden Context" into the system prompt, automating the user's preferences without them typing a single extra word.

---

## 🔬 Research & Methodology
I evaluated PRISM using the **OpenAssistant/oasst1** dataset. 
- **Methodology**: Developed a retrospective analysis script to identify "Preventable Turns"—instances where a user's intent was already clear from past data but the AI failed to adapt.
- **Engineering Rigor**: The project includes a full test suite and a research-ready data pipeline for streaming large-scale Hugging Face datasets.

---

## 🚀 Impact & Future
PRISM transforms AI from a **Reactive tool** into a **Proactive assistant**. 
- **Token Efficiency**: Reduces the need for multi-turn clarifications.
- **User Experience**: Creates a "Hyper-Personalized" feel, similar to high-end recommendation systems.
- **Interactive Demo**: Features a **Gradio-based Web UI** that visualizes the intent extraction and the "Adapted Prompt" sent to the local LLM.

---

## 🛠️ Built With
- **Language**: Python
- **LLM Engine**: Ollama (Llama 3.2:3b)
- **Web UI**: Gradio
- **Data Engineering**: Hugging Face `datasets`, `pandas`
- **Persistence**: JSON Document Store

---
*Created by Pankaj yadav as a showcase of bridging Data Engineering principles with LLM Orchestration.*
