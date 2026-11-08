# Visible-example solve record

## Exposure and scope
Earlier rule exposure: **yes**. I repaired the generator and inspected the
canonical rule before this solve phase. This is not a blind independent solve.
After `solve_episode.py prepare`, I used only `challenge.json`, the new
`solution.py`, my visible-example experiment, and the check tool's feedback.
No generator source, Racket rule, reference solution, old solution explanation,
or private query label was consulted during this solve.

## Revision 1: preserve and slide row blocks
The visible examples move a contiguous run of green 3s left within its row,
preserving its length. The nearest cyan 8 originally to its left stops it; with
no such cell it reaches column zero. Other rows and other nonzero colors remain.
The second example demonstrates an interior block and cyan to its right. The
third demonstrates that a 7 along the traversed path is not a stopping wall.
The fourth demonstrates a length-three block. These observations rule out
suffix-only movement, all-nonzero walls, and a maximum moved width of two for
these examples.

The implementation records the original green run, locates the left stopping
position using only original cyan cells, clears the old run, and paints the
same length at the destination. Clearing before painting avoids overlap bugs.
It does not import or execute reference code.

Probe command, from the packet root:
`python3 solve/experiments.py > checks/solve-visible-probes.json`

This log is a concise record of hypotheses and observable checks, not a raw
internal reasoning transcript. No intentionally broken submission was made.

## Observed result and stopping boundary
`solve/experiments.py` matched **4/4 visible examples**, preserved per-row green
counts and other nonzero cells on all four, and produced both query predictions.
`solve_episode.py check --intent solve` recorded revision 1, execution completed,
visible passed 4/4, and **reported_label: unknown**. That feedback is not a
private-query accuracy result. There was one genuine solution revision and no
failed submissions to hide. Stop because the visible tests pass, both queries
execute, and private correctness is intentionally withheld. A more general
unseen input grammar is not established by these six inputs.
