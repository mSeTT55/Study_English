#!/usr/bin/env python3
"""Recalculate evidence-based per-skill mastery from JSONL practice attempts.

Usage:
  python scripts/recalculate_mastery.py          # updates mastery.csv
  python scripts/recalculate_mastery.py --dry-run # prints computed counts; no writes

The learning event log is append-only; each row of mastery.csv is a derived view.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "learning" / "learning_events.jsonl"
MASTERY = ROOT / "data" / "learning" / "mastery.csv"
FIELDS = [
    "item_type", "item_id", "skill", "tense", "form", "attempts",
    "independent_correct", "assisted_correct", "last_seen_at", "last_tested_at",
    "next_review_at", "level", "common_error", "updated_at",
]


def parse_date(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"Timestamp must include timezone: {value!r}")
    return parsed


def calculate(events: list[dict], now: datetime | None = None) -> list[dict[str, str | int]]:
    now = now or datetime.now(timezone.utc)
    groups: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    for event in events:
        if event.get("result") == "unassessed":
            continue
        key = tuple(str(event.get(field, "")) for field in ("item_type", "item_id", "skill", "tense", "form"))
        groups[key].append(event)
    result = []
    for key in sorted(groups):
        items = sorted(groups[key], key=lambda x: parse_date(x["occurred_at"]))
        correct = [x for x in items if x.get("result") == "correct"]
        independent = [x for x in correct if x.get("assistance") == "independent"]
        assisted = [x for x in correct if x.get("assistance") in {"hint", "model_given"}]
        distinct_prompts = {x.get("prompt", "") for x in independent}
        distinct_days = {parse_date(x["occurred_at"]).date() for x in independent}
        newest = items[-1]
        last_ok = newest.get("result") == "correct" and newest.get("assistance") == "independent"
        interval = (parse_date(independent[-1]["occurred_at"]) - parse_date(independent[0]["occurred_at"])) if independent else timedelta(0)
        if last_ok and len(independent) >= 3 and len(distinct_days) >= 2 and interval >= timedelta(days=7):
            level = 4
        elif last_ok and len(independent) >= 2 and len(distinct_prompts) >= 2:
            level = 3
        else:
            level = 2  # attempted but not yet independently stable
        gap = 1 if newest.get("result") == "incorrect" else {2: 2, 3: 7, 4: 21}[level]
        last_time = parse_date(newest["occurred_at"])
        reviews = [x for x in reversed(items) if x.get("result") != "correct"]
        error = str(reviews[0].get("feedback", ""))[:300] if reviews else ""
        row = dict(zip(("item_type", "item_id", "skill", "tense", "form"), key))
        row.update({
            "attempts": len(items),
            "independent_correct": len(independent),
            "assisted_correct": len(assisted),
            "last_seen_at": newest["occurred_at"],
            "last_tested_at": newest["occurred_at"],
            "next_review_at": (last_time + timedelta(days=gap)).isoformat(timespec="seconds"),
            "level": level,
            "common_error": error,
            "updated_at": now.isoformat(timespec="seconds"),
        })
        result.append(row)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    with EVENTS.open(encoding="utf-8") as stream:
        events = [json.loads(line) for line in stream if line.strip()]
    rows = calculate(events)
    print(f"Processed {len(events)} events into {len(rows)} mastery records.")
    if not args.dry_run:
        with MASTERY.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Updated {MASTERY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
