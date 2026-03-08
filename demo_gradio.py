from __future__ import annotations

import gradio as gr

from agent_logic import ask_agent_text


def chat_fn(question: str) -> str:
    return ask_agent_text(question, top_k=5)


demo = gr.Interface(
    fn=chat_fn,
    inputs=gr.Textbox(
        lines=2,
        label="שאל שאלה על תחנות טעינה",
        placeholder="לדוגמה: איפה יש עמדת DC מהירה בבאר שבע?",
    ),
    outputs=gr.Textbox(
        lines=12,
        label="תשובת הסוכן",
    ),
    title="Paz AI Charging Assistant",
    description="דמו מהיר של סוכן חיפוש והמלצה לעמדות טעינה",
)


if __name__ == "__main__":
    demo.launch(share=True)