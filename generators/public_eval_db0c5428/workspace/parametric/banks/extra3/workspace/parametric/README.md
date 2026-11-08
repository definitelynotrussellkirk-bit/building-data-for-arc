# Central directional keys and selective radial reflections

`extension_policy=all_tiles` exactly equals the general public reference.
It reconstructs a missing 3x3 center from the inward-facing pixel of each of
eight surrounding 3x3 tiles, with the modal tile base in the center cell. Every
original tile reflects outward along the row/column axes on which it lies.
Input is preserved and new copies clip at canvas boundaries.

`largest_port_run` reconstructs the same center, then finds its unique largest
four-connected same-color nonbase component. Each of its cells addresses one
surrounding tile; only those tiles are reflected outward. Connectivity, not
aggregate color count, is the intermediate needed by the placement step.
Independent separated rings act separately. This generated multi-ring extension
is explicit; all four official labels use a single ring and were checked too.

The native folder is self-contained. The sampler uses cyan as the background,
complete 3x3 tiles, a unique modal base and a unique largest port run. Tile colors
and ornaments vary independently of the center's directional votes. Run lengths
2..5, rotations, translations, rectangular canvases, clipped copies, and one,
two or four rings occur. It does not claim arbitrary tile sizes, occluded rings,
overlapping projected rings, unrestricted parents or universal uniqueness.
The 30x30 query has four rings (288 foreground input cells), each with a different
winning run length; full canonical completion reaches all four boundaries.

Two-demo repair: the first lesson now has a two-cell winning run and explicitly
separates four-connectivity from diagonal-only connections. The second has a
four-cell winner. The former 3/2 lesson schedule admitted the executable
second-most-frequent-center-color shortcut; exact historical inputs and programs
are retained under checks for protected replay, not regenerated from changed code.
The repaired 2/4 schedule breaks it without increasing the demo minimum.

API supports independently requested demos 2..6 and query prefixes 1..4. Full
four-query banks are privately shuffled before prefixing. `public_turn` explicitly
whitelists demonstration input/output and the selected query input. Keep seeds,
settings, programs, answers, future queries and output-directory listings private.

Run from the packet outer folder:

    python3 review.py run python3 generators/public_eval_db0c5428/workspace/parametric/audit.py --out ../checks/public_eval_db0c5428/audit-new --seeds 20

Outputs must be new. The reusable audit checks count boundaries, setting-neutral
inputs, prefix stability, metadata invariance, exact public-file IDs, real Racket
parity, and the finite authored rival bank. Pair-instance counts include repeated
prefix requests. It grants no native owner acceptance or training admission.
