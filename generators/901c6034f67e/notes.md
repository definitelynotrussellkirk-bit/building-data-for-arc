# Working notes: 901c6034f67e

## Review `review-a6a1f156a9790753`

No substantive prior associated note or return was present; the retained
`evidence/associated_notes.jsonl` was empty. The repair was derived from the
selected source, all four canonical pairs, and the canonical Racket authority.
The authority itself was not changed.

Baseline source described and generated a descending **occupied-size** ranking
with sizes `{3,5,7}`. The canonical authority instead counts 4-neighbor contour
cells and ranks ascending. Because every canonical object is a solid rectangle,
occupied area, bounding-box area, and bounding-box perimeter all fit the four
canonical pairs and form strong shortcuts.

## Repair decisions

- Pin `RULE_HASH = "3646fc9eedbe"` and provide an exact Python mirror of the
  authority for source-bound tests and semantic probes.
- Derive four canonical morphology signatures from all public inputs rather
  than maintaining a guessed size range.
- Add two constructive diagnostic families. `area_inversion` orders a dense
  rectangle before a longer sparse line by contour despite the opposite area
  order. `bbox_inversion` orders a large-box L before a denser smaller-box
  rectangle by contour despite both bounding-box metrics preferring the reverse.
- Use a three-slot default schedule so every consecutive three-example lesson
  contains a canonical anchor and both diagnostic roles.
- Make palette variation semantic rather than cosmetic: shared colors challenge
  color-specific object assumptions; arbitrary distinct colors drop input-color
  rank; rank-color mode uses a guaranteed derangement so identity can never be
  accidentally correct.
- Require cross-color orthogonal contact in non-shared canonical anchors. This
  defeats color-blind nonzero connectivity while preserving the authority's
  same-color object definition. Shared-color anchors remain separated to avoid
  merging lawful objects.
- Preserve the canonical transformation fingerprint by excluding rank color 2
  from the shared-color branch. Explicit `rank_colors` cases still supply
  deliberate input/output palette overlap.
- Reject contour ties in the generated teaching grammar. The authority has a
  positional tie-break, but this bounded curriculum teaches contour rank
  directly rather than relying on tie examples.

## TDD and self-review findings retained in tests

The first failing regression caught the missing rule hash and old size
semantics. The first implementation pass then incorrectly required background
separation; a canonical pair reproduced the error and established that
different-color contact is legal. The next full run found that a shuffled
`{2,3,4}` palette could occasionally equal the correct output; rank-color mode
now chooses one of two cyclic derangements.

A later self-review found that generated objects were always background-separated,
allowing a color-blind connectivity shortcut even though one canonical pair
contains cross-color contact. A failing test introduced the rival and the public
anchor placement now guarantees such contact. The first v3.1 battery then
reported `transformation_drift` at exactly 30/60 introductions of color 2; a
60-draw regression reproduced it and the shared palette was narrowed away from
2. The failed intermediate battery is retained under `checks/after-final-v31/`.

## Final measured evidence

Final generator SHA-256:
`bdab70b6181c982eab40837a5659fea7c58a2760032be5a530843dd155defb0d`.

- Complete after battery: 12/12 stages green, including defect lint, semantic
  gate, exact overrides, Racket lint, and authority synchronization.
- Portable selected-task tests: 67 passing.
- Exact override/contact stress: 5,400 draws (3 bands × 6 profiles × 3 palettes
  × 100 seeds) with no generation or observability failure.
- Source-bound census: 100/100 lessons identifiable in each of easy, medium,
  and hard; 1,200 unique inputs total; every declared rival refuted in every
  measured lesson.
- Quick cyclic probe: 18/18 starts in each band; every three-demo window refutes
  all seven competitors.
- Exposed post-repair solve: attempt 1 passed 3/3 visible demonstrations. Earlier
  rule exposure was declared honestly; no reference was consulted during solve.

## Limits

The generator intentionally has exactly three objects and strictly distinct
contour counts. It does not teach the authority's fourth-and-later rank colors or
its positional tie-break. Diagnostics use lines, rectangles, and L-shapes rather
than exhaustively sampling all polyominoes. The declared-rival and finite-sample
results do not rule out an undeclared equivalent hypothesis.
## Current reviewer considerations

