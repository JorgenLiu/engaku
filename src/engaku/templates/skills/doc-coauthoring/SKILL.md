---
name: doc-coauthoring
description: "Co-author design docs, ADRs, RFCs, or task plans. Use when the user wants to write or refine a document collaboratively — not just request a one-shot draft."
context: fork
argument-hint: "Describe the document to co-author: type (ADR, RFC, design doc, task plan), topic, and audience."
user-invocable: true
disable-model-invocation: false
---

# Document Co-authoring

Write documents *with* the user, not for them. The result should reflect the user's thinking, sharpened through dialogue.

## Core Principle

Never produce a full draft unprompted. Ask questions first. Structure second. Draft sections only after scope and audience are aligned.

---

## Stage 1 — Context Gathering

Ask before writing:

1. **Type?** (ADR, RFC, design doc, task plan, runbook, post-mortem, README)
2. **Audience?** (Team, leadership, external contributors, future self)
3. **Decision or outcome to drive?**
4. **Reader's existing context?** What can be assumed vs. must be explained?
5. **Existing docs/code/conversations?** Read them now if they exist.
6. **Desired length and detail?**

Summarize gathered context back in 3–5 bullets. Confirm alignment before Stage 2. Surface conflicting goals explicitly.

---

## Stage 2 — Refinement & Structure

### Propose an outline

**ADR** — Title/Status/Date · Context · Decision · Consequences · Alternatives.
**Design Doc** — Problem · Goals/Non-goals · Overview · Detailed design · Trade-offs · Open questions.
**Task Plan** — Background · Design (approach, file map) · Tasks (ordered, w/ acceptance) · Out of scope.
**RFC** — Summary · Motivation · Detailed proposal · Drawbacks · Alternatives · Unresolved questions.

### Iterate

Ask: "Does this structure capture what you need? Add/remove/reorder?" Revise until approved.

### Draft section by section

One section at a time. Pause after each: "Capture your intent? What should change?" Don't proceed until current is approved or marked "good enough for now."

---

## Stage 3 — Reader Testing

Before declaring complete:

1. Could a reader who wasn't in the conversation understand it? Remove jargon or define it.
2. Does every section earn its place? Cut repetition.
3. Are decisions and trade-offs explicit? "We chose X" without why is incomplete.
4. Right length? Too long → won't be read; too short → useless.
5. Open questions clearly marked?

### Final pass

- Read aloud (or have user do it). Flag anything awkward.
- Check terminology, formatting, tone consistency.
- Confirm: "Ready, or sections to revisit?"

---

## Anti-patterns

- Dumping a full draft without asking → reflects model assumptions, not user needs.
- Polishing prose before structure is agreed → wasted effort.
- Ignoring audience.
- Hiding uncertainty → an honest "open question" beats a confident wrong claim.
