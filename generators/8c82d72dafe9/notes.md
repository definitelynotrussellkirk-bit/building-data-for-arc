# Working notes: 8c82d72dafe9

## Current rule and authority

Canonical `RULE_HASH = 70532d39072c`. A nonzero color qualifies only when it
appears exactly twice in different rows and columns. Its cells are opposite
corners of an axis-aligned rectangle; paint the complete border in that color
on top of the original grid. Preserve non-qualifying colors. Qualifying colors
are processed in row-major first-occurrence order, so the later qualifying
color wins where borders overlap. The canonical Racket program was not edited.

## 2026-10-08 repair (2.0.1 -> 3.0.0)

The imported generator emitted only separated qualifying pairs. It therefore
omitted canonical non-pair distractors, never exercised overlap precedence,
rejected all canonical examples in `self_check`, declared dead palette/texture
axes, and had no rule-hash pin or executable lesson-rival contract.

The replacement generator uses five deterministic schedule profiles. Every
default scene has two to four qualifying rectangles, one or two connected
3/4-cell non-pair distractors, optional exactly-two collinear controls, and an
overlap between the first two qualifying rectangles. The schedule deliberately
contains both numeric-higher and numeric-lower later winners. Exact public axes
are now only `grid_h`, `grid_w`, `n_rects`, `n_nonpair`, and `n_collinear`; unknown,
non-integer, and out-of-range overrides fail loudly.

Two canonical-fitting shortcuts are retained as executable competitors:

- `higher_color_wins_crossings`: fits all canonical pairs because the only
  canonical qualifying-border overlap happens to favor the larger color.
- `expand_all_exactly_two_bboxes`: fits all canonical pairs because they contain
  no exactly-two collinear distractor.

Minimal retained counterexamples are in `counterexamples/` and are covered by
focused tests. The five-slot lesson schedule uses four demonstrations and one
query; every cyclic start and every query rotation is checked against all
declared rivals.

## Decisions and limits

- Overlap is present in every default lesson, even though most canonical pairs
  are disjoint. This is intentional teaching pressure against the strongest
  canonical-fitting precedence shortcut. A one-rectangle scene remains
  available by exact override.
- The production domain is deliberately narrower than the full mathematical
  rule domain: background is 0; dimensions are 9..18 by 10..18; qualifying
  rectangles use two fixed template families with reflections/offsets; and
  non-pair distractors are connected 3/4-cell shapes outside target borders.
- `self_check` accepts the broader canonical rule domain. `strict_canonical_like`
  defines the narrower lesson manifold.
- Declared-rival and finite census results are evidence against those named
  hypotheses only; they do not prove universal rule identifiability.
- No prior return was used as a repair authority. The catalog/associated notes
  supplied only the current-source lead `missing_rule_hash`; all other findings
  were remeasured from the pinned baseline.
## Current reviewer considerations

Source SHA-256: `e86affc7e7a2b99467365d1c40708a330e3dc8f10dc51261d479bc9a00b14aa0`.

# Decisions for `8c82d72dafe9`

Final generator SHA-256:
`e86affc7e7a2b99467365d1c40708a330e3dc8f10dc51261d479bc9a00b14aa0`.
Canonical rule hash: `70532d39072c`.

## D1 — Keep the canonical Racket authority unchanged

**Prior choice and rationale:** The imported generator did not pin the authority.
Its original rationale was not documented. Direct canonical inspection and the
baseline rule-smoke run showed that the Racket transformation itself was
coherent; the defects were in generation, validation, and teaching coverage.

**Choice:** Pin `RULE_HASH = "70532d39072c"` and change only selected generator,
test, note, workspace, and counterexample files.

**Alternatives rejected:** Rewriting the Racket rule to simplify precedence, or
changing canonical examples to fit the old generator. Either would alter the
actual task instead of repairing the sampler.

**Probe/evidence:** Final authority synchronization and execution parity are in
`checks/after/checks/8c82d72dafe9_after_authority_sync.json`; 120 generated
Racket applications and mirror comparisons are in the rule-smoke report.

**Failure mode/limit:** A future canonical rule edit must change the pin and
rerun all source-bound evidence.

## D2 — Replace dead descriptive axes with five exact structural controls

**Prior choice and rationale:** Version 2.0.1 advertised diagnostic
`position_bias`, `density`, and texture choices. No original rationale was
recorded; baseline defect lint showed the helpful textures were byte-identical,
and lint could not meaningfully probe the single-token axes.

**Choice:** Expose only `grid_h`, `grid_w`, `n_rects`, `n_nonpair`, and
`n_collinear`. Values are strict integers with closed ranges; unknown,
non-integer, and out-of-range values fail loudly. `observe_overrides` measures
the returned grid rather than trusting requested metadata.

