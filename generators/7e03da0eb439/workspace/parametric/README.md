# `7e03da0eb439` parametric authoring family

This source-local prototype exposes one parameter:

- `trigger_mode=color_2` — the exact selected canonical program. Copy the input into every output block whose corresponding input cell is color 2.
- `trigger_mode=center_cue` — read the center input cell as the intermediate cue, then copy the input into every output block whose corresponding cell equals that cue.

The alternative is sequential: step A reads an input-dependent color from the center; step B cannot select tile locations until that color is known. The admitted grammar uses odd 3×3 and 5×5 inputs so the center is unique. Because self-tiling maps an `H×W` input to `H²×W²`, the largest lawful odd-square case under ARC's 30-cell limit is 5×5→25×25; an exact 30×30 case is not representable by this rule family.

## Repaired teaching certificate

An adversarial second pass found that the earlier independently transformed demonstrations still admitted fixed non-center cue readers and global/row/column-mode cue rules for some seeds. The first two 3×3 templates now receive the same seed-dependent D4 transform and satisfy two directly checked coordinate invariants:

- their color-2 coordinate sets are disjoint, so no fixed non-center location can recover the canonical trigger in both demonstrations;
- their center-cue coordinate sets intersect only at the center, so no other fixed location can recover the alternative trigger in both demonstrations.

Their line layouts and modal distractors also reject global mode and all three normalized row/column mode readers. The bounded bank now contains 40 alternatives: 8 non-center fixed-anchor cues, 21 global/line-mode rules, 8 fixed colors, and 3 broad shortcuts (`value>1`, nonzero, center-position-only). This is a finite certificate, not a universal uniqueness proof.

Reproduction from the packet root:

```bash
python review.py run python3 -m pytest -q --import-mode=importlib \
  generators/7e03da0eb439/tests/test_parametric_7e03da0eb439.py
python review.py run python3 generators/7e03da0eb439/workspace/parametric/probe.py \
  --out generators/7e03da0eb439/workspace/parametric/evidence/current/study.json
python review.py run python3 -m arcpuzzles.review_programs \
  generators/7e03da0eb439/workspace/parametric/canonical.rkt
python review.py run python3 -m arcpuzzles.review_programs \
  generators/7e03da0eb439/workspace/parametric/center_cue.rkt
```

The default probe runs 70 deterministic jobs over seven seeds, both settings, demonstration counts 2–6, and four queries. It checks the coordinate certificate, all declared rivals, matched inputs, prefix stability, and maximum geometry. `review_base_preflight` independently checks retained labels in protected Racket and binds its receipt to the frozen source inventory. Neither authoring evidence nor this prototype claims owner acceptance or training admission.
