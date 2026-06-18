from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .tool import ToolRegistry, ToolResult

if TYPE_CHECKING:
    from .llm import LLMClient


class Engine:
    def __init__(
        self,
        llm: "LLMClient",
        tools: ToolRegistry,
        system_prompt: str,
        max_steps: int = 12,
        max_tokens: int = 4096,
    ):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.max_tokens = max_tokens
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

    def run(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        final_text = ""

        for _ in range(self.max_steps):
            response = self.llm.chat(
                messages=self.messages,
                tools=self.tools.schemas(),
                max_tokens=self.max_tokens,
            )
            if response.text:
                print(response.text, end="" if response.text.endswith("\n") else "\n")
                final_text += response.text

            self.messages.append(response.message)
            if not response.tool_calls:
                return final_text

            for call in response.tool_calls:
                result = self._execute_tool(call["name"], call["arguments"])
                status = "error" if result.is_error else "ok"
                print(f"[tool:{call['name']}:{status}] {result.content[:300]}")
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": result.content,
                })

        warning = f"Stopped after max_steps={self.max_steps}."
        print(warning)
        return final_text + "\n" + warning

    def _execute_tool(self, name: str, args: dict[str, Any]) -> ToolResult:
        tool = self.tools.get(name)
        if tool is None:
            return ToolResult(f"Unknown tool: {name}", True)

        if not tool.is_read_only() and not _confirm_tool(name, args):
            return ToolResult("Permission denied by user.", True)

        try:
            return tool.execute(**args)
        except Exception as exc:
            return ToolResult(f"Tool error: {exc}", True)


def _confirm_tool(name: str, args: dict[str, Any]) -> bool:
    print(f"\nPermission required: {name}")
    for key, value in args.items():
        preview = str(value)
        if len(preview) > 500:
            preview = preview[:500] + "..."
        print(f"  {key}: {preview}")
    answer = input("Allow? [y/N]: ").strip().lower()
    return answer == "y"