**Alternatives rejected:** Keeping decorative controls marked diagnostic, or
silently clamping unsupported values. Both preserve an API that says more than
the output can demonstrate.

**Probe/evidence:** The exhaustive contract covered 318 boundary/default cases
in each of three bands over 30 seeds: 28,620 generated cases, all passing, with
unknown keys rejected. See `checks/after/checks/8c82d72dafe9_after_override_results.json`.

**Failure mode/limit:** The Cartesian shared gate is expensive; this is tooling
feedback F1, not a task-local correctness defect.

## D3 — Use canonical-supported dimensions and object counts

**Prior choice and rationale:** The baseline produced one qualifying rectangle
per scene. Its rationale was unknown. Baseline defect lint reported canonical
maximum object count 4 outside generated range `[1,1]`, and the profile floor
found zero exact canonical-profile hits in 60 draws.

**Choice:** Dimensions span 9..18 by 10..18. Scheduled production uses two to
four qualifying rectangles; exact override still permits one. Two schedule
profiles use exact canonical dimensions, while other profiles broaden size and
count by difficulty.

**Alternatives rejected:** Copying only the five canonical shapes, which would
be too narrow, and unrestricted random rectangle packing, which made reliable
joint exact overrides and overlap semantics harder to guarantee.

**Probe/evidence:** Final profile floor accepted all five canonical inputs,
found 20 exact and 30 envelope hits in 60 draws, and found exact support in all
three bands.

**Failure mode/limit:** Production does not cover every dimension or arbitrary
rectangle arrangement in every difficulty band; exact public controls cover the
documented range.

## D4 — Use two deterministic layout families with transformations

**Choice:** Draw from two four-box templates, then independently choose a row
reflection, column reflection, and legal offset. The first two boxes always have
border overlap; boxes three and four broaden count without relying on stochastic
packing success.

**Rationale:** The rule's least obvious behavior is overlap precedence. Making
that behavior constructive prevents a lesson from accidentally omitting it and
keeps every exact combination buildable at the minimum 9×10 size.

**Alternatives rejected:** Rejection-sampling arbitrary rectangles. It produced
unnecessary construction risk at the smallest grid with four rectangles and
negative controls. A single fixed template was also rejected as too repetitive.

**Probe/evidence:** Focused boundary tests exercise all 48 combinations of two
bounds for dimensions/counts across three bands; the shared override gate tests
the full case matrix. Diversity and strict semantic gates pass.

**Failure mode/limit:** Geometry remains template-bounded. Reflections, offsets,
corner diagonals, dimensions, counts, colors, and distractors vary, but the
sampler is not a general rectangle-layout enumerator.

## D5 — Restore canonical non-pair distractors without confusing axis observability

**Prior choice and rationale:** The old `self_check` treated every color count
above two as malformed, even though all five canonical inputs contain such
colors. The likely intent was to simplify corner-pair construction, but no
rationale was recorded.

**Choice:** Ordinary production contains one or two connected 3/4-cell shapes
using distinct colors. They are placed outside every target border so their
multiplicity remains observable before and after transformation. Broad
`self_check` accepts all canonical multiplicities; `strict_canonical_like`
requires the selected teaching grammar.

**Alternatives rejected:** Random singleton noise (too unlike canonical data),
placing distractors on target borders (can alter multiplicity and qualification),
and fresh-canvas outputs (contradicts preservation).

**Probe/evidence:** The non-pair witness fired 600/600 semantic draws; all five
canonical inputs pass both validators; the fresh-canvas competitor is refuted.

**Failure mode/limit:** Production non-pair shapes are only connected 3- and
4-cell patterns, while the authority can preserve many other multiplicities and
geometries.

## D6 — Add exactly-two collinear negative controls

**Choice:** Three of five schedule profiles contain one horizontal or vertical
exact pair with at least one intervening cell. The full segment is reserved from
other controls so the bbox-expansion rival necessarily makes an observable
change.

**Rationale:** The shortcut “expand every color occurring exactly twice” fits
all five canonical pairs because none contains this negative case.

**Alternatives rejected:** Adjacent collinear pairs, whose bounding border equals
the two endpoints and therefore does not refute the rival; or relying on
non-pair distractors, which test a different condition.

**Probe/evidence:** `counterexamples/collinear_exact_pair.json`, its Racket
application under `checks/counterexamples/8c82d72dafe9/`, and 354/600 witness
hits in the semantic census.

**Failure mode/limit:** Only one collinear pair is generated per scene; exact
override can omit or require it.

## D7 — Deliberately decorrelate numeric color order from encounter order

**Choice:** Every scheduled scene overlaps the first two qualifying rectangles.
Three profiles make the later first-occurring color numerically higher; two make
it lower. Colors are otherwise drawn distinctly and are not assigned semantic
roles.

