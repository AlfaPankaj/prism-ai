# PRISM: Predicting Response Intent from Session Memory
**Author:** Pankaj Yadav  
**Date:** May 2026  
**Subject:** Personalization in Large Language Models (LLMs)

## 1. Abstract
The "Intent Alignment Tax" refers to the repetitive turns users spend correcting an LLM's output style, format, or complexity. This paper introduces **PRISM**, a model-agnostic framework that leverages chat history to predict and automate user intent. By extracting a User Intent Vector (UIV) and persisting it across sessions using a Big Data architecture, PRISM significantly reduces redundant user effort. Our evaluation using the OpenAssistant dataset demonstrates the presence of measurable intent correction patterns that can be automated.

## 2. Introduction
Current conversational AI systems (e.g., GPT-4, Llama) suffer from a "Cold Start" problem in every new session. They fail to remember that a specific user might always prefer bullet points or simple explanations. This leads to a cycle of:
1. User Query -> 2. AI Response -> 3. User Correction (The "Tax") -> 4. Corrected AI Response.
PRISM aims to move from Turn 1 directly to Turn 4.

## 3. Methodology
PRISM consists of four primary modules:
- **Clarification Detector**: A heuristic engine that identifies stylistic corrections.
- **UIV Builder**: Extracts preferences into a 3-dimensional vector (Format, Complexity, Style).
- **Persistent Profile Store**: A JSON-based document store for cross-session memory.
- **Prompt Adapter**: A system-prompt injection layer.

### 3.1 Experimental Setup
- **Model**: Llama 3.2:3b (Running locally via Ollama).
- **Dataset**: OpenAssistant/oasst1 (Streaming via Hugging Face).
- **Metric**: Frequency of Clarification Turns (CT) per 10,000 messages.

## 4. Results & Analysis
In our evaluation of 10,000 real-world messages from the OpenAssistant dataset, we identified:
- **Total Clarification Turns Detected**: 27
- **Intent Vectors Extracted**: Successfully mapped users to "Concise", "Simple", and "Bulleted" preferences.
- **System Impact**: By injecting the UIV into the Llama 3.2:3b system prompt, we demonstrated that the model correctly adhered to the user's previously stated style without the user needing to repeat it in the new query.

## 5. Conclusion
PRISM proves that "Big Data" principles of user profiling can be effectively applied to AI orchestration. By treating user intent as a persistent asset rather than a transient session state, we can build AI systems that feel more intuitive, personal, and efficient.

## 6. References
- *Hugging Face Datasets: OpenAssistant/oasst1 (2023)*
- *Ollama: Local LLM Orchestration Framework (2024)*
- *Gradio: Interactive Machine Learning Web Interfaces (2024)*

## 7. Production Hardening Update (v1)
To move PRISM from research prototype to deployable system, we implemented a six-phase hardening plan:

1. Hybrid intent extraction with confidence scoring and abstain behavior.
2. Temporal decay over user preference history.
3. Profile lifecycle APIs (save/view/edit/reset + temporary overrides).
4. Structured telemetry for personalization decisions and user correction events.
5. Storage hardening with profile schema v2, export/delete controls, and retention hooks.
6. Operational guardrails including a personalization rollback switch and drift alerts.

### 7.1 New Evaluation Metrics
PRISM evaluation now includes production-style metrics in addition to clarification counting:
- **clarification_rate**
- **first_response_acceptance_rate**
- **preventable_clarification_rate**
- **wrong_personalization_rate**
- **token_savings_proxy**
- **latency_overhead_proxy**

These are computed by the upgraded research evaluation pipeline and exported to `research\outputs\evaluation_metrics.json`.

### 7.2 Dataset Consistency Note
This repository currently uses `OpenAssistant/oasst1` in code. If publishing a paper version that mentions a different dataset, keep dataset references synchronized across code, markdown documents, and manuscript tables.
