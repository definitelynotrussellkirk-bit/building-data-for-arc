# f191c16f6179

Version `3.0.0`. Kind: `per_puzzle`. Canonical Racket rule pin:
`f7b2de2c3ed0`. The generator returns inputs only; the unchanged canonical
Racket rule supplies labels.

## Rule and accepted inputs

Start with a rectangular grid whose background is 0. Group nonzero cells by
color, preserving each color's first occurrence in row-major input order. A
color is eligible only when it occurs exactly twice, its endpoints lie on a
45-degree diagonal, their row/column span is at least two, and every interior
cell is 0 in the **original input**. Fill that diagonal in the endpoint color.

Both diagonal orientations are supported. Crossing diagonals are independently
eligible from the original grid, and the later color in input reading order
wins at a shared gap cell. Numeric color order and checking a progressively
painted grid are different rules.

Non-diagonal pairs, blocked diagonal pairs, singleton colors, and colors with
three occurrences can remain as distractors. At least one eligible bridge must
remain. `self_check` and `strict_canonical_like` accept that endpoint/guard
domain and reject malformed grids, noninteger pixels (including booleans),
colors outside 0..9, dimensions outside 5..16, more than three occurrences of a
color, and inputs with no eligible bridge. Difficulty does not change the
accepted domain. These size and occurrence caps describe the generator's
domain; they are not limits on the unchanged Racket rule's general behavior.

## Exact controls

| Override | Accepted values | Observed meaning |
|---|---|---|
| `grid_h` | Integer 5..16 | Number of rows |
| `grid_w` | Integer 5..16 | Number of columns |
| `pairs` | Integer 1..5 | Number of nonzero colors occurring exactly twice |

All advertised tuples work jointly in every difficulty band. `None` leaves an
axis unset. Booleans, floats, strings, unknown keys, and out-of-range values
raise an error. `observe_overrides(grid)` reconstructs all three values from
pixels. A guard example's three-occurrence color does **not** count as a pair.

The previously inert `palette_kind`, `palette_size`, `n_distinct_colors`,
`position_bias`, `density`, and `texture` arguments are removed and rejected.
The old `pairs=6..8` range is also removed. Five is the maximum number of
disjoint gap-containing diagonal paths possible on a 5×5 clear input; the new
range has a constructive realization on the smallest advertised canvas.

## Default curriculum

`EXAMPLES_NEEDED = 3`. The default schedule is determined by
`(seed + sample_index) % 3` in all difficulty bands:

| Residue / profile | Default construction |
|---|---|
| 0 / `core` | Two disjoint clear bridges of opposite slopes on 7×7 or 8×8, or two such bridges plus one non-diagonal pair on 9×9 |
| 1 / `guard_ascending` | Four or five paired colors, a separate three-occurrence color, and a crossing whose later input color is numerically larger |
| 2 / `guard_descending` | The same guard coverage, with the later crossing color numerically smaller |

Guard canvases default to independently drawn dimensions in 8..10 for easy,
9..12 for medium or unset difficulty, and 11..16 for hard. The compact profile
is retained in every band, including hard. Geometry and palette have separate
keyed RNG streams. Endpoints, slopes, lengths, canvas dimensions, and placement
vary; examples are not limited to recolorings of a fixed drawing.

Each comprehensive guard input includes two crossing eligible bridges, a
blocked diagonal pair, and a clear non-diagonal pair of span at least two.
The three-occurrence color has two clear diagonal endpoints and a third point
off their entire diagonal. That third point blocks a *different* paired color,
so rejecting the triple cannot be explained merely by a blocked triple gap.
A fifth paired color may be another clear bridge or an additional inactive pair.

Pinned controls take precedence over these defaults. A guard slot with
`pairs=1..3` uses the simpler compact construction, with exactly the requested
number of paired colors. That deliberate override-specific restriction means
such lessons need not teach the full guard curriculum. Shape overrides alone
preserve comprehensive guards even on 5×5. Pinned counts four and five remain
fully supported in the compact slot as clear disjoint bridges.

## Placement and semantic checks

An immutable cache enumerates all diagonal segments of span at least two for
the requested shape. Bounded searches construct a complete layout while
protecting meaningful gaps. Explicit 5×5 constructions provide a fallback for
every advertised count, with reflections, transposition, scaling, and padding
for larger shapes. Generated grids are checked after painting: pair counts
must match exactly, a bridge must remain eligible, and every comprehensive
guard must visibly refute its claimed rival. The fallback passes the same
checks; a failed verification raises rather than returning fewer pairs or
weaker guards.

Nine pure rival predictors and nine witnesses cover identity, either single
slope, connecting non-diagonal pairs, ignoring blockers, ignoring exact-two
cardinality, testing eligibility in painted output, and both numeric color
orders. Witnesses check a real predicted pixel disagreement as well as the
relevant structure. Five canonical-fitting guard/order shortcuts are declared.
These diagnostic predictors do not supply dataset labels.

`lesson_identifiable(demos, query)` checks the supplied labeled pairs: a rival
that fits every demonstration and changes the query yields a reason string.
The intended lesson policy is three consecutive demonstrations followed by the
query. This is a finite-rival contract, not a proof against every possible
alternative rule. Arbitrary query rotations are not claimed safe: holding out
the only example of one crossing order can leave the corresponding numeric
order rival unrefuted. Rotation evidence must be reported separately.

Approval remains a property of the catalog's source-bound review evidence;
these declarations do not grant approval.
