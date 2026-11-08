# Working notes: 74a2d06b72b1

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-26 — reviewer build `review-01a2cf183a5aabf8`

- Reproduced the retained teaching defect: seed 9 produced three demonstrations
  with one marker, so the wrong “always choose the outermost frame” rule survived.
- Repaired the ordinary generator with a deterministic selector-coverage schedule
  while preserving explicit `select_idx`; invalid overrides and exhausted layout
  attempts now fail rather than silently returning an unrelated grid.
- Closed the retained semantic-gate failure with an independent `rule_mirror`,
  strict-manifold hook, five branch/counterexample witnesses, and three named
  lesson rivals (`always_outermost`, `always_innermost`, and
  `fill_selected_interior`). The packet semantic gate measured 600/600 strict
  draws, verified every witness/rival claim, and found all 12 sampled lessons
  plus 48 query rotations identifiable.
- Added the exact-default `frame_order=outer_first|inner_first` native family.
  Step A uses marker count and order to select an input-dependent frame; step B
  fills that frame’s ring relative to the next inner frame.
- Bounded audit covers seeds 0–127, all declared count corners and both settings;
  owner source review, native qualification and fresh acceptance remain required.
