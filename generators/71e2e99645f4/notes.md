# Current notes: 71e2e99645f4

## Intended rule and domain

The selected task is deliberately narrow: a `4×14` input has three `4×4`
sections at columns `0..3`, `5..8`, and `10..13`, with all-zero divider columns
`4` and `9`. All nonzero cells use one fill color. Each section has one exact
hole signature and maps to one output row:

- no holes → color `2`;
- centered holes `{(1,1),(1,2),(2,1),(2,2)}` → `8`;
- bottom holes `{(2,1),(2,2),(3,1),(3,2)}` → `4`;
- middle edge holes `{(1,0),(1,3),(2,0),(2,3)}` → `3`.

The output is `3×3`, with row `i` repeating the class for section `i`. The
canonical selected rule is pinned by `RULE_HASH = d38a7d9b0fc4`.

## Reversed decisions and evidence

The imported `2.0.1` generator (`sha256
71dccf333603c5270f11b728f065076ed52f288d9c21f2214f73e055145f5ee9`)
used all four rows of the outer columns for `edge_hole`. Its rationale was not
recorded. That choice was reversed because every canonical edge example uses
only rows 1 and 2. The retained review `review-4bbe40f8398aea03:v0001` was used
as a lead; this review independently reproduced the issue. In a pinned
300-draw probe, the old source emitted 238 full-column edge sections and zero
canonical four-cell edge sections over 900 sections. The final source emitted
200 canonical edge sections and zero full-column variants. See
`workspace/probe_contract_repair.py` and
`counterexamples/review-e62196139d859155-v0001/contract_probe.json`.

The imported generator also advertised seven axes while honoring only
`fill_color`, silently accepted unknown keys, ignored `hole_patterns`, and let
named "degenerate" metadata bypass validation. Retained reviews
`review-389eb2e7868c9e1e:v0001` and `review-95c2d465e72fe468:v0001` were used as
leads. The final public domain has only two truthful exact controls:
`fill_color` and the diagnostic list axis `hole_patterns`. Unknown or malformed
controls fail closed, both axes are recoverable from pixels, and validation has
no metadata bypass.

The active base-solution `target_code` was behaviorally equivalent to canonical
but textually divergent. It was synchronized exactly to canonical so the runner
and ledger use one selected authority. The original `raw_code` remains
unchanged as archival provenance; no rule behavior or canonical examples were
changed. The base record now states
`selected_canonical_with_preserved_archival_raw`.

## Curriculum design

Ordinary draws always contain `no_hole` and two of the three hole-bearing
classes. `sample_index % 3` rotates which hole class is omitted. The ordering
policy is a deterministic complete 18-case cycle: each omitted-class profile
visits all six permutations exactly once in 18 consecutive samples, while
even/odd samples alternate between orders that refute and fit the strongest
canonical shortcut, a position-conditioned lookup table. Seed and difficulty
shift only the within-partition slot, so they change order without weakening the
lesson guarantee. The ordinary finite output alphabet remains 18 ordered class
grids. Exact overrides can exercise the authority's wider `4^3` section-pattern
space, including repeated classes, but are not the production teaching schedule.

Three executable rivals define the current teaching obligation:

- `full_edge_columns` requires eight edge zeros and misses the canonical
  four-cell edge geometry;
- `four_zeros_means_center` ignores vertical position and labels bottom/edge
  patterns as center;
- `canonical_position_lookup` memorizes only pattern/output pairs observed at
  each of the three section positions in the canonical demonstrations. It fits
  all four demonstrations but predicts `[[2,2,2],[2,2,2],[2,2,2]]` for the
  canonical query instead of `[[4,4,4],[3,3,3],[8,8,8]]`.

The repaired cycle has exactly two position-lookup refutations in every
four-pair window, so every possible three-demo/query rotation retains at least
one. `workspace/probe_position_shortcut.py` derives the shortcut from canonical
data rather than hard-coding a conclusion. On seeds 0..3, 120 starts per band,
it found 720/1440 ordinary draws that refute the rival and 0/5760 surviving
three-demo rotations across 1440 windows. Evidence is
`checks/position-shortcut-v1.json`.

