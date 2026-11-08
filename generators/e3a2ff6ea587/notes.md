# Working notes: e3a2ff6ea587

- Final base generator version: `4.0.0`; source SHA-256 `5c7b1ee8866c4659b49636c621eae355bdae97307fee9d2bc8ce21567e98942f`.
- The three prior current-hash findings were reproduced: ordinary draws were positive-only, six advertised controls plus unknown keys were inert, and no native family existed.
- Base repair is constructive and fail-closed. Every ordinary draw now contains at least one exact four-corner rectangle and one named near-miss (`three_corners`, `misplaced_four`, or `extra_cell`); only five observable controls remain.
- `rule_mirror()` preserves the canonical first-appearance paint order and matches all five original labeled pairs. The canonical Racket program remains byte-identical (`a596b3cbf1c7d8bd735741635f5070c80fbd2de31967b833c199854d7d8b7ed4`).
- Native parameter: `cascade_mode=canonical|triggered_cascade`. Inputs are matched across settings; all six demonstrations and four queries are built before slicing, with the last query exactly 30×30.
- Sequential rule: Stage A is the canonical fill. Stage B reads the completed Stage-A grid and bridges a two-point color only when exactly one endpoint still shows the first qualifying rectangle's color.
- Deep review found a real fixed-boundary shortcut in the first sampler: active triggers could be inferred from endpoint boundary roles without reading Stage A. Trigger roles are now sampled after Stage A, boundary/interior profiles are crossed in the two-demo minimum, rectangle layouts are mirrored, and the former shortcut is a regression/rival.
- Final finite probe defeats 13 executable rivals on 16 episodes at the 2- and 6-demo boundaries. A separate 129-seed audit covers 516 episodes, 1,290 distinct inputs, 2,580 labeled pairs, and 3,870 causal ablations.
- Protected Racket authoring preflight passed four jobs, 24 parametric pairs, all five canonical pairs, and 32 evaluations. A wrong-order witness changes 25 final cells.
- Sequential public projection passed 16 saved views, four first-turn checks, 24 private/future-query invariance mutations, and four visible-change controls.
- Finite tests do not prove universal identifiability. Owner source review, native qualification/acceptance on integrated bytes, and any training admission remain pending and were not claimed.
