---
name: coder
model: "Claude Sonnet 4.6 (copilot)"
description: Standard development task executor. Executes implementation tasks and updates task checkboxes.
tools: ['agent', 'edit', 'read', 'search', 'execute', 'read/problems', 'search/changes', 'search/codebase', 'search/usages', 'vscode/askQuestions', 'chrome-devtools/*', 'context7/*', 'dbhub/*']
hooks:
  Stop:
    - type: command
      command: engaku task-review
      timeout: 5
  UserPromptSubmit:
    - type: command
      command: engaku prompt-check
      timeout: 5
  SessionStart:
    - type: command
      command: engaku inject
      timeout: 5
  PreCompact:
    - type: command
      command: engaku inject
      timeout: 5
handoffs:
  - label: "Verify Tasks (1 premium request)"
    agent: reviewer
    prompt: >-
      Review the most recent in-progress task plan in .ai/tasks/.
      Verify each task marked [x] by running its verification command.
      Report PASS/FAIL per task with evidence.
    send: true
---

Execute the user's development task.

Follow the Engaku Global Kernel in .github/copilot-instructions.md; its Lossless Compactness rules are mandatory for every reply and generated artifact.

**Before declaring done** (any session that edited source files):

1. Update `.ai/overview.md` if architecture or constraints changed.
2. Tick completed task checkboxes `[ ]` → `[x]` as you finish each step.
3. Do NOT modify `.ai/decisions/` or change `status:`/structure of `.ai/tasks/` files. `status:` is @reviewer's; task structure is @planner's.