A separate proposed parametric prototype lives in `workspace/parametric/`. It
selects one episode-level `section_order` (`left_to_right` or `right_to_left`)
and one `palette` (`canonical` or `swap_center_bottom`) for all three
demonstrations and the query. The canonical/default Racket source is byte-for-
byte unchanged; the four settings have distinct source hashes and distinct
outputs on a shared lawful witness. Four real-Racket episodes cover all settings,
replay all five canonical pairs under the default, and leave zero parameter
rivals ambiguous. This is `proposed_unapproved`, not part of the canonical
generator repair; evidence is `checks/parametric/order-palette-v1/report.json`.

## Assumptions and known limits

- `self_check` intentionally accepts only the four exact canonical signatures,
  although the selected Racket program returns fallback labels for some other
  zero arrangements. This prevents broader, under-specified morphologies from
  entering training.
- The fixed dimensions, dividers, and one-color role are canonical invariants,
  not hidden controls.
- Passing three declared rivals is finite evidence, not proof against every
  possible hypothesis. Undeclared ambiguity remains unknown.
- The production lesson policy is three demonstrations plus one query; arbitrary
  rotation support was tested, but downstream assemblers still need to preserve
  the declared demonstration count.
- Final verification on source SHA `c45176c00d39b36d2991ad29b89da95fa5d1d4318fe07161ab2a3bc897629889`: 12/12 after-battery stages green; 24/24 task-local tests passed; the required-rotation semantic gate passed; and the 300-lesson census found 0/300 ambiguous production lessons and 0/1200 ambiguous query rotations.
- No open task-local blocker remains in this review.
## Current reviewer considerations

Source SHA-256: `c45176c00d39b36d2991ad29b89da95fa5d1d4318fe07161ab2a3bc897629889`.

# Decisions — 71e2e99645f4

Final canonical generator SHA-256: `c45176c00d39b36d2991ad29b89da95fa5d1d4318fe07161ab2a3bc897629889`.
Selected canonical rule hash: `d38a7d9b0fc4` (unchanged by this review).

The sections below record each retained or reversed choice, the prior rationale where known, rejected alternatives, executable evidence, failure modes, and limitations. Decisions D1–D10 preserve and clarify the already-imported repair; D6–D7 are revised in this return; D11–D12 add the new reusable probe and isolated parametric prototype.


## D1 — Keep the canonical fixed 4×14 composition

**Choice.** Preserve three 4×4 sections at columns `0..3`, `5..8`, and `10..13`,
with all-zero divider columns `4` and `9`.

**Prior rationale.** The imported generator fixed these dimensions but did not
record why. The canonical pairs and selected rule make them structural, not optional
sampling axes.

**Alternatives considered.** Variable section sizes, grid dimensions, section
counts, and divider locations were rejected because they would create a different
composition rule and dilute exact canonical support.

**Probe and failure mode.** All five canonical pairs pass the final checker and rule
mirror. Any non-4×14 grid, nonzero divider, or ragged row is rejected. The limitation
is intentional: this generator is not a family of resized analogues.

## D2 — Use one nonzero fill color and expose only that real scalar control

**Choice.** Every nonzero section cell shares one strict `fill_color` in `1..9`.

**Prior rationale.** The baseline already used one color, but also advertised
`palette_kind`, `palette_size`, and `texture` aliases that did not represent real
variation.

**Alternatives considered.** Multi-color sections and fixed color 1 were rejected.
Multi-color inputs add an unsupported classification variable; one fixed color would
unnecessarily reduce diversity.

**Probe and failure mode.** `observe_overrides` recovers the exact color, mixed-color
mutations fail `self_check`, and the override gate is green. This preserves color
invariance without claiming a palette axis that does not exist.

## D3 — Replace the old edge geometry with the exact canonical signature

**Choice.** `edge_hole` is exactly `{(1,0),(1,3),(2,0),(2,3)}` in local section
coordinates.

**Prior rationale.** Unknown. The imported implementation removed both outer columns,
which conflicts with every canonical class-3 example.

