# Review notes: 064e439acd2d, version 3.0.0


## Current review: review-2cfb18b73cf69677 (2026-10-24)

Finished the retained `edge_mode=near|far` work as a native adapter without
changing the approved production generator. Production SHA-256 remains
`5b86079e3f368a9daff406db90831819f0494ec61b0b3598b446154ca7f13203`;
the canonical/default Racket source remains byte-exact at
`2f6c9a24ba7e9532d3517bf2e2f50f461c8d096a7755c6d8070334ba791e8a07`.
The native API now supports independent 2–6 demonstration and 1–4 query counts,
stable prefixes, matched inputs across settings, four distinct private queries,
and one-query public turns with no future/count hints. The largest query is a
substantive 30×30 scene.

A protected-Racket self-audit ran 160 evaluations over both settings, seeds 0
and 17, and the 2/6-demo boundaries. Two visible demonstrations eliminate the
alternate setting and eight retained shortcuts. Native qualification passed four
jobs and 40 protected labels using three demonstrations and four queries. The
required causal witness is bound to that qualification: deriving the cyan bbox
and source-side classifications is Step A; edge selection is Step B. Shifting
the derived `cmin` before Step B changes four output cells under protected Racket.

Status is reviewer-ready/native-qualified, not owner-accepted. Owner exact-source
acceptance and any training admission remain pending. Finite rivals, seeds and
witnesses do not establish universal identifiability or measured training gain.

## Current review: review-59a3f43f8a82341e (2026-10-19)

Final generator SHA-256: `5b86079e3f368a9daff406db90831819f0494ec61b0b3598b446154ca7f13203`. Canonical Racket rule/hash `7288da9bfc7e` is unchanged. Prior return `review-30645eda24a688cb:v0001` was used as a lead, then remeasured.

The only production defect found was direct call-scalar validation: booleans, floats, strings and negative sample indices were accepted, yielding 30 baseline strict-scalar warnings. `generate` now validates `seed` and `sample_index` before `gen_ctx`. `VERSION` remains `3.0.0` so valid deterministic draws do not remap; focused tests pin pre-repair output bytes.

Final evidence: all 12 battery stages green with schedule period enumeration and required rotations; 555/555 portable task tests pass; profile exact support is 31/60 with every band represented; the 300-lesson census has 1,500 unique inputs and zero ambiguity in production or all 1,500 query rotations. The first strict after run is retained because it correctly failed only the missing schedule-enumeration evidence warning.

A separate **prototype** under `workspace/parametric/` defines fixed-per-episode `edge_mode = near | far`. `near` is byte-exact canonical; `far` paints the opposite bbox edge while preserving object roles, sources, colors and diagonal-ignore behavior. Exact Racket execution agrees with the Python assertion mirror on 10/10 retained pairs, and every demo/query distinguishes the settings. This does not change production approval or authority.

Known limits remain: projection-target collisions are outside the declared domain; the rival checks are finite; the far variant is only proposed. The strongest canonical-fitting shortcut is `border_only`; a refreshed emitted witness is under `counterexamples/review-59a3f43f8a82341e/`.

## Prior review: review-30645eda24a688cb (2026-10-07)

Review assignment `review-30645eda24a688cb`, 2026-10-07. The pinned canonical
rule remains `7288da9bfc7e`. This work repairs the input sampler and its teaching
contract; generated answers still come from canonical Racket execution.

## Intended rule and supported domain

Color 8 forms one solid horizontal line, vertical line, or rectangle on a
color-0 background. Each exterior nonzero, non-8 source aligned with a region
row or column copies its color onto the near bounding-box edge. Keep its
original cell. Sources diagonal to the box do nothing. Repeated source colors
are lawful and all four available canonical inputs pass `self_check`.

The sampler chooses dimensions 5..14 and 1..8 aligned source cells. `n_dots`
counts aligned cells, not distinct colors and not diagonal decoys. `diag_decoy`
adds exactly one extra unaligned cell; `plain` has none; `both_sides` has none
and guarantees a pair on opposite sides with distinct targets. The checker is
deliberately broader than these sampling size/count caps so lawful canonical
inputs are not rejected merely for exceeding a sampling preference.

Every intended projection target is distinct. Collision priority in the
reference rule is outside this sampler's declared domain and is explicitly
rejected by the checker. The no-dot and full-grid textures remain callable
negative fixtures, excluded from the normal texture axis and rejected as
training inputs. Colors 0 and 8 have fixed roles; other source colors vary.

## Reproduced defects and repair

**R1 — Exact controls.** The original sampler could return fewer sources than
requested (seed 0, index 7, 9x10, hline, n_dots=4, plain returned three), silently
substitute hline for vline, accept unknown keys, and reject declared legal sizes
depending on difficulty. Geometry now starts with feasible shapes and distinct
target groups; source placement is constructive, with no partial-count fallback.
Explicit integer controls require actual integers, excluding booleans, floats
and strings. Unknown controls reject. `None` still means unspecified. Impossible
combined controls raise `ValueError` with the active `.incompatible_axes`.

