# 1d9a320d33c0 — Domino Square Grow

A zero-background grid contains two to four same-color dominoes in distinct ARC colors. Every ordinary lesson contains at least one horizontal and one vertical domino. A horizontal domino copies its color into the two cells directly below; a vertical domino copies its color into the two cells directly right. Each object therefore becomes a solid 2×2 square while the original cells remain.

## Input grammar

- Grid height: 7..10; width: 8..12.
- Domino count: 2..4, with colors sampled without replacement from 1..9.
- Every object is exactly one straight, adjacent two-cell component.
- Input dominoes never touch orthogonally, and their eventual 2×2 footprints never overlap.
- Diagonal contact is lawful and deliberately represented because it occurs in the canonical examples.
- Growth targets are in bounds and zero.

## Curriculum

Four of every eight sample-index residues use one of the four canonical `(height, width, count)` profiles: `(7,9,3)`, `(8,8,3)`, `(7,10,3)`, or `(8,9,3)`. The other residues provide bounded scale/count extrapolation. Easy draws use two or three dominoes, medium draws two to four, and hard draws three or four. Sample-index parity alternates between diagonal-contact scenes and fully separated scenes.

Both orientations are present in every generated input. This prevents a horizontal-only or vertical-only solver from succeeding on an ordinary lesson.

## Contract and controls

The only public override axes are the exact observable controls `grid_h`, `grid_w`, and `domino_count`. Unknown, removed, mistyped, and out-of-range controls fail loudly. `RULE_HASH = "528b7a20c766"` pins the selected canonical Racket authority.

The generator provides a task-linked `self_check`, `strict_canonical_like`, a Python rule mirror, two named rival rules, witness-to-rival claims, and lesson identifiability checks. Named malformed examples remain private negative fixtures and are not part of the ordinary override domain.

Kind: `per_puzzle`. Current version: `3.0.0`.
