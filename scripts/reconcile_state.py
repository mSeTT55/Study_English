#!/usr/bin/env python3
"""Check local CSV/JSONL snapshot against the last verified GitHub manifest.

Run from a checkout (or equivalent exported files):
    python scripts/reconcile_state.py
    python scripts/reconcile_state.py --json

Exit: 0 = consistent; 1 = unsynced/drift/incomplete; 2 = invalid data.
This script does NOT fabricate or automatically overwrite missing study events.
ChatGPT Web/Voice should perform equivalent checks via its GitHub tools.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "state" / "sync_manifest.json"
STREAMS = {
    "data/learning/learning_events.jsonl": ("event_id", "occurred_at"),
    "data/learning/exposure_events.jsonl": ("exposure_id", "occurred_at"),
    "data/learning/context_checkpoints.jsonl": ("checkpoint_id", "created_at"),
}
SUMMARY_FILES = (
    "state/active_session.md",
    "state/current_state.md",
    "data/learning/mastery.csv",
    "data/learning/sessions.csv",
)


def git_blob_sha(content: bytes) -> str:
    """Return Git's SHA-1 object ID for file bytes (not a regular file SHA)."""
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def load_log(path: Path, id_key: str, at_key: str) -> tuple[dict, list[str]]:
    rows = []
    errors = []
    if not path.exists():
        return {"count": None, "last_id": None, "last_at": None, "blob_sha": None, "rows": []}, [f"Missing {path}"]
    text = path.read_text(encoding="utf-8")
    known = set()
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("a JSON object is required")
            ident = row.get(id_key)
            date = row.get(at_key)
            if not isinstance(ident, str) or not ident or ident in known:
                raise ValueError(f"missing or duplicate {id_key}")
            if not isinstance(date, str):
                raise ValueError(f"missing {at_key}")
            timestamp = datetime.fromisoformat(date.replace("Z", "+00:00"))
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("timestamp lacks UTC offset")
            known.add(ident)
            rows.append(row)
        except (json.JSONDecodeError, ValueError) as error:
            errors.append(f"{path}:{line_no}: {error}")
    last = rows[-1] if rows else {}
    return {
        "count": len(rows),
        "last_id": last.get(id_key),
        "last_at": last.get(at_key),
        "blob_sha": git_blob_sha(path.read_bytes()),
        "rows": rows,
    }, errors


def read_active(path: Path) -> tuple[str | None, str | None]:
    if not path.exists():
        return None, None
    content = path.read_text(encoding="utf-8")
    status_match = re.search(r"(?im)^Status:\s*\*{0,2}(idle|active|paused)\*{0,2}\s*$", content)
    session_match = re.search(r"(?im)^Session ID:\s*(?:\*\*)?([^\r\n*]+)", content)
    status = status_match.group(1).lower() if status_match else None
    session = session_match.group(1).strip() if session_match else None
    return status, None if not session or session.lower() == "none" else session


