# 9900de625ddd — every monochrome 3×3 window contributes its center

Generator version: `3.0.1`. Kind: `per_puzzle`. The selected Racket authority is
unchanged and pinned by `RULE_HASH = f64febd0911d`.

## Rule and teaching repair

Scan **every** nonzero, monochrome, filled 3×3 window. Place its color at its
center in an otherwise zero grid of the same dimensions. Overlap is intentional:
a filled 4×4 square yields a 2×2 square of output cells, and a filled 5×5 square
yields a 3×3 square. A mixed-color or incomplete window yields no center.
Generation returns inputs only; the existing Racket runtime provides labels.

The previous input distribution contained isolated 3×3 squares exclusively.
It could not distinguish the window rule from reducing objects to one point,
greedily finding disjoint windows, ignoring colors, or checking only some
neighbors. The revised distribution includes larger solid rectangles, a positive
nonrectangular overlap patch, and contrasting near misses while retaining all
five canonical size/palette profiles.

## Sampled input domain

All grids have dimensions 5..24, background zero, and 1..6 visible foreground
colors chosen without fixed color roles from 1..9. They contain 1..6 separated
nonzero patches and at least one actual matching window. Distinct patches have
a background gap, including diagonally; patches may touch a canvas boundary.

Patch grammar: complete monochrome rectangles with each dimension 3..5;
monochrome 4×4 squares with one corner missing;
monochrome 2×2 squares; 3×3 squares with one zero hole; full 3×3 squares whose
colors occur eight times and once; and a complete 3×3 square with one attached
tail cell. Holes, small squares and tails occur as optional extra contrast
patches. Geometry and foreground colors vary independently of their role.

This is a bounded teaching domain. It excludes zero-match inputs, canvases
without background, larger or arbitrary connected shapes, touching patches,
and more than six patches or foreground colors, even though the Racket rule
has meaningful behavior on many such grids. `self_check` validates this stated
grammar, rectangularity, types, bounds, colors, separation and a positive match.
`strict_canonical_like` uses that same task domain; its declared floor is 1.0.
It does not mean every input has canonical dimensions or isolated 3×3 objects.

## Exact public controls

| Control | Domain | Observable meaning |
|---|---|---|
| `grid_h`, `grid_w` | Integer 5..24 | Returned dimensions |
| `blocks` | Integer 1..6 | Number of separated nonzero patches, including decoys; not the number of matching windows |
| `n_distinct_colors` | Integer 1..6 | Distinct nonzero colors actually present |
| `texture` | `3x3`, `overlap`, `contrast` | Patch family recoverable from pixels |

`3x3` produces only filled monochrome 3×3 patches. `overlap` always includes a
4×4 patch and may add other complete 3..5 by 3..5 rectangles. When `texture`
is unforced, the first 4×4 has one corner missing: its fifteen cells contain
three valid windows in a nonrectangular component. This distinguishes the
rule from eroding only complete rectangular components. Explicit
`texture="overlap"` keeps a complete 4×4 patch, so the original full-square
case remains directly reachable. `contrast` always includes a valid 3×3
patch, a full 3×3 patch with a recolored corner, and
another with a recolored edge midpoint; extra patches vary within the grammar.
Those two separate decoys distinguish checking orthogonal neighbors from
checking diagonal neighbors, and reject the approximate eight-of-nine rule.

The exact-color constraint is `n_distinct_colors <= blocks`. Contrast requires
`blocks >= 3` and `n_distinct_colors >= 2`. For its constructive layout, the
sampler reserves square cells of side `s=3` (`3x3` or `contrast`) or `s=4`
(`overlap`) with one-cell gaps. A requested count must not exceed
`floor((grid_h+1)/(s+1)) * floor((grid_w+1)/(s+1))`. This is a conservative
packing policy, not a geometric impossibility claim about every alternative
arrangement. Random slot sizes, margins, slot assignment and within-slot
positions vary the final layout. No patch is silently dropped after placement.

Each valid scalar control is constructible in every difficulty band. When
some axes are pinned, free axes are chosen compatibly; impossible combinations
raise `IncompatibleOverrides`, a `ValueError` containing `incompatible_axes`.
`observe_overrides(grid)` reconstructs all five controls from returned pixels.
Unknown names, booleans and strings in integer axes, null controls and values
outside the declared domains are rejected.

The formerly inert `palette_kind`, `palette_size`, `position_bias` and `density`
axes are removed. The old palette and degenerate texture names are removed.
`n_distinct_colors` is now an exact 1..6 foreground count instead of the unused
1..9 promise. A 4×4 block is an ordinary lawful overlap case, not a negative
fixture. Retired names fail explicitly rather than being silently ignored.

## Consecutive-demonstration schedule and its limit

The unforced schedule is `(seed + sample_index) % 3`:

| Residue | Declared profile | Guaranteed teaching content |
|---|---|---|
| 0 | `canonical` | Isolated 3×3 patches; one of the five canonical dimension/palette profiles |
| 1 | `overlap` | A corner-notched 4×4 patch demonstrating three overlapping centers in a nonrectangular component |
| 2 | `contrast` | Valid target plus corner-recolored and edge-recolored decoys |

Thus any three consecutive unforced demonstrations contain both distinguishing
profiles. Canonical profile dimensions and palette cardinalities are retained
in every band. Easy/medium/hard change soft preferences for object count and
canvas size on the expanded profiles; they do not remove public axis values.
All randomness comes from the keyed generator context. There is no global RNG,
mutable schedule state, cached sample list or generated-output cache.

The ten executable `CANONICAL_SHORTCUTS` / `LESSON_COMPETITORS` are exact-3×3
components, one center per component, one center per color, occupancy windows,
cross centers, diagonal centers, at-least-eight matching cells, bounding-box
erosion, erosion restricted to complete rectangular components, and greedy
disjoint windows. Each fits all five original pairs. Named
witnesses claim specific disagreements and are checked against Racket outputs
by the semantic gate and the source-bound task-local probe.
`lesson_identifiable` reports every rival that survives the demonstration
outputs; it does not use query labels to claim that the demonstrations taught.

This is elimination of a finite declared rival set, not unique induction among
all programs. Fewer than three demonstrations, nonconsecutive/reordered draws,
or public overrides need not retain the teaching guarantee. The profile cycle
also creates a detectable curriculum regularity. Arbitrary-shape coverage and
alternative rivals remain explicit limits, with actual lesson/sample counts
recorded in the review evidence rather than inferred from witness frequency.

No training approval or safety label is changed by this repair or its checks.
