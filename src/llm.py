"""Thin Ollama wrapper that returns schema-validated JSON (structured outputs)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

import httpx
import ollama
from pydantic import BaseModel, ValidationError

from config import (
    KPI_MODEL,
    LLM_MAX_OUTPUT_TOKENS,
    LLM_NUM_CTX,
    LLM_SEED,
    LLM_TEMPERATURE,
    LLM_TIMEOUT_S,
    OLLAMA_HOST,
)

log = logging.getLogger(__name__)


@dataclass
class LLMStats:
    """Counts LLM calls and time spent, per run."""

    calls: int = 0
    retries: int = 0
    seconds: float = 0.0
    prompt_tokens: int = 0
    output_tokens: int = 0
    log: list[dict] = field(default_factory=list)


class LLMError(RuntimeError):
    """Raised when the model fails to return valid JSON after retrying."""


_client: ollama.Client | None = None


def _get_client() -> ollama.Client:
    global _client
    if _client is None:
        _client = ollama.Client(host=OLLAMA_HOST, timeout=LLM_TIMEOUT_S)
    return _client


def _chat_with_retry(model: str, msgs: list[dict], schema: type[BaseModel], options: dict):
    """One chat call; on a timeout or connection error, wait and try once more."""
    for attempt in range(2):
        try:
            return _get_client().chat(model=model, messages=msgs, keep_alive="30m",
                                      format=schema.model_json_schema(), options=options)
        except (httpx.TimeoutException, httpx.TransportError) as e:
            if attempt == 1:
                raise LLMError(f"Ollama call failed twice: {type(e).__name__}") from e
            log.warning("Ollama call failed (%s); retrying in 20s", type(e).__name__)
            time.sleep(20)
    raise AssertionError("unreachable")


def chat_json(
    messages: list[dict],
    schema: type[BaseModel],
    model: str = KPI_MODEL,
    stats: LLMStats | None = None,
    retries: int = 1,
) -> dict:
    """Send `messages` to Ollama with `schema` as the JSON output format.

    Validates the reply with Pydantic and retries once (feeding back the error) when the
    JSON is invalid. Returns the validated object as a dict.
    """
    msgs = list(messages)
    options = {"temperature": LLM_TEMPERATURE, "seed": LLM_SEED, "num_ctx": LLM_NUM_CTX,
               "num_predict": LLM_MAX_OUTPUT_TOKENS}
    last_err = ""
    for attempt in range(retries + 1):
        start = time.perf_counter()
        resp = _chat_with_retry(model, msgs, schema, options)
        elapsed = time.perf_counter() - start
        content = resp.message.content or ""
        log.info("llm %s: %.1fs, prompt %s tok, output %s tok", schema.__name__, elapsed,
                 resp.prompt_eval_count, resp.eval_count)
        if stats is not None:
            stats.calls += 1
            stats.retries += int(attempt > 0)
            stats.seconds += elapsed
            stats.prompt_tokens += resp.prompt_eval_count or 0
            stats.output_tokens += resp.eval_count or 0
            stats.log.append({"schema": schema.__name__, "seconds": round(elapsed, 2),
                              "prompt_tokens": resp.prompt_eval_count,
                              "output_tokens": resp.eval_count})
        try:
            return schema.model_validate_json(content).model_dump()
        except ValidationError as e:
            last_err = str(e)[:800]
            msgs = [*msgs, {"role": "assistant", "content": content},
                    {"role": "user", "content": f"That JSON was invalid: {last_err}\n"
                     "Return corrected JSON that matches the schema exactly."}]
    raise LLMError(f"invalid JSON after {retries + 1} attempts: {last_err}")
