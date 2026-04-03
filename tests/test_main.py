import json
from unittest.mock import patch

from main import lambda_handler


def test_health(api_event):
    result = lambda_handler(api_event("GET", "/health"), None)
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["status"] == "healthy"
    assert "model" in body


def test_options_returns_cors(api_event):
    result = lambda_handler(api_event("OPTIONS", "/summarize"), None)
    assert result["statusCode"] == 200
    assert "Access-Control-Allow-Origin" in result["headers"]


def test_not_found(api_event):
    result = lambda_handler(api_event("GET", "/nope"), None)
    assert result["statusCode"] == 404


def test_missing_body(api_event):
    result = lambda_handler(api_event(body=None), None)
    assert result["statusCode"] == 400


def test_invalid_json_body(api_event):
    result = lambda_handler(api_event(body="not json"), None)
    assert result["statusCode"] == 400
    assert "Invalid JSON" in json.loads(result["body"])["error"]


def test_missing_sprint_data(api_event):
    result = lambda_handler(api_event(body=json.dumps({"other": 1})), None)
    assert result["statusCode"] == 400
    assert "sprint_data" in json.loads(result["body"])["error"]


@patch("main.generate_summary", return_value="## Summary\nAll done.")
def test_successful_summary(mock_gen, api_event):
    body = json.dumps({"sprint_data": {"sprint": {"name": "Sprint 1"}}})
    result = lambda_handler(api_event(body=body), None)
    assert result["statusCode"] == 200
    data = json.loads(result["body"])
    assert data["summary"] == "## Summary\nAll done."
    assert data["model"] == "eu.amazon.nova-micro-v1:0"
    assert data["prompt_length"] > 0
    mock_gen.assert_called_once()


@patch("main.generate_summary", return_value="Short.")
def test_model_params_forwarded(mock_gen, api_event):
    body = json.dumps({
        "sprint_data": {"x": 1},
        "model_params": {"max_tokens": 100, "temperature": 0.1},
    })
    lambda_handler(api_event(body=body), None)
    _, kwargs = mock_gen.call_args
    assert kwargs["max_tokens"] == 100
    assert kwargs["temperature"] == 0.1


@patch("main.generate_summary", side_effect=RuntimeError("boom"))
def test_bedrock_error_returns_500(mock_gen, api_event):
    body = json.dumps({"sprint_data": {"sprint": {"name": "S1"}}})
    result = lambda_handler(api_event(body=body), None)
    assert result["statusCode"] == 500
    assert "Failed" in json.loads(result["body"])["error"]