def analyze() -> dict:
    errors = []
    drift = []
    warnings = []
    if not MANIFEST.exists():
        return {"status": "invalid", "errors": ["Missing sync_manifest.json"], "drift": [], "warnings": []}
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as error:
        return {"status": "invalid", "errors": [str(error)], "drift": [], "warnings": []}
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        errors.append("Manifest has invalid schema_version (expected 1)")
    expected_streams = manifest.get("streams", {})
    if not isinstance(expected_streams, dict):
        expected_streams = {}
        errors.append("Manifest streams must be an object")
    snapshots = {}
    all_rows = {}
    for name, (id_key, time_key) in STREAMS.items():
        current, problems = load_log(ROOT / name, id_key, time_key)
        snapshots[name] = {k: current[k] for k in ("count", "last_id", "last_at", "blob_sha")}
        all_rows[name] = current["rows"]
        errors.extend(problems)
        stored = expected_streams.get(name)
        if not isinstance(stored, dict):
            drift.append(f"Manifest is missing snapshot for {name}")
            continue
        for field in ("count", "last_id", "last_at", "blob_sha"):
            expected = stored.get(field)
            if field == "blob_sha" and expected is None and manifest.get("status") == "baseline_no_study_session":
                continue
            if expected != snapshots[name][field]:
                drift.append(f"{name}: {field}: manifest={expected!r}; actual={snapshots[name][field]!r}")
    for path in SUMMARY_FILES:
        ref = manifest.get("state_files", {}).get(path, {})
        expected_sha = ref.get("blob_sha") if isinstance(ref, dict) else None
        actual_sha = git_blob_sha((ROOT / path).read_bytes()) if (ROOT / path).exists() else None
        if actual_sha is None:
            errors.append(f"Missing summary file {path}")
        elif expected_sha is not None and expected_sha != actual_sha:
            drift.append(f"{path}: blob_sha differs from verified manifest")
        elif expected_sha is None and manifest.get("status") != "baseline_no_study_session":
            drift.append(f"{path}: no verified blob SHA in manifest")
    active_status, active_id = read_active(ROOT / "state" / "active_session.md")
    if active_status is None:
        errors.append("active_session.md must include Status: idle|active|paused")
    elif active_status != manifest.get("session_status"):
        drift.append(f"Active session status {active_status!r} differs from manifest {manifest.get('session_status')!r}")
    if active_id != manifest.get("session_id"):
        drift.append(f"Active session ID {active_id!r} differs from manifest {manifest.get('session_id')!r}")
    rows = all_rows["data/learning/context_checkpoints.jsonl"]
    if rows:
        last_checkpoint = rows[-1].get("checkpoint_id")
        if last_checkpoint != manifest.get("checkpoint_id"):
            drift.append("Latest checkpoint ID differs from manifest")
    elif manifest.get("checkpoint_id") is not None:
        drift.append("Manifest references checkpoint not in log")

    sessions = ROOT / "data" / "learning" / "sessions.csv"
    completed = set()
    if sessions.exists():
        with sessions.open(encoding="utf-8", newline="") as file:
            completed = {row.get("session_id") for row in csv.DictReader(file)}
    if active_status in ("active", "paused"):
        if active_id in completed:
            warnings.append("Active session is also in completed sessions: inspect whether close was interrupted")
        else:
            warnings.append("Active/paused session has no normal close; verify available transcript at the next start")
    elif active_status == "idle" and active_id is not None:
        warnings.append("Idle session has a non-empty Session ID")

    if manifest.get("status") == "baseline_no_study_session":
        warnings.append("No verified study session has been committed yet; this is the initial baseline")
    if errors:
        status = "invalid"
    elif drift or manifest.get("status") in ("partial", "needs_reconciliation", "unverified"):
        status = "needs_reconciliation"
    elif manifest.get("status") == "baseline_no_study_session":
        status = "baseline_consistent"
    elif manifest.get("status") == "verified":
        status = "consistent"
    else:
        status = "invalid"
        errors.append(f"Unsupported manifest status: {manifest.get('status')!r}")
    return {
        "status": status,
        "generation": manifest.get("generation"),
        "last_verified_at": manifest.get("verified_at"),
        "last_data_commit_sha": manifest.get("last_data_commit_sha"),
        "active_session_id": active_id,
        "active_session_status": active_status,
        "streams": snapshots,
        "drift": drift,
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    args = parser.parse_args()
    result = analyze()
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Study English synchronization audit:", result["status"])
        print("Last verified:", result.get("last_verified_at") or "no verified lesson")
        for name, data in result.get("streams", {}).items():
            print(f"  {name}: {data['count']} rows; last ID: {data['last_id']}")
        for category in ("errors", "drift", "warnings"):
            for item in result[category]:
                print(f"  {category.upper()}: {item}")
    return 2 if result["status"] == "invalid" else 1 if result["status"] == "needs_reconciliation" else 0


if __name__ == "__main__":
    raise SystemExit(main())
