# Working notes: 80bd3177b03c

## 2026-10-24 review-d6519a124d84a876

### Finding

The canonical rule connects exactly-two same-color markers on either a clear row or a clear column. The version 2.1.0 sampler nevertheless emitted horizontal pairs only: the retained audit counted 1,928 horizontal and zero vertical pairs across 600 generated inputs. Its `position_bias` override was inert, so a horizontal-only shortcut could fit every generated lesson.

### Repair

Version `2.2.0` provides three exact, observable position families:

- `horizontal_row_pairs`
- `vertical_column_pairs`
- `mixed_pairs`

Without an override, sample indices 0, 1, and 2 schedule those families in that order. Constructive backtracking reserves complete output segments, uses distinct rows/columns for parallel pairs, and prevents cross-color segment intersections. The public observer recovers the selected family and pair count from the grid. Unknown controls and impossible combinations fail closed.

The metadata was narrowed to controls this generator actually implements (`grid_h`, `grid_w`, `n_pairs`, `position_bias`, and explicit textures), removing the prior inert palette/density claims. An exact Python `rule_mirror` was added for canonical and generated-case checking.

### Verification

- New focused task suite: **11 passed** after a nine-failure RED run.
- Protected-Racket probe: **30/30** generated cases matched the Python mirror (10 per position family).
- Canonical authority: **5/5** labeled pairs matched both the Python mirror and protected Racket.
- Default lesson schedule observed exactly `horizontal_row_pairs`, `vertical_column_pairs`, `mixed_pairs`.
- Evidence: `WORK/checks/peer-80bd3177b03c/probe.json` and `command.json`.

### Remaining bounded gap

Standard lessons still do not teach the rule's negative branches: blocked paths, singleton colors, colors occurring more than twice, or unaligned two-cell distractors. The canonical examples exercise those cases; a future support-expansion ticket should add them without weakening the strict standard-profile observer.