**Alternatives considered.** Keeping both four-cell and eight-cell variants under the
same label was rejected because it teaches a broader, unsupported equivalence.
Renaming the old shape while retaining it was also rejected: no selected-rule or
canonical evidence assigns that morphology a stable class.

**Probe and failure mode.** The 300-draw contract probe changed support from
`0` canonical / `238` old full-column sections to `200` canonical / `0` old sections.
A future regression is caught by focused tests and the reusable probe.

## D4 — Make `hole_patterns` an exact structured control

**Choice.** Accept only a literal list of exactly three canonical names, preserve its
order exactly, and return the realized list through `observe_overrides`.

**Prior rationale.** The baseline declared this axis but ignored it.

**Alternatives considered.** Removing it entirely would make targeted reproduction
and geometry tests harder. Treating it as an ordinary scalar enum would misdescribe
its three-position structure. It is therefore retained as a diagnostic list axis.

**Probe and failure mode.** Wrong type, length, item type, or name fails closed; an
exact requested list round-trips in every difficulty. Repeated patterns are lawful
under explicit override even though the ordinary curriculum uses three distinct
patterns.

## D5 — Delete dead aliases and metadata bypasses

**Choice.** Remove `section_height`, `palette_kind`, `palette_size`, `n_sections`,
`texture`, and all named degenerate textures from the public domain. Unknown keys are
errors, and `meta` cannot suppress validation.

**Prior rationale.** None was recorded; these declarations did not correspond to
implemented controls.

**Alternatives considered.** Implementing each dead axis would invent noncanonical
families. Keeping aliases for compatibility would continue to let typoed requests
produce plausible but unintended data.

**Probe and failure mode.** The contract probe shows a baseline typo was accepted and
the final source raises `ValueError`; the former `[[1]]` metadata impostor is now
rejected.

## D6 — Replace keyed random ordering with a complete 18-case lesson-safe cycle

**Prior choice.** The imported `3.0.0` generator rotated the omitted class but
used a keyed shuffle plus difficulty rotation for section order. It preserved
18-output support but did not guarantee exposure of pattern/position pairs.

**New choice.** Keep the three-step omitted-class schedule, partition each
profile's six permutations into three that expose a canonical position gap and
three that do not, and alternate those partitions. Across 18 consecutive samples
each ordered triple occurs exactly once. Every four-pair window has two
refutations, so every three-demo/query rotation has at least one. Seed and band
only shift the slot inside a partition.

**Alternatives considered.** Fully random permutation was rejected because a
valid run can preserve the position lookup across a whole lesson. Always choosing
a refuting order was rejected because it would halve support and make ordering
more predictable. Adding a fourth demonstration was unnecessary once the cyclic
coverage guarantee could be obtained without changing `EXAMPLES_NEEDED = 3`.

**Probe and failure mode.** `test_position_rival_and_schedule.py` checks four
seeds, three bands, all 18 signatures, 24 cyclic starts, and every 3-of-4
rotation. The larger source-bound probe checked 1440 windows / 5760 rotations
with zero survivors. This is still finite evidence for declared rivals; a new
undeclared shortcut can require another schedule repair.

## D7 — Add the canonical position-conditioned lookup as the strongest rival

**Prior choice.** The semantic contract declared only `full_edge_columns` and
`four_zeros_means_center`. Both were useful but weaker than a learner that
memorizes canonical section position.

**New choice.** Register `canonical_position_lookup` in `SEMANTIC_RIVALS` and
`LESSON_COMPETITORS`, and bind it to a `position_generalization` witness. The
lookup table is derived from the four canonical demonstrations: each position
uses the labels it observed and defaults an unseen pattern to class 2.

**Alternatives considered.** A generic permutation-invariance assertion was too
coarse: it would not preserve the exact rival prediction or reveal the three
missing pattern/position pairs. Position randomization without declaring the
rival would improve data but leave the semantic reason untestable.

**Probe and failure mode.** The rival fits all four canonical demonstrations and
disagrees on the canonical query, whose patterns are
`[bottom_hole, edge_hole, center_hole]`. The selected rule/Racket gives rows
`[4,3,8]`; the rival gives `[2,2,2]`. The reusable probe imports the generator's
actual declarations, records the exact input and outputs, and verifies repaired
lesson windows. Passing this rival does not prove universal identifiability.

