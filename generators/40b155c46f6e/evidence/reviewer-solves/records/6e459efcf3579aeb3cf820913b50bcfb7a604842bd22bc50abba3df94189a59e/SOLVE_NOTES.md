# Fresh episode solve work log

This is a model-authored work log and executable-probe summary, not a captured
conversation, token-level reasoning trace, or log-probability record.

## Exposure boundary

Earlier rule exposure: **yes**. I read the original generator, canonical examples,
and Racket rule while repairing the assigned task. This attempt is consequently
not blind and must not be classified as an unexposed solve. After preparation I
read only `solve/challenge.json` and my own solve/probe files for the solving
phase. I did not consult the generator, Racket rule, previous solution explanations,
reference solvers, or private labels during this phase.

## Visible observations

There are three visible demonstrations and two masked query inputs. The visible
changes are two cells in demonstration 0, three in demonstration 1, and three in
demonstration 2. Each changed cell lies in a nonzero row and takes that row's
repeated color. Every zero stays zero. Changed rows include zero-based rows 0,
4, and 6; the operation is not restricted to odd-numbered rows. The odd cell
appears at the beginning, interior, and end of a nonzero run.

Demonstration 1 uses the colors 2, 4, and 6 in different roles in different rows.
For example, 4 changes to 2 in one row but is the preserved repeated color in
another. That rejects a single global color substitution as the complete rule.

## Hypothesis and actual probes

H1: within each row, ignore zeros, and when there are two distinct nonzero colors
with frequencies one and more than one, replace the singleton by the repeated
color. Otherwise preserve the row.

`visible_probe.py` compares H1 and the alternatives "use the first nonzero value"
and "use the last nonzero value" on the visible training pairs only. Its complete
results are in `visible-probes.json`. H1 fits all three demonstrations. The first
value alternative fails demonstrations 1 and 2; the last value alternative fails
demonstration 2. Those alternatives were deliberate diagnostic comparisons, not
failed submitted solutions or accidental model mistakes.

## Revision 1

Implemented `solution.py` with row-local frequency counts and a new output copy.
No location, color-ID, width, run-length, or active-row-count special cases are
used. This is the first actual solve attempt; no failed attempt is invented.
The behavior on rows without the observed singleton pattern is conservative
preservation, not something uniquely established by these demonstrations.

The visible checker result will determine whether a revision is needed. Masked
query correctness is not available during this solve and is not claimed here.
