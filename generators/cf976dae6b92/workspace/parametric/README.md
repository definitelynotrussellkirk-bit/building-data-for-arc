# Relay-policy family

`relay_policy=fixed_4` is the exact canonical `2 → 4 → 3` rule.
`relay_policy=nearest_to_2` computes the uniquely nearer of colors 3 and 4 by
Manhattan distance from color 2, then routes `2 → selected relay → other`.
Every leg moves horizontally first and vertically second. The input grammar
excludes distance ties, keeps exactly one marker of each color, supports 2–6
demonstrations, and always materializes four distinct queries.

The bundled adversarial probe uses a finite, declared hypothesis class.  The
`fixed_4` two-demo audit attacks the declared nearest/farthest alternatives,
Euclidean and Chebyshev shortcuts, and route-construction errors.  Coordinate-only
selectors are not claimed to be globally falsifiable from the same two shared
scenes; the probe records that limit explicitly.  The `nearest_to_2` audit also
attacks row/column, absolute-extreme, and coordinate-sorted-route shortcuts.
