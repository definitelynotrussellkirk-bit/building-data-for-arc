# 1b39c0e8ebc7

A grid contains one color-8 marker and one color-9 marker. Their signed row/column displacement is the operative vector. For every color-3 source, translate by that vector; when the landing cell is color 4, place color 7 at the landing coordinate in an otherwise all-zero output. Input cells are not copied into the output.

The repaired ordinary generator supports 8–30 rows and columns, exact signed vectors including all canonical magnitudes, 2–16 forward matches, 1–16 reverse-direction traps, and explicit unmatched source/target decoys. It validates every declared override rather than silently clipping or ignoring it. The reverse traps and unmatched cells make recolor-all-targets, marker-free, and wrong-direction shortcuts visibly incorrect.

The task-local native family adds one episode-fixed semantic parameter while preserving the exact canonical default:

- `vector_direction=forward`: use the exact 8→9 displacement and exact canonical Racket source;
- `vector_direction=reverse`: use the 9→8 displacement with the same translate/intersect/output operation.

Matched-input episodes support 2–6 demonstrations and exactly four distinct queries; the fourth query is a substantive 30×30 scene. This source is reviewer-ready for owner qualification/acceptance, not approved or training-admitted.

Kind: `per_puzzle`. Proposed version: `3.0.0`.
