# Solve work log

I had no earlier exposure to this task's rule or solution and did not inspect any
rule, generator, notes, audit evidence, or private labels before solving.

## Revision 1

The 3x14 input is three 3x4 panels separated by solid columns of color 9.  Each
panel has one blank edge column, leaving a 3x3 motif.  The first two motifs form
an analogy: infer the square symmetry carrying panel A to panel B, then apply the
same symmetry to panel C.

Visible checks by hand:

- example 0: A -> B is 90 degrees clockwise; rotating C gives the shown output;
- example 1: A -> B is 180 degrees;
- example 2: A -> B is 90 degrees counter-clockwise.

The program splits the panels, removes their blank edge padding, enumerates all
eight dihedral symmetries, and applies the matching symmetry to the query.  It
rejects a missing match or a query-relevant ambiguity instead of silently
choosing an unsupported rule.  I also checked the two unseen query structures:
query 0 encodes a left-right reflection and query 1 an anti-diagonal reflection.

## Revision 2

Revision 1 failed before evaluating any example.  The parser treated every solid
nonzero column as a divider, but example 0 also has solid motif columns (columns
1 and 10).  The traceback reported candidates `[1, 4, 9, 10]`.  The actual two
dividers are distinguished structurally: they have the same nonzero color and
split the width into three equal 4-column panels.  I changed only that inference;
the symmetry hypothesis and transform code are unchanged.
