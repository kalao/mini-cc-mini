from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from openai import OpenAI


@dataclass
class LLMResponse:
    message: dict[str, Any]
    text: str
    tool_calls: list[dict[str, Any]]


class LLMClient:
    def __init__(self, api_key: str, base_url: str | None, model: str):
        self.model = model
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int = 4096,
    ) -> LLMResponse:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools or None,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        msg = choice.message
        message = {
            "role": "assistant",
            "content": msg.content,
        }
        tool_calls: list[dict[str, Any]] = []
        if msg.tool_calls:
            message["tool_calls"] = []
            for call in msg.tool_calls:
                raw_args = call.function.arguments or "{}"
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append({
                    "id": call.id,
                    "name": call.function.name,
                    "arguments": args,
                })
                message["tool_calls"].append({
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": raw_args,
                    },
                })
        return LLMResponse(
            message=message,
            text=msg.content or "",
            tool_calls=tool_calls,
        )
