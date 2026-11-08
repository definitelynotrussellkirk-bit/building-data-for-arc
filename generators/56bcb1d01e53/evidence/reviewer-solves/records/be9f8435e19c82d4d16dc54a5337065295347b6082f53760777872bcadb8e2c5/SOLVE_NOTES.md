# Post-repair visible-only solve notes

The demonstrations show multiple monochrome partial icons on the modal background.
The output preserves every observed cell and adds symmetry partners inside each
icon's local box.

Hypothesis used for revision 1:

1. Find 8-connected foreground components, but join components that face each
   other across exactly one background cell in a cardinal direction. Train 2's
   broken outlines require this bridge closure.
2. For square logical icons, close each cell under quarter-turn rotations about
   the box center. This includes half-integer centers for even boxes.
3. For a non-square icon, round the box center, expand each dimension symmetrically
   around that center, and close under left/right and up/down reflection.
4. For an odd square whose center is still empty, fill the center when the four
   cardinal neighbors support it. I also retained the analogous size-7 diagonal
   plus boundary-midpoint support visible in the broader examples.

The implementation reads partner colors only from the original input, preventing
newly inferred pixels from becoming unsupported sources. No generator, Racket
source, reference output, or private query label was consulted after preparation.
Earlier rule exposure is yes because this solve follows the generator review.
