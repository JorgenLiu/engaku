---
id: 016
title: Bundled Office helper toolchain
status: accepted
date: 2026-05-09
related_task: 2026-05-09-office-read-skills
---

## Context

Office document work needs to be repeatable without asking agents to invent one-off scripts every run. The target use cases are DOCX content reading, XLSX/CSV/TSV data reading, and XLSX formula relationship inference. Python 3.8.4 support remains required, while Engaku's CLI should keep its stdlib-only runtime contract.

## Decision

Engaku will ship original bundled Office skills with helper scripts and Python 3.8.4-pinned requirements files copied into `.github/skills/` by `engaku init` and `engaku update`. The helper dependencies remain optional and project-local: they are not added to Engaku's main `pyproject.toml` dependencies. The first implementation will include `docx-read` for content extraction and `xlsx-analyze` for workbook inspection, tabular profiling, and formula dependency graph extraction.

## Consequences

Agents should call stable helper scripts instead of writing ad hoc parsing scripts for common Office workflows. Engaku must support copying whole skill directories, package non-Markdown skill resources, and test that helper scripts plus requirements are generated. Office formula work is relationship inference only: formula calculation and LibreOffice-based recalculation stay out of scope until a separate plan justifies the extra dependency surface.