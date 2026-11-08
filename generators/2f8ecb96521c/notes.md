# Current notes: 2f8ecb96521c

## Intended task

The selected authority identifies exactly two solid 4-connected color-4 rectangles,
orders them by area, and recolors only their strict interiors: smaller rectangle
with color 1, larger rectangle with color 2. Borders and background remain
unchanged. The selected canonical Racket authority was not edited; the generator
pins `RULE_HASH = "32d5e32db8fe"`.

## Generator design (v2.0.0)

- Input dimensions are 10–14 by 10–14, weighted toward canonical 10×10.
- The input palette is fixed to `{0, 4}`.
- Small shapes are `3x3`, `3x4`, or `4x3`; large shapes are `3x5`, `5x3`,
  `4x4`, or `5x5`. The 5×5 branch was added because canonical large-object area
  support reaches 25.
- Layout is one of `stacked`, `side_by_side`, or `diagonal`; `small_role` is
  `near` or `far`. Every advertised joint override combination is constructed
  directly, including on the minimum 10×10 canvas.
- Four demonstrations and one query use a five-step default profile cycle:
  `stacked:near`, `side_by_side:far`, `stacked:near`,
  `side_by_side:far`, `diagonal:near`. Holding out any one pair leaves witnesses
  against row projection, column projection, and position order.
- `self_check`, strict-profile classification, override observation, executable
  rivals, semantic witnesses, and lesson-identifiability checks are explicit.

## Reversed decisions and evidence

The selected baseline (v1.3.0) generated only diagonally separated rectangles,
so a column-projection shortcut fit 300/300 sampled inputs. It also advertised
controls it did not honor and lacked the authority pin. The retained finding from
`review-a17bad0aece71558:v0001` was used as a lead, then remeasured against the
selected baseline. The replacement uses truthful finite axes and constructive
placement rather than retry-based sampling.

An initial side-by-side implementation allowed the nominally near object to begin
below the far object, which preserved a row-major position-order shortcut. The
focused test exposed the exact placement; side-by-side placement now also requires
the near top row not exceed the far top row. A later defect-lint run showed that
large-object area support stopped below the canonical median; the 5×5 large shape
closed that gap. The standalone `workspace/reference_probe.py` initially relied
on the check runner's injected `PYTHONPATH`; a subprocess regression test exposed
and fixed its repository-root calculation.

## Verification summary

The decisive evidence is retained under `WORK/checks/`:

- focused red evidence under `checks/task-tests-red/`;
- final task-local tests under `checks/task-tests-final/` and the later final rerun;
- completed after battery under `checks/after/`;
- independent 100-draw-per-band probe in `checks/reference-probe-final.json`;
- production lesson census in `checks/lesson-census-final.json`.

The 300-lesson census materialized 1,500 labelled pairs and checked all 1,500
single-query rotations: zero declared-rival ambiguities, zero materialization or
scoring errors, and 1,268 unique inputs. These are finite results for the five
declared rivals, not a proof of unique induction against every possible rule.

## Known limits and open questions

- The generator intentionally covers solid rectangles only; it does not claim the
  complete set of every lawful canonical-like placement or arbitrary nonrectangles.
- Output colors 1 and 2 and input color 4 are semantic constants, not palette axes.
- The default profile cycle is deterministic and index-periodic. Explicit layout
  and role overrides remain available for independent sampling.
- Declared-rival checks cover column projection, row projection, position order,
  same-color interiors, and reversed area rank. Undeclared hypotheses remain
  untested.
- No selected Racket or canonical source changed.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-a17bad0aece71558:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `925548f9e53a62e164b0c07cd862f6812170c84192d75c968eb927e9ac1807be`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted repair review-bc6dab8f534b276d:v0001, exact source 97c3f5b9742f87d77bfcc4de2d3bee0f84d21059c16dd1d651829026afac7a0e, constructs stacked/side-by-side/diagonal support, truthful exact controls and selected authority pin; old diagonal/projection and ignored-control findings addressed. Reviewer reports 58 focused tests, 12/12 battery and 300 lessons/1500 rotations; owner inspected the repair/evidence but did not rerun those batteries. Original audit/source/witness retained in this bounded assessment; no universal identifiability or training admission.

