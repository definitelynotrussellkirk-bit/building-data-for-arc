# Solve work log

I had no earlier exposure to this task's rule, generator, reference solution, private labels, or prior solution notes. I used only the public challenge and visible-example feedback.

## Revision 1 — line motifs and two missing cells

All three demonstrations preserve the grid and add exactly two color-8 cells. The nonzero color other than 4 contains a straight run of three cells and one disconnected singleton. One added 8 extends a straight run of three 4s at the end opposite the marker singleton: the singleton touches one end of the run, and the new 8 goes one cell beyond the other end.

The other added 8 repairs a repeated all-4 motif. A maximal straight run of three 4s has a blank just beyond one end and an isolated 4 diagonally beside that blank. Filling the blank joins the isolated cell to the extended run as an elbow. This accounts for (2,3) and (7,0) in example 0, (3,7) and (20,2) in example 1, and (1,6) and (18,3) in example 2.

I first ran an assertion over all visible pairs against the untouched template and observed the expected `NotImplementedError`. I then implemented only these two motifs. Remaining uncertainty: a hidden query could contain accidental additional triples satisfying the local geometry, but the requirement that runs be maximal length three and that the elbow cell be an isolated 4 is intended to reject longer lines and already-connected L shapes.
