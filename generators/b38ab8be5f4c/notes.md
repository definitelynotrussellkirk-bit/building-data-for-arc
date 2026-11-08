# Current notes: b38ab8be5f4c

Final reviewed generator SHA-256:
`87f47e0d9bea2bc142adbb0efd44a9695ea0325ced1b7e33542f5f0ef8a4f900`.
Imported historical records remain in `evidence/associated_notes.jsonl`.

## Intended rule

The sole nonzero cell in row 0 supplies guide color `G`. In rows 1+, exactly one of three connected
body objects has color `G`. Return the raw tight bounding-box slice spanning all body cells colored
`G`; preserve any other colors inside that rectangle. Canonical rule hash: `439c1e733337`.

## Current distribution

- Four ordered demonstrations are required.
- Canonical canvas profiles, marker columns `0/2/5/9`, colors 1–9, target zones, target shapes, and
  one-per-four bbox intruders are deterministically scheduled.
- At `sample_index % 4 == 2`, target `p5` is selected by the marker while a larger, higher-priority
  `ring8` is a distractor. This refutes both largest-object and fixed-morphology selectors.
- `shape_priority_morphology` is declared as a canonical-fitting shortcut and lesson competitor;
  `target_not_shape_priority` is its decisive witness.
- Call metadata and overrides require literal declared scalar types; booleans/floats are not accepted
  as integer/color aliases.

## Decision changes in this review

1. Replaced the prior `solid9` size-only distractor with the canonical-shape role swap above. The
   retained prior audit showed the morphology rival fit 5/5 canonical pairs and 720/720 defaults.
2. Removed zone-only semantic witnesses with no rival claims; zone coverage remains directly tested.
3. Reversed the prior choice to preserve a comment-only selected Racket divergence. The selected
   bank `target_code` is now exact to canonical/raw source; executable semantics did not change.

## Evidence and limits

- Native final battery: 12/12 green under `checks/after-v2/`.
- Focused portable regressions: 32/32 green; retained role-swap Racket output in
  `checks/shape-priority-racket-final.json`.
- Production lesson census: 300/300 ordered bundles unambiguous with four demos and one query.
- Arbitrary query rotation is **not supported**: 450/1,500 hold-one-out rotations are ambiguous.
- Difficulty bands share structural coverage and differ mainly by color phase; no strong semantic
  easy-to-hard progression is claimed.
- Generator `VERSION` remains `3.0.0`; all review provenance is bound to full source SHA-256.
- The inherited frozen task-test fixture has a fixed-depth canonical path and fails portable preflight.
  It is library-owned and intentionally unchanged; new task-local tests pass.

Open maintainer work: migrate that frozen fixture to `reviewer_support` helpers. If downstream lesson
assembly begins shuffling the query position, redesign the five-pair bundle and require rotation
identifiability before export.
## Current reviewer considerations

Source SHA-256: `87f47e0d9bea2bc142adbb0efd44a9695ea0325ced1b7e33542f5f0ef8a4f900`.

# Decisions — b38ab8be5f4c

Final generator SHA-256: `87f47e0d9bea2bc142adbb0efd44a9695ea0325ced1b7e33542f5f0ef8a4f900`.
All paths are relative to `WORK/`.

## D1: Preserve the guide-color crop rule

**Choice.** Keep the canonical semantics unchanged: the first nonzero value in row 0 names a body
color; return the untouched tight bounding-box slice spanning that color in rows 1+.

**Original rationale.** The five canonical pairs and rule hash `439c1e733337` agree on color-role
selection and raw slicing. The existing `bbox_intruder` branch correctly exposes that cells of other
colors inside the rectangle must survive.

**Alternatives rejected.** Masking non-guide cells, cropping all objects, selecting by size, position,
or morphology all disagree with lawful counterexamples. Rewriting the Racket rule was unnecessary
because live Racket and the independent Python mirror already agree.

**Probe/failure mode.** `checks/shape-priority-racket-final.json` binds the repaired witness to the
selected Racket rule. `checks/after-v2/checks/b38ab8be5f4c_after_rule_smoke.json` and authority sync cover canonical parity.

## D2: Replace the size-only anti-shortcut with a role-swapped morphology witness

**Prior choice.** At `sample_index % 4 == 2`, the baseline used a generalized `solid9` distractor to
refute “pick the largest.” That did not vary canonical object morphology roles. A fixed ranking
`ring8 > stair5 > p5 > c5 > tee4` still fit 5/5 canonical pairs and 720/720 sampled defaults.

**New choice.** In that slot, keep target `p5` but use a larger `ring8` distractor. The row-0 marker,
not morphology or area, is now necessary. This single change refutes both “largest object” and the
retained marker-free morphology ranking within every intended four-demo window.

**Why this option.** It is lawful, uses canonical shapes, preserves `EXAMPLES_NEEDED = 4`, and puts
the counterexample in the production schedule rather than a rare random tail.

**Alternatives rejected.** A rare stochastic role swap would not protect every lesson; adding a
fifth demonstration would change downstream assembly; retaining `solid9` would keep the reproduced
morphology shortcut; globally randomizing all shape-role links would reduce canonical-profile
support without additional value.

**Probe/failure mode.** The focused test checks all 60 schedule residues in easy/medium/hard.
The final 300-lesson census checks actual assembly. The predictable four-step schedule is acceptable
because sample indices are not visible to the learner; only the grid is.

## D3: Declare the actual rival and decisive witness

