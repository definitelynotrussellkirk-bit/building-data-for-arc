# Post-repair solve work log

This is an assistant-authored work log of the actual experiment and solution
revision, not a token-level conversation trace. I had already inspected the
task's rule and generator during the repair. Earlier rule exposure is **yes**;
this episode is therefore exposed, not blind. From preparation through finishing
this solve, I used the displayed challenge, Python and visible-only checker;
I did not reopen the generator, Racket rule, reference solutions, canonical
labels or private query answers.

## Visible observations and hypothesis

The three training pairs separate a sparse top-row script from a lower,
single-color object. Outputs preserve the object's nonzero cells and discard
the large surrounding canvas. Leading and internal zero cells occur in scripts,
so I treat zero as spacing. I hypothesize that nonzero top-row cells encode
geometric operations composed from left to right on the cropped lower object.

Example 2 has a single code 4 and reverses the order of the object's rows.
Example 0 has four leading code-1 operations followed by 4 and 1; clockwise
quarter turns explain its final orientation when combined with the observed
vertical reflection. Example 1 repeats code 2 twice, then applies 4 and 3;
it does not by itself identify code 2. The object there also uses color 4, so
the top-row/body distinction is positional, not a disjoint-palette assumption.

## Experiment: finite candidate search from visible labels

Command from `WORK/`: `python3 solve/visible_probe.py` (exit 0).
The standalone experiment reads only `solve/challenge.json` and enumerates
all 4,096 constant codebooks of four D4 transforms under the crop-and-compose
hypothesis. **Eight codebooks fit all three visible labels.** They all assign
clockwise rotation to code 1 and vertical reflection to code 4; code 2 remains
underdetermined and affects the paired interpretation of code 3.

All eight fitting codebooks predict the same grid for each of the two public
queries. `visible_probe.json` retains the complete candidate list and the
unscored predictions. This is finite-family agreement, not knowledge of the
masked answers or proof against every possible program. The experiment also
shows why a claim that these three demonstrations uniquely identify every
individual instruction would be too strong.

## Revision 1

I selected the natural representative 1=clockwise quarter turn, 2=left/right
reflection, 3=half turn, 4=up/down reflection. The choice of code 2 alone is not
uniquely justified by these examples; prior exposure may influence that choice.
The finite search establishes that this representative's two query predictions
do not depend on which of the eight fitting codebooks is chosen.

`solution.py` crops the body independently of the script color, then transforms
the current result for each nonzero code. It does not import generator or
reference code, read files, or special-case the visible arrays. This is the
only attempted solution revision. No accidental failure or intentional teaching
negative has been invented. Checker results and the final stopping reason will
be recorded below after the actual check.
