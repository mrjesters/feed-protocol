"""Model adapters — one `ask()` over OpenAI / Anthropic / Gemini, plus a `mock`
provider for offline pipeline testing. SDKs are imported lazily so the harness runs
(in mock mode) without any of them installed.

Keys come from the environment: OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY.
A neutral system prompt is used on purpose — we are testing whether the document's OWN
instructions work, not adding grounding instructions ourselves.
"""

from __future__ import annotations

import os

NEUTRAL_SYSTEM = "You are a helpful assistant."

DEFAULT_MODELS = {
    "openai": os.getenv("FEED_EVAL_OPENAI_MODEL", "gpt-4o-mini"),
    "anthropic": os.getenv("FEED_EVAL_ANTHROPIC_MODEL", "claude-haiku-4-5"),
    "gemini": os.getenv("FEED_EVAL_GEMINI_MODEL", "gemini-2.0-flash"),
}
MAX_TOKENS = int(os.getenv("FEED_EVAL_MAX_TOKENS", "500"))


def ask(provider: str, user_content: str, model: str | None = None) -> str:
    """Send one message to a provider and return the answer text."""
    provider = provider.lower()
    model = model or DEFAULT_MODELS.get(provider)
    if provider == "mock":
        return _mock(user_content)
    if provider == "openai":
        return _openai(user_content, model)
    if provider == "anthropic":
        return _anthropic(user_content, model)
    if provider == "gemini":
        return _gemini(user_content, model)
    raise ValueError(f"unknown provider: {provider}")


def _openai(content: str, model: str) -> str:
    from openai import OpenAI
    client = OpenAI()
    r = client.chat.completions.create(
        model=model, max_tokens=MAX_TOKENS, temperature=0,
        messages=[{"role": "system", "content": NEUTRAL_SYSTEM},
                  {"role": "user", "content": content}],
    )
    return r.choices[0].message.content or ""


def _anthropic(content: str, model: str) -> str:
    import anthropic
    client = anthropic.Anthropic()
    r = client.messages.create(
        model=model, max_tokens=MAX_TOKENS, system=NEUTRAL_SYSTEM,
        messages=[{"role": "user", "content": content}],
    )
    return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")


def _gemini(content: str, model: str) -> str:
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    r = client.models.generate_content(model=model, contents=f"{NEUTRAL_SYSTEM}\n\n{content}")
    return r.text or ""


# --- offline mock: canned answers so the pipeline runs with no keys/SDKs ---
def _mock(content: str) -> str:
    # isolate the question (real providers see the whole message; the mock keys off the
    # question so its canned answers are sensible).
    c = content.rsplit("QUESTION:", 1)[-1].lower()
    if "joint gap" in c:
        return "The auxiliary spillway joint gap has widened to 9 mm, above the 6 mm serviceable limit [E001]."
    if "what should we do" in c or "by when" in c:
        return ("Schedule remedial joint sealing before November 2026 — the sealant is end-of-life, "
                "with the joint gap at 9 mm past the 6 mm limit [E001] and hardness down to 35 from 55 [E002].")
    if "storage capacity" in c or "megalitres" in c:
        return "Not supported by this document."
    if "biggest safety risk" in c:
        return "Not supported by this document."
    if "confirm ingestion" in c:
        return "FEED v0.2 · grounding: STRICT · 3 evidence (E001–E003) loaded. I will cite IDs or decline."
    return "Not supported by this document."
