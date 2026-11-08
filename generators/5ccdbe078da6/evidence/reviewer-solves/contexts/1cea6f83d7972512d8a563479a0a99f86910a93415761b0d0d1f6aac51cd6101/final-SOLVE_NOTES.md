# Public-example solve record

## Exposure and scope
Earlier exposure: **yes**. Before preparing this episode, I reviewed the assigned
source and its reference transformation while repairing the generator. This is
not an independent blind solve. From `solve_episode.py prepare` until finishing
this episode, I consulted only `solve/challenge.json`, the episode's public
instructions/template, and my own newly written Python experiments. I did not
open the generator, Racket/reference implementations, earlier solution notes,
or private query labels during the solve phase.

## Revision 1
Observed public evidence: all three demonstrations contain two markers per
nonzero color. Their outputs draw the boundaries of the markers' axis-aligned
bounding boxes; the second demonstration includes horizontal segments. The
first and third demonstrations contain overlapping boundaries. The implemented
candidate processes colors in first-occurrence order and allows a later
boundary to overwrite an earlier one, including an original marker.

A Python probe computed that candidate separately on all three public inputs:
**3/3 exact visible matches**. This check used the provided public outputs only.
The submitted implementation rejects unobserved non-pair color multiplicities
rather than silently inventing an extension. No code from another solver or
reference implementation was consulted during this episode.

Submission: one genuine candidate, `solve/solution.py`. No deliberately broken
attempts were manufactured. The two query inputs were available, but no query
answers were available or consulted. Generalization and hidden-query exact
correctness remain for the packet's independent evaluator.
