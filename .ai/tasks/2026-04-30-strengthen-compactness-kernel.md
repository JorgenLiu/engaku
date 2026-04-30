---
plan_id: 2026-04-30-strengthen-compactness-kernel
title: Strengthen Lossless Compactness kernel with hard NEVER/ALWAYS rules
status: done
created: 2026-04-30
---

## Background
The current Lossless Compactness section in the global kernel uses soft language (`Default to`, `Prefer`, `Cut`) that models treat as optional weights rather than hard constraints. The repo-level `compact.instructions.md` already uses NEVER/ALWAYS patterns and is observably more effective. The kernel should match that tone to prevent affirmations, intent narration, and pre-tool status updates.

## Design
Replace the soft Lossless Compactness bullet list in both the live file and the template with NEVER/ALWAYS framing aligned to `compact.instructions.md`. No structural changes; the section heading and surrounding content stay the same. Both files must be updated in one operation per policy.

**Before:**
```
- Default to compact, information-dense output.
- Cut `Now let me...`, `I will now...`, filler, and mood-setting.
- No arbitrary answer caps; be complete when detail matters.
- Preserve exact evidence: commands, paths, schemas, outputs, errors, and acceptance criteria.
- Prefer terse updates and fragments over process narration.
- Use full text for safety warnings, destructive confirmations, and ambiguity checks.
- Reply in English unless quoting user text or preserving exact non-English evidence.
```

**After:**
```
- ALWAYS output compact, information-dense responses. Fragments over sentences.
- NEVER say "Great!", "Sure!", "Happy to help!", or any affirmation.
- NEVER narrate intent: no "Now let me...", "I will now...", "Let me start by...". Report findings and actions only.
- NEVER send status updates before using tools. Use tools immediately; narrate nothing.
- NEVER use flowing prose when bullets or a table are clearer.
- When detail matters, be complete. No arbitrary answer caps.
- Preserve exact evidence: commands, paths, schemas, outputs, errors, and acceptance criteria.
- Full text only for safety warnings, destructive confirmations, and ambiguity checks.
- Reply in English unless quoting user text or preserving exact non-English evidence.
```

## File Map
- Modify: `.github/copilot-instructions.md`
- Modify: `src/engaku/templates/copilot-instructions.md`

## Tasks

- [x] 1. **Rewrite Lossless Compactness section in both files**
  - Files: `.github/copilot-instructions.md`, `src/engaku/templates/copilot-instructions.md`
  - Steps:
    - Replace the soft-language bullet list under `### Lossless Compactness` with the NEVER/ALWAYS version in both files simultaneously using `multi_replace_string_in_file`.
  - Verify: `grep -n "NEVER\|ALWAYS" .github/copilot-instructions.md src/engaku/templates/copilot-instructions.md`

- [x] 2. **Update overview to reflect v1.1.12 continuation**
  - Files: `.ai/overview.md`
  - Steps:
    - Append one sentence to the overview noting that the Lossless Compactness kernel now uses hard NEVER/ALWAYS constraints matching `compact.instructions.md`.
  - Verify: `grep "NEVER" .ai/overview.md`

- [x] 3. **Bump version to 1.1.13**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`
  - Steps:
    - Change `version = "1.1.12"` → `version = "1.1.13"` in `pyproject.toml`.
    - Change `__version__ = "1.1.12"` → `__version__ = "1.1.13"` in `src/engaku/__init__.py`.
  - Verify: `grep -n "1.1.13" pyproject.toml src/engaku/__init__.py`

## Out of Scope
- Changes to `compact.instructions.md` (already uses correct tone).
- Changes to agent prompts or hook templates beyond the kernel.
- Changelog entry.
