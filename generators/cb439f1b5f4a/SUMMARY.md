# cb439f1b5f4a — header count repeats the whole body crop

Version: **3.0.0**. Kind: per_puzzle. Pinned Racket rule hash: **33d95b8e8c4d**.
The Racket authority is unchanged by this repair.

Count color-1 cells in row 0 to obtain K. Below row 0, take the bounding
rectangle of all nonzero cells in the one connected prototype. Preserve every
color and every zero inside that rectangle, including blue body cells. Repeat
that crop K times horizontally with exactly one zero column between copies.
For a crop of H rows by W columns, the output is H by K*W + K-1.

Generated controls are exact: grid_h 4..12, grid_w 6..15, K 1..4,
prototype_color 2..9, and texture solid, notched, multicolor, or blue_motif.
The prototype_color is the row-major first nonblue body cell. Every advertised
joint setting is constructed without silently shrinking a requested control;
the body width is chosen to keep the output within 30 columns. Unknown controls
and invalid values are rejected explicitly.

Default five-input cycles contain two compact monochrome examples, one taller
multicolor example, and two taller examples with blue inside the body. Four
demonstrations plus one query cover the cycle; the declared semantic hook must
also pass on the actual assembled lesson. This schedule supplies counterexamples
to seven canonical-fitting shortcuts and nine additional rival rules. Claims
about query rotation apply to the default consecutive assembly and the declared
rivals; arbitrary override mixtures are not certified.

The validator intentionally accepts a wider lawful domain than the sampler,
including singleton crops, K=1, all-blue bodies, and body cells immediately below
the header. Non-solid generated shapes have an outer row-and-column spine;
multicolor sampling uses two body colors. Many other lawful shapes and palettes
are not sampled. See notes.md and workspace/ for evidence and limitations.

Approval is derived by the catalog from current code and retained evidence.
The review retains a strict shared-linter warning requiring maintainer disposition;
this description is not an approval or a training-admission decision.
