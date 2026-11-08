# Working notes: 729429f8ea2c

## Current decision

The production generator now has a strict consumed override contract and rejects
unknown keys. Declared `grid_h` and `grid_w` bounds work independently of the
difficulty band; degenerate textures honor their requested dimensions; and an
inapplicable `distractor_count` plus degenerate texture is rejected instead of
silently ignored. Ordinary examples contain one unique largest color-2 component
and one unique largest color-3 component plus 1–3 smaller disconnected
distractors of each color. Generation retries unless the intended
largest-component result differs from the normalize-all-cells shortcut, so the
selection clause is actually taught in every ordinary sample. The retained
override and largest-component findings are addressed by the new source and
focused tests. Their bundled review index remains byte-identical to the packet
baseline because retained evidence is outside the allowed return patch scope.

## Retained audit repair coverage

The patched source and focused tests cover all three retained return IDs:

- `review-8292552d8414577e:v0001`: strict override validation and a consumed AXES contract.
- `review-a2c266162772fd6b:v0001`: smaller disconnected distractors plus an explicit all-cells inequality teach largest-component selection.
- `review-9bf45b629fc1f96f:v0001`: both defects are reproduced by regression tests and repaired.

The owner should reconcile these historical statuses against the exact patched bytes during source review;
this authoring return does not rewrite `evidence/review_index.json` or claim owner acceptance.

The task-local parametric family adds `mode=parity_transform` while preserving
the exact canonical `mode=intersection` default. Step A computes the normalized
largest-component intersection and its parity. Step B rotates odd intersections
clockwise or reflects even intersections left-to-right. The first two demos cover
both branches, four queries are retained, and the final query is a substantive
30×30 case. A protected-Racket wrong-parity witness changes the output.

The strongest canonical shortcut is to normalize every cell of each source
color without selecting connected components. Protected Racket confirms that it
fits all four canonical demonstrations because each contains one component per
color. The repaired generator emits a concrete disagreement at seed 0,
sample 0, difficulty `medium`; the full exact input and both outputs are retained
in `checks/729429f8ea2c/shortcut-review.json`. A separate bounded receipt covers
400 ordinary cases across all difficulty bands and every 20×20 degenerate mode
in `checks/729429f8ea2c/stress.json`.

Authoring preflight, public projection, first-turn privacy, and causal replay
passed under `checks/729429f8ea2c/`. Owner source review, native qualification on
integrated bytes, and fresh acceptance remain required; no training admission is
claimed.
