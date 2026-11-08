# Working notes: 62757098b2dd

## Current decision

Retain the production generator and selected canonical rule unchanged. The task-local native family is ready for owner source review under `workspace/parametric/`; it is not owner-accepted and has not been admitted to training.

## Family built

- Parameter: `palette_scope`.
- `local` is the exact canonical source, byte-for-byte: each solid gray rectangle reads its own four diagonal markers, erases them, and fills its four floor-split quadrants.
- `largest_rectangle` is the nearby composed branch: find the unique largest gray rectangle by area, read its ordered TL/TR/BL/BR marker palette, erase all markers, then use that selected palette for every rectangle.
- The sampler is setting-neutral and matched across settings, deterministic, global-RNG isolated, prefix-stable, and supports 2–6 demonstrations plus 1–4 queries. Four-query episodes use 16×20, 21×25, 27×29, and substantive 30×30 queries.

## Teaching and causal design

Every sampled scene contains exactly three rectangles. The unique largest rectangle is the middle row-major object, while the first object has a larger perimeter, so “first,” “largest perimeter,” “last,” “smallest,” local palettes, marker retention, ceiling splits, and anchor-only painting are executable rivals rather than aliases. A bounded demonstration-only audit over seeds 0, 17, and 97 leaves no rival that fits the demonstrations and changes a query answer.

The required sequential dependency is: A selects the unique largest rectangle and reads its ordered marker palette; the intermediate records the source rectangle, areas, bounding box, and palette; B fills all rectangles using that palette. The protected counterfactual selects the first rectangle instead and changes the final grid. Evidence is in `checks/62757098b2dd/causal/`.

## Verification retained

- Focused task-local suite: 22 passed.
- Full changed-target task suite: 28 passed.
- Three complete Racket programs passed strict one-form parsing.
- Authoring preflight: 4 setting/seed jobs, 40 protected-Racket evaluations, passed.
- Causal witness: protected intended/counterfactual replay, `reviewer_replayed`.
- Public projection: 4 episodes, 16 one-query views; 24 private-field invariance checks and 4 visible-change controls passed.
- Source inventory: `workspace/parametric/evidence/manifest.json`.

A final contract pass found and repaired an initial 3-demo minimum; the current adapter and promotion contract now support the required 2–6 range, and every source-bound receipt was regenerated after that edit.

## Next owner action

Review the parameter semantics and exact source, replay the packaged qualification and causal witness, then run native qualification and acceptance on the integrated bytes. Preserve `local` as the canonical default. Owner acceptance and training admission remain pending.
