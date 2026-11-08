# Current native extension — review-db65cf48f1dddb72

Production **3.0.0** remains unchanged: generator SHA-256
`079d0c5f6441d19daed57f2446faea8400518b09b32fc7442786a082e78a21de`.
The default retains the exact **676-byte** canonical Racket program, SHA-256
`0aa57664563a8a3f288e5b44baf9447974b609431b006611db324d4f9c92defd`.
The native adapter, implementation, contract and evidence inventory are under
`workspace/parametric/`; these are reviewer prototypes, with owner acceptance
pending and `training_admitted=false`.

## Current rule and teaching decisions

`combine=xor|difference` preserves color-ordered extraction and independent
normalization. The alternative subtracts the higher-color shape from the
lower-color shape. Both render cyan in the shared normalized frame, retain
blank leading rows/columns, remove canceled trailing extent, and return `[[0]]`
for an empty result. The expanded grammar permits axes 1..30, exact integer
ARC cells, exactly two nonzero colors and one four-connected component per
color. Arbitrary sizes, holes, different-color touching, identical normalized
shapes and subsets are lawful; production's narrower grammar is unchanged.

Requests use exact integer seeds 0..2**63-1, 2..6 demonstrations and 1..4 private
queries; ordinary defaults are three demos/four queries. Separate setting/demo/
query streams build the full six-plus-four bank before slicing, so count prefixes
and input matching across settings are preserved. The first two cores retain
leading blanks while canceling trailing extent and reverse color roles relative
to position, cell count and bounding-box area. Dense comb profiles remain
connected and distribute **360/346 foreground cells** across distinct 30x30 demo/
query inputs. No retries or solved-output filtering are used.

A supplies the independently normalized coordinate sets; B consumes them for
membership and ordered subtraction. The causal intervention changes only A's
second stored set to its observed coordinates. B's set operation and renderer
remain unchanged. Two seed-0 teaching cases change output under that intervention;
the recipe retains **four protected intermediate executions**, and the native
witness builder separately constructs and replays the full/counterfactual labels.

## Current executed evidence

Paths below are relative to `WORK/` in this return.

- `checks/95f849a2fe0f/native-and-audit.xml` and its command receipt: **97 tests
  passed** (37 native, 60 independent-audit tests). Read-only implementation
  review found no Critical, Important or Minor issue; it ran no extra tests.
- `checks/95f849a2fe0f/sampler-v1.json`: **96/96 requests passed**, with 157
  distinct inputs, 64 distinct query inputs and 32 distinct 30x30 inputs.
- `checks/95f849a2fe0f/teaching-v1/private/audit.json` and `executions.jsonl`:
  **40 intended labels** matched independent Python and protected Racket;
  **104 hypothesis fits** yielded 92 refutations, four intended survivors and
  eight explicitly equivalent XOR operand-order aliases. The aliases are reverse,
  position, ascending-area and descending-area ordering, each at seeds 0/17;
  XOR commutativity makes them equivalent. All surviving query scores agree.
  Accounting is **296 requests, 244 protected evaluations, 52 exact cache hits**.
  Task source hashes, runtime source hashes and live runtime identity stayed
  unchanged. Fitting uses only the first two demos and freezes survivors before
  scoring all four private queries.
- `checks/95f849a2fe0f/qualification/{qualification,execution}.json`: native
  qualification passed four jobs, six demos/four queries each, with **64 protected
  evaluations**. `workspace/parametric/evidence/manifest.json` binds current source,
  tests and compact evidence.
- `checks/95f849a2fe0f/causal-recipe.json` and `causal/{witness,replay}.json`:
  two source-bound causal cases are `reviewer_replayed`.
- `checks/95f849a2fe0f/preview/`: **16 public single-query views** exported and
  verified from the four qualified episodes. Projection verification is a
  serialization/source-binding check, not another label replay.
- `checks/95f849a2fe0f/design_core_probe.json`: 12 protected design evaluations
  retain core masks, empty/subset/touching literals and two changed-intermediate
  controls. Earlier expected-red and audit-literal correction receipts remain
  separate from the successful current checks.

These are finite seed, count and named-rival checks, not a proof of universal
identifiability. Both inherited entries remain **`needs_triage`**:
`review-c8354d27669163ad:v0001` reports the inert-extra-object defect on superseded
source; `review-3fc8d25412e66c0b:v0001` reports no issue on current production
source but still awaits triage. Neither status is closed by this extension.
The next owner action is qualification and acceptance of the exact integrated
native source. No training admission or activation was performed.

---

# Working notes: 95f849a2fe0f

## Review `review-f8eecbaf95a4b240`

The selected `2.0.1` implementation generated an unrelated “gallery pack” task with two to five arbitrary colors and therefore had transformation drift from the pinned authority. Version `3.0.0` replaces only the Python input sampler and retains the canonical Racket program unchanged.

### Repaired domain

