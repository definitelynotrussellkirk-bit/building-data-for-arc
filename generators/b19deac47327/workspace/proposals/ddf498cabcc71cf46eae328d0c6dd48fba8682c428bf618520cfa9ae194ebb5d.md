# Review — `b19deac47327`
- Task/version: `b19deac47327`, generator `2.0.0`; baseline source `e8eeb470…`, final source `66a3c56f…`.
- Defect → repair: reject bool/float/string seeds and sample indices, plus negative sample indices, before schedule arithmetic.
- Distribution defect → repair: change scheduled `tie_horizontal.grid_h` from 13 to 15, widening default height support from `{12,13}` to `{12,13,15}` without changing the rule.
- Final canonical checks: strict after battery **12/12 green** with required query rotations and explicit four-slot schedule enumeration.
- Focused tests: **50/50 passed** in the portable task-test runtime; standalone lint also passed.
- Lesson policy: **3 ordered demonstrations + 1 query**, four-slot periodic schedule; production **12/12 identifiable**, rotations **48/48 identifiable** in the strict gate.
- Larger census: **300/300 lessons**, **1,200/1,200 unique inputs**, **0 production ambiguities**, **0/1,200 rotation ambiguities** against declared rivals.
- Parametric status: runnable **prototype only** for episode-fixed `projection_span ∈ {1,2}`; 2/2 episodes and 8/8 query rotations identifiable, canonical span 1 remains selected.
- Racket authority: **unchanged**; canonical/default rule hash remains `2b2e46dd36cc`.
- Final generator SHA-256: `66a3c56f61986c75dc40053dce167a0b6f0c513892a78de98ba521379d7809ac`.
- Acceptance: **routine**; no remaining canonical-repair blocker. Prototype variants still require a separate approval decision.

## Scope and result

The selected generator was already semantically strong and lesson-identifiable. The before battery found one blocking stage, `defect_lint`, with two concrete classes: invalid scalar call arguments were silently accepted, and the default height schedule used too little of its declared range. The production patch is deliberately small: a strict `_validate_call_arguments` guard and one scheduled height adjustment. No canonical row, base Racket source, rule hash, semantic rival, or lesson-order contract changed.

The ordinary after command retained a useful intermediate failure: 11/12 stages were green, but the semantic gate rejected a declared periodic curriculum that had not been explicitly enumerated. Rerunning the same final source with `--require-rotations-identifiable --enumerate-schedule-period --schedule-seed 0` produced the final 12/12 pass. This was a verification-policy interaction, not a second source repair.

## Findings

| ID | Finding and action | Evidence | Status |
|---|---|---|---|
| R1 | `seed` and `sample_index` accepted booleans, floats, and strings; negative indices also reached modulo scheduling. Added strict integer/type and nonnegative validation before context construction. | `checks/before/`; red/green focused runs in `checks/task-tests-red-call-contract/` and `checks/task-tests-green-call-contract/`; final `checks/task-tests-final/` | Fixed; 33 new scalar-contract cases pass inside the 50-test suite. |
| R2 | Default scheduled heights occupied only 12–13 despite a wider declared axis. Changed only `tie_horizontal.grid_h` from 13 to 15 and added a regression requiring a nontrivial default span. | `checks/before/checks/b19deac47327_before_defect_lint.log`; `checks/defect-lint-after/`; `checks/after-enumerated/` | Fixed; defect lint and all downstream stages green. |
| R3 | A small original-family parameter is viable: project one or two cells toward the matching border, chosen once per episode. Built an isolated prototype with executable Racket rules, examples, an identifiability gate, and portable tests. | `repo/generators/b19deac47327/workspace/parametric/`; `checks/parametric/projection-span-evidence.json`; `checks/task-tests-green-parametric-2/` | Proposed only; not wired into canonical generation. |
| R4 | The default after command did not enumerate a declared schedule period and therefore failed strict semantic policy despite correct labels and zero observed rotation ambiguity. Retained the failure and completed an enumerated rerun. | `checks/after/`; `checks/after-enumerated/` | Verification resolved; no source change required. |
| R5 | Blind pre-work solve inferred the hole/no-hole recoloring task and passed 4/4 visible examples. The post-repair exposed solve inferred the selected border-projection rule and passed 3/3 visible examples on revision 1. | `solve-blind/summary.json`; `solve/summary.json` | Complete; exposure declarations preserved. |

## Canonical repair details

### Strict invocation contract

`_validate_call_arguments` uses `type(value) is int`, deliberately rejecting `bool` even though `bool` subclasses `int`. It also rejects negative `sample_index`. Validation occurs in `schedule_profile`, so both direct schedule calls and normal `generate` calls share the same contract. The implementation does not coerce strings or numeric scalars and does not alter valid deterministic inputs.

