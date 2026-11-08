# 7e9fd4cf84a9

Repaired generator version `3.0.0` for the canonical holed-green-rectangle rule.

- Input: a 0-background grid with 1–6 separated green rectangles, each missing exactly one strictly interior cell, plus 1–5 unrelated non-green distractors.
- Canonical transformation: fill every rectangle hole cyan (8) and preserve every other cell.
- Strict controls: `grid_h`, `grid_w`, `n_rectangles`, `distractor_count`, and `layout_profile`.
- Native parametric family: exact canonical `all_rectangles` default versus episode-fixed `largest_only`.
- Native limits: 2–6 demonstrations and exactly four distinct controller-side queries, including a substantive 30×30 case.

Reviewer authoring evidence is retained under `workspace/parametric/evidence/` and `checks/7e9fd4cf84a9/` in the return package. Owner source review, native qualification/acceptance, and training admission remain separate.
