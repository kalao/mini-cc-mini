#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from typing import Any


DEFAULT_URL = "http://10.58.198.219:8880/v1/chat-messages"
DEFAULT_USER = "mini-cc-ask-data"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Call the EHR Dify workflow for SQL generation or execution."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate one SQL from a question")
    gen.add_argument("--query", required=True, help="User question or subquestion")

    exe = sub.add_parser("execute", help="Execute one SQL")
    exe.add_argument("--sql", required=True, help="SQL to execute")

    parser.add_argument("--url", default=os.getenv("EHR_DIFY_URL", DEFAULT_URL))
    parser.add_argument("--api-key", default=os.getenv("EHR_DIFY_API_KEY"))
    parser.add_argument("--user", default=os.getenv("EHR_DIFY_USER", DEFAULT_USER))
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()

    if not args.api_key:
        print(json.dumps({"ok": False, "error": "EHR_DIFY_API_KEY is required."}, ensure_ascii=False))
        return 2

    if args.command == "generate":
        payload_type = "1"
        query = args.query
    else:
        payload_type = "2"
        query = args.sql
        validation_error = validate_sql(query)
        if validation_error:
            print(json.dumps({"ok": False, "type": payload_type, "error": validation_error}, ensure_ascii=False))
            return 2

    try:
        answer = call_dify(
            url=args.url,
            api_key=args.api_key,
            payload_type=payload_type,
            query=query,
            user=args.user,
            timeout=args.timeout,
        )
    except Exception as exc:
        print(json.dumps({"ok": False, "type": payload_type, "error": str(exc)}, ensure_ascii=False))
        return 1

    if args.command == "generate":
        sql = extract_sql(answer)
        output = {
            "ok": bool(sql),
            "type": payload_type,
            "mode": "generate",
            "sql": sql,
            "raw_answer": answer,
            "error": None if sql else "No SQL found in response.",
        }
    else:
        output = {
            "ok": True,
            "type": payload_type,
            "mode": "execute",
            "data": parse_json_if_possible(answer),
            "raw_answer": answer,
        }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["ok"] else 1


def call_dify(
    *,
    url: str,
    api_key: str,
    payload_type: str,
    query: str,
    user: str,
    timeout: int,
) -> str:
    payload = {
        "inputs": {"type": payload_type},
        "query": query,
        "response_mode": "streaming",
        "conversation_id": "",
        "user": user,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    answers: list[str] = []
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for raw in resp:
            line = raw.decode("utf-8", errors="replace").strip()
            if not line.startswith("data: "):
                continue
            try:
                event = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            event_name = event.get("event")
            if event_name == "message":
                answer = event.get("answer")
                if isinstance(answer, str):
                    answers.append(answer)
            elif event_name == "workflow_finished":
                answer = event.get("data", {}).get("outputs", {}).get("answer")
                if isinstance(answer, str):
                    answers.append(answer)
            elif event_name == "message_end":
                break

    if not answers:
        raise RuntimeError("Dify response did not contain an answer.")
    return answers[-1]


def extract_sql(text: str) -> str:
    fenced = re.findall(r"```sql\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        return fenced[-1].strip().rstrip(";")
    stripped = text.strip()
    if validate_sql(stripped) is None:
        return stripped.rstrip(";")
    return ""


def validate_sql(sql: str) -> str | None:
    normalized = sql.strip().rstrip(";")
    lowered = normalized.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        return "SQL must start with SELECT or WITH."
    if re.search(r"\b(insert|update|delete|truncate|create|drop|alter)\b", lowered):
        return "SQL contains a forbidden write/DDL keyword."
    if re.search(r"(<[^>]+>|\{\{.*?\}\})", normalized, flags=re.DOTALL):
        return "SQL contains unresolved placeholders."
    return None


def parse_json_if_possible(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


if __name__ == "__main__":
    raise SystemExit(main())
