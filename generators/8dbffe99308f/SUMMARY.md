# 8dbffe99308f

Generate a 6×6 through 10×10 zero-background square with exactly 4–10
nonzero markers in four to six foreground colors. The teaching curriculum
cycles through above-side, below-side, anti-diagonal-axis, and unequal
pre-filled mirror-pair scenes. At most one anti-diagonal mirror pair is
pre-filled, and when present its colors differ so immutable-snapshot swap
semantics are visible.

Rule: overlay the input with its reflection across the anti-diagonal `/`.
For every nonzero input cell at `(r, c)`, write its original color to
`(n-1-c, n-1-r)` while retaining the original. The reflection is computed
from an immutable input snapshot, so two occupied mirror partners exchange
colors rather than one overwriting both positions.

The six-slot schedule alternates ordinary and conflict profiles. Therefore
every normal three-demonstration window contains a conflict witness, and every
four-pair window contains two, allowing any one pair to be rotated into the
query position while refuting the declared `fill_empty_only` shortcut.

Kind: `per_puzzle`. Selected version: `3.1.0`. Canonical rule hash:
`e248d283a2c2`. Approval remains derived by the catalog from current code and
retained evidence.