### Assessment or prior finding

## 2f8ecb96521c

**A2 — Reproduced positional support gap and observational shortcut.** Generator SHA256 `925548f9e53a62e164b0c07cd862f6812170c84192d75c968eb927e9ac1807be`; selected rule hash `32d5e32db8fe`.

The placement loop requires both row and column separation; it therefore emits diagonal layouts only, including its fallback. A cheaper rival can segment objects by blank **column runs** instead of2-D connectivity, sort those groups by area, and recolor their interiors. This is an executable segmentation shortcut, not just a label attached to a suspected bias.

Same census policy as A1: **300 draws over289 unique inputs**, every draw validator-clean. Projected column-span overlap is **0/300**, and the column-projection rival matches **300/300** selected-Racket outputs. All **three canonical examples** have overlapping column spans, remain accepted by self_check, and refute this rival; selected Racket agrees with their stored outputs. Thus larger random default samples alone cannot expose this missing family, and any lesson assembled entirely from those sampled defaults leaves this rival viable on a canonical query.

At seed17/index3/medium, `position_bias='stacked'` and `'diagonal'` produce the identical input hash; `blob1_w=3` and6 also produce the same grid, whose first rectangle width is5. Advertised `grid_w=10` raises an error against medium bounds12..14, although canonical grids are10×10. Exact results and bounding boxes are in `checks/audits/report.json`.

`checks/audits/2f8ecb96521c-counterexample.json` contains two separated solid rectangles with areas9 and12, overlapping column spans, and different vertical positions. It passes self_check and belongs to the documented two-distinct-rectangle domain. Selected Racket recolors the interiors; the column-projection rival leaves the grid unchanged because it sees one column run. It is a hand-constructed supported-domain counterexample, not a claimed generated draw. Recommended separate repair: generate stacked/side-by-side/diagonal configurations with overlap in one projection, honor observable controls, and add this rival to lesson checks. No target files were modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-a17bad0aece71558-v0001/audit_assets.json), manifest SHA-256 `3a4133aa971ef74ecad853b8d2d82a40b6e98ccc3238eaa80ef27d53641380a6`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `97c3f5b9742f87d77bfcc4de2d3bee0f84d21059c16dd1d651829026afac7a0e`.

# Decisions: 2f8ecb96521c

## D1 — Keep the selected rule; repair only the generator

**Choice.** Preserve the canonical Racket program and pin
`RULE_HASH = "32d5e32db8fe"`.

**Rationale.** All three canonical pairs agree with an independent geometry
oracle and the selected authority. The demonstrated defect was lesson input
support, not label computation.

**Alternatives rejected.** Rewriting or duplicating the Racket rule would add
source-authority churn without addressing the shortcut.

**Evidence / limitation.** Rule smoke and authority sync are green. The Python
oracle is supplementary and is not treated as label authority.

## D2 — Replace generic advertised axes with a truthful finite domain

**Choice.** Expose only dimensions, small shape, large shape, layout, and
small-role axes. Reject unknown keys and invalid scalar types/ranges.

**Rationale.** The baseline advertised controls it did not use. Exact finite
axes make override checks meaningful and permit exhaustive joint testing.

**Alternatives rejected.** Keeping decorative `palette_kind`, density, texture,
or count axes would preserve a false contract. Input and output colors are fixed
semantic roles, not exchangeable styling choices.

**Failure modes / limits.** This intentionally narrows the generator to solid
rectangles with palette `{0,4}`. It does not claim nonrectangular support.

## D3 — Construct placements instead of retrying

**Choice.** Enumerate legal near/far top-left placements and select one
deterministically from a keyed RNG.

**Rationale.** Every advertised combination must work even on 10×10; direct
construction avoids silent undershoot and retry-budget failures.

**Alternative rejected.** Random rejection sampling is shorter but can fail or
bias rare joint overrides.

**Probe.** Focused tests enumerate every small shape × large shape × layout ×
role in all four bands and compare an independent observer with the requested
values.