Source SHA-256: `bdab70b6181c982eab40837a5659fea7c58a2760032be5a530843dd155defb0d`.

# Decisions — 901c6034f67e

## D1 — Preserve the canonical authority

**Choice.** Keep the Racket rule unchanged and pin `RULE_HASH = 3646fc9eedbe`.
Implement an exact Python mirror only for validation, rivals, and tests.

**Rationale.** All four canonical input/output pairs agree with the selected
Racket authority. The contradiction was in the generator, not the rule.

**Alternatives rejected.** Editing the authority to match the old occupied-size
generator, or changing canonical examples. Either would replace a synchronized
source of truth to accommodate a bad sampler.

**Probe.** Final rule smoke, Racket lint, and authority sync all pass in
`checks/after-final-v311/`.

**Limit.** The generated grammar excludes contour ties even though the authority
has a top-left tie-break.

## D2 — Use same-color 4-connected objects and contour-cell count exactly

**Choice.** Discover monochrome 4-connected components. A contour cell is an
object cell with at least one orthogonal neighbor outside that component. Sort
ascending by `(contour_count, top_left)` and paint 2, 3, 4.

**Rationale.** This is the behavior of the canonical authority and explains all
four public pairs. The first implementation incorrectly required background
separation; canonical train pair 2 demonstrated that differently colored
objects may touch while remaining separate objects.

**Alternatives rejected.** Occupied area, boundary-edge perimeter, color-blind
nonzero connectivity, and descending contour order. Each is either contradicted
by the authority or now has an executable counterexample.

**Probe.** Canonical-pair tests, the Racket rule smoke, and the
`different_colours_touch` witness.

**Failure mode.** A future change to component semantics should add a rival and
source-bound witness before changing the sampler.

## D3 — Retain all four canonical morphologies as linked profiles

**Choice.** Extract each canonical object's normalized shape and canvas size,
then place those same three shapes in randomized lawful positions.

**Rationale.** This preserves real-task dimensions and morphology without
copying exact coordinates. It also gives the profile floor a source-bound target.

**Alternatives rejected.** A guessed size range or only one canonical template.
The baseline's `{3,5,7}` size story was not the task, and a single template would
encourage lookup.

**Probe.** `strict_canonical_like`, linked signatures, exact override tests, and
the profile-floor stage.

**Limit.** These profiles preserve canonical shape classes rather than sampling
all shapes with equivalent contour counts.

## D4 — Engineer two diagnostic profile families

**Choice.** Add `area_inversion` and `bbox_inversion`.

- `area_inversion`: a short line, a dense rectangle, and a longer sparse line
  make contour order disagree with occupied-area order.
- `bbox_inversion`: a short line, a large-box L, and a dense smaller-box
  rectangle make contour order disagree with both bounding-box area and
  bounding-box perimeter.

**Rationale.** The strongest canonical-fitting shortcuts are geometric proxies.
One deterministic inversion family per proxy class guarantees a contradiction
instead of relying on random luck.

**Alternatives rejected.** Unconstrained random polyominoes, which may preserve
the same rankings in an entire three-example lesson; or one special case that
breaks area but not bounding-box metrics.

**Probe.** `checks/question-area-v311/`, canonical-shortcut tests, the semantic
gate, census, and cyclic probe.

**Limit.** The diagnostic vocabulary is lines, rectangles, and L-shapes; an
undeclared feature program could still agree on this finite grammar.

## D5 — Use a three-slot lesson schedule

**Choice.** Cycle canonical anchor → area inversion → bbox inversion. Keep
`EXAMPLES_NEEDED = 3`.

**Rationale.** Every consecutive three-demo window receives both shortcut
counterexamples and one task-shaped anchor. This makes the teaching contract
inspectable and keeps lesson length unchanged.

**Alternatives rejected.** Independent random profile draws, which allow weak
windows; or increasing demonstrations merely to compensate for scheduling.

**Probe.** `workspace/probe_lessons.py` rotates 18 starts per band. All 54/54
windows refute every declared competitor.

**Limit.** The production census samples consecutive pairs but does not rotate
every pair into query position; the workspace probe supplies that bounded check.

## D6 — Make palette variation semantic

**Choice.** Support three exact modes:

