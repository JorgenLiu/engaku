---
applyTo: "src/engaku/templates/**"
---
Template file conventions for the engaku project.

Files under `src/engaku/templates/` are copied verbatim to target repos by `engaku init`. When updating any template agent or hook file, always update BOTH the template version (`src/engaku/templates/`) AND the live version (`.github/`) in the same operation — never update one without the other. Template stubs should be generic enough to apply to any project; project-specific conventions belong in the actual `.github/instructions/` files inside each target repo after init.