**R2 — Domain and authority.** The prior negative texture declaration overlapped
the normal axis and the selected base record contained stale Racket target text.
Normal and negative textures are now separate. Only the selected record's
`racket_target.target_code` was synchronized to the already pinned canonical
text; its archival `raw_code` and the complete canonical ledger are unchanged.
The count range extends the old cap of five to eight, including canonical
six/seven-source cases. This is an intentional interface extension, not a claim
that every newly failing baseline test represented a previously promised case.

**R3 — Teachable lessons.** The old source supplied no executable lesson
contract. Four plausible shortcuts fit every available canonical pair:
border-only sources, projecting diagonals to a corner, rectangle-only
projection, and ignoring touching sources. Eight executable competitors now
cover those plus one source per color, moving sources, horizontal-only
projection and vertical-only projection. Diagnostic Python predictions never
supply training labels; Racket-backed checks verify the disagreements.

## Distribution and lesson policy

Without explicit controls, the four-index profile cycle is
`rich_hline, broad, rich_vline, broad`. Every even-index rich draw independently
refutes all eight rivals: three aligned sources and one diagonal source on a
10x10 board include repeated color, a touching interior source, both projection
axes, and an unpainted endpoint that exposes the diagonal rival. Geometry,
source palette and reflections vary. Odd-index draws sample all feasible line
and rectangle shapes, dimensions, source counts and helpful textures, with
band-weighted preferences that do not change explicit-axis validity.

Four demonstrations are declared. A consecutive five-pair bundle contains at
least two rich draws; after holding out any one pair, at least one remains in
the demonstrations. The public runner was tested with its actual accepted
sample indices, both in production order and with every pair held out once
while preserving remaining order. This establishes only the declared finite
rival comparison on retained instances, not identifiability against every
possible program. Explicit non-None overrides choose ordinary draws and do not
inherit the default schedule's witness guarantee.

Self-review caught a new restriction in the first candidate: every ordinary
slot was a rectangle. A genuine four-band failing test and that exact source
were retained before restoring all feasible shapes. Rich draws still occupy
half of default indices and intentionally fix several statistics; broad draws
provide variation. More random examples alone would not prove complete lessons
contain a distinguishing example, so the fix also tests actual lesson windows.

## Retained verification and reusable tools

Final generator SHA-256:
`5fae92ec1c148a4208fe55eebc5150b33a81a9969ad8c92e4cff60f4dc5410c3`.

The return's `checks/after-final/` records all 12 battery stages green with
query rotations required. `checks/task-tests-final-ready/` records 516 portable
task tests passing (217 override/domain tests and 299 semantic/schedule tests).
`checks/override-probe-final-v2.json` records all 1,528 calls passing: 191 cases,
seeds 0..7 paired with sample indices 7..14, 496 unique generated inputs.
This probe tests pixels and API behavior, independently of Racket labels.

`checks/lesson-census-final.json` records 300 lessons, 100 per band, with four
demonstrations and one query each: 1,500 unique inputs and 1,500 held-out query
rotations, no ambiguity, hook warnings, scoring errors or materialization
errors. Indices are 0..99 per band; seeds follow the report's deterministic
SHA-256 recipe. `checks/schedule-census-final.json` covers starts 0..3 at seed 0
in all three bands: 12 overlapping lessons, 60 rotations, 14 unique inputs.
Both production and rotation verdicts are `no_ambiguity_found`.

Use `workspace/probe_override_contract.py` for a source-bound, finite API census;
`tests/contract_support.py` independently reads geometry from pixels and uses
the portable root locator. See `workspace/README.md` for commands. Small actual
Racket-labelled witnesses are retained in `counterexamples/`. Before,
intermediate, genuine failing and final evidence remain in the review return;
compressed successful intermediate reports include hashes and restoration
instructions. The final handoff also records fresh extraction/patch replay.

There was no task evidence index or substantive prior local note to follow;
`evidence/associated_notes.jsonl` was empty. These notes record this review's
decisions, not an invented prior review history. The post-repair Python solve
matched 4/4 visible examples in one attempt, explicitly declared earlier rule
exposure, and did not consult reference source during the solve. Hidden-query
correctness remains unknown. No training-admission claim is made.
## Current reviewer considerations

Source SHA-256: `5b86079e3f368a9daff406db90831819f0494ec61b0b3598b446154ca7f13203`.

# Decisions for review-59a3f43f8a82341e

## D1 — repair only the measured scalar call contract

**Prior choice:** the approved v3 generator validated advertised overrides and difficulty but passed direct `seed` and `sample_index` arguments to `gen_ctx` without local type/range checks.

