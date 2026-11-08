# Working notes: 8dd7ace7de9a

## Selected rule

The rule searches candidate row periods in ascending order and, within each row period, candidate column periods in ascending order. Color `6` is ignored while fitting. A candidate is accepted only when all observed non-6 cells agree by residue class and every tile residue has at least one clean representative. The first complete fit is repeated across the original grid; if no fit exists, the rule returns an all-zero grid.

Canonical normalized rule hash: `0f05e4e27969`.

## Baseline findings

The imported `1.2.0` generator had useful periodic examples but was not an honest, source-bound curriculum:

- no `RULE_HASH` pin;
- advertised axes were ignored, clamped, aliased, or not recoverable from pixels;
- dimensions were usually below the canonical 12–16 by 12–19 profile;
- duplicate noise placements weakened the requested noise count;
- no executable semantic witnesses, named rivals, or lesson identifiability contract;
- active selected `target_code` copies were execution-equivalent but textually divergent from the canonical source.

The retained baseline battery is `checks/before/result.json`: 5 green, 2 advisory, and 5 failed stages.

## Repair decisions

### Constructive periodic tile

The clean tile has a unique color at `(0, 0)` and a different color along the remainder of its first row and first column. This constructively proves the requested fundamental row and column periods: every smaller candidate conflicts with `(0, 0)`. Extra palette colors are placed only after that certificate exists.

### Exact noise

Noise cells are sampled without replacement. At least one clean representative of every residue is protected. The first row and column of the tile remain clean because they certify the fundamental period. `clean_anchor=False` forces one safe interior anchor cell to noise, so the boolean is observable even at `noise_count=1`.

### Canonical-scale curriculum

An independent four-step scale schedule uses the three canonical profiles `(12,12)`, `(15,19)`, and `(16,16)`, plus a broader canonical-envelope branch. Difficulty changes exact noise count ranges: easy 18–34, medium/default 30–52, hard 45–64.

### Semantic schedule

Three consecutive samples use exact periods `(3,3)`, `(2,2)`, and `(4,3)`. The final profile is simultaneously rectangular and period-four, so each complete three-demo lesson refutes both canonical-compatible rivals:

- `square_period_only`;
- `periods_at_most_three`.

The canonical examples themselves fit both rivals, which is why generated counterexamples are required rather than optional diversity.

### Authority synchronization

The canonical Racket program was not semantically changed. The two active selected `racket_target.target_code` fields were replaced with the exact canonical text. Their archival `raw_code` fields were deliberately preserved. Final authority status is `selected_synchronized_archival_divergent`, with execution parity passing.

## Tests and retained tools

