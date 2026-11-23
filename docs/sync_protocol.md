# Synchronization, verification, and recovery protocol (v1)

This is a **read → write → read back → reconcile** protocol for ChatGPT Web/Voice and the GitHub repository. It is mandatory whenever repository operations are available; no "saved" claim based only on generating text or receiving a commit SHA.

## Important terms
- **Checkpoint**: a short recorded summary of a conversation's current topic, unfinished question, and next move.
- **Write verified**: GitHub returned a successful commit AND a fresh read retrieved the expected record IDs and exact intended values.
- **Manifest verified**: the committed `state/sync_manifest.json` was fetched again, and its counts, IDs, stored blob SHAs and active-session reference match the current repository contents.
- **Reconciled**: after a previous incomplete/interrupted save, persisted records were compared and any repair was made from actual available evidence.
- **Potential gap**: a session appears interrupted, and some spoken conversation may not have been saved. A Git diff or timestamp comparison alone cannot reconstruct speech that never reached GitHub.

## Durable files
`state/sync_manifest.json` is the last completed, verified snapshot. `state/active_session.md` preserves an active/paused turn. The three JSONL logs store learning, exposure and context events; `mastery.csv`, `sessions.csv`, and `state/current_state.md` are summaries. `state/sync_manifest.json` has no recursive hash of itself.

The manifest stores `schema_version`, `generation`, `status`, `verified_at`, `last_data_commit_sha`, `session_id`, `checkpoint_id`, `session_status`, and `streams`. Each stream contains `count`, `last_id`, `last_at`, and `blob_sha` (GitHub content blob SHA). State summaries have `blob_sha` entries under `state_files`. Null is allowed for an empty/baseline record; it is not proof of a synced lesson.

## START OF EACH SESSION (mandatory preflight)
1. Fetch `AGENTS.md`, the manifest, active/current state, all three JSONL logs, `sessions.csv` and `mastery.csv` (plus content tables as needed). Use the current default branch and timestamps in ISO-8601 with timezone.
2. Run the structural validations in `docs/schema.md`. Compare actual record counts and last IDs with the manifest for each stream. Compare GitHub blob SHAs and state/session pointers; inspect per-session IDs and `occurred_at` / `created_at` ordering.
3. Check whether the last active session is marked active/paused but no normal close appears in `sessions.csv`. A crash might have happened even when some checkpoints are valid. Compare the last saved checkpoint to the latest **available** chat context. Do not invent missing answers.
4. **No divergence:** resume the unfinished topic/question directly, or start normal review when no pending question exists.
5. **Divergence:** report which IDs/counts/SHAs differ; inspect relevant commits or diff if available. Reconstruct summaries from recorded events/checkpoints, append a recovery checkpoint (not a fabricated study event), then persist and verify again. Do not delete newer data merely because it was not referenced by the old manifest. If chat content still contains unsaved attempts, backfill *only those directly observable* and link them to their original session, avoiding duplicates.
6. **Unknown spoken segment:** if the GitHub snapshot ends before the apparent interruption and the missing utterances are not available in the current chat/transcript, mark a potential gap. Resume from the latest reliable checkpoint and ask only a short clarification when necessary. Do not claim it was recovered.
7. If a fatal verification fails, try to repair in the same interaction using the current connected GitHub access; if impossible, expose the unsynced status explicitly rather than pretending success.

## WRITE/CHECKPOINT TRANSACTION (at natural conversation boundaries)
1. Build a small batch of real evidence, assigning stable IDs and an optional `sync_batch_id` shared by the batch. Keep the latest question/current turn in memory during the process.
2. Fetch newest file versions and blob SHAs. Deduplicate by ID and update append-only JSONL **without removing old rows**. For a SHA conflict, refetch/merge/retry.
3. Update `state/active_session.md`, `state/current_state.md`, and summaries (mastery from tested attempts only). Write `sessions.csv` **only** when a session has really been completed. Do not mark a session idle just because voice disconnected unexpectedly.
4. **Read-after-write:** fetch each changed file again. Compare all expected IDs, record counts, last timestamp, and expected checkpoint/active-topic text. A successful API write response alone is insufficient.
5. If any file failed verification: mark the batch **incomplete** and reconcile it; do not advance the manifest or claim completion.
6. After verifying all data files, update `state/sync_manifest.json` last using the freshly observed blob SHAs, counts, timestamps, latest IDs, session pointer, and data commit SHA. Then refetch manifest AND its referenced data to confirm they match.
7. Only then report **"GitHub: sincronização verificada"**, with timestamp/commit if useful. Otherwise report **"GitHub: gravação parcial/não verificada"** and the affected file(s). Avoid narrating technical bookkeeping during natural voice conversation.

## Abrupt interruption / next start
- Distinguish **interruption suspected** from **data definitely lost**. A gap in clock time is not itself proof of lost speech: the learner may have stopped talking.
- If active session is unfinished, match the latest verified checkpoint `checkpoint_id`, compare recorded evidence IDs and timestamps, and check any available chat transcript after it.
- Recover omitted summary/missing manifest from valid persisted logs, and restore a usable active-session checkpoint. Record reconciliation separately from learning mastery.
- When exact recent speech is visible, write the missing original attempt with true assistance/result and a new unique event ID; verify after write.
- When speech is unavailable, explicitly mark `potential_gap`; never hallucinate an attempt. Continue from the last reliable question.
- A Git diff shows **repository changes**, not an exact diff between speech and repository content. The latter requires source conversation text/audio to still be available.
- This protocol works when the active ChatGPT surface exposes the connected GitHub operations; it does not make ChatGPT run after the app is closed or create an OS-level end-of-call hook.

## GitHub audit (optional)
If Git commands are available in an execution environment, inspect relevant changes since a known commit with:

```bash
git log --oneline -- data/learning state/
git diff <last_data_commit_sha>..HEAD -- data/learning state/
python scripts/reconcile_state.py
```

Without a local clone, inspect GitHub commit history/content through the connected API and run the same manifest-versus-record checks directly in the chat. These operations require real tool access, not just a prompt.

## Safety / honesty
The repository is currently public. Persist only short, learning-relevant, minimally identifying records, not entire private voice conversations. Save actual observations, not fabricated data. When the current ChatGPT session has GitHub access, perform the checks and writes; don't make a blanket assumption that all clients expose identical tool methods.
