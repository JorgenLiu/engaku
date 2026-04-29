---
name: doc-coauthoring
description: "Co-author design docs, ADRs, RFCs, or task plans. Use when the user wants to write or refine a document collaboratively — not just request a one-shot draft."
argument-hint: "Describe the document to co-author: type (ADR, RFC, design doc, task plan), topic, and audience."
user-invocable: true
disable-model-invocation: false
---

# Document Co-authoring

Write documents with the user, not for them. The goal is a document that reflects the user's thinking, structured and sharpened through dialogue.

## Core Principle

Never produce a full draft unprompted. Ask questions first. Structure second. Draft sections only after alignment on scope and audience.

---

## Stage 1 — Context Gathering

Before writing anything, understand what the document needs to accomplish.

### Questions to ask the user

1. **What type of document is this?** (ADR, RFC, design doc, task plan, runbook, post-mortem, README)
2. **Who is the audience?** (Team, leadership, external contributors, future self)
3. **What decision or outcome should this document drive?**
4. **What context does the reader already have?** What can be assumed vs. what must be explained?
5. **Are there existing documents, code, or conversations that provide background?**
   - If yes, read those files now to absorb context before proceeding.
6. **What is the desired length and level of detail?**

### What to do with answers

- Summarize the gathered context back to the user in 3-5 bullet points.
- Confirm alignment before moving to Stage 2.
- If the user's answers reveal ambiguity or conflicting goals, surface that explicitly.

---

## Stage 2 — Refinement & Structure

### Propose an outline

Based on Stage 1, propose a section outline. For common document types:

**ADR (Architecture Decision Record)**:
- Title, Status, Date
- Context — what forces are at play
- Decision — what was decided
- Consequences — what follows from the decision
- Alternatives considered

**Design Doc**:
- Problem statement
- Goals / Non-goals
- Design overview
- Detailed design (per component)
- Trade-offs and alternatives
- Open questions

**Task Plan**:
- Background
- Design (approach, file map)
- Tasks (ordered, with acceptance criteria)
- Out of scope

**RFC**:
- Summary
- Motivation
- Detailed proposal
- Drawbacks
- Alternatives
- Unresolved questions

### Iterate on structure

- Present the outline and ask: "Does this structure capture what you need? Should any sections be added, removed, or reordered?"
- Revise until the user approves the outline.

### Draft section by section

- Write one section at a time.
- After each section, pause and ask for feedback: "Does this capture your intent? What should change?"
- Do not write the next section until the current one is approved or marked "good enough for now."

---

## Stage 3 — Reader Testing

Before declaring the document complete, test it from the reader's perspective.

### Checklist

1. **Can a reader who was not in the conversation understand the document?** Remove jargon or define it. Fill in assumed context.
2. **Does every section earn its place?** Cut sections that repeat information or add no value.
3. **Are decisions and trade-offs explicit?** A design doc that says "we chose X" without explaining why is incomplete.
4. **Is the document the right length?** Too long and it won't be read. Too short and it won't be useful.
5. **Are open questions clearly marked?** Use a dedicated section or inline markers so they are not lost.

### Final pass

- Read the full document aloud (or ask the user to). Flag anything that sounds awkward or unclear.
- Check for consistency: terminology, formatting, tone.
- Confirm with the user: "Is this ready, or are there sections you want to revisit?"

---

## Anti-patterns

- **Dumping a full draft without asking questions.** This produces documents that reflect the model's assumptions, not the user's needs.
- **Over-polishing prose before structure is agreed.** Beautiful sentences in the wrong structure waste effort.
- **Ignoring the audience.** A document for the team reads differently than one for leadership.
- **Hiding uncertainty.** If something is unclear, say so. An honest "open question" is better than a confident wrong statement.

## Token Budget

- Draft documents in English by default; switch language only when explicitly requested.
- Keep sections compact; remove repeated framing and restated context across revisions.
- Preserve decisions, constraints, and open questions verbatim; cut hedging and mood-setting prose.
