"""Amazon Bedrock client for generating sprint summaries."""

import logging
from functools import lru_cache

import boto3
from botocore.config import Config

from core.config import (
    BEDROCK_MAX_TOKENS,
    BEDROCK_MODEL_ID,
    BEDROCK_REGION,
    BEDROCK_TEMPERATURE,
    BEDROCK_TOP_P,
)

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_client():
    """Lazily create and cache the Bedrock Runtime client.

    Lazy so that (a) tests don't need AWS credentials at import time and
    (b) the client is reused across warm Lambda invocations.
    """
    return boto3.client(
        "bedrock-runtime",
        region_name=BEDROCK_REGION,
        config=Config(
            connect_timeout=60,
            read_timeout=120,
            retries={"max_attempts": 2},
        ),
    )


def generate_summary(
    prompt: str,
    *,
    max_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    model_id: str | None = None,
) -> str:
    """Invoke Bedrock Converse API and return the generated text.

    All parameters fall back to environment-variable defaults (see core.config)
    when not provided, allowing per-request overrides from the API caller.
    """
    effective_model = model_id or BEDROCK_MODEL_ID
    effective_max_tokens = max_tokens if max_tokens is not None else BEDROCK_MAX_TOKENS
    effective_temperature = temperature if temperature is not None else BEDROCK_TEMPERATURE
    effective_top_p = top_p if top_p is not None else BEDROCK_TOP_P

    logger.info(
        "Invoking model=%s max_tokens=%d temperature=%.2f top_p=%.2f",
        effective_model, effective_max_tokens, effective_temperature, effective_top_p,
    )

    response = _get_client().converse(
        modelId=effective_model,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={
            "maxTokens": effective_max_tokens,
            "temperature": effective_temperature,
            "topP": effective_top_p,
        },
    )

    output = response["output"]["message"]["content"][0]["text"]

    usage = response.get("usage", {})
    logger.info(
        "Bedrock response: input_tokens=%s output_tokens=%s",
        usage.get("inputTokens", "?"),
        usage.get("outputTokens", "?"),
    )

    return output
