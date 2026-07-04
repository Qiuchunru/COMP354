from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from sponsor_pipeline.config import Settings


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required. Set it in your environment or .env file."
            )
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    def complete(self, prompt: str, context: dict[str, Any] | None = None) -> str:
        user_content = prompt
        if context:
            user_content += "\n\nContext:\n" + json.dumps(context, indent=2, default=str)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a sponsor research assistant for Hack Canada, "
                        "a student hackathon with a strong Waterloo and Canadian audience. "
                        "Be realistic about sponsorship fit, not company fame."
                    ),
                },
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    def complete_structured(self, prompt: str, schema_hint: str) -> dict[str, Any]:
        full_prompt = (
            f"{prompt}\n\n"
            f"Return ONLY valid JSON matching this shape:\n{schema_hint}\n"
            "Do not include markdown fences."
        )
        text = self.complete(full_prompt)
        return _parse_json(text)


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)
