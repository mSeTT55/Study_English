#!/usr/bin/env python3
"""Validate the Study English CSV/JSONL learning database (stdlib only).

Usage:
    python scripts/validate_data.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "data" / "content"
LEARNING = ROOT / "data" / "learning"

TABLES = {
    "verb": ("verbs.csv", "verb_id", "V"),
    "grammar": ("grammar_patterns.csv", "pattern_id", "G"),
    "chunk": ("chunks.csv", "chunk_id", "C"),
    "topic": ("topics.csv", "topic_id", "T"),
    "source": ("sources.csv", "source_id", "S"),
    "lesson": ("lesson_catalog.csv", "lesson_id", "L"),
}
ERRORS: list[str] = []


def problem(message: str) -> None:
    ERRORS.append(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        if not reader.fieldnames:
            problem(f"{path}: missing CSV header")
            return []
        result = []
        for line_no, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                problem(f"{path}:{line_no}: wrong number of fields")
            result.append(row)
        return result


def main() -> int:
    tables: dict[str, list[dict[str, str]]] = {}
    known: dict[str, set[str]] = {}
    for kind, (name, key, prefix) in TABLES.items():
        path = CONTENT / name
        if not path.exists():
            problem(f"Missing table: {path}")
            continue
        rows = read_csv(path)
        tables[kind] = rows
        ids = [row.get(key, "") for row in rows]
        if not all(ids):
            problem(f"{name}: empty ID")
        if len(ids) != len(set(ids)):
            problem(f"{name}: duplicate IDs")
        if any(not ident.startswith(prefix) for ident in ids):
            problem(f"{name}: unexpected ID prefix")
        known[kind] = set(ids)

    def reference(src: str, field: str, value: str, target: str) -> None:
        if value and value not in known.get(target, set()):
            problem(f"{src}: {field} references missing {target} ID {value!r}")

    for row in tables.get("chunk", []):
        ident = row["chunk_id"]
        reference(ident, "focus_grammar_id", row["focus_grammar_id"], "grammar")
        reference(ident, "topic_id", row["topic_id"], "topic")
    for row in tables.get("source", []):
        for topic in filter(None, row["topic_ids"].split(";")):
            reference(row["source_id"], "topic_ids", topic, "topic")
    for row in tables.get("lesson", []):
        reference(row["lesson_id"], "topic_id", row["topic_id"], "topic")
        reference(row["lesson_id"], "source_id", row["source_id"], "source")
    rel_path = CONTENT / "content_relations.csv"
    if rel_path.exists():
        for row in read_csv(rel_path):
            reference("relation", "from_id", row["from_id"], row["from_type"])
            reference("relation", "to_id", row["to_id"], row["to_type"])
    else:
        problem(f"Missing table: {rel_path}")

    event_file = LEARNING / "learning_events.jsonl"
    event_ids: set[str] = set()
    event_count = 0
    if event_file.exists():
        with event_file.open(encoding="utf-8") as stream:
            for line_no, raw in enumerate(stream, 1):
                if not raw.strip():
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError as exc:
                    problem(f"learning_events.jsonl:{line_no}: {exc}")
                    continue
                if not isinstance(obj, dict):
                    problem(f"learning_events.jsonl:{line_no}: object expected")
                    continue
                event_count += 1
                ident = str(obj.get("event_id", ""))
                if not ident or ident in event_ids:
                    problem(f"learning_events.jsonl:{line_no}: missing/duplicate event ID")
                event_ids.add(ident)
                for key in ("session_id", "occurred_at", "item_type", "item_id",
                            "skill", "prompt", "user_answer", "result", "assistance"):
                    if key not in obj:
                        problem(f"learning_events.jsonl:{line_no}: missing {key}")
                kind = obj.get("item_type", "")
                reference(ident, "item_id", obj.get("item_id", ""), kind)
    else:
        problem(f"Missing event log: {event_file}")

    # Validate separate exposure and continuity records; no score is inferred.
    extra_logs = (
        ("exposure_events.jsonl", "exposure_id",
         ("session_id", "occurred_at", "item_type", "item_id",
          "exposure_type", "channel", "source_id", "context_summary")),
        ("context_checkpoints.jsonl", "checkpoint_id",
         ("session_id", "created_at", "mode", "topic_id",
          "conversation_summary", "learner_intent",
          "last_tutor_question", "pending_reply", "next_move")),
    )
    extra_counts: dict[str, int] = {}
    for filename, id_key, required_keys in extra_logs:
        path = LEARNING / filename
        extra_counts[filename] = 0
        if not path.exists():
            problem(f"Missing event log: {path}")
            continue
        seen: set[str] = set()
        with path.open(encoding="utf-8") as stream:
            for line_no, raw in enumerate(stream, 1):
                if not raw.strip():
                    continue
                try:
                    item = json.loads(raw)
                except json.JSONDecodeError as exc:
                    problem(f"{filename}:{line_no}: {exc}")
                    continue
                if not isinstance(item, dict):
                    problem(f"{filename}:{line_no}: object expected")
                    continue
                extra_counts[filename] += 1
                ident = item.get(id_key, "")
                if not isinstance(ident, str) or not ident or ident in seen:
                    problem(f"{filename}:{line_no}: missing/duplicate {id_key}")
                seen.add(ident)
                for field in required_keys:
                    if field not in item:
                        problem(f"{filename}:{line_no}: missing {field}")
                if filename == "exposure_events.jsonl":
                    reference(f"{filename}:{line_no}", "item_id",
                              item.get("item_id", ""), item.get("item_type", ""))
                    reference(f"{filename}:{line_no}", "source_id",
                              item.get("source_id", ""), "source")
                else:
                    reference(f"{filename}:{line_no}", "topic_id",
                              item.get("topic_id", ""), "topic")

    for name in ("mastery.csv", "sessions.csv"):
        if not (LEARNING / name).exists():
            problem(f"Missing learning summary: {name}")
        else:
            read_csv(LEARNING / name)

    print("Study English database validation")
    for name, rows in tables.items():
        print(f"  {name}: {len(rows)} records")
    print(f"  learning events: {event_count}")
    for filename, count in extra_counts.items():
        print(f"  {filename}: {count}")
    if ERRORS:
        print(f"FAILED: {len(ERRORS)} issue(s)")
        for err in ERRORS:
            print(" - " + err)
        return 1
    print("PASS: CSV fields, keys, references, and JSONL syntax are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
