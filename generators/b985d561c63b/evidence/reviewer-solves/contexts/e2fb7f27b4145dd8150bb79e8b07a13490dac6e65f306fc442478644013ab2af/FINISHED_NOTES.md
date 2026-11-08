# Final-source solve work log

This is a reviewer-authored work-log summary, not a token-level model trace.
Earlier exposure: yes, including generator repair, canonical rule inspection
before solving, and the earlier exposed solve on the preceding generator
hash. That earlier episode remains under `checks/prior-solve-593540b0/`.
The final generator change required a newly prepared episode with new source
identity. During this solve I read only its visible `challenge.json`; I did
not consult generator/reference source, private answers, or the earlier solve
files and explanations.

## Revision 1

The first visible example copies a 3x2 two-color source into three gray 3x3
targets. Its empty lower-left source corner is copied as zero, and the extra
gray column remains. The middle example copies a dense 4x3 pattern into two
congruent targets. The third copies a 3x2 source with an empty top-right corner
and leaves two surplus gray columns unchanged.

Implemented the complete crop bounded by the nonzero non-gray cells, including
any zeros in that rectangle. Find each original gray component using orthogonal
connectivity, then paste the crop at that component's top-left corner without
clearing cells outside the stamp. Source location and source colors are read
from the input. The masked inputs visibly fit the same structure.

No failed solve or deliberate negative was manufactured. This is one genuine
revision for the final source. The checker reports visible-example correctness
and execution only; masked-query correctness remains for maintainer scoring.
The solver assumes stamps fit inside the grid, as in the visible examples and
masked inputs. It does not claim to resolve unsupported multiple-source scenes.

## Metadata recovery

The first check of this same final-source program passed 3/3 visible examples,
but finish encountered a stale prior-source FINISHED_NOTES file and attempt.
The mixed public state is preserved under checks/solve_refresh_stale_state/.
This exact final-source challenge was officially prepared again, and the same
already-authored program is rechecked here without another model revision.
This recovery is not a new independent or blind solve, and no private labels
were inspected.