- exactly two separated connected objects, colors `2` and `3`;
- each object is one fixed tetromino (the complete 19-shape D4 catalogue);
- canonical dimensions `(7,12)`, `(7,13)`, and `(8,14)` are used across easy, medium, and hard bands;
- output is normalized-shape XOR in color `8`, rendered from shared origin `(0,0)`;
- exact public profiles reproduce all three canonical inputs.

### Teaching decision

All canonical pairs are compatible with a plausible wrong rule: compute the normalized XOR and then crop away blank leading rows/columns. The default six-profile cycle is:

`leading_row, anchored, leading_col, anchored, leading_both, anchored`.

Every four consecutive pairs therefore contain two counterexamples, and every possible three-demonstration query rotation keeps at least one. `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable` expose this contract to shared tooling.

### Evidence and limits

Task-local regressions cover canonical replay, independent XOR calculation, all exact profiles, Racket/Python parity, schedule rotations, malformed inputs, determinism, diversity, and the retained workspace probe. The shared 300-lesson census materialized 300/300 lessons and checked 1,200 query rotations with no declared-rival ambiguity or scoring error; this is finite evidence against the declared re-crop rival, not a universal proof of identifiability. The shape grammar is intentionally restricted to tetrominoes, and difficulty changes canvas size/layout rather than rule depth.

No selected-task prior return note existed in `evidence/associated_notes.jsonl`; the retained passing task `b90d4c3d5553` was used only as an interface/contract example, not as a semantic template.
## Current reviewer considerations

Source SHA-256: `079d0c5f6441d19daed57f2446faea8400518b09b32fc7442786a082e78a21de`.

# Decisions for `95f849a2fe0f`

## D1 — Preserve the Racket authority

**Choice.** Leave `repo/shared/data/canonical/puzzles.jsonl` and the task-local base authority unchanged; pin `RULE_HASH = "0aa57664563a"` in the Python generator.

**Rationale.** The canonical examples and executable program agree on normalized-shape symmetric difference. The defect was wholly in the selected Python input distribution. Source-bound rule smoke, authority synchronization, and a direct apply receipt all pass with the existing program.

**Alternatives rejected.** Rewriting the authority to match the old gallery sampler would have changed the task rather than repaired it. Refactoring the Racket program without a semantic need would have added review risk.

**Failure mode / limit.** The Python mirror is test machinery only. Production outputs must continue to come from the pinned Racket source.

## D2 — Use exactly two canonical color roles

**Choice.** Every normal generated input contains one connected red object (`2`) and one connected green object (`3`) on background `0`; the output role remains cyan `8` in the authority.

**Rationale.** This matches every public pair and the authority's color-sorted two-object operation. Exact color roles also avoid creating unsupported color-permutation claims.

**Alternatives rejected.** The baseline's 2–5 arbitrary colors and motifs were transformation drift. Adding extra distractor colors would require a different selection rule not supported by the canonical task.

**Failure mode / limit.** Color invariance is not taught because it is not asserted by this task. The palette is deliberately fixed.

## D3 — Complete fixed-tetromino grammar

**Choice.** Build ordered pairs from all 19 fixed tetrominoes obtained by D4 closure of the five free tetrominoes; require the normalized shapes to differ.

**Rationale.** Four-cell connected shapes are broad enough to produce many overlaps/cancellations, small enough to enumerate and classify exhaustively, and consistent with the public objects. Pool sizes are 252 anchored, 40 leading-row, 40 leading-column, and 10 leading-both ordered pairs.

**Alternatives rejected.** Hand-listing a few motifs would create a hidden shape shortcut. Sampling arbitrary larger polyominoes would add placement complexity and an unsupported object-size axis without improving the core rule test.

**Probe.** `workspace/lesson_probe.py` reports every pair-pool size and samples 100 inputs per band.

**Failure mode / limit.** The curriculum does not teach generalization to object sizes other than four cells. This is explicit in the summary and invariants.

## D4 — Preserve the shared normalized origin

**Choice.** Render the XOR in the frame whose origin is `(0,0)` after independently normalizing each source shape. Do not re-crop the resulting nonzero cells.

**Rationale.** This is the non-obvious distinction encoded by the authority. Cancellation may remove all cells from the top row or left column while those empty coordinates remain part of the output frame.

**Alternatives rejected.** A final nonzero crop fits every canonical pair, making it the strongest plausible shortcut, but disagrees on generated leading-blank cases.

**Probe.** `checks/shortcut-witness/record.json` contains an exact Racket-labeled disagreement.

## D5 — Make the shortcut an explicit semantic contract

**Choice.** Declare `recrop_xor` in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; expose `leading_blank_frame` in `SEMANTIC_WITNESSES`; implement `lesson_identifiable`.

**Rationale.** A label-correct sampler can still teach the wrong rule. Executable declarations let shared tooling first verify that the rival fits every canonical pair, then require demonstrations that refute it.

**Alternatives rejected.** Documentation-only warnings cannot be measured. A larger unnamed random sample would not establish whether complete lessons distinguish the rival.