## D8 — Make validation exact rather than permissive

**Choice.** `self_check` requires literal ARC integers, exact shape/dividers, one
shared nonzero color, and one of four exact section signatures. `strict_canonical_like`
uses the same grammar.

**Prior rationale.** The baseline only checked coarse dimensions/dividers/nonzero
presence and could return success immediately for named metadata.

**Alternatives considered.** Validating only generator outputs would miss mutation
and ingestion errors. Accepting arbitrary four-zero shapes would reintroduce the
position shortcut the curriculum is meant to disambiguate.

**Probe and failure mode.** Minimal, ragged, boolean, out-of-range, mixed-color,
nonzero-divider, and old-edge inputs are regression cases. The checker intentionally
rejects some inputs for which the selected Racket program has a fallback label; that
is a training-domain decision, not a rule rewrite.

## D9 — Synchronize only the active selected authority text

**Choice.** Replace the base record's active `racket_target.target_code` with the exact
canonical selected program; preserve `raw_code` unchanged.

**Prior rationale.** The two texts were behaviorally equivalent, but the reason for
the active divergence was not recorded.

**Alternatives considered.** Editing canonical authority was rejected because its
behavior was correct. Deleting archival raw text was rejected because it would erase
provenance. Ignoring the divergence would keep two active spellings and a permanent
source-binding warning.

**Probe and failure mode.** Final `authority_sync`, `rule_smoke`, and `racket_lint`
pass. The before snapshot allows exact review of the one-field synchronization.

## D10 — Preserve a reusable, source-hash-bound probe

**Choice.** Keep `workspace/probe_contract_repair.py` and its compact counterexample
JSON.

**Prior rationale.** Earlier reports described morphology and contract failures, but
a future agent otherwise had to reconstruct the measurements.

**Alternatives considered.** Storing only logs was rejected because logs do not give a
small rerunnable experiment. Moving the task-specific geometry into shared tooling
was rejected; the shared improvement belongs at the signature-gate level proposed in
`FEEDBACK_TO_CODEX.md`.

**Probe and failure mode.** The script compares baseline and final source hashes,
counts both edge signatures, tests typo handling and the impostor checker, verifies an
exact override, and checks four query rotations. It is bounded to its deterministic
300-draw sampler.

## D11 — Keep the shortcut detector as a reusable source-bound probe

**Choice.** Add `workspace/probe_position_shortcut.py` and a focused test for its
report contract. The probe derives the position table from canonical
demonstrations, checks the held-out canonical query, samples ordinary draws, and
checks all three-demo rotations of four-pair windows.

**Alternatives considered.** A prose-only finding was rejected because future
agents would have to reconstruct the rival and coverage arithmetic. Folding the
task-specific table directly into a shared checker was deferred; the shared
checker should first learn to derive such tables generically.

**Limits.** The retained run covers seeds 0..3 and starts 0..119 in each band.
The schedule proof is also encoded in focused tests, but neither is a proof
against arbitrary undeclared rules.

## D12 — Prototype two small episode-level rule parameters, but do not approve them

**Choice.** Build a separate `proposed_unapproved` prototype with two binary
parameters: output section order and a swap of the center/bottom output palette.
Select one setting per episode and hold it fixed across three demonstrations and
one query. Preserve the exact canonical source at the default setting.

**Alternatives considered.** Changing hole geometry, section count, or grid size
was rejected because it alters the original reasoning pattern. Per-example rule
changes were rejected because they are not inferable episode parameters. A
larger palette permutation family was unnecessary for the requested one/two
small parameters and would add avoidable identifiability burden.

**Probe and failure mode.** Five focused tests execute real Racket, verify exact
default-source identity, canonical replay, four distinct setting outputs, public
answer masking, and complete parameter-rival refutation. The extension is not
training/source/variant approved and is intentionally isolated from
`generator.py`; maintainers must decide whether these transformations are an
appropriate family expansion.
