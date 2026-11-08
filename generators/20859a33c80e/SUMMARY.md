# 20859a33c80e

Recolor nonzero same-color four-connected components by inclusive bounding-box
containment depth: 1→2, 2→3, 3→4, 4→5, 5→6, deeper→9. Equal bounding boxes do not
count as containing one another. Source color and visual enclosure are not the rule.

Selected version: **3.1.0**. Kind: `per_puzzle`.
Canonical authority remains `c7c12a48b62f`; no Racket change.

Normal draws have four components, one or two roots, and maximum depth 2–4.
Five scheduled scenes teach nested frames, independent roots, boundary children,
non-frame bounding-box containers, and depth four. Alternating distinct/repeated
source-color patterns teaches the distinction between a color and a component
inside each consecutive five-demo lesson. Joint 11×11 anchors every seven draws
retain canonical-profile support without removing the other advertised sizes.

The task-local tests and workspace probes verify actual declared rivals,
malformed-pair handling, exact controls and full lessons. They do not establish
universal induction or approve data for training; approval remains catalog-derived.
