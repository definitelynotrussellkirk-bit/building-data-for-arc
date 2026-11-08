# Current notes: 536de2f7591b

## Source binding

- Current version: `3.1.0`
- Current generator SHA-256: `c0f5598cf011e36aa5302bc3fd897c8f3fdc8851e043ccb64d05c4f5065fcf06`
- Issued version for review: `3.0.1`
- Issued SHA-256: `4ba262eb534bd9ed0e77ead953643f59dd5b02d636a7ff8d0a5897a64a2109a1`
- Canonical `RULE_HASH`: `02c227b9b2a6` (unchanged)
- Review assignment: `review-bc2e64a9e7d5c628`

Original historical notes remain in `evidence/associated_notes.jsonl`; the prior maintained source and decisions remain represented in the frozen baseline and review index.

## Intended rule

For each row containing one contiguous color-3 block, move that entire block left until it begins immediately after the nearest color-8 cell originally to its left. With no such 8, move it to column zero. Preserve block length. Color-8 cells, inactive rows, and lawful nonmarker distractors are unchanged.

The defended production grammar includes block lengths 1–3, suffix and interior starts, right-side cyan decoys, and inert path distractors. Fixed color roles are intentional. The Racket program remains the sole label authority.

## Decisions retained from version 3.0.1

Version 3 restored contiguous blocks after an older singleton-only shortcut, added exact controls, synchronized the selected base target text to the unchanged canonical program, and introduced four scheduled profiles:

1. `canonical_suffix` for canonical-size and suffix support;
2. `interior` to refute suffix-only motion;
3. `path_distractor` to refute treating any nonzero cell as a barrier;
4. `wide_block` to refute width-at-most-two motion.

Canonical shape pairs `(7,6)`, `(7,8)`, `(9,8)`, and `(9,9)` remain jointly sampled on the core profiles. Exact controls remain `grid_h`, `grid_w`, `n_green_rows`, `max_block_width`, and `n_distractors`. Old ambiguous v2 control names are not accepted.

## Changes in version 3.1.0

### Public call validation

`seed` must be a literal integer, and `sample_index` must be a literal nonnegative integer; booleans are rejected. Difficulty remains limited to `None`, `easy`, `medium`, and `hard`. The same validation is owned by both `schedule_profile` and `generate`, preventing negative tuple indexing and coercion-like replay identities.

This reverses the incidental v3.0.1 behavior that accepted invalid scalar calls. Evidence: the before defect linter reported 24 warnings; the final linter reports zero.

### Rotation-resilient lesson composition

The schedule period and canonical profile are unchanged, but noncanonical profiles now overlap witnesses:

- `interior`: interior motion + path distractor;
- `path_distractor`: path distractor + width-three block;
- `wide_block`: width-three interior motion + right-side cyan decoy.

The prior ordered curriculum had 0/300 ambiguous production lessons but 513/1,500 ambiguous query rotations. A five-pair lesson could hold out its only witness for one rival. The overlap design ensures each declared witness appears at least twice in any five consecutive default samples, so every four-of-five holdout retains all three.

The path profile defaults to width at least seven to fit a length-three source, destination, and intervening distractor. Explicit width overrides still use the full declared axis and are exact; they are not promised to preserve the default witness bundle.

## Separate proposed parameter family

`workspace/parametric/prototype.py` explores one hidden episode-level parameter:

- `direction=left`: canonical/default, exact canonical Racket program;
- `direction=right`: mirrored nearest-right-wall/right-edge behavior.

The parameter is chosen once per episode and omitted from public challenges. Both exact programs run through Racket and are cross-checked with independent Python mirrors. Retained seeds 0 and 2 cover both settings, and every retained demonstration/query distinguishes them. This remains a proposed authoring variant; it does not modify production, catalog approval, or canonical authority.

## Verification bound to current source

- Full battery: 12/12 stages green.
- Task-local tests: 62/62 passed.
- Strict defect linter: zero findings.
- Lesson census: 300/300 materialized, 1,500 unique pairs, zero production ambiguity.
- Query rotations: 0/1,500 ambiguous, with no hook or scoring errors.
- Canonical authority sync, rule smoke, Racket lint, exact controls, and profile floors pass.
- Post-repair visible solve: 4/4 demonstrations; prior rule exposure yes, reference not consulted during solve, masked correctness unknown.

Use `checks/lesson-census.compact.json`, `checks/after/`, and `checks/task-tests/` from the corresponding return for source-bound evidence. Do not carry success across a source hash.

