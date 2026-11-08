# Working notes: 5a01897eb8be

## Current rule and generator

Version `3.0.0`; generator SHA-256 `b1b317f6740a9ee086cc71f0f33acc5b026357ad0aad565597b1ae2db5c70be9`; pinned normalized rule hash `00935b1c1bf9`.

For every non-background color, the rule measures (1) the maximum dimension of its bounding box and (2) its longest monochrome arm from a bounding-box corner. Colors are allocated to available odd ring sizes by the authority’s fit order; the output draws four corner Ls on each assigned ring using the measured arm. The top-left input cell defines the background.

## Reversed prior choices

The retained audit `review-51acd07e08f44fc3:v0002` was the repair lead. Version 2.1.0 fixed background to zero, used exact odd sizes with full-arm Ls, and shelf-packed largest-first. That made first-appearance order equal ring order and made each output ring a solid border. A scan-order/solid-border rival matched 12/12 audited default labels while ignoring both intended measurements; all four canonical inputs were rejected only because their backgrounds were nonzero.

Version 3.0.0 reverses those choices:

- arbitrary ARC background, read from the top-left;
- 3–6 colors with center and no-center branches;
- exact and one-loose-glyph allocation branches;
- connected, two-corner and four-corner glyphs with partial arms;
- randomized placement with a required disagreement between first appearance and ring order;
- six exact observable controls only: `grid_h`, `grid_w`, `shape_count`, `has_center`, `background`, `loose_shape`;
- strict rejection of unknown, mistyped and out-of-range controls;
- three demonstrations plus one query, with executable `scan_order` and `solid_rings` competitors.

The six deterministic profiles include the four canonical `(height, width, palette-size)` anchors and two broader profiles. Every difficulty band gets the same branch support; band-keyed geometry prevents byte-identical examples without redefining the rule.

## Evidence

- Before battery on source `9ef313...`: 5 green, 1 advisory, 6 failed.
- Final battery: 12/12 green; rule smoke and execution parity pass.
- Portable focused tests: 55/55 pass. The initial test-first run retained 50 expected failures against the old source; a second red run retained two targeted geometry failures.
- Override matrix: 53,730/53,730 accepted legal draws across 597 cases, zero findings/warnings, unknown key rejected.
- Wide lesson census: 300 lessons (100/band), 1,200 unique pairs, 0 production ambiguity and 0/1,200 ambiguous rotations against declared rivals.
- Six-start probe: 18 fixed-seed lessons and 72 query rotations, zero ambiguity; 27/27 independent outputs match source-bound Racket.
- Default distribution probe: 120 draws, all six profiles represented 20 times; both old shortcuts refuted 120/120.
- Minimal retained witness: `counterexamples/review-692b19ae6464c0cd/shortcut_witness.json`.
- Reusable independent oracle/probes: `workspace/reference_probe.py`.

## Authority decision

The canonical rule was not changed. The active `racket_target.target_code` in the selected augmented base record was synchronized to canonical text so selected authorities agree. Its different `raw_code` remains intact and explicitly archival. Final authority-sync status is `selected_synchronized_archival_divergent`, with execution parity PASS.

## Known limits and open questions

The generator intentionally covers 13–24 rows, 17–24 columns, 3–6 colors and the six listed axes; it does not claim every validator-lawful reference grid. Only declared rivals and a small generic battery were tested, so semantic uniqueness is not proved. The loose branch generates one even-size claimant rather than all combinations of loose fits. “Difficulty” changes geometry/distribution but is not calibrated model difficulty. Training approval remains false pending maintainer intake.
## Current reviewer considerations

Source SHA-256: `b1b317f6740a9ee086cc71f0f33acc5b026357ad0aad565597b1ae2db5c70be9`.

# Decisions — 5a01897eb8be

## D1 — Preserve the pinned rule; replace the evidence distribution

**Choice.** Keep `RULE_HASH = 00935b1c1bf9` and repair the sampler/validator/lesson contract rather than alter the transformation.

