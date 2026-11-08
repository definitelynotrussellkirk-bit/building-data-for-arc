# 1198580cc354 — Top-row beam fill

Every nonzero top-row seed projects its own color down its column. A color-9
blocker is preserved and stops only that column; an unblocked beam reaches the
bottom.

Selected generator version: `2.0.0`. Canonical rule hash: `018c975f3e7f`.

The ordinary schedule cycles all four canonical height/width/palette profiles
plus two broader profiles. Every generated input has 2–4 distinct seeds,
contains color 1, and includes both blocked and unblocked seed columns. The
public controls are exactly recoverable: `grid_h=7..10`, `grid_w=7..12`, and
`seed_count=2..4`.

Executable review hooks cover three plausible rivals: ignoring blockers,
treating the earliest blocker as a global stopping row, and ignoring color 1.
`EXAMPLES_NEEDED = 3`; every ordinary example independently refutes all three.

Kind: `per_puzzle`. Approval remains catalog-derived from current code and
retained evidence.
