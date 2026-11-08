# Native crop-then-dominant-key rotation family for `f2e717c7c250`

The default `postprocess=crop_only` returns the byte-exact canonical program: read the two key colors from row zero, discard the blank separator, and crop the body to the union bounding box of those key-colored cells.

The alternative `postprocess=dominant_key_rotate` adds a genuine input-dependent second stage. Step A constructs the canonical crop. Its intermediate records the two key-cell counts and which header-ordered key is dominant. Step B consumes the complete crop and rotates it clockwise when the first key dominates or counterclockwise when the second key dominates. The first two demonstrations exercise opposite branches; scattered and excluded distractors make fixed rotation, whole-grid rotation, color-value, and ignore-the-crop shortcuts fail.

Inputs are shared across settings and support 2–6 demonstrations plus 1–4 prefix-stable queries. Geometry, colors, header positions, distractors, crop shapes, and dominant branch vary. The fourth query is a substantive 30×30 case whose selected body crop spans all 28 body rows and all 30 columns. Settings, programs, source order, future queries, and answers remain private; `public_turn` reveals one query input only.

`audit.py` checks a finite rival set, protected-Racket labels, and a wrong-dominant-direction counterfactual. Native owner qualification and exact-source acceptance remain separate; no training admission is claimed.
