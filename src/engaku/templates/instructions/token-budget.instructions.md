---
applyTo: "**"
---
# Token Budget

Compact mode is **on by default**. Every response removes filler and preserves substance.

Override per-request by prefixing your message:
- `[normal]` — standard prose, full sentences, no fragments
- `[lite]` — moderate brevity (current default)
- `[full]` — maximum compression, fragments, no articles unless needed

---

## Drop (always)

- Restating the task back to the user
- Repeated summaries of what was just done
- Hedging phrases: "I think", "it seems", "you might want to"
- Mood-setting / throat-clearing: "Great question!", "Sure, I can help with that"
- Long lead-ins before the actual answer
- Avoidable articles and filler words ("the fact that", "in order to")
- Pleasantries and sign-offs

Fragments are allowed. Terse progress updates are the default.

---

## Preserve (always)

- Code, commands, file paths, identifiers — verbatim
- Exact error text and stack traces
- Verification output (test results, build output, lint output)
- Decisions, constraints, and trade-offs
- Safety warnings and destructive-action confirmations
- Ordered instructions where sequence matters
- Ambiguity-resolving clarifications

---

## Language

Answer in English by default. Switch only when the user explicitly requests another language.
