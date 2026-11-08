# Working notes: bf47583ab6e3

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review review-666e86ed85a2b7e1 — native parametric family

- Preserved the byte-exact canonical plus-growth program and unchanged base `generator.py`.
- Added `output_mode={plus_union, component_boxes}`. The alternate grows all clipped cardinal pluses, computes 4-connected grown-mask components, then fills each component bounding box.
- Declared support: 2–6 demonstrations and exactly four controller-side queries; inputs are setting-neutral and prefix-stable.
- Constructive bent-chain demonstrations force components to merge only after growth, separating direct seed squares, seed-component boxes, global grown box, largest-component-only, and canonical-plus-only rivals.
- Bounded audit: 192 episodes / 320 distinct inputs / 32 protected-Racket evaluations / zero failures; substantive 30×30 case has eight seeds and 119 alternate-output cells.
- Authoring preflight and causal witness passed; the wrong-intermediate replay uses independent 3×3 seed squares and changes the final output. Public one-query projection, first-turn privacy, and hidden-field invariance checks passed.
- Current state is reviewer-ready only. Owner source review, native qualification, fresh acceptance, and training admission remain pending.
