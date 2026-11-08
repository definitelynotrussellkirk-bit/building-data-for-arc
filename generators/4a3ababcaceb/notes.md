# Working notes: 4a3ababcaceb

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`; those historical files are unchanged.

Review assignment `review-47a0a3d8066b6da9`, final source SHA-256 `b29280e7128efaaf0ebc04e84a4b0f2235075eca5ed17855d582981002b42b7f`.
The canonical Racket program and ledger were not edited.

The principal change is semantic contrast rather than gratuitous visual variety:
select by red count, ignore non-red source cells, and replace the entire marked
target. Early dense-everywhere sampling inflated object counts and was rejected.
A later five-rival-green version still admitted purity/sparsity shortcuts, leading
to the complementary sparse weaker-red profile and eight explicit rivals.

Default profiles are scheduled, not independently random. Keep seed and
consecutive sample indices together when constructing the three-demonstration
lessons that this generator tests. `lesson_identifiable` is query-conditional;
`workspace/contrast_probe.py --require-refutation` is the stronger demonstrated-
contrast gate. Both are finite-rival checks, not a proof of unique induction.

Meaningful knobs only: tile rows/columns, red source count, target marker offset.
Use `observe_overrides` to verify exact postconditions. Illegal negative fixtures
live in `mutation_fixtures`, not the public AXES domain. Structural validation
permits ignored nuisance colors including cyan; global palette introduction is
not the same thing as performing the target transformation.

Tests: 28 task-local cases pass, final 12-stage battery and standalone lint pass,
final reference-backed census has 963 executions and no reference/validator
mismatches. These counts refer to the pinned source and recorded review; they are
not assertions about future edits. The whole-repository suite retains one local
startup-timing test failure with 169 other tests passing.

Limits: only eight specified rivals are tested. Profile-conditioned composites,
fixed one-cell source noise, independent-lesson sampling, and actual model
learning need further falsification. No Qwen training or masked-query scoring
was performed by the reviewer. See returned REVIEW/DECISIONS/RESULTS for exact
seeds, denominators, failures, provenance and source-version solve history.
## Current reviewer considerations

Source SHA-256: `b29280e7128efaaf0ebc04e84a4b0f2235075eca5ed17855d582981002b42b7f`.

# Distribution and implementation decisions

Task `4a3ababcaceb`, final generator `b29280e7128efaaf0ebc04e84a4b0f2235075eca5ed17855d582981002b42b7f`. IDs refer to `REVIEW.md`.

| Choice | Original rationale / evidence | Alternatives considered | Decision, probe, limitation |
|---|---|---|---|
| Tile geometry (R2) | Existing implementation chose 2–3 rows and 3–4 columns; why it excluded one row is unknown. Canonical inputs are 3×11. | Keep only larger grids; copy only original dimensions. | Anchor one profile at one row/three columns, retain broader layouts. Final ordinary layout coverage 192/480 at 3×11; broad profiles and legal 1..5 / 3..6 overrides remain. |
| Fixed tile size and role colors | Imported authority divides a lattice and uses literal 2, 3, 8, 9. | Arbitrary palette permutations or tile size extension. | Preserve 3×3 and role colors; no unsupported color equivariance. Source count/domain, not unrelated geometry invention, is the target skill. |
| Red-source count (R1/R2) | Original hardcoded 4..6 regardless of `src_size`. | A singleton source, tiny uniform mask, or uniform 1..9. | Sample 2..9, including full nine as a boundary anchor; lower sizes allow near-count competitors. Validator also accepts lawful source-size-one inputs without advertising that as a training knob. Endpoint matrix verifies exact overrides. |
| Three-example schedule (R2/R5) | No explicit counterexample schedule in original. | Independent randomness only; force every contrast into every grid. | `(seed+sample_index)%3` gives canonical anchor, dense earlier competitor, sparse/pure later competitor in any consecutive default window. No statistical guarantee for unrelated seed/index sampling. Tests use 144 overlapping small-seed windows; reference census uses 120 separately seeded lesson evaluations. |
| Dense weaker candidate (R2) | Only the original source had substantial nonzero mass. | Fill every decoy densely; use only blue distractors. | Designated weaker red tile has source count minus one and remaining cells non-red; before source on profile 1. This rejects occupancy and first-red heuristics. Other tiles are sparse; dense-everywhere trial failed object-count gate and was discarded. |
| Sparse/pure weaker candidate (R5) | Initial repair accidentally left purity and sparsity correlated with the right answer. | Add more of the same dense clutter; accept five-rival success. | Profile 2 puts a weaker pure-red tile after the noisy source. Actual eight-rival reference census rejects these alternatives. Composite conditional heuristics are not ruled out. |
| Source clutter (R2/R5) | Original source had only red. | Copy every nonzero cell; heavy multicolor source. | One non-red source cell on contrast profiles distinguishes a red mask from any nonzero mask. At explicit source-size-nine override no extra cell fits; lesson guarantee is therefore not promised under arbitrary overrides. Fixed nuisance count is a remaining diversity limitation. |
| Marked target and erasure | Canonical labels erase target cells, not merely add cyan. | Center marker only; one marker with empty surroundings; redraw all clutter randomly. | Profile 1 uses an off-center marker; contrast targets have uniform non-red clutter. Replace target with cyan/zero. Less unnecessary object noise than unrelated random cells. `marker_offset` is independently observable 0..8. |
| Nuisance palette (R4) | Legacy palette axes were inert; original nuisance colors varied without a real control. | Exact palette-size promise; no cyan anywhere; randomize all role colors. | Anchor/dense profile uses blue nuisance; broad profile uses 1/4/5/6/7/8. No fake palette axis. Cyan as nuisance is lawful and can confuse a naive new-color detector without breaking the label. Do not generalize role colors. |
| Axis cleanup (R1) | Many advertised categories were unprobed, constant, or ignored. | Keep inert aliases for compatibility; implement an expansive new override API. | Remove dead axes; raise for unknown controls; advertise only four exact integer axes with full bounds at every difficulty. This intentionally changes interface behavior: migrate callers from legacy names. Version 3.1.0 documents the major break. |
| Validator (R3) | Original checked aggregate colors, not equal tiles/complete dividers/unique source. | Check only samples; silently repair invalid input; reject every noncanonical palette. | Nonmutating structure-first check rejects ragged dimensions, invalid colors, interior9/broken dividers, missing/duplicate target, tied source and red target. It does not assume irrelevant nuisance colors are semantically invalid. |
| Authority | No evidence that canonical output logic was wrong. | Change Racket to match easier generator sampling. | Leave authority and canonical labels unchanged; mirror is test-only and repeatedly compared to actual Racket. |
| Gate (R6) | A wrong rule can fit all demos and sampled query, escaping a query-ambiguity-only hook. | More marginal diversity thresholds; a Qwen training run for every edit. | `--require-refutation` fails unless each measured three-demo lesson contradicts each task-declared rival, with nonempty/complete evidence. Original fails, final passes. Genuine within-domain equivalence requires a declared exemption, not forced OOD negatives. |
| Audits (A1/A2) | Duties assign findings-only reviews of two distinct tasks. | Patch unrelated generators and shared tests opportunistically. | Do not expand patch scope. Save concrete inputs/reference outputs and identify real defects separately from OOD or documentation concerns. |
| Solve evidence | An exposed reviewer is not a blind solver. | Claim hidden correctness; delete the earlier source-version episode; manufacture a failure. | Preserve both episodes, record exposure and intent, keep private answers closed. Final visible score is 3/3 only. |

## Rejected iterations and evidence integrity

The first dense draft's hash is `a947317742a7963f8f405b2febdd41630a3b2bcc88f3dc008563abb511eb5587`.
The reduced-density five-rival version-3.0 hash is `aeb1278baab900e120cf979306e170ca8ea00c82f2e9410065e36e65369b6806`.
Generator snapshots and failures are retained, rather than normalizing all old reports to the final version. An older record that says `contrast-after.json` now has an explicit relocation note to `contrast-3.0.json`.

No Git metadata was supplied, so there is no fabricated commit or branch. The packet's immutable baseline and return builder provide the delta. No shared test was edited to hide E1, and no output authority was modified to make a test pass.
