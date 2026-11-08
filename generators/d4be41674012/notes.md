# Working notes: d4be41674012

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 canonical repair and parametric review

- The retained generator modeled hole-count sorting and horizontal packing, but
  the selected rule sorts objects by left edge, transposes each crop, and stacks
  the pieces vertically. Rebuilt `generator.py`, summary, mirror, controls and
  focused tests around the selected authority. All four canonical pairs now
  match, and representative generated boundary scenes replay through protected
  Racket exactly.
- Removed fake palette/texture/density axes. Current observable controls are
  `grid_h`, `grid_w`, and `color_count`; generated scenes contain three separated
  asymmetric objects with unique left edges and outputs bounded by 30×30.
- Built `workspace/parametric/` with `transform=transpose|rotate_cw`. Inputs,
  ordering and packing are matched across settings; only the crop transform
  changes, and every retained object is constructive evidence against the rival.
- Supports 2–6 demonstrations and four prefix-stable queries. The final 30×30
  query uses five objects spanning both axes while keeping both packed outputs
  within ARC limits. Protected-Racket qualification uniquely identifies both
  settings from demonstrations and verifies every private label.
- Final author review added a RED→GREEN regression for a scene whose three objects
  were all transpose-invariant. `self_check` now requires at least one object to
  visibly change under transpose, matching the documented teaching invariant.
- Canonical repair and prototype remain reviewer-reported; the alternate rule is
  not owner-qualified, accepted, or admitted to training.