**Rationale.** The prior audit `review-51acd07e08f44fc3:v0002` showed a distribution shortcut, not a wrong canonical label: version 2.1.0’s row-major appearance and full borders let a rival bypass the rule’s measurements. Racket already matched canonical outputs.

**Alternatives considered.** Rewrite the Racket rule; add ad hoc output perturbations; keep the sampler and merely declare the shortcut. All were rejected because they would either change correct semantics or leave low-value training examples.

**Probe/evidence.** `checks/final-counterexample/counterexample.json`, before/after batteries, and `workspace/reference_probe.py`.

**Failure modes/limits.** Only named rivals and measured source properties were tested; an undeclared shortcut may remain.

## D2 — Axis choices

| Axis | Final choice and rationale | Rejected alternative | Probe | Limits |
|---|---|---|---|---|
| `grid_h` | Exact integer 13–24; scheduled anchors 13, 17, 18, 19, 20. Covers canonical heights and room for separated glyphs. | Legacy stale ranges and silently clamped sizes. | Boundary override matrix; exact task tests. | Does not claim smaller/larger lawful reference inputs. |
| `grid_w` | Exact integer 17–24; scheduled anchors 17, 18, 19, 21, 22. Covers canonical widths and broad layouts. | Legacy widths that were metadata-only. | Boundary override matrix; `observe_overrides`. | Same bounded-domain caveat. |
| `shape_count` | Exact 3–6 non-background colors. This spans canonical palette sizes while keeping every glyph assignable to a unique ring. | Legacy 2–6 declaration and unconstrained counts. | Joint overrides and assignment test over 64 draws. | Two-shape lawful cases are intentionally outside this curriculum. |
| `has_center` | Exact Boolean. Both center and no-center branches are scheduled. | Always forcing a singleton/center. | Branch witnesses, all-profile test, census. | Boolean branch does not encode all possible reference edge cases. |
| `background` | Exact ARC color 0–9, read from the top-left. Canonical examples use 8, 4, 3 and 1, so zero-only validation was incorrect. | Fixed zero background. | Four canonical pairs, full color override domain, scheduled six-color sample. | A top-left foreground grid is outside the stated domain. |
| `loose_shape` | Exact Boolean. A single even-size glyph can claim the first fitting odd ring before exact fits, exercising the authority’s allocation order. | Exact odd sizes only. | Loose-fit witness, joint override matrix, cyclic lessons. | One loose glyph is enough to teach the branch; multiple simultaneous loose fits are not generated. |

Unknown axes, Boolean-as-integer values, wrong types and out-of-range values now fail explicitly. This was chosen over compatibility aliases because the old axis surface contained controls that were not observable or honored.

## D3 — Six-slot profile schedule

**Choice.** Use four canonical dimension/palette-size anchors plus two broad profiles, repeating every six sample indices in every band.

**Rationale.** The profile floor requires canonical support, while exclusively replaying canonical dimensions would collapse variety. A deterministic period makes coverage reviewable and inexpensive to enumerate.

**Alternatives considered.** Pure random dimensions (risk of missing anchors); canonical-only profiles (distribution overfit); band-specific semantic branches (some branches absent from some bands).

**Probe/evidence.** `checks/lesson-census/lesson-census.summary.json` and `checks/schedule-cycle/result.json`; all six start residues, three bands and four query positions were checked.

**Failure modes/limits.** The formal generator does not declare `LESSON_SCHEDULE_PERIOD`; the direct retained probe records the six-slot behavior. Fixed-seed cyclic coverage does not prove all seeds.

## D4 — Corner-glyph construction rather than full Ls

**Choice.** Generate singleton, connected, two-corner and four-corner glyphs. Their full bounding box supplies the size measurement, while arm lengths may be partial.

**Rationale.** Full Ls made every output ring a solid border and reduced the task to color ordering. The mixed glyph family preserves the intended measurements and brings connected-component scale close to canonical inputs.

