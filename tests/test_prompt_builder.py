from core import PROMPT_CONFIG
from prompt.builder import build_prompt


def test_default_prompt_includes_sprint_data():
    data = {"sprint": {"name": "Sprint 1"}, "metrics": {"total": 5}}
    prompt = build_prompt(data)
    assert "Sprint 1" in prompt
    assert '"total": 5' in prompt
    assert "{sprint_data}" not in prompt


def test_string_sprint_data():
    prompt = build_prompt("raw text input")
    assert "raw text input" in prompt


def test_additional_instructions():
    prompt = build_prompt({"x": 1}, {"additional_instructions": "Focus on bugs."})
    assert "Focus on bugs." in prompt
    assert "Additional Instructions" in prompt


def test_custom_template_bypasses_config():
    prompt = build_prompt(
        {"sprint": {"name": "S2"}},
        {"template": "CUSTOM: {sprint_data}"},
    )
    assert prompt.startswith("CUSTOM:")
    assert "S2" in prompt


def test_config_sections_rendered():
    prompt = build_prompt({"x": 1})
    assert "Sprint Overview" in prompt
    assert "Key Accomplishments" in prompt
    assert "Risks & Blockers" in prompt
    assert "Recommendations" in prompt


def test_formatting_rules_rendered():
    prompt = build_prompt({"x": 1})
    assert "json" in prompt.lower()
    assert "450 words" in prompt
    assert "business_value_score" in prompt


def test_config_loads_successfully():
    config = PROMPT_CONFIG
    assert "role" in config
    assert "sections" in config
    assert len(config["sections"]) >= 4
    assert "formatting" in config
