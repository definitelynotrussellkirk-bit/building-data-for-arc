# Post-repair solve work log

## Revision 1

From the three visible training pairs, each non-empty row contains a prefix of a
horizontal repeating sequence anchored at column 0. The prefix can include zeros,
so zeros cannot be treated as margin. Its endpoint is the row's rightmost
non-zero cell. Infer the shortest period consistent with every cell from column
0 through that endpoint, then tile the period to the full row width. Leave fully
zero rows unchanged.

Implementation scans candidate periods from 1 upward, ensuring the chosen period
is the smallest one supported by the visible prefix. This handles partial final
repeats and leading zero residues rather than copying the whole visible block.
