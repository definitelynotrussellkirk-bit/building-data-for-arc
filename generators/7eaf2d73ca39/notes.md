# Working notes: 7eaf2d73ca39

The canonical rule recolors four-connected same-color green objects by orientation:
horizontal lines become 1 and vertical lines become 8. Ordinary generated inputs
must contain both nontrivial orientations, with every green object straight.

The validator now checks actual four-connected green components. Its previous
global row/column cell counts incorrectly accepted all three built-in degenerate
textures: parallel horizontal lines, parallel vertical lines and an L-shaped blob.
The degenerate generators remain deliberate negative fixtures. Diagonal contact
between separate objects remains valid, matching the canonical reference.

This change leaves the generation path and VERSION unchanged, preserving seeded
default draws. Focused evidence is in `checks/7eaf2d73ca39/`: one bounded negative
validation probe and regressions; no full battery or parametric work was performed.
The narrow check does not assess the declared but unused palette/object-count axes.

<!-- arcpuzzles-trainer-ambiguity:start -->
## Current trainer ambiguity follow-up

Claude supplied 1 exact canonical lesson(s) with a proposed alternative rule. Retained privately with source hashes and all stored queries: `evidence/trainer-ambiguity-current/current.json`. These are **open describer flags**, not confirmed wrong labels or failed current parametric qualifications. Check whether the proposed rival fits every demonstration and changes any stored query; distinguish source revisions before repairing. Approval and training state are unchanged.
<!-- arcpuzzles-trainer-ambiguity:end -->
