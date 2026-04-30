---
applyTo: "src/engaku/templates/**"
---
# Templates

Files under `src/engaku/templates/` are copied verbatim by `engaku init`. When updating any template agent or hook file, update BOTH the template (`src/engaku/templates/`) AND the live version (`.github/`) in the same operation — never one without the other.

Template stubs must be generic enough for any project. Project-specific conventions belong in each target repo's `.github/instructions/` after init.
