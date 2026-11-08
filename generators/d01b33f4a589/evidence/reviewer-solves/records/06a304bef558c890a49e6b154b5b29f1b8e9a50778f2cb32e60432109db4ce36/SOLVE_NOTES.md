# Fresh visible-example solve work log

Prepared after final generator work, for generator SHA256
`52b10583ab11154a71c7178c961bd98beeeae8c57ca8893c868476af09a17d66`.
Earlier exposure: **yes**. I had inspected this task's generator and reference
rule while repairing it. During this solve phase I read only the newly prepared
`solve/challenge.json` and my new Python files/results. No generator, reference
source, previous explanations, or private query labels were consulted. This is
not a blind solve and is not evidence of independent neural-model generalization.
These are a reviewer-authored work log and retained program/probe artifacts,
not a captured token-level model conversation or log-probability trace.

## Visible observations and hypotheses

Four demonstrations have one compact colored interior figure and four corners
using values 1..4. The outputs contain four copies of the interior color. All
outputs here are 6x6 and can be partitioned into four 3x3 cells. In demo 1 the two
left corners are both 2 and the two left output cells match. This supports a
corner-to-quadrant command interpretation rather than treating corner colors as
part of the figure. Demo 2's interior color is itself 2, so excluding all command
colors would destroy the figure; the exclusion must be positional.

Candidate family: the eight D4 transforms of the cropped non-corner figure,
selected by the four corner values in reading order, with a common top/bottom
and left/right alignment within each output cell. This is a finite hypothesis
family motivated by the visible scenes, not a uniqueness claim over all programs.

## Actual Python experiment

Command from packet root: `python3 solve/visible_probe.py`.
It reads only the visible training examples. For each of four alignments, it
intersects the compatible D4 transforms for each command over all sixteen
observed quadrants. The complete observations are saved in
`visible_probe_results.json`.

Only top-left placement survives. Every command has exactly one D4 candidate:
1 = clockwise 90 degrees; 2 = 180 degrees; 3 = left/right reflection;
4 = rotate 180 then left/right reflection, equivalently up/down reflection.
The three other common alignments have no surviving mapping. These were
explicit diagnostic hypotheses, not failed submitted solution revisions.

## Submitted revision 1

Implement the fitted mapping, excluding only the four corner coordinates,
cropping the remaining nonzero points, and arranging transformed crops in
uniform cells whose dimensions are the maxima of the selected variants.
Do not hard-code the observed 6x6 output size. Return a fresh list-of-lists and
reject malformed grids or unobserved command values clearly.

There was no accidental failed solution revision to preserve. The D4/alignment
probe preceded this first submitted attempt; it did not use any query answer.
The checker exposes demonstration fit and query execution only. Correctness of
the two withheld query outputs must be scored by the maintainer, not asserted
from execution success. The finish record and checker feedback retain the actual
observed result.
