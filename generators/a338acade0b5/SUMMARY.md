# a338acade0b5

The input is a 5..14 by 5..14 background-0 grid containing exactly two equal
nonzero endpoint cells. The endpoints are horizontally aligned, vertically
aligned, or separated along a 45-degree diagonal. Return a separate one-row
bar of color 8 whose width is the inclusive Chebyshev span between endpoints:
`max(abs(dr), abs(dc)) + 1`.

The generator exposes exact controls for segment length (2..14), orientation,
and endpoint color. Its six-slot alternating lesson schedule covers both diagonal slopes and gives
every four-pair window two vertical cases, so every three-demonstration/one-query rotation retains a counterexample to the
canonical-supported `column_span_only` shortcut.

Kind: `per_puzzle`. Generator version: `3.0.0`. Canonical rule hash:
`5661890ac5fd`. Approval is derived by the catalog from current code and retained
evidence.
