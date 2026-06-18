# mini-cc

A minimal coding agent inspired by cc-mini.

It keeps only:

- OpenAI-compatible LLM calls
- Agent loop
- Read / Edit / Bash tools
- Basic permission confirmation
- Built-in skills
- Simple CLI

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
```

For Qwen / DashScope:

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export MINI_CC_MODEL=qwen3-coder-plus
```

## Usage

```bash
mini-cc -p "hello"
mini-cc
mini-cc "/explain /absolute/path/to/file.py"
mini-cc "/review security"
```

## Project Layout

```text
mini_cc/
  main.py      CLI
  engine.py    agent loop
  llm.py       OpenAI-compatible model adapter
  tool.py      Tool interface and registry
  tools.py     Read / Edit / Bash
  skills.py    built-in and file-based skills
  prompt.py    system prompt
```
