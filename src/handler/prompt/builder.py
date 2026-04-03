"""Builds the LLM prompt from root config.yaml and sprint data."""

import json
from typing import Any

from core.config import PROMPT_CONFIG


def build_prompt(sprint_data: Any, prompt_context: dict | None = None) -> str:
    """Assemble the full prompt from config + sprint data.

    Args:
        sprint_data: Sprint data (dict, list, or string).
        prompt_context: Optional per-request overrides:
            - template: Full prompt string (bypasses config prompt entirely).
            - additional_instructions: Extra instructions appended after the
              config-driven sections.
    """
    prompt_context = prompt_context or {}

    sprint_data_str = (
        json.dumps(sprint_data, indent=2, default=str)
        if isinstance(sprint_data, (dict, list))
        else str(sprint_data)
    )

    if custom_template := prompt_context.get("template"):
        return _render_custom_template(custom_template, sprint_data_str, prompt_context)

    return _render_from_config(sprint_data_str, prompt_context)


def _render_custom_template(template: str, sprint_data_str: str, ctx: dict) -> str:
    additional = ctx.get("additional_instructions", "")
    additional_block = f"\n## Additional Instructions\n\n{additional}\n" if additional else ""

    result = template.replace("{sprint_data}", sprint_data_str)
    result = result.replace("{additional_instructions}", additional_block)
    return result


def _render_from_config(sprint_data_str: str, ctx: dict) -> str:
    config = PROMPT_CONFIG

    parts: list[str] = []

    parts.append(config.get("role", "").strip())
    parts.append("")
    parts.append("## Instructions")
    parts.append("")
    parts.append("Analyze the sprint data below and produce a clear, well-structured summary covering:")
    parts.append("")

    for i, section in enumerate(config.get("sections", []), 1):
        parts.append(f"{i}. **{section['title']}** — {section['instruction'].strip()}")

    formatting = config.get("formatting", {})
    parts.append("")
    parts.append("## Formatting Rules")
    parts.append("")
    parts.append(f"- Output format: **{formatting.get('output_format', 'markdown')}**.")
    parts.append(f"- Keep the total summary under {formatting.get('max_words', 800)} words.")
    parts.append(f"- Tone: {formatting.get('tone', 'professional')}.")

    for rule in formatting.get("rules", []):
        parts.append(f"- {rule}")

    additional = ctx.get("additional_instructions", "")
    if additional:
        parts.append("")
        parts.append("## Additional Instructions")
        parts.append("")
        parts.append(additional)

    parts.append("")
    parts.append("## Sprint Data")
    parts.append("")
    parts.append("```json")
    parts.append(sprint_data_str)
    parts.append("```")

    return "\n".join(parts)