**Failure mode / limit.** One declared rival is not an exhaustive program search. Other ambiguity remains unknown unless named and tested.

## D6 — Use a rotation-safe six-slot schedule

**Choice.** The default profile cycle is `leading_row, anchored, leading_col, anchored, leading_both, anchored`. A lesson has three demonstrations plus one query.

**Rationale.** Every four consecutive pairs contain two rival witnesses. Holding out any one pair leaves at least one witness among the three demonstrations, so arbitrary query rotation remains identifiable against re-cropping.

**Alternatives rejected.** IID profile sampling can produce all-anchored demonstration sets. A schedule with only one witness per four pairs loses that witness when it becomes the query. Making every pair a witness would over-regularize the output-frame phenomenon and omit ordinary anchored cases.

**Probes.** Task tests enumerate all starts and held-out positions; `workspace/lesson_probe.py` checks 72 band/start/rotation combinations; the shared census checks 1,200 materialized rotations.

**Failure mode / limit.** The schedule is deterministic and therefore learnable as metadata. Correct solving still requires shape geometry because the profile does not determine the XOR pattern, and seeds vary pair choice and placement.

## D7 — Retain exact public profiles

**Choice.** Advertise `public_train_1`, `public_train_2`, and `public_test_1` as exact `scene_profile` overrides in addition to the four general profiles.

**Rationale.** Exact replay makes canonical support directly testable and guarantees the profile-floor requirement without weakening strict validation.

**Alternatives rejected.** Merely matching dimensions/palette would not prove that the canonical examples are inside the selected domain. Making public replay part of the normal schedule would overfit recurring examples.

**Failure mode / limit.** These exact controls are diagnostic endpoints, not default draws.

## D8 — Canonical dimensions by difficulty, no cosmetic axes

**Choice.** Easy uses `7×12`, medium/unspecified uses `7×13`, and hard uses `8×14`. The only declared exact axis is `scene_profile`.

**Rationale.** Every band hits a canonical size/palette while changing actual placement space. Removing the old motif-count, color, texture, and packing controls prevents dead or overlapping axes.

**Alternatives rejected.** Arbitrary grid sizes weakened canonical profile coverage. Difficulty-specific rule changes would create multiple tasks. Cosmetic texture axes would add no semantic value.

**Failure mode / limit.** Difficulty reflects canvas/layout variation, not reasoning depth; this is stated rather than inflated into a curriculum claim.

## D9 — Placement with separation and vertical freedom

**Choice.** Place the two shapes side by side with a 2–3 column gap, vary their horizontal order and vertical origins, and keep general draws below row 1.

**Rationale.** Separation makes object extraction unambiguous; varied order prevents reading-position from encoding color role; canonical canvases easily contain every tetromino pair. Starting below row 1 avoids accidentally replaying public inputs while preserving translation invariance.

**Alternatives rejected.** Touching differently colored shapes could look like one object. Fixed positions would create a location shortcut. Arbitrary rejection sampling was unnecessary for this small bounded grammar.

**Failure mode / limit.** Side-by-side layout is a residual regularity. It does not determine the normalized XOR, but future expansion could add above/below placement after proving unambiguous extraction.

## D10 — Strict validation and exact-or-loud controls

**Choice.** `self_check` requires canonical dimensions, exact palette, exactly four cells per color, one 4-connected component per color, background separation, non-identical normalized shapes, and a declared profile. Unknown controls and invalid difficulties raise errors.

**Rationale.** The generator should never silently emit outside the reviewed semantic manifold, and every advertised override must be observable from the returned grid.

**Alternatives rejected.** Best-effort coercion or ignored kwargs make battery results misleading. Accepting identical shapes creates an empty XOR degeneracy not represented publicly.

**Failure mode / limit.** `strict_canonical_like` equals the full selected domain, yielding a strict fraction of 1.0; that is appropriate only because all general profiles deliberately stay canonical-sized and canonical-colored.

## D11 — Retain reusable task-local diagnostics

**Choice.** Add `workspace/lesson_probe.py` and a portable regression that executes it from the staged task-test runtime.

**Rationale.** The shared census samples production lessons but intentionally does not enumerate every cyclic start. The retained probe closes that exact finite gap, reports generator/source hashes, and gives future agents one command to recheck the schedule after edits.

**Alternatives rejected.** A one-off notebook or undocumented shell snippet would be difficult to replay. Copying rival-name lists into the probe could drift; the tool reads the generator's declarations.

**Failure mode / limit.** The probe uses the Python mirror for post-repair diagnostics and does not replace Racket receipts.

## D12 — Prior-return use and provenance

The selected task's `evidence/associated_notes.jsonl` was empty, so no prior selected-task return was available as a semantic lead. The packet's retained passing generator `b90d4c3d5553` was consulted only for portable test and semantic-contract patterns, as instructed; none of its task-specific geometry, palette, or rule choices were copied.
