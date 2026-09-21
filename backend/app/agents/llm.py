"""
Shared OpenAI helper for every agent.

This module exists to break the circular import that used to happen:

    supervisor.py  ->  qa_agent.py  ->  supervisor.py   (ask_llm)

Agents now import `ask_llm` from here, and this module imports nothing
from the agents package.
"""

from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL


class LLMError(Exception):
    """Raised when the language model cannot produce an answer."""


# The client is created lazily so that importing this module never
# crashes the whole application when the API key is missing.

_client = None


def get_client() -> OpenAI:
    """Return a cached OpenAI client, creating it on first use."""

    global _client

    if not OPENAI_API_KEY:
        raise LLMError(
            "OPENAI_API_KEY is not set. "
            "Add it to backend/.env and restart the server."
        )

    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)

    return _client


def ask_llm(prompt: str, system: str | None = None) -> str:
    """
    Send a prompt to the configured OpenAI model and return the text.

    Every failure is converted into an LLMError with a message that is
    safe and useful to show to the user.
    """

    if not prompt or not prompt.strip():
        raise LLMError("Cannot send an empty prompt to the language model.")

    client = get_client()

    messages = []

    if system:
        messages.append({"role": "system", "content": system})

    messages.append({"role": "user", "content": prompt})

    try:

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
        )

    except Exception as error:

        raise LLMError(
            _explain_openai_error(error)
        ) from error

    if not response.choices:
        raise LLMError("The language model returned an empty response.")

    answer = response.choices[0].message.content

    if not answer or not answer.strip():
        raise LLMError("The language model returned an empty response.")

    return answer.strip()


def _explain_openai_error(error: Exception) -> str:
    """Translate an OpenAI SDK exception into a readable message."""

    text = str(error)

    status = getattr(error, "status_code", None)

    if status == 401 or "invalid_api_key" in text or "Incorrect API key" in text:
        return (
            "OpenAI rejected the API key (401). "
            "Check OPENAI_API_KEY in backend/.env."
        )

    if status == 404 or "model_not_found" in text or "does not exist" in text:
        return (
            f"The model '{OPENAI_MODEL}' is not available for this API key. "
            "Set OPENAI_MODEL in backend/.env to a model you can use "
            "(for example gpt-4o-mini)."
        )

    if status == 429 or "rate_limit" in text or "insufficient_quota" in text:
        return (
            "OpenAI request was rejected (429): rate limit reached or the "
            "account has no remaining quota."
        )

    if "Connection" in text or "timeout" in text.lower():
        return "Could not reach the OpenAI API. Check your internet connection."

    return f"OpenAI request failed: {text}"