- `distinct`: three arbitrary non-rank input colors;
- `shared`: one common color, excluding output color 2; and
- `rank_colors`: a guaranteed cyclic derangement of `{2,3,4}`.

**Rationale.** Distinct colors show input hue is irrelevant. Shared colors show
disconnected same-color regions remain separate objects. Deranged rank colors
defeat identity and “input color already gives rank.” Excluding 2 only in the
shared branch preserves the canonical color-introduction fingerprint while the
explicit rank branch keeps input/output overlap.

**Alternatives rejected.** A random shuffle that can accidentally be correct,
or letting all default branches contain output color 2 often enough to trigger
transformation drift.

**Probe.** Palette regressions, the failed intermediate v3.1.0 battery, the final
60-draw introduction test, and clean final defect lint.

**Failure mode.** Adding a new palette mode without an observable recovery rule
would create a dead or aliased exact control.

## D7 — Require cross-color contact only when colors distinguish objects

**Choice.** Non-shared canonical anchors must contain at least one orthogonal
contact between differently colored objects. Shared-color anchors keep all
objects background-separated.

**Rationale.** Without contact, a solver can ignore color and compute connected
nonzero regions. With a shared color, contact would instead merge two lawful
objects under the true same-color definition, so separation is required there.

**Alternatives rejected.** Always separated objects (shortcut leak) and always
touching objects (invalid shared-color scenes).

**Probe.** 5,400-draw stress: 2,400 non-shared public anchors had required
contact and 1,200 shared public anchors remained three separated components.

**Limit.** Diagnostic profiles themselves need not carry the contact witness
because every complete scheduled lesson contains a canonical anchor.

## D8 — Fail closed on ambiguous teaching examples

**Choice.** `self_check` requires exactly three objects, at least three cells per
object, distinct contour counts, a declared profile, and a declared palette
mode. Exact overrides must be recoverable from pixels.

**Rationale.** The selected curriculum teaches contour ranking directly. Ties,
undeclared morphology, or unobservable overrides would weaken supervision.

**Alternatives rejected.** Accepting all rule-valid grids. The Racket rule is
broader than the intentionally bounded training grammar.

**Probe.** Mutation tests, override gate, 67 task tests, and 5,400-draw stress.

**Limit.** This validator deliberately rejects some inputs the Racket rule can
lawfully transform, including more than three objects and contour ties.

## D9 — Build a reusable cyclic-window probe

**Choice.** Add `workspace/probe_lessons.py`, which imports the current
`LESSON_COMPETITORS` rather than copying a fixed rival list.

**Rationale.** The source-bound census is authoritative but comparatively heavy
and does not rotate every pair into query position. The probe is fast enough for
edit loops and automatically grows when competitors are added.

**Alternatives rejected.** An ad hoc notebook or hard-coded rival names, both of
which would silently become stale.

**Probe.** The probe itself is covered by the selected-task test suite; final
report is `checks/cyclic-probe-final-v311.json`.

**Limit.** It uses the Python mirror, so it supplements rather than replaces the
Racket-bound census and battery.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-3d8a2923eaad77a7:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `bdab70b6181c982eab40837a5659fea7c58a2760032be5a530843dd155defb0d`. At disposition, audited bytes match the current source.

### Current decision

Bounded exact-source audit:67reported task tests and54cyclic windows across3bands, all7declared rivals refuted. No issue in this tested grammar/source; this closes only the new no-issue report, not independent findings or universal induction. Target unchanged.

### Assessment or prior finding

## 901c6034f67e

**No issue found after focused adversarial checks.** The current source SHA-256 is
`bdab70b6181c982eab40837a5659fea7c58a2760032be5a530843dd155defb0d` and pins
rule `3646fc9eedbe`. Its 67 task-local tests passed in the portable audit runtime.
The source-bound cyclic probe checked 18 consecutive three-demonstration windows
per band (54 total); all 54 were identifiable, and every window refuted all seven
declared rivals: area, bounding-box area/perimeter, color-blind connectivity,
identity, reversed contour rank, and scan order. Evidence:
`checks/audit/901c6034f67e-task-tests/` and
`checks/audit/901c6034f67e/cyclic-probe.json`.

This is finite evidence over the declared grammar and rivals, not a proof against
all possible shortcuts. I left the audit target unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
