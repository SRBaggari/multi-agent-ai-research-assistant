"""
Shared OpenAI helper for every agent.

This module exists to break the circular import that used to happen:

    supervisor.py  ->  qa_agent.py  ->  supervisor.py   (ask_llm)

Agents now import `ask_llm` from here, and this module imports nothing
from the agents package.
"""

from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL


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
        # base_url is only passed when configured, so the default
        # behaviour (talking to OpenAI) is completely unchanged.
        if OPENAI_BASE_URL:
            _client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        else:
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
        where = OPENAI_BASE_URL or "OpenAI"
        return (
            f"The model '{OPENAI_MODEL}' is not available at {where}. "
            "Set OPENAI_MODEL in backend/.env to a model this provider offers."
        )

    # A 429 means two very different things, so tell them apart:
    # no money on the account vs. too many requests per minute.
    if "insufficient_quota" in text or "credit_balance_exhausted" in text \
            or "no credits remaining" in text:
        return (
            "Your OpenAI account has no credits left, so the answer could not "
            "be generated. Add credits at "
            "https://platform.openai.com/settings/organization/billing/ "
            "(the API key itself is valid)."
        )

    if status == 429 or "rate_limit" in text:
        return (
            "OpenAI is rate limiting the request (429). Wait a few seconds "
            "and try again."
        )

    if "Connection" in text or "timeout" in text.lower():
        return "Could not reach the OpenAI API. Check your internet connection."

    return f"OpenAI request failed: {text}"
