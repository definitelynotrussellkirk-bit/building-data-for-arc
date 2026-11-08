# c2b9484357c1

A 0-background grid contains two differently colored hollow objects and optionally one larger solid distractor. Select the hollow object with the greatest number of colored cells, fill **every** enclosed zero region of that object with its own color, and leave every other object unchanged.

Kind: `per_puzzle`. Current implementation: `2.1.0` (review of imported `2.0.0`). Canonical rule hash `4d65cf4d4b83`, unchanged.

Four scheduled profiles expose first/last selection, hole-count, bounding-box and solid-object shortcuts. The fourth has a thick-walled two-hole winner with a shorter outer perimeter than its rival. Keyed row/column stretching adds noncosmetic geometry variation without changing declared axes or the 25% strict canonical-like anchor floor.

Ordinary lessons require **four demonstrations**. The shared export API defaults to three; explicitly request four and validate the actual emitted episodes with `workspace/validate_lessons.py`. The gate is not automatically integrated into the shared exporter.

`workspace/README.md` documents tools, commands and limits. Approval remains derived by the catalog from current code and retained evidence; this review does not promote approval.
