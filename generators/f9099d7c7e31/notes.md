# Working notes: f9099d7c7e31

## Review 2026-10-02

Assignment `review-c3cb6cd10667d2ef`. Historical imported notes remain unchanged in `evidence/associated_notes.jsonl`. This note describes the new review, not a replacement for historical evidence.

### What failed
The baseline passed its entire 12-stage battery, yet largest-bounding-box-area, widest-then-tallest, and border-only selection agreed with the authority on all 384 default samples in an independently implemented probe. The existing four declared rivals could not detect these omitted hypotheses. The initial regression suite reproduced 27 failures before production edits.

### Construction and retained support
Slots 0 and 3 retain canonical L-shape morphology anchors. Slot 1 remains the literal-crop/foreign-pixel example and now prefers an interior target, teaching the border distinction within the three-demo prefix used by the packet's fresh-solve helper. Slot 2 is the adversarial tie example: a connected 3×5 staircase with 10 occupied cells beats both a taller 4×5 eight-cell L and a shorter 1×5 five-cell line. A narrower 4×3 twelve-cell rectangle loses despite having more cells; it may intrude into the target's recess. Slot 3 also prefers interior placement. Placement preferences are followed by the existing lawful search, not rejection-free guarantees for arbitrary pinned controls.

Dense tie geometry applies only to 3×5 `width_tie_size` targets. Smaller exact-control targets retain the prior lawful construction: a tall connected same-width loser needs enough cells that it cannot be beaten in a small crop while retaining the required foreign pixel and zero. Exact controls are not silently changed to manufacture a stronger lesson.

Keep `EXAMPLES_NEEDED=4`, the eight declared axes, `_CANONICAL_LINKED_PROFILES`, and `MIN_STRICT_FRAC=0.20`. Measured strict canonical-like default share remained 58.33% before and after. Horizontal/vertical reflection and nonzero-palette permutation are checked; 90-degree rotation is deliberately NOT treated as a symmetry of a width-selection rule.

### Negative results retained
Replacing the short tie by only a tall tie created a widest-then-shortest shortcut. An additional short equal-width loser fixes that reversal. Moving only slot 3 inside the grid left border-only selection consistent with the first three demonstrations; slot 1 was also moved inside. Tests captured both failures before the corresponding changes. The four new rivals are now registered in the normal semantic gate, not only the independent tool.

### Evidence and limits
The return ZIP contains source-bound before/after reports, saved numeric input/output grids, HTML counterexamples, all failed probes, and staged task-test receipts. Final independent evaluation checked 2,153 authority-labeled cases: five canonical pairs, 384 defaults, 1,728 exact-axis combinations, and 36 reflection/palette variants. All eight named rivals were contradicted within each of 192 complete four-demonstration windows. This finite hypothesis bank is not an exhaustive proof against shortcuts. Axis domains were exhausted at one seed/index per difficulty; the seed space was not exhausted. No Qwen training run, hidden-query solve score, or catalog approval is claimed.

See `workspace/README.md` for runnable checks. Root review documents in the compact return contain the full decision log, two findings-only audits, and handoff.
## Current reviewer considerations

Source SHA-256: `637dab454ea60d0c41d371506033ef592ec2a949fc61d0b5972af1060a065b80`.

# Decisions — f9099d7c7e31

## Scope and authority

The immutable draw selects only `f9099d7c7e31`; two separate audit targets receive findings, not source edits. The improvement is in the input distribution. Canonical Racket code, all canonical inputs/labels, shared tooling, and catalog approval data are untouched. Original generator version 3.0.0 becomes 4.0.0.

## Input choices

