# Hollow compass-tile completion

## Rule and scope
The general reference is inferred from all three supplied demonstrations and the
provided test gold. For each nonbackground hollow 9x9 motif, read its eight 3x3
tiles. The inward-facing corner/edge-center color from each tile populates the
corresponding compass position in the missing 3x3 core; the motif's modal color
fills the center. Reflect each tile into its next outward radial position, flipping
its row/column axis precisely when that direction component is nonzero. Preserve
all original cells. Background is the most frequent canvas color, lowest on ties;
modal motif ground uses the same tie rule. Clip an extension at the canvas edge.

This is a general geometry rule, not a lookup of supplied grids. Original-label
agreement does not prove a unique rule outside those examples. In particular,
tile size is deliberately fixed at the parent's 3x3; other tile sizes are not
claimed. Generated directional/asymmetric textures and multiple motifs are an
explicit extension of the admitted grammar. Motifs' 15x15 output regions are
disjoint, so paint order cannot resolve collisions accidentally.

## Native family
`extension_scope=all` is byte-identical to reference.rkt. `rarest_tip` measures the
eight tip-color observations per motif, retains every color tied for the smallest
positive count, and reflects only those tiles. The core and original ring are
preserved in either setting. The histogram is a genuine input-derived intermediate:
whole-pixel color counts are not interchangeable with semantic tip counts.

Sampler inputs are independent of settings. Two demos deliberately use distinct
histograms, including ties, and reverse numeric-color correlations. Texture counts
are independent of tip frequencies. Support is 2..6 demos and exactly four queries;
query bank is independent of demonstration count. Queries cover 15x19, 21x23,
15x30 and 30x30; the final case has four independent motifs spanning all quadrants.
Generate all four privately and shuffle before exposing one at a time.

## Implementation and evidence
The ordinary generator is standalone. Its native sampler.py resource is an exact
copy, tested for byte equality; this duplication avoids an out-of-resource runtime
import while preserving relocation. Python outputs are claims independently checked
by protected Racket. Task-local audit.py attacks 14 named policies from demos alone.
No universal identifiability is claimed. Authoring preflight, exact-source causal
replay, public exports, and tests are retained under checks/public_eval_db0c5428.
Owner registration, native qualification/acceptance, and training admission are
separate pending decisions. Shared authority is unchanged.
