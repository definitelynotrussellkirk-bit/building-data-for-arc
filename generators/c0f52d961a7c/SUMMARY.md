# c0f52d961a7c

A black grid contains one connected magenta (`6`) payload and one direction
marker. Marker colors encode a one-cell translation: `1=left`, `2=up`,
`3=right`, `4=down`. The output is a fresh black grid containing only the
translated payload; the marker is discarded.

Generator version: `3.0.0`. Canonical rule hash: `0f51670bbbc2`.

## Curriculum

Each four-example block exposes all four marker meanings. Marker placement is
intentionally anti-correlated with the commanded direction, so the plausible
shortcut “move the payload toward the marker” is contradicted rather than
reinforced. Half of the eight-index blocks use exact canonical canvas sizes;
the alternating half explores the full declared size range.

Live exact override axes:

- `grid_h`: `6..20`
- `grid_w`: `7..22`
- `payload_size`: `3..8`
- `marker_color`: `1|2|3|4`

Payloads are connected polyominoes with a one-cell border, so every direction
override is constructible without clipping. Unknown overrides and invalid
difficulty values are rejected.

## Contracts

The module provides keyed draw provenance, `observe_overrides`, `self_check`,
`strict_canonical_like`, a pure `rule_mirror`, semantic witnesses, explicit
rival rules, canonical shortcut probes, and four-demo lesson
identifiability. The Racket authority was reviewed and left unchanged.

The retained after battery is all green: 12/12 stages, including 600/600
strict semantic draws, 12/12 identifiable lessons, 55,620 accepted override
matrix draws with zero findings, and exact authority parity on all canonical
pairs.