**Rationale:** “Higher color wins crossings” is the strongest simple rival that
fits every canonical pair. Both precedence directions are required to teach the
actual row-major first-occurrence law.

**Alternatives rejected:** Random color assignment without a coverage schedule;
it could produce a complete lesson where all four demonstrations accidentally
support numeric priority. Making every query a lower-color case was also
rejected because demonstrations, not query position, should carry the evidence.

**Probe/evidence:** The exact 5×5 lower-color witness and Racket output are under
`checks/counterexamples/8c82d72dafe9/`. The higher and lower overlap witnesses
fired 351/600 and 249/600 semantic draws, respectively.

**Failure mode/limit:** More complex order shortcuts remain possible in
principle; the finite competitor set is documented rather than presented as a
proof.

## D8 — Four demonstrations, one query, and required query-rotation support

**Choice:** `EXAMPLES_NEEDED = 4`. Five deterministic profiles repeat in a
cyclic schedule. For every five-pair window, any one pair may be the query and
the remaining four must refute every declared competitor.

**Rationale:** Four demonstrations allow both precedence directions, a
collinear negative, and distractor preservation to be visible simultaneously.
The downstream assembly permits query rotation, so identifiability cannot
assume a privileged final slot.

**Alternatives rejected:** Three demonstrations, which cannot reliably expose
all scheduled distinctions under every hold-one-out rotation; and an ordered-only
curriculum, which would hide a position dependency.

**Probe/evidence:** Focused tests enumerate every cyclic start and all five query
positions for each difficulty. The semantic gate checked 60/60 rotations. The
large census materialized 300 lessons and checked 1,500 rotations with zero
ambiguities or hook/scoring errors.

**Failure mode/limit:** The large census does not enumerate all schedule starts
with new random draws; the focused deterministic test covers all five starts,
and the census provides broader sampled evidence.

## D9 — Separate lawful-domain validation from production-manifold validation

**Choice:** `self_check` validates rectangular ARC grids and requires at least
one qualifying diagonal pair, while allowing canonical distractors.
`strict_canonical_like` additionally enforces two to four rectangles, at most
one collinear pair, and one or two 3/4-cell non-pair colors.

**Rationale:** The authority's lawful domain is broader than the chosen lesson
manifold. Combining the two caused the baseline to reject real canonical inputs;
making `self_check` as narrow as production would repeat that error.

**Alternatives rejected:** A permissive `self_check` that accepts blank or
singleton grids, and a production validator that silently infers generator
metadata.

**Probe/evidence:** All canonical inputs pass; mutation fixtures reject blank,
singleton-only, collinear-only, invalid-color, and ragged near-misses; strict
rate is 600/600 on generated scenes.

**Failure mode/limit:** `self_check` does not prove that every accepted grid was
sampled by this generator; that is intentional.

## D10 — Declare executable rivals and retain minimal counterexamples

**Choice:** Declare five semantic competitors: collinear-bbox expansion,
higher-color precedence, lower-color precedence, fresh-canvas rendering, and
identity. Mark the two that fit every canonical pair as
`CANONICAL_SHORTCUTS`. Keep two minimal JSON witnesses under
`counterexamples/` and independently test their expected and rival outputs.

**Rationale:** Named executable hypotheses make shortcut claims reproducible and
allow lesson-level ambiguity checks rather than relying on prose.

**Alternatives rejected:** A prose-only shortcut list, or treating successful
canonical imitation as evidence of correctness.

**Probe/evidence:** Both canonical shortcuts fit 5/5 canonical pairs. Actual
Racket applications of both witnesses match the retained expected outputs.
No declared competitor survives any measured lesson while changing its query.

**Failure mode/limit:** The list is not exhaustive; untested hypotheses remain
unknown.

## D11 — Leave the two audit targets unchanged

**Choice:** Reproduce and document defects in `7fd453cd0339` and
`e0fc08522773`, retain source-bound inputs and Racket outputs, and do not patch
them.

**Rationale:** The assignment explicitly limits source edits to the selected
repair target. Audit findings are intake leads, not approvals or implicit repair
permission.

**Evidence:** `AUDIT.md` and `checks/audit/<task_id>/`.

## D12 — Preserve failures and verify the final delta in isolation

**Choice:** Keep the interrupted initial battery, targeted baseline failures,
intermediate probes, full final battery, task-test snapshot, census, audit
reproducers, solves, and a pristine-packet patch replay.

**Rationale:** The initial aggregate was not a completed verdict. Isolated
baseline stages distinguish genuine pre-repair defects from interruption, while
the final replay proves the returned source delta is portable.

**Failure mode/limit:** Timing measurements depend on the review environment;
semantic and hash results are the acceptance evidence, not wall-clock speed.
