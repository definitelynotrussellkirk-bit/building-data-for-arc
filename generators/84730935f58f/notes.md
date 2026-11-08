# Working notes: 84730935f58f

## Current design

The canonical default remains the exact selector-controlled union rule: selector 1 chooses the cardinal plus stencil, selectors 2–7 choose the diagonal X stencil, every non-selector nonzero cell is a seed, and the output is a fresh zero grid painted cyan where any selected stencil lands.

The nearby native setting is `render_mode=overlap_highlight`. Step A expands every seed with the selector-chosen stencil while retaining per-cell hit multiplicity. The intermediate is that coverage-count map. Step B paints count-one cells cyan (8) and count-two-or-more cells red (2). The hidden setting is fixed for an episode and the two settings receive matched inputs for equal seed/count requests.

## Repairs and reversals

- Repaired the ordinary generator's all-PLUS four-demonstration failure by alternating plus/X selectors by `sample_index`; every consecutive four samples, and every four-of-five query rotation, now contains both branches.
- Corrected the textual rule: the canonical output is a fresh grid and does **not** preserve the selector.
- Made `height`, `width`, `mode`, `num_seeds`, `n_distinct_colors`, `palette_kind`, and helpful `texture` controls observable and strict; unknown or malformed controls now fail loudly.
- Added a protected canonical Python mirror, structural self-check, safe selector halo, deterministic fresh outputs, and task-local tests.
- Rejected an initial oversized adversarial sweep as poor evidence after it exceeded the bounded runtime. Replaced it with a targeted audit over selector, render, seed-center, crossed-control, boundary, and size shortcut classes.

## Bounded evidence and remaining limits

The final bounded audit covered 768 ordinary-generator draws, 144 parametric episodes / 1,104 labeled pairs, 144 minimum lessons, and 24 crossed controls. Within those samples every minimum lesson identified the declared setting and refuted the declared wrong-render and fixed-stencil rivals; no universal uniqueness claim is made. Protected authoring preflight executed 32 Racket labels, and the causal witness protected-replayed both the qualified program and a wrong-intermediate counterfactual. Public serialization was checked separately, including first-turn invariance and five rejection controls.

Owner source review, native acceptance, and training admission remain pending. The next useful action is owner replay of the exact packaged source, qualification, and causal witness; do not infer approval from this reviewer-ready return.
