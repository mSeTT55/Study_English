# Study English

**Voice-first, bilingual English learning memory — GitHub + ChatGPT + real-life immersion**

A small, text-first learning system built to keep English practice coherent across ChatGPT sessions. Rather than only storing lists of words, it tracks **what was introduced, what was actually attempted, what needed help, and what should be reviewed next**.

> Status: **v0.1 — foundation and initial content catalog**. No real mastery scores have been calculated yet.

## Why?
Chat history can become too long to reliably use as a study database. This repository is the durable reference. The tutor should read its state before a lesson and only report updates when the write operation has succeeded.

## Our method
**Review → Input → Notice → Speak → Correct → Re-test → Log**

- Learn with everyday micro-actions, conversations, news, videos, stories and technical tutorials.
- Mix verb to be, regular/irregular tenses, auxiliaries and useful chunks.
- Practice present, past, future and present continuous; add more advanced tenses when appropriate.
- Keep genuine conversation going: **React → Correct → Continue**.
- **Voice-first and bilingual**: speak manageable English, explain and answer questions in Portuguese as needed, and adapt the balance over time.
- Proactively save **context checkpoints** at natural boundaries when GitHub writing is actually available.
- Track listening, recognition, guided production and independent use separately.
- Personalize by topics: home life, remote work, Discord, gaming, Formula 1, football, technology, Linux, DevOps, programming, data, AI and interviews.
- Try spaced review, active recall, comprehensible input, pronunciation practice, shadowing and real conversations.

## Repository map

```text
Study_English/
├── AGENTS.md                        # Full tutor/agent operating protocol
├── README.md                        # Project guide
├── instructions/
│   ├── PROJECT_PROMPT.md            # Paste into ChatGPT Project Instructions
│   └── LEARNING_METHOD.md           # Pedagogical principles
├── docs/
│   ├── schema.md                    # Exact data contracts
│   └── sync_protocol.md            # Read-back verification and crash recovery
├── data/
│   ├── content/
│   │   ├── verbs.csv                # Conjugations and frequency priority
│   │   ├── grammar_patterns.csv     # To be / auxiliaries / tenses
│   │   ├── chunks.csv               # Useful ready-to-use expressions
│   │   ├── content_relations.csv    # Cross-references by stable IDs
│   │   ├── topics.csv               # Everyday, professional and hobby topics
│   │   ├── sources.csv              # Sites and YouTube reference channels
│   │   └── lesson_catalog.csv       # Lesson and media queue
│   └── learning/
│       ├── learning_events.jsonl    # Append-only real practice attempts
│       ├── exposure_events.jsonl    # Items introduced/read/heard, not 'mastered'
│       ├── context_checkpoints.jsonl # Small resumable conversation snapshots
│       ├── mastery.csv              # Summary per item, skill and form
│       └── sessions.csv             # Completed sessions only
├── scripts/
│   ├── validate_data.py            # Validate CSV/JSONL and references
│   ├── reconcile_state.py          # Compare logs vs last verified snapshot
│   └── recalculate_mastery.py      # Derive review state from real attempts
└── state/
    ├── active_session.md           # Live/paused topic + pending turn
    ├── sync_manifest.json          # Last verified IDs/counts/file hashes
    └── current_state.md            # Current priorities / next session
```

## How to start in ChatGPT Web / Voice
1. Replace the project instructions with [the Voice-first prompt](instructions/PROJECT_PROMPT.md). It says how to read and synchronize without requiring repeated "remember/save" commands.
2. Connect an authorized GitHub app/workflow with the permissions available to that chat. The **standard** GitHub app may expose only reading; do not infer writes from a connected status.
3. Start talking naturally in the same ChatGPT Project. The tutor should check [AGENTS.md](AGENTS.md), [active_session.md](state/active_session.md), and [current_state.md](state/current_state.md) at session entry if tools permit, resuming any unfinished topic.
4. Continue mainly in English, with Portuguese explanations/questions whenever needed. Review weak content when starting *fresh*, not in the middle of an unfinished topic.
5. At topic boundaries and before a normal goodbye, the tutor **writes and reads back** checkpoint data, then updates `sync_manifest.json` only after confirming it. At the beginning of the next session it automatically compares logged records against the last verified manifest and investigates differences. A disrupted call is checked on the next start.

### How conversation memory survives context limits
- **Active checkpoint:** current topic, unfinished question, recent corrections and the next move.
- **Checkpoint log:** short summaries of natural topic transitions, not complete private transcripts.
- **Learning and exposure events:** separate what the learner actually *produced* from what they only *encountered*.
- **Project memory:** can help retrieve prior chats but cannot replace verified repository state.
A checkpoint is an actual, **verified read-after-write transaction** when the connected GitHub operations are available, not a continuously running background recorder. If Voice stops abruptly, startup reconciliation compares event IDs, timestamps, last stored state and GitHub changes; a diff cannot reconstruct unrecorded speech.

**Important:** putting `AGENTS.md` in GitHub does **not** make ChatGPT automatically read it. The Project prompt requests startup reads and reconciliation; verify the operation actually happened. Read/write capability depends on the tools active in the session. Python scripts in this repository do not run automatically merely because they are in GitHub.

## Optional maintenance commands

Run these in a Python environment from the repository root (stdlib only):

```bash
python scripts/validate_data.py
python scripts/reconcile_state.py
python scripts/recalculate_mastery.py --dry-run
python scripts/recalculate_mastery.py
```

The last command overwrites the derived `mastery.csv` view from actual `learning_events.jsonl` evidence. **It does not run automatically in GitHub or ChatGPT Web.** The scoring thresholds are provisional and can be refined as real practice data accumulates.

## Evidence, not wishful scores
A word seen in a screenshot is not a word mastered. Historical lessons are seeded as **known content / previous exposure** without invented test scores. See [schema](docs/schema.md) for stable IDs and assessment levels.

Example:
- `went` can be recognized, yet `Did you go?` still be difficult.
- An expression understood in a video may still be hard to use spontaneously.
- New content should be linked to already studied material before adding unrelated items.

## Source policy
Sources include [WordReference](https://www.wordreference.com/), [YouGlish](https://pt.youglish.com/), [The Fable Cottage](https://www.thefablecottage.com/), [Listen in English](https://www.listeninenglish.com/), [News in Levels](https://www.newsinlevels.com/), [NGSL](https://www.newgeneralservicelist.com/word-lists), educational YouTube channels and verified news/technical sites. Full reference list and intended uses: [sources.csv](data/content/sources.csv).

Follow copyright and licensing. Save links, short summaries and original exercises, not full third-party transcripts, story texts or paid textbook content.

## Privacy
**This repository is public.** Do not save complete personal conversations, names of Discord participants, credentials, confidential workplace information, or other sensitive data.

## Current scope
This is a designed foundation, not an automatically running learning app. CSV and JSONL remain the canonical storage formats; no SQLite migration is planned.