## Known limits and open scope

- Rotation identifiability is only against the three declared rivals, not all possible hypotheses.
- Exact overrides may suppress scheduled witnesses; the default lesson guarantee does not cover arbitrary forced combinations.
- Widths above three, multiple disconnected color-3 groups in one row, and collisions with unrelated objects are outside the defended grammar.
- Palette permutation is not supported because the rule has fixed color roles.
- The proposed rightward parameter is not approved production behavior.
- Finite Racket/Python agreement and census results are evidence, not training admission or catalog approval.
## Current reviewer considerations

Source SHA-256: `c0f5598cf011e36aa5302bc3fd897c8f3fdc8851e043ccb64d05c4f5065fcf06`.

# Decisions: 536de2f7591b

## D1 — own the public scalar contract

**Choice.** Require a literal integer `seed`, a literal nonnegative integer `sample_index`, and a declared difficulty at both `schedule_profile` and `generate`.

**Prior rationale.** The issued implementation had no explicit rationale for accepting coercible or index-like values; the behavior appears incidental to Python and `gen_ctx` rather than intentional API design.

**Alternatives considered.** Coercing strings/floats to integers was rejected because it creates nonobvious replay identities. Accepting booleans was rejected because `True == 1` hides caller mistakes. Allowing negative indices was rejected because profile selection then depends on Python tuple semantics rather than the documented schedule.

**Probe.** Ten red tests cover booleans, floats, strings, and a negative index. The strict linter independently exercised 24 banded cases.

**Failure modes and limits.** This does not validate arbitrary integer magnitude; large nonnegative indices remain lawful and deterministic. The guard raises `ValueError` rather than preserving whatever exception a downstream helper might previously have produced.

## D2 — preserve the four-profile schedule but overlap witnesses

**Choice.** Keep `canonical_suffix`, `interior`, `path_distractor`, and `wide_block` in the existing four-step cycle, while making each noncanonical profile carry two adjacent semantic witnesses.

**Prior rationale.** Version 3.0.1 guaranteed all three witness types in each ordered four-example lesson. That was sufficient only while the fifth pair was always the query. The historical reason for relying on a fixed query position is unknown.

**Alternatives considered.** Increasing the training set from four to five was rejected because it changes the episode contract and still leaves arbitrary holdout behavior unspecified. Random witness duplication was rejected because short lessons could miss a contrast. Adding a fifth production profile was unnecessary; overlap within the existing cycle gives a deterministic four-of-five guarantee with less interface churn.

**Probe.** The pre-repair source had 0/300 ambiguous production lessons but 513/1,500 ambiguous rotations. The final source has 0/300 and 0/1,500 respectively. Focused tests exhaust all five holdouts over 20 seeds, four cycle starts, and all difficulty values.

**Failure modes and limits.** The guarantee is against declared rivals only. Explicit overrides can suppress witnesses and are excluded from the default-curriculum claim. Future rival additions must add a corresponding witness and re-run the rotation test.

## D3 — use width three in the path profile and preserve exact overrides

**Choice.** Default `path_distractor` and `wide_block` samples use a width-three primary block; the path profile defaults to canvas width at least seven. Explicit controls still accept the full declared width range and remain exact.

**Rationale.** The path profile must now refute both the path-barrier rival and the width-capping rival in the same pair. Width seven is the smallest clean default canvas that can hold a length-three source block, a length-three destination, and a path cell between them without overlap.

**Alternatives considered.** Reusing a second active row for width three was possible but makes the contrast depend on row count and row ordering. Silently clipping a requested width or block size was rejected because exact controls must remain observable.

**Probe.** Crossed-boundary tests cover heights 5/6/18, widths 6/20, row counts 1/5/6, widths 1/2/3, distractor counts 0/3, all bands, and all cycle starts. A requested impossible row count is rejected instead of clipped.

**Failure modes and limits.** Default path lessons no longer sample width six. Explicit width six remains legal, but a forced combination is not promised to carry the full default witness bundle.

## D4 — leave canonical authority and canonical profile unchanged

**Choice.** Do not edit the Racket program, canonical ledger, `RULE_HASH`, or the `canonical_suffix` profile.

**Rationale.** Both reproduced defects were in call validation and lesson composition, not label semantics. Changing authority would expand review scope without addressing either root cause.

