# Study English

**Adaptive English learning memory — GitHub + ChatGPT + real-life immersion**

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
│   └── schema.md                    # Exact data contracts
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
│       ├── mastery.csv              # Summary per item, skill and form
│       └── sessions.csv             # Completed sessions only
└── state/
    └── current_state.md             # Current priorities / next session
```

## How to start in ChatGPT Web
1. Add the [project instructions](instructions/PROJECT_PROMPT.md) to this ChatGPT Project.
2. Enable a GitHub connection where repository access is available.
3. At the start of a learning session, ask the tutor to consult [AGENTS.md](AGENTS.md) and [current_state.md](state/current_state.md).
4. Do a short active review **before** new content.
5. At the end, record only actual attempts and identify whether files were successfully updated.

**Important:** putting `AGENTS.md` in GitHub does **not** make ChatGPT automatically read it. Read/write capability depends on the active tools and permissions. Python scripts (if added later) will not run automatically merely because they are in the repository.

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