| Choice | Prior rationale or evidence | Decision, alternative, and failure mode |
|---|---|---|
| Background and object identity | The existing generator and canonical family use background 0 and monochrome four-neighbor objects. | Retain zero background and distinct object colors. Same-color disconnected objects are supported by the independent extractor's tests, but are not newly introduced into this generator. Do not use color as identity in the reference mirror. |
| `grid_h`, `grid_w`: 9–11 | Existing linked canonical profiles and difficulty schedule cover these sizes. The original reason for the precise upper bound beyond that support is unknown. | Retain both exact axes and all nine rectangular combinations. Expanding canvas bounds would dilute canonical support without addressing the demonstrated shortcuts. |
| `n_objects`: 3–4 | Existing canonical profiles contain three or four objects. | Retain. In the default four-object tie slot, spend the fourth object on the shorter equal-width loser rather than an uninformative ordinary distractor. Three-object pinned controls remain legal but need not refute every rival in one sample. |
| `target_width`: 4–5; `target_height`: 2–3 | Existing canonical crop morphology. | Retain exact values. Strong tie geometry is restricted to 3×5; other pinned dimensions retain lawful old geometry rather than being overwritten. |
| Target shape | Original L-shaped targets preserve holes and canonical morphology. They also made height/bounding-box-area reliable proxies for tie-breaking. | Keep L-shaped anchors and add a connected 3×5 staircase with row lengths 2, 3, 5 in the tie slot. Ten cells beat a connected taller 4×5 L with eight cells. Target holes remain; the whole bounding box is not filled. Arbitrary polyomino generation was rejected as unnecessary distribution drift. |
| `selection_mode` | Existing unique-width and width-tie/size branches teach the canonical ordering. | Retain both. The default tie includes taller and shorter losers of equal width. Replacing only the short loser with a tall one was rejected after three tests showed it merely inverted the shortcut. |
| `intruder_in_crop` | Existing comments and semantic witnesses deliberately distinguish literal input cropping from masking the selected object. | Retain exact Boolean behavior. The new target recess admits foreign pixels while still retaining zero cells. Do not sanitize them from the label. |
| `larger_narrow_decoy` | Existing anti-largest-cell-count witness. | Retain exact Boolean behavior. For the dense tie slot, use a 4×3 rectangle (12 cells) rather than the old 3×3 (nine), which would no longer exceed the new ten-cell target. It remains narrower and therefore loses. |
| Placement | Original slot 0 was top-edge, slots 1/2 right-edge, slot 3 bottom-left. Why every winner had to touch an edge is unknown. | Preserve slot 0/top and slot 2/right preferences. Prefer strict interior for slots 1 and 3. Interior only at slot 3 was rejected because the packet's three-demo solve prefix left border-only selection viable. |
| Colors and reflections | Existing random distinct nonzero colors and reflected L shapes provide nuisance variation. | Retain. Validate left-right reflection, up-down reflection, and nonzero color permutation with actual Racket. Correct the old comment implying quarter-turn invariance; width and height are not interchangeable. |
| Difficulty and episode schedule | Existing easy/medium/hard schedule plus `EXAMPLES_NEEDED=4` ties demonstrations to canonical anchors and anti-shortcut slots. | Preserve the schedule length and difficulty mapping. Test four consecutive demonstrations at starts 0–3, not just a single aligned window. The new three-demo prefix test addresses the packet helper; arbitrary three-example windows are not promised to be sufficient. |
| Strict canonical profile floor | Existing linked morphology profiles and 20% minimum prevent teaching examples from replacing all canonical support. | Keep the floor and profile definition unchanged. Both independent runs measured 58.33% default acceptance. This is the generator's explicit profile metric, not a claim that the full distribution is unchanged. |

## Test-first iterations and rejected alternatives

Initial new tests: 27 failures, 12 passes (`checks/regression_before.log`). Geometry changes then passed those cases. Registering the new rival hooks was separately tested. Adding only a tall loser caused three failures (`checks/height_inversion_before.log`); the additional short loser resolved them. Placing the only interior winner after the first three demonstrations caused three prefix failures (`checks/fresh_prefix_before.log`); slot 1 became interior too. These logs are intentionally retained, not overwritten by green runs.

The independent tool initially failed because a raw runtime directory lacked sibling `scripts` modules, then because `runtime_identity` was called as a method rather than read as a property. Those exceptions are retained. The final tool stages the complete executable runtime and records the actual property value. It does not stub or bypass Racket.

## Measurement boundary

Use final-source evidence in `checks/after_final`, `checks/independent_after_v3`, and `checks/task_tests_final`. `checks/intermediate_after.zip` and preliminary override/test reports are intermediate and must not be attributed to the final source. Override-domain coverage is exhaustive only over declared finite controls at the recorded seed/index and difficulty bands. Default seeds, morphologies, and rival hypotheses remain sampled/finite. No training or hidden-solve improvement was measured.
