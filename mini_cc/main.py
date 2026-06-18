from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .engine import Engine
from .llm import LLMClient
from .prompt import build_system_prompt
from .skills import SkillRegistry
from .tool import ToolRegistry
from .tools import default_tools


def main() -> None:
    parser = argparse.ArgumentParser(prog="mini-cc")
    parser.add_argument("prompt", nargs="?", help="Prompt to run")
    parser.add_argument("-p", "--print", action="store_true", help="Run one prompt and exit")
    parser.add_argument("--model", default=os.getenv("MINI_CC_MODEL", "qwen3-coder-plus"))
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL"))
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY"))
    parser.add_argument("--max-steps", type=int, default=12)
    parser.add_argument("--max-tokens", type=int, default=4096)
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("OPENAI_API_KEY is required.")

    cwd = str(Path.cwd())
    skills = SkillRegistry(cwd)
    system_prompt = build_system_prompt(cwd=cwd, skills_section=skills.prompt_section())
    engine = Engine(
        llm=LLMClient(api_key=args.api_key, base_url=args.base_url, model=args.model),
        tools=ToolRegistry(default_tools()),
        system_prompt=system_prompt,
        max_steps=args.max_steps,
        max_tokens=args.max_tokens,
    )

    if args.print or args.prompt:
        prompt = args.prompt or sys.stdin.read()
        engine.run(skills.expand_if_skill(prompt))
        return

    print(f"mini-cc ({args.model})")
    print("Type /review, /test, /explain, or Ctrl-D to exit.")
    while True:
        try:
            user_input = input("\n> ").strip()
        except EOFError:
            print()
            return
        except KeyboardInterrupt:
            print()
            continue
        if not user_input:
            continue
        engine.run(skills.expand_if_skill(user_input))


if __name__ == "__main__":
    main()
