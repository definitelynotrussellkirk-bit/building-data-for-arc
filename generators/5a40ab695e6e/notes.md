# Working notes: 5a40ab695e6e

## Review scope and baseline

Assignment `review-9c93d6a9269c5c94` used the selected baseline generator SHA-256
`7b6df73893ac492e4bfd800e8aa7b31ae03d9c553397282afd1e396b09aa0472`.
`evidence/associated_notes.jsonl` was empty, so no prior return was used as a
technical lead. The canonical examples and the current source were the primary
references.

The before battery was not close to an exact-contract pass: 5 of 12 stages
failed (`lint`, `selfcheck`, `defect_lint`, `profile_floor`, `override`) and one
was advisory. The source lacked `RULE_HASH`, rejected canonical examples in its
own validator, advertised controls it did not reliably honor, and had dead or
overlapping texture controls.

## Canonical rule and strongest rival

The Racket rule classifies each object's tight mask by left-right and up-down
reflection symmetry and recolors it to `2/3/4/6`. No authority change was needed.

All four canonical demonstrations are also fit by this wrong lookup:

```text
(2,2,4) -> 2
(2,3,5) -> 3
(3,2,5) -> 4
anything else -> 6
```

The key discriminator is a larger mask whose dimensions/area do not appear in
the canonical table but whose symmetry is decisive—for example a 3×3 plus or
ring, which is symmetric on both axes and therefore must become `2`, not `6`.
The exact Racket-backed witness is retained under
`checks/question-generator-shortcuts/`.

## Repair decisions

1. Replaced the misleading eight-axis surface with three total exact controls:
   `grid_h=9..14`, `grid_w=10..16`, and `n_objects=3..4`.
2. Replaced rejection-prone free placement with a constructive four-corner
   layout. Every legal joint override combination is placeable and observable.
3. Added shape banks for all four symmetry signatures. Each bank includes a
   canonical mask and broader 3×3 masks.
4. Added canonical-scale profiles in every band plus a `bbox_trap` profile that
   refutes the canonical-fitting dimensions/area shortcut.
5. Changed the teaching cycle after a cyclic-query regression exposed that one
   trap per four pairs can disappear into the masked query. The final cycle has
   two trap pairs: `canonical_lr, bbox_trap, canonical_ud, bbox_trap`.
6. Reserved result colors `{2,3,4,6}` from source palettes after the defect lint
   correctly flagged an earlier version in which an input object could already
   be color `2`.
7. Added a pinned Python audit mirror, strict canonical-profile support,
   executable semantic witnesses/rivals, and `lesson_identifiable`.
8. Added `workspace/semantic_probe.py` so future reviewers can check every cyclic
   query rotation and the full joint override product, not only the shared
   census's production query position.

## Test-first record

The selected-task tests were written against the baseline and initially produced
10 failures. Subsequent retained red iterations caught two non-obvious defects:

- `checks/task-tests-cyclic-red/`: a sole trap could become the query, leaving
  three demonstrations that did not refute the rival;
- `checks/task-tests-palette-red/`: source color `2` made one recoloring branch
  visually ambiguous.

The final selected-task suite has 13 tests and passes 13/13.

## Final measured state

Final generator SHA-256:
`8a05657f73e6cdee399bed2fadf98609578e1859db60857e707169d5ce61fdd7`.

- Official after battery: 12/12 green, zero advisory/failed stages.
- Selected-task tests: 13/13 passed.
- Shared Racket-backed census: 100 lessons per band, 300/300 materialized,
  0 ambiguous, 0 hook warnings, 0 scoring errors, 1,200/1,200 unique pair inputs.
  The declared rival was refuted in 100/100 lessons in each band.
- Task-local probe: 400 cyclic query rotations per band, 1,200/1,200 identifiable;
  252/252 exact joint override cases accepted and observed.
- Fresh exposed solve: revision 1 explained all three visible demonstrations and
  passed 3/3 visible checks. Earlier rule exposure was declared honestly.

## Remaining limits

The evidence establishes behavior on the generated manifold and against the
strongest declared canonical-fitting rival; it is not a proof of universal
induction. Shapes are drawn from a finite 3×3 bank, scenes contain only three or
four objects, and a solver could still memorize that finite bank rather than
learn reflection symmetry for arbitrary larger polyominoes. Those are explicit
domain limits rather than hidden claims.
## Current reviewer considerations

Source SHA-256: `8a05657f73e6cdee399bed2fadf98609578e1859db60857e707169d5ce61fdd7`.

# Design and review decisions

## D1 — Reduce the public control surface to three exact axes

**Choice.** Keep only `grid_h=9..14`, `grid_w=10..16`, and `n_objects=3..4`.

**Rationale.** The baseline advertised eight axes, but several were dead,
overlapping, manually consumed rather than provenance-tracked, or incompatible
with the actual generation bounds. Exact controls should describe properties
recoverable from returned pixels.

**Alternatives rejected.** Retaining `texture`, palette, anchor, halo, and
asymmetry controls would require additional observability contracts and would
not improve teaching of the rule. Silently treating them as hints would preserve
the original defect.