- `tests/test_generator.py`: 32 source-bound regression tests, including 512 boundary Cartesian override cases, canonical parity, schedule coverage, deterministic replay, validator mutations, and authority preservation.
- `tests/test_lesson_probe.py`: deterministic regression test for the retained lesson census.
- `workspace/reference_probe.py`: independent period-search mirror, canonical/authority readers, observable-axis recovery, and source-bound loader.
- `workspace/lesson_probe.py`: replays the inherited semantic-gate sampler, dynamically reads `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, checks all cyclic starts, and records source hashes, uniqueness, observed limits, witnesses, and rival survival.

The final 100-lessons-per-band report is `checks/lesson-probe-final.json`: 300/300 lessons identifiable, 1,200/1,200 unique generated inputs, zero surviving rivals, and zero hook or competitor errors.

## Verification-driven evidence

The TDD sequence is retained:

- `checks/task-tests-red.log`: baseline failures before production changes;
- `checks/task-tests-intermediate-1.log`: 31 passing tests with the selected-authority mismatch still exposed;
- `checks/task-tests-green.log`: the original 32-test suite green;
- `checks/lesson-probe-red.log` and `checks/lesson-probe-green.log`: missing-tool failure followed by the implemented probe passing;
- `checks/task-tests-final.log`: final combined task-local suite.

The final inherited battery is `checks/after/result.json`: all 12 stages green.

## Remaining limits

This is a compact teaching distribution, not evidence of universal rule induction. The semantic contract names two high-value canonical-compatible rivals; it does not enumerate every program that might coincide on the sampled domain. The schedule deliberately guarantees those witnesses rather than trying to approximate a natural unrestricted puzzle distribution. Catalog approval and downstream model-value checks remain separate.
## Current reviewer considerations

Source SHA-256: `5989a1f783b99c801dfaca05ae5d36bd777497bd7a1da985f53d7f742940cbf9`.

# Decisions: 8dd7ace7de9a

## D1 — Preserve the selected rule; repair the curriculum

**Original rationale:** unknown beyond imported notes. The canonical rule already solved all canonical pairs and had a clear lexicographic period-search semantics.
**Choice:** leave the canonical program unchanged and bind the generator to rule hash `0f05e4e27969`.
**Alternatives:** simplify the Racket source, change search order, or make noise recovery use a fixed period.
**Probe:** canonical parity, 120 real Racket applications, A-B-A reentrancy, independent Python mirror.
**Failure mode avoided:** a generator repair silently paired with a semantically changed labeler.
**Limit:** the independent mirror is still code and cannot substitute for the real Racket smoke check.

## D2 — Use canonical-scale dimensions

**Original rationale:** the baseline defaulted mostly to 6–12, despite canonical inputs at 12×12, 15×19, and 16×16.
**Choice:** exact axes `grid_h=12..16`, `grid_w=12..19`; cycle through all three canonical profiles and a broader in-envelope branch.
**Alternatives:** preserve the small baseline grids, use completely uniform dimensions, or pin every draw to canonical sizes.
**Probe:** canonical profile floor, morphology diagnostic, exact observer, 100-lesson-per-band census.
**Failure mode avoided:** models learn a small-grid proxy that does not match the actual task.
**Limit:** height variation is intentionally concentrated in the canonical anchors; the broad branch reuses height 12 to break width/height aliasing without inventing out-of-profile sizes.

## D3 — Construct the fundamental period instead of hoping random tiles have it

**Original rationale:** random tiles can accidentally admit a smaller period.
**Choice:** make `(0,0)` unique and the remainder of the first row/column a different color.
**Alternatives:** rejection-sample random tiles until an oracle reports the requested period, or accept observed smaller periods.
**Probe:** independent period recovery over every boundary Cartesian override and all generated tests.
**Failure mode avoided:** requested `period_r`/`period_c` cannot be recovered from the pixels.
**Limit:** this certificate introduces a recurring tile motif; palette and noise variation prevent byte-level template collapse but do not make tiles unconstrained natural samples.

## D4 — Use exact noise positions without replacement

**Original rationale:** the baseline loop could hit the same cell repeatedly, so nominal density and actual count diverged.
**Choice:** advertise `noise_count`, sample exact distinct positions, and protect at least one clean representative per residue.
**Alternatives:** retain density, retry collisions, or permit unrecoverable examples.
**Probe:** exact observer, count assertions, full override boundary matrix, real rule execution.
**Failure mode avoided:** controls lie and the rule returns all zeros because a residue was fully erased.
**Limit:** the maximum is 64 so every allowed size/period combination can preserve the recovery certificate.

## D5 — Keep `clean_anchor` only because it is pixel-observable

**Original rationale:** anchor corruption can be pedagogically useful, but a metadata-only flag is not an honest axis.
**Choice:** `False` forces one safe interior anchor cell to noise; `True` protects the complete first tile.
**Alternatives:** remove the axis or make it probabilistic.
**Probe:** exact `observe_overrides` equality for every Cartesian boundary case.
**Failure mode avoided:** two override values produce indistinguishable returned grids.
**Limit:** the observer defines “anchor” as the recovered first tile; that definition is task-specific.

## D6 — Three-example deterministic semantic schedule

**Original rationale:** all canonical pairs fit square-only and period≤3 shortcuts. Random coverage does not guarantee a complete lesson refutes either.
**Choice:** periods `(3,3)`, `(2,2)`, `(4,3)` by `sample_index % 3`; `EXAMPLES_NEEDED=3`.
**Alternatives:** random periods with aggregate witness counts, a longer curriculum, or one adversarial example in every draw.
**Probe:** every consecutive three-draw window, all cyclic starts, 100 lessons per band, dynamically scored declarations.
**Failure mode avoided:** a lesson looks diverse globally but its actual demos leave a canonical-compatible shortcut alive.
**Limit:** deterministic scheduling can be recognized; it is chosen for guaranteed teaching support, not claimed as a natural sampling process.

## D7 — Name only two canonical-compatible rivals

**Original rationale:** these are simple, plausible programs that exactly fit every unique canonical pair and fail on a single `(4,3)` witness.
**Choice:** `square_period_only` and `periods_at_most_three`.
**Alternatives:** enumerate many arbitrary malformed algorithms or claim universal identifiability.
**Probe:** verify each shortcut against every usable canonical pair, then record disagreements on actual lessons.
**Failure mode avoided:** semantic checks use rivals that do not even explain the public task.
**Limit:** an undeclared more complex shortcut may still exist; the reports explicitly avoid a universal-induction claim.

## D8 — Synchronize active authority text but preserve provenance

**Original rationale:** selected `target_code` was execution-equivalent but did not match canonical text.
**Choice:** replace two active `target_code` values with exact canonical source; leave `raw_code` untouched.
**Alternatives:** edit canonical, delete archival source, or accept diagnostic divergence.
**Probe:** exact selected-source grouping plus execution parity across distinct source texts.
**Failure mode avoided:** downstream tools do not know which active source is authoritative.
**Limit:** archival divergence remains intentionally visible and is not described as exact global synchronization.

## D9 — Add independent retained probes

**Original rationale:** generator helpers can agree with their own bugs, and the inherited semantic gate samples only 12 lessons.
**Choice:** separately implement period recovery and a source-bound 100-lessons-per-band census.
**Alternatives:** rely only on generator self-checks or add one-off notebooks.
**Probe:** test-first tool creation, deterministic replay, hashes, unique-input counts, cyclic starts, canonical shortcut fit.
**Failure mode avoided:** a green small smoke sample is overgeneralized into a population claim.
**Limit:** the large probe uses the independently written Python label mirror after real Racket parity is established; it does not launch 1,200 Racket calls.


## 2026-10-23 audit reconciliation

The retained audit `review-027a21eee2143eb8:v0001` reproduced against source
`2eea8b924e39232fedb437de952aa7e283a12f9fe3d532ea4a3791e9c8f0b2bb`.
Its pinned easy lesson (`seed=213974615879964`, start index `66`) had three
clean-anchor demonstrations and a noisy-anchor query. The shortcut “infer the
period, then repeat the literal top-left tile” fit all demonstrations and failed
the query because `clean_anchor` was independently random per pair.

Generator `2.1.0` preserves both exact boolean overrides but changes the default
to the same three-slot lesson schedule as the period profiles: clean, clean,
noisy. Thus every cyclic three-demonstration window contains an anchor-recovery
example. `literal_top_left_tile` is now a declared lesson competitor with an
`anchor_recovery_required` witness. It is deliberately not a
`CANONICAL_SHORTCUT`: it fits only one of the three unique canonical pairs, while
the two existing canonical-fitting shortcuts still fit all three.

The canonical Racket text and normalized hash `0f05e4e27969` are unchanged.
Final generator SHA-256 is
`5989a1f783b99c801dfaca05ae5d36bd777497bd7a1da985f53d7f742940cbf9`.
Focused verification retained the TDD failure, then 42 passing task-local tests;
a 300-lesson census found 300/300 identifiable lessons and 1,200/1,200 unique
inputs; two representative real-Racket cases matched the independent mirror;
and a research-mode production episode produced three demonstrations plus four
distinct queries. Catalog approval remains false until ordinary intake reviews
the changed source.

## Proposed output-extent parameter

`workspace/parametric/` now contains a separate proposed parameter
`output_extent ∈ {full_grid, tile_only}`. `full_grid` is the exact canonical
program and remains the default. `tile_only` performs the identical
lexicographic period search and noise recovery, but returns one recovered clean
period tile rather than expanding it to the original dimensions. The setting is
fixed for an episode and is visible from every demonstration’s output shape.

Both three-demonstration/four-query retained episodes use seven distinct inputs
and real Racket labels. Exact program SHA-256 values are
`261d2d3cf5140309e762979fc31c9765a29a05440810b16893b64eecc3c50a2b`
for `full_grid` and
`27b1a00dfd2db15570b192665d2762b9abb86f4f772fc54e2df7360bf156faa2`
for `tile_only`. Public filenames are hashes of only visible demonstrations and
query inputs, and the writer rejects duplicate visible-content IDs rather than
silently overwriting them. The prototype is proposed and unapproved; it does not alter
production generation, canonical authority, catalog state, or training
admission.

## D10 — Coordinate anchor corruption with the lesson schedule

**Prior choice:** draw `clean_anchor` independently for every pair.
**New choice:** default to clean, clean, noisy by semantic profile while leaving
explicit `True` and `False` overrides exact.
**Reason:** aggregate randomness did not guarantee that the actual demonstrations
teach recovery from a corrupted first tile.
**Evidence:** the pinned audit replay, all cyclic three-demo windows, and the
300-lesson census.
**Tradeoff:** default anchor randomness is reduced; override coverage still spans
both values and all other stochastic axes remain unchanged.

## D11 — Keep output extent as an isolated prototype

**Choice:** materialize `full_grid` and `tile_only` as exact Racket programs under
`workspace/parametric/`, not as a new production axis.
**Reason:** output extent is a small executed-rule change that preserves the
family’s central period-recovery reasoning, but it is not part of the canonical
rule and therefore needs separate promotion review.
**Evidence:** focused real-Racket tests, two complete retained episodes, exact
visible-content public IDs, and a bounded public/private adversarial check.
**Limit:** retained evidence covers two settings and two seeds, not every seed or
future canonical-source revision.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-027a21eee2143eb8:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `2eea8b924e39232fedb437de952aa7e283a12f9fe3d532ea4a3791e9c8f0b2bb`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Original source 2eea8b924e39232fedb437de952aa7e283a12f9fe3d532ea4a3791e9c8f0b2bb allowed the literal-top-left rival in the pinned seed/sample66 lesson. Reviewer-reported current source 5989a1f783b99c801dfaca05ae5d36bd777497bd7a1da985f53d7f742940cbf9 schedules a noisy anchor in each three-demo window; sample68 now refutes that rival. Before/after witness, 42focusedtests and bounded Racket comparisons retained in `generators/8dd7ace7de9a/evidence/clean-anchor-audit-resolution/manifest.json`. Explicit resolution of this finding only; owner did not rerun submitted programs.

### Assessment or prior finding

## 8dd7ace7de9a

**Classification: reproduced teaching ambiguity.** Audited generator SHA-256:
`2eea8b924e39232fedb437de952aa7e283a12f9fe3d532ea4a3791e9c8f0b2bb`;
declared rule hash: `0f05e4e27969`.

The generator recovers a periodic tile, but its `clean_anchor` choice is random
per pair rather than coordinated at lesson level. The pinned production-plan
lesson at difficulty `easy`, seed `213974615879964`, start sample index `66`
has three clean-anchor demonstrations (indices 66–68) and a noisy-anchor query
(index 69). A plausible shortcut can infer the period dimensions and repeat the
literal top-left tile, never recovering corrupted top-left residues from later
copies. It fits all three demonstrations but differs from the Racket answer on
60 query cells. The query input passes the target generator's `self_check`.

Reproduction from packet root:

```bash
python3 WORK/checks/audit/8dd7ace7de9a/top_left_tile_shortcut.py \
  > WORK/checks/audit/8dd7ace7de9a/top_left_tile_shortcut.json
python3 review.py run python3 -m arcpuzzles apply 8dd7ace7de9a \
  --input ../checks/audit/8dd7ace7de9a/input.json \
  --out ../checks/audit/8dd7ace7de9a/racket.json
```

The first script is a deterministic local replay. The second ran from the
source-bound `WORK/repo` runtime through `review.py run`; it exited 0, and the
retained Racket report binds the same generator source. Evidence:

- `checks/audit/8dd7ace7de9a/finding.json`
- `checks/audit/8dd7ace7de9a/top_left_tile_shortcut.py`
- `checks/audit/8dd7ace7de9a/top_left_tile_shortcut.json`
- `checks/audit/8dd7ace7de9a/input.json`
- `checks/audit/8dd7ace7de9a/rival_output.json`
- `checks/audit/8dd7ace7de9a/racket.json`

No fix was made to this audit target. A repair should schedule at least one
noisy-anchor recovery demonstration in every lesson window, then test all
permitted held-out query positions.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-027a21eee2143eb8-v0001/audit_assets.json), manifest SHA-256 `9fd3a221d2d1292a3e7148af9257498c255ee78ccffded039e30db005d55d59e`.
<!-- arcpuzzles-current-audit-assessment:end -->
