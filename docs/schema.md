# Data dictionary and contracts (v0.1)

All CSVs are UTF-8, comma-delimited, with a header and RFC4180-style quoting. Keys are stable, case-sensitive, never reused. Blank value means "unknown/not applicable", NOT "already mastered".

## Content catalogs

### `data/content/verbs.csv`
Fields: `verb_id` (V###), `lemma`, `verb_type` (regular|irregular), `past`, `past_participle`, `third_person`, `ing_form`, `meaning_pt`, `priority`, `source_note`.
Future simple uses `will + lemma`; do not store misleading forms like "will fought". The vocabulary list does NOT imply mastery.

### `data/content/grammar_patterns.csv`
Fields: `pattern_id` (G###), `category` (to_be|auxiliary|continuous), `tense`, `person`, `form` (affirmative|negative|question|negative_question), `formula`, `example_en`, `example_pt`, `note`.
Examples are illustrative, not transcripts. Tense-specific explanations take precedence when generic translation glosses are broad.

### `data/content/chunks.csv`
Fields: `chunk_id` (C###), `text_en`, `meaning_pt`, `context`, `template`, `focus_grammar_id` (optional G###), `topic_id` (T###), `origin` (prior_conversation|curated_example|corrected_example), `note`.
A chunk is an expression in context, not evidence that the learner can produce it.

### `data/content/topics.csv`
Fields: `topic_id` (T###), `slug`, `label_pt`, `description`, `priority`.
Topics cover household actions, international conversations, games, interviews, infrastructure, programming, data, tech, F1, football and more.

### `data/content/sources.csv`
Fields: `source_id` (S###), `title`, `url`, `source_type`, `language`, `primary_use`, `level_hint`, `topic_ids` (semicolon-separated T###), `verification_status`, `access_notes`.
`user_supplied` or `user_supplied_metadata` means the link was provided, NOT that its transcript has been analyzed. `site_checked` means the website's general purpose was checked. Re-verify current video/news accessibility when used.

### `data/content/lesson_catalog.csv`
Fields: `lesson_id` (L###), `title`, `topic_id`, `source_id` (optional S###), `target_level`, `focus`, `activity`, `source_url`, `status`, `notes`.
`queued` is a suggestion, not a completed session. An exact article/video URL is selected and verified at study time.

### `data/content/content_relations.csv`
Fields: `from_type`, `from_id`, `relation`, `to_type`, `to_id`, `notes`.
Recognized type values: `verb`, `grammar`, `chunk`, `topic`, `source`, `lesson`; IDs must exist in their respective tables. Relations may be semantic and do not prove learner proficiency.

## Verified synchronization state (read-before-write, read-after-write)
See `docs/sync_protocol.md` for full preflight/checkpoint/recovery logic.

### `state/sync_manifest.json`
- `schema_version`: current version `1`.
- `generation`: integer incremented only on a fully verified checkpoint transaction.
- `status`: `baseline_no_study_session` for an untouched initial dataset; `verified` after a confirmed learning checkpoint; `partial`, `needs_reconciliation`, or `unverified` when integrity cannot be established (do **not** report those as success).
- `verified_at`: ISO-8601 timestamp with timezone of the read-back verification; null for baseline.
- `last_data_commit_sha`: the final changed data-file commit SHA (not the manifest's own SHA; avoiding self-reference).
- `session_id`, `checkpoint_id`, `session_status`: the session/last checkpoint referenced and idle|active|paused.
- `streams`: per learning/exposure/context JSONL path with `count`, `last_id`, `last_at`, `blob_sha`.
- `state_files`: per current/active state and summary CSV path with `blob_sha`. GitHub reports blob SHAs from `fetch_file`; an offline git checkout can recompute Git's blob SHA from the file bytes.
- A fully verified manifest is updated **last**, only after each data file is read back and confirmed. On a partial save, preserve the last verified manifest as a recovery reference until reconciliation succeeds.

### Event grouping and recovery
Optional `sync_batch_id` can appear in all three JSONL event types, allowing recovery from a partially committed batch. Use stable IDs for idempotent merge and never append duplicates. The next session compares the actual count/latest ID/timestamp/blob SHA and session state to the manifest. Check the available transcript if recent content seems missing. Reconstruct only recorded events and genuinely visible utterances; otherwise mark a potential gap. An unknown time interval is **not** a guaranteed missing attempt.

Run `python scripts/reconcile_state.py` from a checkout for a local audit. In ChatGPT Web/Voice, execute the same checks by reading GitHub through available tools. Recalculate mastery only after event integrity is resolved.

## Learning history

## Voice-first bilingual interaction and session continuity
The Project is primarily used with ChatGPT Voice. English is the target/practice language; Portuguese is available for explanations, questions, clarifying grammar, and retrieving conversation meaning. Do not force English-only mode. Speech-to-text artifacts or uncertainty are not proof of a grammar or pronunciation error.

### `state/active_session.md` (mutable)
One small **current** live/paused checkpoint. Contains a session ID if known, status (idle|active|paused), last checkpoint timestamp, current topic, learner intent, last meaningful learner turn *summary*, the tutor's last unanswered question (if any), pending correction or re-test, recently encountered items, observed independent usage, and next conversational move. Do not store raw private transcripts. Update at natural boundaries and before a known goodbye, only if current tools permit.

### `data/learning/context_checkpoints.jsonl` (append-only)
A log of compact **conversation continuity snapshots** (one object per line) taken at natural boundaries, not every utterance. Required keys:
- `checkpoint_id` (unique string), `session_id` (may be empty for an unstarted chat), `created_at` (ISO-8601 with offset), `mode` (voice|text|unknown), `topic_id` (optional T###).
- `conversation_summary`: brief, non-sensitive context; `learner_intent`: why they were talking; `last_tutor_question`: exact short question if unfinished; `pending_reply`: boolean; `next_move`: what to say/do next.
Optional fields: `recent_item_ids`, `error_patterns`, `pending_review_ids`, `write_notes`. Do not put full conversations or personal names in this public file. A checkpoint is **not** an assessed language attempt.

### `data/learning/exposure_events.jsonl` (append-only)
Record actual encounters separately from production, one JSON object per line. Required keys:
- `exposure_id` (unique string), `session_id`, `occurred_at`, `item_type` (verb|grammar|chunk), `item_id` (stable ID), `exposure_type` (introduced|heard|read|shadowed|explained|noticed), `channel` (voice|text|reading|video|discord), `source_id` (optional S###), `context_summary` (short learner-safe note).
"Introduced" only means the tutor showed/taught content; "heard/read" means a specific exposure actually occurred. Do not infer successful comprehension or spontaneous usage from exposure. An item's absence from `learning_events.jsonl` means **production not observed in the tracked sessions**, not "never used" or "not learned".

### `data/learning/learning_events.jsonl` — Voice considerations
Existing required fields apply; optional `channel`, `speech_transcript_uncertain` (boolean) and `origin` (exercise|spontaneous_conversation|reported_discord) may be added. A statement actually produced spontaneously can be recorded as `independent_production`. If voice recognition makes the answer doubtful, prefer `unassessed` or clarify once; don't assign a wrong score or claim to measure real pronunciation solely from text.

### Synchronization procedure
1. Read current state and any valid active checkpoint at session startup.
2. During live conversation, keep the last turn's immediate context locally so the next response addresses it; GitHub is the **durable** continuation layer, not an excuse to reread on every word.
3. When an exercise block, topic transition, important correction cluster or expected ending occurs, attempt an authorized write: append exposures and real assessment events, append a context checkpoint, update active_session.md, then recompute/update mastery and current_state.md if justified.
4. Avoid frequent saves during continuous Voice; prefer concise batching that does not break conversation.
5. For each mutable path, fetch its current version/SHA before overwriting it; preserve already-written rows, avoid duplicate event IDs, and verify the final commit. If one write fails, report partial success, never all-or-nothing success.
6. End a normal session with a session summary and idle active_session; keep pending reviews in current_state.md. No assumption of a callback when Voice is closed abruptly, no background writer, no guaranteed plugin availability.
7. All content remains minimally identifying because this GitHub repository is public.


### `data/learning/learning_events.jsonl`
Exactly one JSON object per line; append-only. Zero bytes is valid for no practice events. Required fields per event:
- `event_id`: unique E#### or UUID.
- `session_id`: SESS-YYYYMMDD-## (referencing `sessions.csv` when closed).
- `occurred_at`: ISO 8601 timestamp with timezone (e.g. 2026-11-23T15:00:00-03:00).
- `item_type`: verb|grammar|chunk; `item_id`: stable ID.
- `skill`: recognition|listening|guided_production|independent_production.
- `tense`: optional; `form`: optional.
- `prompt`: task actually asked; `user_answer`: actual learner answer; `expected_answer`: natural model/example, not necessarily the only valid answer.
- `result`: correct|partial|incorrect|unassessed.
- `assistance`: independent|hint|model_given.
- `feedback`: short objective observation.
- `source_id`: optional external content reference.

No fabricated backfilled exercise results. Do not copy entire private discussions or third-party transcripts. A listening exposure without a test is not a `correct` listening event.

### `data/learning/mastery.csv`
Fields: `item_type`, `item_id`, `skill`, `tense`, `form`, `attempts`, `independent_correct`, `assisted_correct`, `last_seen_at`, `last_tested_at`, `next_review_at`, `level`, `common_error`, `updated_at`.
The unique key is (`item_type`,`item_id`,`skill`,`tense`,`form`). Suggested levels:
0 unseen; 1 introduced; 2 developing; 3 independently usable; 4 maintained after delayed correct retrieval. These are operational labels, not scientific CEFR measurements. Do not assign 3/4 without independent evidence. No rows in mastery initially = **not assessed**.

The optional `scripts/recalculate_mastery.py` uses a **provisional**, explicit heuristic: level 2 after an attempted assessment; level 3 after at least 2 correct independent attempts with distinct prompts and a latest independent success; level 4 after at least 3 correct independent attempts spanning at least 7 days, with at least 2 distinct dates and a latest independent success. A later assisted or incorrect answer drops the state to level 2 for that specific skill/form. Review intervals from the last attempt are 1 day after an incorrect attempt, otherwise 2/7/21 days for levels 2/3/4. This is an engineering heuristic, **not** a validated psychological score. Level 1 is a catalog-introduction label and is not generated from evidence events.

### `data/learning/sessions.csv`
Fields: `session_id`, `started_at`, `ended_at`, `topic_ids`, `focus_items`, `source_ids`, `notes`, `recorded_events`, `next_steps`.
Semicolon-separated topic/item IDs. Only record actually completed sessions.

## State
`state/current_state.md` is a human-readable, compact pointer: current focus, imported exposures, weak skills supported by evidence, due reviews, pending diagnostic and planned next activity. It is NOT the sole source of truth.

## Workflow
1. Before lesson: load active session, current state, then relevant catalogs, exposure records, checkpoints and learning evidence.
2. Active review and new content are selected against relevant topics and due items.
3. On real responses: append events and compute/adjust mastery from evidence; don't overwrite raw events.
4. Checkpoint meaningfully during the session when possible; at closure, summarize completed work and update current state.
5. Confirm GitHub commit or explain that persistence did not occur.
6. Revalidate all IDs and CSV syntax after writes; avoid concurrent edits to the same path.

## Privacy and copyright
This is a PUBLIC repository. Store minimal original study examples and non-sensitive practice records. Do not copy full copyrighted transcripts, paid books, private Discord conversations or confidential work details.

## Limitations
These files provide a schema and initial content; they are not an always-on service. No background execution or automatic ChatGPT Project attachment is implied. Scripts, if present, must be run by an actual supported execution environment.