**Alternatives considered.** Encoding the rule in Python as a new label source was rejected. Rewriting canonical examples to fit the new overlap scheme was also rejected; production diversity should extend around canonical support, not redefine it.

**Probe.** Authority sync, Racket lint, rule smoke, canonical pair tests, and the full final battery are green. The selected `left` parametric program is byte-for-byte canonical.

**Failure modes and limits.** Python mirrors are verification aids only. A shared conceptual error between the reviewer and canonical program remains possible, although real Racket execution is retained.

## D5 — keep the direction variant separate and hidden once per episode

**Choice.** Build a proposed `direction ∈ {left,right}` family under `workspace/parametric/`, with one deterministic hidden draw per episode. Do not put the parameter into the production generator or public challenge.

**Rationale.** Direction is a genuine rule change, not an input axis. Varying it per pair would create an incoherent lesson; selecting it once per episode supports inference from demonstrations. Keeping it separate prevents accidental catalog or canonical changes.

**Alternatives considered.** A public direction flag was rejected because it reveals the answer. Per-example random direction was rejected because no single rule would explain the lesson. Reimplementing both labels only in Python was rejected because the task requires actual Racket authority checks.

**Probe.** Retained seeds 0 and 2 cover right and left. Both programs agree with independent Python mirrors, every demonstration/query distinguishes settings, and public test records omit outputs and parameter metadata.

**Failure modes and limits.** The rightward rule is proposed and unapproved. Evidence covers retained seeds and the prototype's collision-free contiguous-block grammar, not every possible input or hypothesis.

## D6 — compact large evidence without discarding the failure

**Choice.** Keep the exact hashes, source bindings, command, counts, and first failure witness in compact census reports; retain the full 34 MiB reports locally outside the packaged `checks/` tree.

**Rationale.** The return contract has a 25 MiB expanded-evidence limit. Packaging both full reports would make a valid return impossible.

**Alternatives considered.** Dropping the pre-repair failure was rejected. Keeping only prose was rejected because it would lose source binding and reproducibility. The compact reports preserve the decisive regression and the full-report SHA-256 values.

**Limits.** A maintainer cannot inspect every retained instance from the small return alone. The focused red test and representative witness are included, and the full census can be regenerated from the exact command.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-88cfe058026b16ea:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `c0f5598cf011e36aa5302bc3fd897c8f3fdc8851e043ccb64d05c4f5065fcf06`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/536de2f7591b/generator.py,unchanged SHA256 c0f5598cf011e36aa5302bc3fd897c8f3fdc8851e043ccb64d05c4f5065fcf06. Explicit bounded no_issue:48default/88endpoint/24crossed cases and4expectedincompatibility rejections;24five-pair windows/120holdouts against3rivals useindependentPythonmirror.22representativeactualRacket inputs (12generated+4canonical+6handboundaries) match. Validwidth6forcedoverride isoutsidedefaultwitnessguarantee,notdefect. No fullbattery, malformedinputexhaustion, widergrammar orrightwardvariantqualification. No ownerauditrerun ornewtargetapproval. Quoted basenames mean exacttarget-localpaths: `checks/audit/536de2f7591b/AUDIT_SECTION.md` `checks/audit/536de2f7591b/canonical.json` `checks/audit/536de2f7591b/comparisons.json` `checks/audit/536de2f7591b/finalize.py` `checks/audit/536de2f7591b/generated.json` `checks/audit/536de2f7591b/inputs.json` `checks/audit/536de2f7591b/probe-summary.json` `checks/audit/536de2f7591b/probe.py` `checks/audit/536de2f7591b/probe.stderr.txt` `checks/audit/536de2f7591b/probe.stdout.txt` `checks/audit/536de2f7591b/racket-cases.json` `checks/audit/536de2f7591b/racket.json` `checks/audit/536de2f7591b/racket.stderr.txt` `checks/audit/536de2f7591b/racket.stdout.txt` `checks/audit/536de2f7591b/receipt.json` `checks/audit/536de2f7591b/rotations.json`

### Assessment or prior finding

## 536de2f7591b

**Outcome: `no_issue_found` within the bounded scope below.** No target files were edited. Generator version `3.1.0`, SHA-256 `c0f5598cf011e36aa5302bc3fd897c8f3fdc8851e043ccb64d05c4f5065fcf06`; canonical rule hash `02c227b9b2a6`.

### Scope and rationale