**New choice:** reject non-`int` seeds, non-`int` sample indices, and negative sample indices before any generation work. Python booleans reject because the check uses `type(value) is int`, not `isinstance(value, int)`.

**Reason and evidence:** the completed baseline had one failing stage and exactly 30 strict-scalar warnings. Test-first coverage reproduced all 30 failures across easy/default/hard. No other baseline stage indicated a production repair.

**Alternatives rejected:** coercing strings/floats would make call identity ambiguous; allowing negative indices would contradict the shared call contract; changing shared `gen_ctx` would exceed selected-task scope.

**Failure modes/limits:** this validates the public call scalars only. It does not claim every malformed Python object passed through private helpers is covered.

## D2 — preserve `VERSION = 3.0.0` and valid deterministic outputs

`VERSION` participates in the generator’s random namespace. A semantic-version bump for a validation-only patch would remap every valid seed/index and obscure whether the repair changed the curriculum. I therefore preserved the version string and pinned representative pre-change output bytes in a regression test. Source SHA and packet receipts identify the repair unambiguously.

Alternative considered: introduce a separate RNG version constant and bump the display version. Rejected as unnecessary surface area for a three-check fix.

## D3 — preserve canonical Racket authority exactly

The selected rule `7288da9bfc7e` already matches all canonical labels and passed rule smoke/authority sync. No rule text, canonical ledger row, approval hash, or base authority was edited. Diagnostic Python rivals remain assertions only; Racket supplies retained labels.

Projection-target collisions remain outside the sampler’s declared domain. Expanding that domain would require an explicit priority lesson and is not justified by this assignment.

## D4 — choose `edge_mode = near | far` as the bounded prototype parameter

`near` is the original behavior. `far` changes only the target edge: a source aligned with the cyan bounding box paints the opposite edge rather than the closest edge. Object roles, bbox reasoning, alignment tests, source preservation, colors, and diagonal-ignore behavior remain invariant.

This is a meaningful executed transformation rather than a cosmetic reskin. It creates a nearby rule family whose hidden setting can be inferred from demonstrations.

Alternatives considered:

- **Output/source color parameter:** rejected as mostly cosmetic and weaker reasoning variation.
- **Move versus copy sources:** rejected because it changes source persistence as well as target placement and is already a declared shortcut rival.
- **Horizontal-only/vertical-only projection:** rejected because it deletes half the canonical reasoning rather than parameterizing a symmetric choice.
- **Collision priority:** rejected because collisions are outside the current domain and would require new input constraints plus conflict lessons.

The episode mode is selected deterministically once from seed parity. Four rich even-index demonstrations ensure both horizontal and vertical examples and each refutes the alternative; the query also differs. Exact Racket sources are retained, with `near` byte-identical to canonical. This remains **prototype** evidence and does not update production approval.

## D5 — satisfy schedule evidence rather than modify a sound schedule

The first strict after run failed only because the declared four-index period was not enumerated. The measurements themselves were green. I retained that failed run, then reran the same source with `--enumerate-schedule-period --require-rotations-identifiable`. The final battery is all green, and a separate 300-lesson census checks 1,500 query rotations.

Alternative rejected: remove or hide `LESSON_SCHEDULE_PERIOD` to avoid the warning. That would weaken provenance instead of satisfying it.

## D6 — strongest canonical shortcut is `border_only`

Four plausible shortcuts fit all four canonical labelled pairs. I selected `border_only` as the strongest qualitative rival because it is a minimal modification of the intended program: ignore interior sources while retaining all other logic. A 5×5 emitted input provides a one-cell disagreement and was re-executed through canonical Racket against the final generator SHA.

“Strongest” is not claimed as a proof over every hypothesis. `rectangle_only`, `project_diagonal_to_corner`, and `ignore_touching_sources` also fit all canonical pairs and remain declared competitors.

## D7 — prior evidence used only as a lead

I consulted prior return `review-30645eda24a688cb:v0001` for its retained test architecture and semantic-rival definitions. I reran the current pinned source instead of importing its approval as a measurement. The current source differs only by the direct scalar validator plus task-local prototype/tests/evidence.

## D8 — no repairs to adversarial audit targets

Audit targets are findings-only. I reproduced one false count contract in `508ae94c035c` and one ignored distinct-color control in `5a09c683cd25`, recorded exact hashes/calls/grids, and did not edit either source.

## Execution rulings

- The packet is an isolated non-Git workspace, so provenance is represented by source hashes, red/green receipts, the package delta, and fresh replay rather than commits.
- Keeping `VERSION` stable prioritizes byte-stable valid behavior. Cost if project policy requires every source edit to bump it: a maintainer may prefer a separate display/RNG version split later.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/064e439acd2d/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