**Choice.** Add `shape_priority_morphology` to `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and
`CANONICAL_SHORTCUTS`; add `target_not_shape_priority` and bind it in `WITNESS_RIVALS`.
Remove the three zone-only entries from `SEMANTIC_WITNESSES` because they had no rival claim.

**Rationale.** A generator should make its strongest canonical-fitting shortcut executable so shared
semantic tooling can test it. Coverage-only facts remain useful in focused tests but should not be
presented as semantic counterexamples.

**Alternative rejected.** Keeping the rival only in a one-off review script would let future changes
silently reintroduce it.

**Limitation.** Declared-rival success is finite evidence, not proof against every possible heuristic.
This motivates F1 in `FEEDBACK_TO_CODEX.md`.

## D4: Enforce literal API scalars before `gen_ctx`

**Observed failure.** The first semantic repair passed the main gates but defect lint found 81
malformed variants accepted through Python coercion, including booleans/floats on integer or color
axes and invalid call metadata.

**Choice.** Validate exact types for `seed`, `sample_index`, `difficulty`, and every declared override;
reject negative indices and unknown axes before constructing a context.

**Alternatives rejected.** `int()`/truthiness coercion is convenient but creates aliases and makes
controls nonliteral. Relying only on downstream range checks misses `True == 1` and integral floats.

**Probe/failure mode.** `checks/strict-scalars-red.log` records the failing test first;
`checks/strict-scalars-green.log` and the final defect-lint stage are green. This is boundary
validation only; lawful control domains are unchanged.

## D5: Input distribution choices

| Input choice | Current policy and rationale | Alternatives / failure modes | Evidence |
| --- | --- | --- | --- |
| Canvas size | Cycle the four canonical `(h,w)` profiles, phase-shifted by seed. This preserves exact profile support instead of inventing unsupported scale. | Wider size generalization is executable but not needed for this compact task; fixed one-size data would overfit. | Final profile floor 60/60 exact and envelope. |
| Marker column | Cycle `0,2,5,9`. Original associated note intended to refute canonical column-0 coincidence. | Always column 0 permits `guide_only_from_column_zero`; arbitrary invalid columns must reject. | Witness 450/600; exact override tests. |
| Guide color | Cycle colors 1–9 with a band offset. This separates semantic role from a fixed numeric color. | A narrow palette would permit color identity shortcuts. | Final diversity/override stages. |
| Target shape | Four-step `tee4,c5,p5,stair5`, with `ring8` at index 19; the repaired index-2 role swap makes `p5` outrank-independent. | Full randomization would weaken guaranteed lesson composition; fixed morphology roles created G1. | Cyclic-window regression and census. |
| Target zone | Cycle left/center/right with seed phase. This prevents position-only selectors. | One fixed zone permits leftmost/topmost heuristics. | `target_not_leftmost` 410/600 and `target_not_topmost` 406/600. |
| Bbox intruder | True once per four samples. This exposes raw-crop preservation. | No intruder lets masking fit canonical examples; always intruder would distort the prior. | Witness 147/600 and masking rival checks. |
| Distractor shapes | Canonical linked shapes ordinarily; at index 2 use the `ring8` role swap; intruder branch uses one internal cell plus external `cross5`. | `solid9` was an overgeneralized size witness that failed to break morphology ranking. | G1 retained counterexample and final semantic gate. |
| Difficulty | Bands share structural scheduling and mainly shift colors. | A fabricated semantic difficulty ladder would add unsupported complexity. | Known limitation retained from prior notes; per-band checks all pass. |

## D6: Ordered lesson policy, not arbitrary query rotation

**Choice.** Support the deployed order: four consecutive demonstrations, then the fifth pair as
query. Do not claim that any of the five may be held out.

**Evidence.** Production census: 300/300 bundles unambiguous. Rotation diagnostic: 450/1,500
ambiguous, chiefly when the held-out pair carries the only decisive witness for a rival.

**Alternative rejected.** Expanding every five-pair bundle so every possible query is identifiable
would require multiple role swaps/intruders in four remaining demos and would materially change the
training distribution. That can be a future requirement, but it is not the current downstream
assembly.

**Failure mode.** Any caller that shuffles demonstrations and query violates this contract. The
census report makes that visible rather than silently treating ordered success as universal.

## D7: Exact Racket source synchronization

**Prior choice.** An imported associated note said to preserve the explanatory comment because
comment-only divergence was not a correctness problem.

**New choice.** Make selected `target_code` byte-for-byte equal to canonical/raw code. The current
packet's mandatory strict battery treats the divergence as a blocker, while the frozen baseline
retains the comment for history. No executable token or rule behavior changed.

**Probe.** Final authority sync reports exact/normalized equality and execution parity. The selected
bank file is the only Racket-related patch.

## D8: Keep generator `VERSION = "3.0.0"`, bind by source hash

**Choice.** Do not bump the RNG version for this targeted schedule repair. The packet, every check,
solve episode, census, and retained counterexample bind the full source SHA-256, so provenance is
unambiguous while unaffected scheduled outputs remain stable.

**Alternative rejected.** A version bump would reseed dimensions/colors/layouts globally and obscure
whether the role swap itself fixed G1. A future release process that treats `VERSION` as the sole
cache key should bump it and regenerate evidence; this review assumes the repository's source-hash
binding contract.

## D9: Do not edit the frozen inherited test

**Choice.** Leave `repo/generators/b38ab8be5f4c/tests/test_generator_b38ab8be5f4c.py` unchanged despite its portable fixed-depth
path defect. Add regressions only under the allowed task test directory.

**Reason.** DUTIES explicitly assigns frozen-fixture migration to the maintainer and requires blocked
completion on preflight failure. A temporary portable copy was used only as verification evidence;
it is not part of the source patch.