**Alternatives considered.** Arbitrary polyominoes (harder to guarantee a unique corner-arm statistic); all disconnected endpoints (object complexity too low); full Ls only (the reproduced shortcut).

**Probe/evidence.** Component-count/maximum-component tests, `checks/generator-probe.json`, and the `solid_rings` rival.

**Failure modes/limits.** The glyph grammar is still narrower than all validator-accepted reference-lawful shapes.

## D5 — Randomized placement with a required order disagreement

**Choice.** Place glyphs without overlap and reject layouts where row-major first appearance equals outer-to-inner assignment order.

**Rationale.** This directly removes the prior largest-first shelf leak while preserving every shape’s normalized geometry and color.

**Alternatives considered.** Ascending shelf order (replaces one fixed cue with another); random shuffle without checking (some lessons still leak); post-hoc color remapping alone (can leave positional correlation).

**Probe/evidence.** `scan_order` rival, 120/120 default-draw refutations, and the source-bound seed-9100 counterexample.

**Failure modes/limits.** The negative condition guarantees disagreement with one simple scan-order rule, not all positional heuristics.

## D6 — Difficulty changes geometry, not semantic support

**Choice.** Keep the same six profiles and exact axis support in all bands, but key glyph geometry and placement streams by band.

**Rationale.** Earlier versions could emit byte-identical grids across difficulty labels. Distinct geometry makes the labels meaningful operationally without withholding a rule branch from a band.

**Alternatives considered.** Narrow easy counts/sizes and broad hard counts/sizes; this was rejected because downstream sampling could miss a semantic branch in easy data.

**Probe/evidence.** `test_difficulty_bands_materially_change_geometry` and the 100-per-band census.

**Failure modes/limits.** “Difficulty” is distributional variation, not a calibrated human/model hardness score.

## D7 — Three demonstrations, one query, explicit rivals

**Choice.** `EXAMPLES_NEEDED = 3`; complete lessons contain three demonstrations and one query. The executable competitors are `scan_order` and `solid_rings`, with witnesses for order, partial arms, center/no-center and loose fit.

**Rationale.** Two guesses are not a teaching guarantee. Three demos allow the scheduled profiles to distinguish both measurement clauses while keeping examples compact.

**Alternatives considered.** Single-pair examples; metadata-only witnesses; a larger generic hypothesis search with no task-specific competitors.

**Probe/evidence.** 300-lesson census, 1,200 query rotations, and six-start cyclic probe.

**Failure modes/limits.** Passing declared competitors is not universal program identification.

## D8 — Synchronize only the active selected authority copy

**Choice.** Replace `racket_target.target_code` in `shared/data/base/solutions/augmented/4290ef0e__a45d77a65589.json` with the selected canonical rule text; retain `raw_code` unchanged as archival source.

**Rationale.** Before repair, execution parity passed but authority synchronization reported a selected-text divergence. The canonical rule and normalized rule hash did not need changing.

**Alternatives considered.** Modify canonical source; delete archival code; ignore the sync failure. All were rejected.

**Probe/evidence.** Final authority-sync status `selected_synchronized_archival_divergent`, execution parity PASS.

**Failure modes/limits.** This is text/role synchronization, not new semantic evidence.

## D9 — Independent oracle and TDD

**Choice.** Put the independent rule mirror and observations in `workspace/reference_probe.py`, and keep focused portable tests under `tests/`.

**Rationale.** Tests should not merely call the generator’s own helper to validate itself. The oracle independently computes components, measurements, assignment, and rivals.

**Alternatives considered.** Snapshot-only tests; importing private runtime aliases; checking only generated metadata.

**Probe/evidence.** Initial 50 intended failures established that the regressions detected the old implementation; final 55/55 portable tests pass, including real Racket parity.

**Failure modes/limits.** Python and Racket can still share a conceptual misunderstanding; canonical pairs and direct Racket applications reduce but do not eliminate that risk.

## D10 — Keep the parametric extension task-local and finite

