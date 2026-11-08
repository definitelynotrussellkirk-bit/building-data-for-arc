# Post-repair visible-example solve

Earlier rule exposure: yes. I reviewed this family's generator and reference during authoring before this solve began. During this solve I opened only the generated public challenge and the solve commands; I did not reopen the generator, Racket, canonical answers, previous solution programs, or private query labels. This is an exposed solve, not independent blind evidence.

This file is an authored work log and concise hypothesis summary, not a captured token-level model trace.

## Visible observations

- Train 0: input 17 rows x 19 columns; output 17 rows x 19 columns. Fifteen binary cells become 8. A downward sparse chevron and an upward chevron are filled; all green markers stay 3.
- Train 1: input 17 rows x 15 columns; output 17 rows x 15 columns. Twenty-three binary cells become 8. Left- and right-opening sparse chevrons are filled, including gaps on the implied diagonal edges.
- Train 2: input 13 rows x 12 columns; output 13 rows x 12 columns. Fifteen binary cells become 8. The longer arm determines the supported depth; filling reaches the matching unmarked position on the shorter arm.
- Query 0 input is 15 rows x 14 columns; output unknown. Query 1 input is 16 rows x 17 columns; output unknown. No query outputs were read.

## Revision 1

Hypothesis: group nearby aligned/diagonal green marks, identify a shared apex and two 45-degree arms, and fill the supported solid triangular wedge with 8 while preserving green marks and all outside cells. The implementation represents each orientation in axial/transverse coordinates and handles every marker group. Binary background values do not select regions.

The visible examples motivate using the farther arm for depth and filling missing edge markers. Prior authoring exposure also informs the grouping model; these details must not be treated as wholly independent discovery. No intentionally wrong revision was manufactured.

Validation: the official visible-only check completed with 3/3 demonstrations correct, exit 0, on revision 1. Masked-query correctness remains unknown until maintainer scoring. Cases outside the observed clean-chevron component grammar are not established by these demonstrations.