## D4 — Use three spatial families and an explicit role reversal

**Choice.** Generate stacked, side-by-side, and diagonal layouts, with the
smaller rectangle either near or far.

**Rationale.** Stacked examples refute column segmentation, side-by-side examples
refute row segmentation, and `small_role=far` refutes order-by-first-position.
The original diagonal-only support refuted neither projection rule.

**Intermediate reversal.** The first side-by-side implementation allowed the
near object's top row to begin below the far object's top row. A regression
showed that row-major order could then disagree with the nominal near/far order.
The final legal-placement predicate requires `near_top <= far_top`.

**Limit.** “Near” is defined by top/bottom for stacked, left/right for
side-by-side, and north-west/south-east for diagonal; it is not a metric-distance
axis.

## D5 — Include a 5×5 large rectangle

**Choice.** Large shapes are 3×5, 5×3, 4×4, and 5×5.

**Rationale.** The first repair topped out at area 16. Defect lint compared this
with canonical large-object support and found the canonical median at area 25.
A 5×5 rectangle composes with every small shape and layout on the minimum canvas.

**Alternative rejected.** Weakening the profile gate would hide the support gap
rather than teach it.

## D6 — Four demonstrations and a five-step cyclic schedule

**Choice.** Use four demonstrations plus one query with profiles:

1. `stacked:near`
2. `side_by_side:far`
3. `stacked:near`
4. `side_by_side:far`
5. `diagonal:near`

The cycle repeats by sample index.

**Rationale.** Holding out any pair still leaves at least one stacked witness,
one side-by-side witness, and one far-small witness. This supports arbitrary
single-query rotation within the five-pair window.

**Alternatives rejected.** Pure random profiles can produce complete lessons
without a needed witness. A three-demonstration schedule did not have enough
redundancy to survive every holdout.

**Tests.** Every cyclic start, all four bands, all five query positions, and all
five declared rivals are checked locally. The larger census checks 300 sampled
lessons and 1,500 rotations.

**Naming decision.** The implementation uses `SCHEDULE_CYCLE` rather than the
special gate-enumeration constant. The cycle is still exhaustively tested in the
task suite; this avoids claiming the shared fixed-seed schedule enumerator is the
only or complete evidence.

## D7 — Declare executable competitors and witnesses

**Choice.** Declare column projection, row projection, position order, same-color
interiors, and reversed area rank. Map concrete witnesses to each rival.

**Rationale.** Correct individual labels do not make a lesson teachable. An
executable competitor lets the gate retain exact counterexamples and evaluate
both normal and rotated queries.

**Alternatives rejected.** Natural-language rival names without code cannot be
scored. Treating the independent Python oracle as authority would duplicate the
selected Racket source.

**Limit.** The list is finite. Passing it is evidence against these hypotheses,
not proof of unique induction.

## D8 — Make the strict manifold the complete validated domain

**Choice.** `strict_canonical_like` delegates to `self_check`, with
`MIN_STRICT_FRAC = 1.0`.

**Rationale.** Every produced input is intended to be a lawful task instance;
there is no broad off-manifold augmentation branch.

**Alternative rejected.** Reporting a lower strict fraction would misdescribe a
sampler designed entirely for task-lawful grids.

## D9 — Build an independent reusable probe

**Choice.** Add `workspace/reference_probe.py` with independent component
analysis, rule mirror, rival implementations, observed-axis extraction, and a
100-draw-per-band CLI audit.

**Rationale.** Future reviewers need a small tool that does not import the
generator's private geometry helpers.

**Intermediate reversal.** The first path calculation worked only under the
check runner's injected `PYTHONPATH`. A subprocess test with `PYTHONPATH` removed
failed at import time; the root calculation was corrected and the regression is
now permanent.

**Limit.** Its Python expected-output mirror is supplemental. Selected Racket
receipts remain the source-bound parity evidence.

## D10 — Preserve genuine solve provenance

The blind task was solved before source inspection. The post-repair task was
solved only from visible examples after preparation, but earlier rule exposure is
recorded as `yes`. No artificial failed solve was created, and masked-query
correctness is not claimed.

