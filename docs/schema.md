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

## Learning history

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

### `data/learning/sessions.csv`
Fields: `session_id`, `started_at`, `ended_at`, `topic_ids`, `focus_items`, `source_ids`, `notes`, `recorded_events`, `next_steps`.
Semicolon-separated topic/item IDs. Only record actually completed sessions.

## State
`state/current_state.md` is a human-readable, compact pointer: current focus, imported exposures, weak skills supported by evidence, due reviews, pending diagnostic and planned next activity. It is NOT the sole source of truth.

## Workflow
1. Before lesson: load state, then relevant catalogs and learning evidence.
2. Active review and new content are selected against relevant topics and due items.
3. On real responses: append events and compute/adjust mastery from evidence; don't overwrite raw events.
4. Close the session and update current state.
5. Confirm GitHub commit or explain that persistence did not occur.
6. Revalidate all IDs and CSV syntax after writes; avoid concurrent edits to the same path.

## Privacy and copyright
This is a PUBLIC repository. Store minimal original study examples and non-sensitive practice records. Do not copy full copyrighted transcripts, paid books, private Discord conversations or confidential work details.

## Limitations
These files provide a schema and initial content; they are not an always-on service. No background execution or automatic ChatGPT Project attachment is implied. Scripts, if present, must be run by an actual supported execution environment.