**Choice.** Add a prototype-only two-parameter family under
`workspace/parametric/`: `ring_step` is `2` (canonical adjacent odd rings) or
`4` (one blank cell between successive rings), and `corners` is `all`
(canonical four corner Ls) or `diagonal` (top-left and bottom-right only). Keep
one fixed setting per episode, three demonstrations and four distinct queries.
The production generator, canonical ledger and selected base authority remain
unchanged.

**Rationale.** These are small output-construction changes that preserve the
original reasoning chain: infer the background, measure each colour's bounding
extent and corner arm, allocate colours by fit order, and render concentric
rings. A four-setting finite family is large enough to require both proposed
parameters to be learned from demonstrations but small enough to exhaustively
check every lawful alternative on every query.

**Canonical/default contract.** `(ring_step=2, corners=all)` materializes the
canonical Racket program byte-for-byte. All labels and rival predictions run
through the protected Racket bridge; the Python transform is an independent
cross-check only. Input draws are setting-independent, so all four settings see
the same examples for a given seed.

**Evidence.** The focused suite passes 31/31. Retained seed-17 evidence contains
four opaque public episodes, 3 demonstrations and 4 unique queries per episode,
16 total query labels, exact parity on all 8 canonical rows, 152 Racket
executions, and demonstration-only identification of every query setting.
Public directory IDs are SHA-256 hashes of exact visible challenge bytes;
settings, programs, seeds and answers remain private. See
`checks/parametric/all-settings/private/summary.json` and
`checks/parametric/green-export.log`.

**Limits/status.** Identifiability is exhaustive only over these four declared
settings and the reviewed production input distribution. The diagonal renderer
is intentionally one bounded alternative, not a claim to cover arbitrary corner
subsets. This is a proposed authoring prototype, not production approval,
training admission, or a change to the existing dataset identity.

## 2026-10-24 native parametric promotion review

The existing four-setting corner-ring prototype was promoted to the native
adapter contract without changing `generator.py` or the canonical Racket rule.
The exact default remains `(ring_step=2, corners=all)`; the alternatives are
`ring_step=4` and/or `corners=diagonal`. Supported episodes use 2–6
demonstrations and exactly four distinct queries with setting-neutral inputs.

A first adapter implementation called the prototype's full protected-Racket
teaching audit from inside every native qualification job. Single jobs passed,
but a multi-job qualification could wait beyond seven minutes. The repaired
adapter now emits deterministic Python claim labels only; native qualification
is the independent protected-Racket authority. A regression test forbids the
adapter from constructing `RacketBridge`.

The fourth query is now a parametric-only 30×30 stress profile. It translates six
lawful source glyphs to all four boundaries while preserving every color's
bounding box and corner arm; this is not blank padding. The production sampler
remains intentionally bounded to 13–24 rows and 17–24 columns.

Current reviewer evidence:

- focused tests: 12 native-adapter tests and 32 prototype tests pass;
- changed-task suite: 99/99 tests pass;
- native qualification: four settings × seeds 0/17, eight jobs, all with one
  demonstration-only survivor and protected-Racket label parity;
- causal witness: per-color `{color, max_dim, arm}` measurements feed allocation
  and rendering; replacing measured arms with `1` changes the protected-Racket
  output and replays successfully.

Source bindings: generator `b1b317f6740a9ee086cc71f0f33acc5b026357ad0aad565597b1ae2db5c70be9`,
prototype `232aa9567fe2a8c5682046c6f3a476153e24f7e91c4a45a7bbbe06a6dab3c62c`,
adapter `a3fcc286d7798512b18785a474d1f485f00439482ebbac7305652ceee5e51531`,
and inventory `f52bdb14ff903ff2092a6703dd6a655d6436d66fcc5989fdea332522b4727a3c`.

Decision: report MAIN as native `ready`, with owner exact-source integration,
qualification, acceptance replay, and any training-use decision still pending.
Optional peers were left unrun after completing and debugging MAIN.