**Probe.** `workspace/semantic_probe.py` enumerates all
`6 × 7 × 2 × 3 = 252` joint axis/difficulty cases. Final result: 252 accepted,
252 exactly observed, zero failures (`checks/semantic-probe.json`).

**Limit.** Palette and layout still vary internally, but are not promised as
exact caller controls.

## D2 — Use constructive corner placement

**Choice.** Place up to four ≤3×3 masks in shuffled corner regions with one-cell
jitter.

**Rationale.** This makes every legal minimum-size/count combination possible
without retries or a semantically different fallback. It also makes separation
and object count easy to validate.

**Alternative rejected.** Random rejection placement can silently narrow the
joint support or fall back to smaller/different objects under crowded settings.

**Failure mode checked.** The exhaustive joint override probe and the selected
regression suite cover all minimum/maximum size and count combinations.

## D3 — Organize masks by actual symmetry class

**Choice.** Maintain four explicit banks: `both`, `lr`, `ud`, and `none`; verify
every bank member with `_symmetry_class`.

**Rationale.** The transformation depends on the tight mask, so the source
vocabulary should encode and test that semantic partition directly. Canonical
masks remain present, while 3×3 plus/ring/T/crown/stair masks broaden support.

**Alternative rejected.** A small six-shape list without class assertions can
accidentally mislabel or omit a branch and encourages lookup memorization.

**Limit.** The bank is finite and capped at 3×3. This does not demonstrate
arbitrary-polyomino generalization.

## D4 — Teach against the strongest canonical-fitting rival

**Choice.** Declare `bbox_area_lookup` in `CANONICAL_SHORTCUTS`,
`SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`, and produce `bbox_trap` profiles.

**Rationale.** The rival fits all four canonical pairs exactly, making it a more
plausible shortcut than all-one-color or size-only baselines. A 3×3 plus/ring is
both-axis symmetric but falls outside the canonical lookup table, forcing the
intended mask test.

**Evidence.** Canonical fit 4/4; exact Racket-backed disagreement in
`checks/question-generator-shortcuts/`; shared census refuted the rival in
100/100 lessons per band.

## D5 — Use two trap profiles in every four-pair cycle

**Choice.** Final profile cycle:
`canonical_lr, bbox_trap, canonical_ud, bbox_trap`.

**Original attempt.** A three-profile cycle with one trap per four assembled
pairs passed the production-position census.

**Why changed.** A new cyclic-query regression moved each pair into the query
slot. When the only trap became the query, the remaining demonstrations no
longer refuted the rival (`checks/task-tests-cyclic-red/`).

**Alternative rejected.** Making `lesson_identifiable` inspect the query when
judging teaching evidence would mask the curriculum defect: a learner does not
see the query output.

**Final probe.** 400 rotations per band, 1,200 total, all identifiable.

## D6 — Reserve result colors from source colors

**Choice.** Source colors are `{1,5,7,8,9}`; result colors are `{2,3,4,6}`.

**Rationale.** Recoloring should be visibly observable. An earlier repair still
allowed source color `2`, so some both-symmetric objects appeared unchanged.

**Evidence.** The new test failed first in `checks/task-tests-palette-red/`, and
the aggregate defect lint independently reported transformation drift in
`checks/after-cyclic-palette-red/`. Final defect lint is green.

## D7 — Recur canonical profiles in every band

**Choice.** Each teaching profile draws from exact canonical dimension/palette
anchors regardless of difficulty; difficulty influences object count and
non-exact variability, not whether canonical support exists.

**Rationale.** The profile-floor contract requires at least one canonical-size
and palette hit in each band. A hard-only large-canvas policy would make the
validator and sampler disagree about support.

**Evidence.** Final `profile_floor` is green and strict canonical-like samples
occur in easy, medium, and hard.

## D8 — Keep the Racket authority unchanged

**Choice.** Pin `RULE_HASH = "5e6364f401b5"`; do not edit canonical data.

**Rationale.** The rule was correct. The defects were in the generator,
validation, controls, and lesson curriculum.

**Evidence.** `rule_smoke`, `racket_lint`, and `authority_sync` are green; the
exact question witness has matching Python-mirror and Racket outputs.

## D9 — Add task-local tests and a reusable semantic probe

**Choice.** Add 13 selected-task tests plus
`workspace/semantic_probe.py`.

**Rationale.** The shared census does not rotate every pair into the query
position and does not exhaust the legal joint override product. Those omissions
were material: cyclic rotation found a real flaw after an otherwise green run.

**Alternative rejected.** Relying only on aggregate battery smoke samples would
leave schedule-specific and cross-axis defects undetected.

## D10 — Stop after final all-green, census, and fresh solve

**Choice.** No further feature expansion after the final hash achieved 12/12
battery stages, 13/13 task tests, 300/300 Racket-backed lessons, 1,200/1,200
cyclic rotations, 252/252 override cases, and a one-revision visible solve.

**Reason.** Further widening beyond 3×3 masks or four objects would change the
stated generator domain rather than repair a demonstrated defect. The finite-bank
limitation is documented for a later deliberate scope decision.