Read the selected `generator.py`, `notes.md`, and `evidence/review_index.json`; retrieved the four labeled canonical pairs using the public `reviewer_support.canonical_pairs` helper. The initial lookup for `_review_index.json` returned exit 1 because that spelling does not exist; the correct public index path is `evidence/review_index.json` and was read successfully. Historical success claims in the notes were treated as background, not as new verification.

The audited rule slides each contiguous green (3) row block immediately after its nearest original cyan (8) cell to the left, or to column zero when none exists. Length and lawful nonmarker cells remain unchanged. The audit uses an independently written Python mirror for bounded structural/rival checks and actual canonical Racket for representative authority checks.

| Check | Scope | Result |
|---|---|---|
| Default profiles | 48 cases: seeds 0, 1, 17; difficulty None/easy/medium/hard; all four profiles | Domain checks, deterministic replay, core canonical profile, and expected default witnesses passed |
| Single exact-control endpoints | 88 cases: seeds 0, 17; all four profiles; height 5/18, width 6/7/20, green-row count 1/6, block maximum 1/3, distractor count 0/3 | Every requested value observed exactly; all domain/replay checks passed |
| Crossed corners | 24 cases: all profiles in easy/hard, seed 17; tuples (h,w,rows,max,distractors) = (5,6,1,1,0), (18,20,6,3,3), (6,7,6,3,3) | All domain/replay/control checks passed |
| Documented incompatible overrides | h=5 with six green rows, all four profiles | Four expected `ValueError: n_green_rows cannot exceed grid_h` rejections |
| Declared-rival holdouts | 24 five-pair windows, five query positions each; seeds 0/17, None/easy/hard, four starting profiles | 0/120 ambiguous holdouts against suffix_only, any_nonzero_barrier, width_at_most_two, using mirror outputs |
| Canonical examples | Four publicly retrieved labeled pairs | All four agree with the independent mirror and with actual Racket |
| Actual canonical Racket | 22 inputs: 12 generated representatives, four canonical pairs, six hand boundaries | 22/22 output matches; no runtime errors; all valid outputs and valid generator-domain checks |

The six hand cases cover an interior block with only a right-side wall, the nearest of multiple left walls, an inert distractor in the travel path, a stationary adjacent-wall block, an overlapping source/destination shift, and a long shift of a width-three block. Inputs and actual outputs are retained, not just summaries.

### Interpretation

Width 6 is a valid exact override even for the path profile; it need not preserve that profile's default two-witness bundle. The notes explicitly exclude forced overrides from the default curriculum guarantee. Accordingly, loss of a default witness under a valid override was not labeled a defect. The h=5/six-row combination is explicitly incompatible and was rejected rather than clipped. No source-backed counterexample was found.

### Commands and observed results

Run from the packet's `WORK` directory; the wrapper executes payloads from `WORK/repo`. All three commands exited 0:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv-review/bin/python run_with_racket.py ../.venv-review/bin/python ../checks/audit/536de2f7591b/probe.py > checks/audit/536de2f7591b/probe.stdout.txt 2> checks/audit/536de2f7591b/probe.stderr.txt
PYTHONDONTWRITEBYTECODE=1 .venv-review/bin/python run_with_racket.py ../.venv-review/bin/python -m arcpuzzles apply 536de2f7591b --input ../checks/audit/536de2f7591b/inputs.json --check-generator-domain --timeout 120 --out ../checks/audit/536de2f7591b/racket.json > checks/audit/536de2f7591b/racket.stdout.txt 2> checks/audit/536de2f7591b/racket.stderr.txt
PYTHONDONTWRITEBYTECODE=1 .venv-review/bin/python run_with_racket.py ../.venv-review/bin/python ../checks/audit/536de2f7591b/finalize.py
```

The public apply receipt binds actual execution to canonical rule `02c227b9b2a6`, rule-text SHA-256 `32f99ab126f8942465379ea89224aae0c8a87e9ca7c66add45ae159a6a4897ab`, and the audited generator hash. The generator, notes, and review-index hashes were identical before and after the audit. `receipt.json` records source hashes, evidence hashes, commands, counts, and scope.

### Limits

This was a bounded audit, not a full battery or exhaustive proof. Only 22 representative cases used actual Racket; the remaining generation, invariant, and rival-rotation checks used the independent mirror. Rival identifiability was checked only against the three declared competitors. Arbitrary malformed inputs, blocks wider than three, disconnected green groups, collisions outside the declared grammar, and the proposed rightward parameter family were not investigated. No training-admission or catalog decision was changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
