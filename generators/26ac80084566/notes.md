# Current notes: 26ac80084566

## Rule and repair

The unchanged canonical rule `4397ca98d7a5` uses a full-height vertical 8-wall.
For a foreground shape on the left, each occupied row fills from its leftmost
shape cell through wall−1; on the right it fills wall+1 through that row's
rightmost cell. Empty rows stay black except for the wall. The previous bbox and
horizontal-wall description was wrong. The previous sampler's left-only support
allowed an always-right shortcut, and its validator accepted malformed and
missing-wall grids. Canonical training includes a right-side shape and the
canonical query contains six foreground cells, outside the old 3–5 claim.

Version 2.0.0 corrects the description, grammar and sampling while leaving the
reference and frozen pairs unchanged. Original shape indices 0–3 retain their
geometry; indices 4–7 add the six-cell canonical profile, a triomino, ring and H.
The positive validator accepts any single connected monochrome foreground on
one side of one interior vertical wall, with a positive gap. It is broader than
the template catalog, including lawful one-row or larger connected shapes.
This grammar deliberately excludes the Racket program's incidental behavior on
mixed sides/colors, wall-free scenes and wall-touching inputs.

## Controls and teaching contract

`grid_h=4..30` and `grid_w=6..30` are valid explicit controls in every band;
default difficulty changes their ranges. Side, wall column, gap, shape row and
color are real controls. Exact numeric types are required, including seed/index;
unknown keys and conflicting aliases raise. `palette_size=1` is the foreground
count and `n_distinct_colors=2` includes the wall. Fixed density/position controls
are checked. Helpful textures are true palette aliases. The three named negative
textures remain reproducible invalid fixtures and fail both validators.

A pinned feasible wall conditions an omitted gap on available space, fixing a
reproduced ten-of-sixteen failure. Explicitly infeasible combinations still
raise. Conditional feasibility is with respect to the selected dimensions,
shape and side; this is not a solver for every partially pinned configuration.

The four default slots are left-rich, right-rich, left-varied, right-varied.
Rich slots use shape 0 or 4 and foreground 9; varied slots use any template and
colors below 8. Thus any three consecutive default draws contain both sides,
a row-varying shape, and both color orders relative to 8. A complete four-slot
block also retains these properties after any one holdout. Explicit shape/side/
color overrides, a palette without 9, or skipped indices do not inherit the full
default guarantee. The actual demo/query check remains authoritative for the
finite declared family.

`lesson_report(demos, query)` and `lesson_identifiable(demos, query)` compare the
intended rule with bbox fill, always-right, always-left, identity, whole-side
rows, lowest-color-only and highest-color-only rivals. Only demonstrations and
query input are read. Programs that survive but agree on a query are allowed;
forged demo labels, invalid grids and differing query predictions are rejected.
These are reusable authoring helpers, not proof against all possible ARC rules.
`rule_mirror` is an audit helper; reference labels come from protected Racket.

## Verification and current decision

Final generator SHA-256: `e54d63489690a77af1ad3a08904b463b5e7465f29ecbefdf57d4c36f035e2fbd`.
Canonical program SHA-256: `4397ca98d7a50d2cde4202f96a77aea0196e0b38a47a8394d93a12d7a7f63db8`.
Final test SHA-256: `41ef90e9b5b2d5e42f138f95544fdfb4bfd37d99f365c1261af9be7746cc5311`.

From the review packet's outer directory:

```bash
python3 review.py run python3 generators/26ac80084566/tests/test_generator_26ac80084566.py
python3 review.py run python3 -m arcpuzzles lesson-census 26ac80084566 --per-band 1 --train 3 --test 1 --period 4 --rotate-query --timeout 90 --out ../checks/main/native-lessons-final.json
```

Final evidence is in `WORK/checks/main/tests-final-v2.txt`, its command receipt,
`native-lessons-final.json`, its compact summary, and `final-summary.json`.
All 27 focused tests passed; 41 unique inputs were evaluated by the canonical
Racket program. Three native lessons contain 12 distinct inputs, with all 12
query rotations free of declared ambiguity. Seven generic advisory mutations
were also refuted on these measured lessons.

Preserved red evidence covers the original validator/unknown-key defects,
the pinned-wall/default-gap regression, and the color-order gap. The first
native lesson check passed five declared rivals but retained two advisory
lowest-color ambiguities; those concrete witnesses motivated the two new rivals
and color scheduling. Do not read its success headline as a broader claim.

The bounded independent review checked 40 geometry/lesson cases and 17 Racket
pairs on intermediate source `ee23902e…`. The subsequent color-only delta is
verified by the final focused suite and native lessons; that earlier review is
not presented as a fresh final-source review. No full battery or all-seed census
was run. No approval, acceptance or training-admission state was changed.
The next owner action is ordinary source review and acceptance if desired;
there is no remaining reproduced failure in the edited scope.
