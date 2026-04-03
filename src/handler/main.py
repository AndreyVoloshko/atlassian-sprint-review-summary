"""Lambda entry point — thin routing layer, delegates everything."""

import json
import logging

from auth import validate_request
from bedrock import generate_summary
from core import BEDROCK_MODEL_ID, LOG_LEVEL, error, success
from prompt import build_prompt

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)


def lambda_handler(event: dict, context) -> dict:
    method = event.get("httpMethod", "")
    path = event.get("path", "")

    if method == "OPTIONS":
        return success({"message": "ok"})

    if path == "/health" and method == "GET":
        return success({"status": "healthy", "model": BEDROCK_MODEL_ID})

    if path != "/summarize" or method != "POST":
        return error(404, "Not found")

    auth_error = validate_request(event)
    if auth_error:
        return error(401, auth_error)

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error(400, "Invalid JSON body")

    sprint_data = body.get("sprint_data")
    if not sprint_data:
        return error(400, "Missing required field: sprint_data")

    prompt_context = body.get("prompt_context", {})
    model_params = body.get("model_params", {})

    try:
        prompt = build_prompt(sprint_data, prompt_context)
        logger.info("Prompt built: %d chars", len(prompt))
        logger.debug("Prompt: %s", prompt)

        summary = generate_summary(
            prompt,
            max_tokens=model_params.get("max_tokens"),
            temperature=model_params.get("temperature"),
            top_p=model_params.get("top_p"),
            model_id=model_params.get("model_id"),
        )
        logger.info("Summary generated: %d chars", len(summary))

        return success({
            "summary": summary,
            "model": model_params.get("model_id") or BEDROCK_MODEL_ID,
            "prompt_length": len(prompt),
        })

    except Exception:
        logger.exception("Summary generation failed")
        return error(500, "Failed to generate summary")
