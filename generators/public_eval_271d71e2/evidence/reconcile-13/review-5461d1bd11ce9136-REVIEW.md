# ARCpuzzles public-evaluation creation review

Assignment: `review-5461d1bd11ce9136`

Both assigned public parents now have complete, task-local authoring builds. They are **reviewer-ready and owner-pending**. This return does not claim owner registration, native qualification, acceptance, measured training benefit, universal identifiability, or training admission.

## `public_eval_271d71e2`

### Canonical parent

Implemented the general rail-box transformation in Python and protected Racket:

1. Detect each black-framed box with gray/orange interior and its pair of parallel maroon rails.
2. Move the box toward the farther rail by `min(rail distance, remaining gray cells)`.
3. Convert one additional interior cell to orange per movement step using the direction-specific sweep order.
4. Reconstruct the moved box and the remaining rail geometry.

The default `all_boxes` program is byte-identical between `reference.rkt` and `workspace/parametric/canonical.rkt` and matches all supplied training labels plus private test gold.

### Parametric branch and dependency

The alternative `post_orange_winner` setting first performs the full canonical motion, then selects the stable first box with maximum **post-motion** orange count and saturates its remaining gray interior.

- **Step A:** move every box and compute actual post-motion orange counts.
- **Intermediate:** shifted box records, actual movement amounts, and post-motion counts.
- **Step B:** select the post-motion count winner and saturate it.
- **Counterfactual:** `wrong_order.rkt` selects from pre-motion counts instead. The protected-Racket replay changes 6 final cells.

The two-demo curriculum constructively distinguishes the two admitted settings and eight declared shortcuts: pre-motion selection, first/last scan order, most-gray, largest-gap, no-motion, uncapped full-distance motion, and saturate-all. A discovered row-order alias was repaired by requiring the true winner and the cap witness to occupy the two middle scan positions. Scene construction is memoized internally but returns fresh mutable grids, preventing caller mutation from contaminating later episodes.

### Verification

- Protected-Racket authoring preflight: passed, four setting/seed jobs, exactly one setting survivor per lesson.
- Official staged task tests: 19 passed, 0 failed.
- 64-seed bounded audit: 640 episodes, 5,120 labeled-pair checks, 640 substantive boundary queries, 640 distinct audit inputs, eight rivals, zero failures.
- Protected-Racket audit executions: 24.
- Public export audit: 16 hash-named one-query files; settings, programs, answers, future queries, and private metadata masked; deliberate answer leak rejected.

## `public_eval_e376de54`

### Canonical parent

Implemented the general parallel-segment normalization rule in Python and protected Racket:

1. Identify the dominant odd family of parallel monochromatic segments.
2. Infer whether their starts or ends share the common perpendicular alignment.
3. Sort the segments by spatial offset.
4. Use the spatially middle segment's length as the target.
5. Resize every segment to that length while preserving the aligned endpoint and unrelated clutter.

The default `normalize` program is byte-identical between `reference.rkt` and `workspace/parametric/canonical.rkt` and matches all supplied training labels plus private test gold.

### Parametric branch and dependency

The alternative `contact_relay` setting normalizes first. Exactly one newly created free endpoint then contacts an isolated color-4 receiver; the contacted segment color is relayed to all receiver and payload cells.

- **Step A:** normalize the family to the spatial-middle target length.
- **Intermediate:** normalized segment cells and the unique color whose new endpoint contacts the receiver.
- **Step B:** recolor all color-4 receiver/payload cells with that contacted color.
- **Counterfactual:** `wrong_order.rkt` inspects contacts before normalization and obtains no relay color. The protected-Racket replay changes 5 final cells.

The generator reserves every declared rival's maximum-length envelope so min/mean/median/max/first/last hypotheses are total rather than “refuted” by exceptions. It also reserves both current and future segment footprints before placing the remote payload. A discovered maximum-color shortcut at seeds 49 and 102 was converted into a regression and repaired constructively by preventing the relay-carrying segment from also being the numeric maximum color.

### Verification

- Protected-Racket authoring preflight: passed, four setting/seed jobs, exactly one setting survivor per lesson.
- Official staged task tests: 21 passed, 0 failed.
- 64-seed bounded audit: 640 episodes, 5,120 labeled-pair checks, 640 substantive boundary queries, 639 distinct audit inputs, 14 rivals, zero failures.
- Protected-Racket audit executions: 24.
- Public export audit: 16 hash-named one-query files; private fields invariant; deliberate answer leak rejected.

## Shared deliverables

Each target includes:

- `generator.py` with the required literal public rule ID.
- General `reference.rkt` and byte-identical task-local canonical source.
- Native `adapter.py`, `promotion.json`, alternative and wrong-order Racket programs.
- Deterministic matched-input generation with 2–6 demonstrations and exactly four prefix-stable novel queries.
- One-query-at-a-time public projection with independent presentation order and no total-query hint.
- Substantive 30×30 cases.
- Focused regression tests, reusable bounded audit runner, source/evidence manifest, protected-Racket preflight, finite rival audit, and replayable sequential witness.

## Limits and owner handoff

The finite rival sweeps are strong bounded checks, not proofs that no unenumerated hypothesis can fit the lessons. Supplied private test gold was used only for authoring verification and is not exposed in public challenge files. The owner must register and review the exact sources, run native qualification unchanged, and separately accept both families before either counts as accepted coverage.

## Clean-room replay

The packaged source patch was applied with strict whitespace checking to a complete fresh extraction of the uploaded packet (`SHA-256 974e90b240b3989d64a57931ff133bf1c4a9f1f8b017b1bf086a34c724a37119`). All **29 patched paths** matched the completed working source byte-for-byte.

Using only that fresh extraction and its newly installed bundled Racket runtime:

- The combined focused suite passed **40/40 tests**.
- All eight changed Python sources compiled.
- Both protected-Racket authoring preflights passed again, four jobs per family.
- Both complete 64-seed audits passed again.
- **48 deterministic audit artifacts** reproduced byte-for-byte, including all **32 public challenge files**, claims, Racket-label receipts, public/privacy checks, and both causal witnesses and replays.

The compact replay receipt is `checks/final/clean-replay.json`; the fresh test output is `checks/final/clean-replay-tests.log`. This remains authoring verification, not owner qualification or acceptance.