## Review `review-31486904d971b7a9` — proposed parameter and source-bound shortcut evidence

The selected production generator remains byte-identical at SHA-256
`97c3f5b9742f87d77bfcc4de2d3bee0f84d21059c16dd1d651829026afac7a0e`;
`RULE_HASH = "32d5e32db8fe"` and the canonical row are unchanged. The fresh before
and final-after batteries are both 12/12 green. The final portable task suite is
62/62 green, and a 300-lesson / 1,500-rotation census found zero ambiguity or
scoring errors against the declared rivals. These are finite checks, not universal
identifiability proof.

### D11 — Keep the approved production path; add a separate rank-order prototype

A proposed prototype now lives under `workspace/parametric/`. It chooses
`rank_order` once per episode from `small_to_large` (the exact canonical default)
and `large_to_small` (the same area-ranked rule with the sorted object list
reversed). Four demonstrations plus one query distinguish the settings on every
retained pair because production inputs have exactly two distinct-area rectangles
with nonempty interiors. Protected Racket and an independent Python mirror agree
on all 20 retained applications. This prototype is not selected, approved, or
training-admitted; it does not change `generator.py`.

### D12 — Retain the canonical-fitting row-projection witness

`row_projection` is the strongest executable shortcut found that fits all labeled
canonical pairs: it segments by occupied row runs instead of 4-connected objects.
It fails on side-by-side rectangles. The exact production witness at seed
`20261020`, sample index `1`, difficulty `medium` is retained in
`counterexamples/row_projection_canonical_fit.json` and covered by
`tests/test_shortcut_witness.py`. The selected output comes from protected Racket;
the rival comes from the independent workspace probe. The existing five-pair
schedule already emits two side-by-side refutations, so no schedule change was
made.

### D13 — Preserve portable source isolation

The first portable prototype run correctly rejected a mixed `puzzle_generators`
source tree. The final prototype loads a repository-layout mirror only after its
SHA-256 is proven equal to the manifest-selected generator; otherwise it uses the
shared selected-generator loader. The original 61-pass/1-fail run is retained,
and the corrected portable snapshot passes 62 tests. The source-tree safety check
was not weakened.

### Open limits

The production family remains intentionally limited to two separated solid
color-4 rectangles. The parameter changes ranking direction only. Declared-rival
and sampled-lesson passes do not rule out every alternate induction. Historical
returns `review-bc6dab8f534b276d:v0001` and
`review-a17bad0aece71558-v0001` were used as leads only; current claims above are
bound to this review's fresh evidence.

## Review `review-f7c9403c23453d70` — native rank/axis family

The production generator and canonical rule remain byte-identical. The native
family exposes episode-fixed `rank_order = small_to_large | large_to_small |
dominant_axis`; `small_to_large` is the exact canonical program. The sequential
setting measures doubled row-center and column-center separations, derives the
unique dominant axis, orders the two rectangles along that axis, and then uses
the canonical interior-color assignment on that order.

The sampler supports every 2–6 demonstration prefix and 1–4 query prefix on
matched inputs, with four distinct queries and a 30×30 fourth query containing
378 foreground cells and touching all boundaries. The first implementation
randomly reflected scenes across the perpendicular axis. Adversarial review
showed that this silently changed whether fixed-row/fixed-column rivals agreed
with the lesson. Seed variation now uses only a joint translation of both
rectangles, preserving every ordering relation. Query profiles were also made
constructively alias-safe for rivals that are indistinguishable on the minimum
lesson. The retained 32-seed audit covers 1,920 episodes, 12,480 labels, and
4,800 public projections with zero findings against the declared rivals.

Native qualification passes all three settings on seeds 0 and 17 with 78
protected-Racket evaluations. The causal witness has row-center distance 18 and
column-center distance 11, so Step A derives `row`; forcing `column` reverses
which rectangle receives interior colors 1 and 2 and changes the final grid.
This is finite source-bound reviewer evidence only. Exact integrated-source
owner acceptance, canonical approval of the added settings, and any training
admission remain pending.
