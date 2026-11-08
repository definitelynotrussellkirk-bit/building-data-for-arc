# 694d3ee0b12a

A zero-background grid contains **two or three independent 7×7 hollow color-7 frames**. Each frame is a local workspace:

- color 2 cells on the left inner axis select rows;
- color 3 cells on the top inner axis select columns;
- one other nonzero interior color is that frame's fill key.

The output preserves the input and paints every selected-row × selected-column intersection with the **key color from the same frame**. Frames must be solved independently.

The selected generator is version `3.0.0`, pinned to rule hash `c13ecc4348dc`. It schedules six canonical-scale two- and three-frame layouts, varies one to three row and column markers per frame, uses distinct local key colors, and deliberately moves at least the first frame's key away from the canonical bottom-right interior location. This refutes three declared rivals: a fixed bottom-right key, a global key reused across frames, and transforming only the first frame.

Contracts include a strict multi-frame `self_check`, a Python `rule_mirror`, canonical-shortcut and semantic-rival declarations, witness functions, lesson identifiability checks, override observation, and deterministic destructive mutation fixtures. The generator intentionally remains narrow to the demonstrated grammar: exact 7×7 frames, two or three frames, one unambiguous key color per frame, and no unrelated distractors.

Kind: `per_puzzle`. Imported version replaced: `2.0.1`. Current version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence; this review does not upgrade approval.
