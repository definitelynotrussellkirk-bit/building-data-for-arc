# 95f849a2fe0f

Version `3.0.0`; canonical rule hash `0aa57664563a`.

The input is a canonical-sized zero-background grid containing exactly two separated 4-connected tetrominoes: red `2` and green `3`. Normalize each object independently to its own top-left corner, take the symmetric difference of the two normalized cell sets, and paint that XOR cyan `8` in the **shared normalized frame**. The output is not re-cropped after cancellation, so a blank leading row or column can be semantically significant.

The generator uses all 19 fixed tetrominoes and classifies ordered shape pairs as `anchored`, `leading_row`, `leading_col`, or `leading_both`. Its six-slot default schedule alternates anchored cases with leading-blank witnesses; every four-pair lesson contains two witnesses, so any three-demonstration query rotation refutes the canonical-fitting “re-crop the XOR” shortcut. The three exact public inputs remain available as explicit `scene_profile` overrides, and every difficulty band uses one canonical input size and the canonical palette `{0,2,3}`.

Kind: `per_puzzle`. The Racket authority was not changed. Approval is derived by the catalog from current code and retained review evidence.