### Default height support

Only the `tie_horizontal` profile changed from height 13 to 15. Orientation, marker count, edge colors, side balance, unseen-edge witness, midline tie witness, schedule order, and four-slot period are unchanged. The final profile floor remains strong: exact canonical-profile hits were 9/20 easy, 11/20 medium, and 8/20 hard; all 60/60 samples were inside the canonical envelope.

### Teaching and distribution verification

The strict semantic gate accepted 600/600 generated grids and all seven declared witness families. It materialized 12 lessons and found 12/12 production-identifiable lessons with 0/48 ambiguous query rotations. The larger production sampler then materialized 100 lessons per band: 300 lessons, 1,200 pairs, 1,200 unique inputs, no materialization/scoring errors, no production ambiguity, and no ambiguity in 1,200 held-out-pair rotations. These are finite results against the eight unique declared rivals, not a proof against every possible hypothesis.

## Parametric prototype — separate from selected execution

The prototype adds one bounded hidden parameter:

- `projection_span = 1`: byte-exact selected/canonical behavior; Racket SHA-256 `18c042039414a6bd8745b9ffc3277879010959e3ce76d64d94d4d16925343dd8`, normalized rule hash `2b2e46dd36cc`.
- `projection_span = 2`: paint the first and second background cells on the same ray toward the matching border; Racket SHA-256 `8b76ae51be34fd3ee18c362e82f719044424c9ff68ed86379c9ce565f217a4d7`, normalized rule hash `b6cc5c55fd5f`.

The setting is selected once by episode seed and held fixed across three demonstrations and one query. Span 1 matches all 4/4 canonical labeled pairs. Both prototype episodes are production-identifiable, all 8/8 possible query holdouts are identifiable, and every materialized pair separates the chosen setting from its one declared rival. Limits are explicit: only seeds 20 and 21 were executed; only the paired span rival was tested; and span 2 requires two clear ray cells, a stricter input domain than the canonical task.

## Source changes

Selected-task changes are limited to:

- `repo/generators/b19deac47327/generator.py`
- `repo/generators/b19deac47327/tests/test_generator_b19deac47327.py`
- `repo/generators/b19deac47327/tests/test_parametric_projection_span.py`
- `repo/generators/b19deac47327/workspace/parametric/README.md`
- `repo/generators/b19deac47327/workspace/parametric/prototype.py`
- `repo/generators/b19deac47327/workspace/parametric/racket/span-1.rkt`
- `repo/generators/b19deac47327/workspace/parametric/racket/span-2.rkt`
- `repo/generators/b19deac47327/workspace/parametric/examples/span-1-public.json`
- `repo/generators/b19deac47327/workspace/parametric/examples/span-2-public.json`
- `repo/generators/b19deac47327/notes.md`

The canonical Racket ledger and base authority files are unchanged.

## Adversarial self-review and limits

Widening one height does not add a new output cue: profile facts already expose dimensions, and every complete lesson retains both orientations, odd-axis tie evidence, unseen orthogonal-edge evidence, and canonical-shape/orientation crossing. Strict schedule enumeration and all query rotations remained identifiable after the change.

The evidence is source-bound but finite. It covers declared rivals and sampled/periodic starts, not arbitrary learned hypotheses. The parametric prototype is intentionally excluded from selected generation, because its stricter two-cell-clearance domain and training value need separate review.

## Return replay and fresh-copy verification

The draft return was replayed against a fresh full extraction of the original 94,130-file packet. `git apply --check` and `git apply` both exited 0 from that extraction's exact `WORK/` root, all ten intended paths were present after application, the patch SHA-256 was `ddf498cabcc71cf46eae328d0c6dd48fba8682c428bf618520cfa9ae194ebb5d`, and the replayed generator SHA-256 was the reported final `66a3c56f61986c75dc40053dce167a0b6f0c513892a78de98ba521379d7809ac`.

The focused suite was then run from the replayed packet rather than the authoring tree: **50/50 passed**. The replay receipt, source-bound runtime manifest, JUnit output, and concise cross-check are retained under `checks/replay-draft/` and `checks/replay-fresh-task-tests/`. The first packaging attempt was also retained: it rejected an executable mode on the new prototype; changing only that mode to `0644` left the prototype and generator byte hashes unchanged before successful packaging.

A near-final candidate containing those replay records was then replayed independently as well. Candidate ZIP SHA-256 `cee2ac6552ac3ade8833e55aa87a277dd5fecea02d00fc147fda95e5316baeb0` produced the same patch SHA-256, the same ten changed-path hashes, and another **50/50** pass from its fresh checkout; see `checks/replay-candidate/` and `checks/replay-candidate-task-tests/`.
