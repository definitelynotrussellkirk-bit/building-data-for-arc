# Blind solve: 3bb94038f4e2

Before solving I read packet workflow instructions and generic ARC design guidance, but no task generator, rule, notes, canonical labels, prior solution, or audit. Earlier rule exposure: no. Reference consultation during this solve: no.

Visible examples 0 and 2 are respectively 7x7 and 6x8, with unchanged dimensions. Each adds blue at the two zero gaps in its bottom-row 1,0,1,0,1 pattern. Visible example 1 is 7x11 and fills the same five-cell pattern on row 1; other colors remain unchanged.

Hypothesis: simultaneously replace horizontal 1,0,1,0,1 windows with five blue cells. A competing rule that connects every blue cell across every row is ruled out by unchanged rows containing three blue points separated by two zeros. Filling gaps through nonzero distractors is ruled out by the unchanged 1,2,1 pattern in example 1. The examples do not establish whether analogous patterns in other colors or vertical orientations should transform; I retain the directly observed horizontal-blue hypothesis.

Revision 1 implements that pattern using the original input for all detections and a copied output, so newly filled pixels cannot trigger cascading rewrites. Check it against all three visible examples and both masked-query execution checks. I did not look at masked-query labels and do not claim their correctness.

Observed result: revision 1 completed and matched 3/3 visible examples. Stopping with this visible-supported hypothesis; masked-query correctness remains unknown.
