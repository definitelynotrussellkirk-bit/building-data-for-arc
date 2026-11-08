# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Exposure and visible observations

I began this blind solve with no earlier rule exposure. I read only this solve
directory's README.md, challenge.json, solution.py, and SOLVE_NOTES.md. I did not
consult the generator, reference rule, private labels, previous solutions, or
notes outside this directory.

The three demonstrations preserve shape and every nonzero input cell. Their
outputs repair zero cells to continue a rectangular repeating pattern. Examples
0 and 2 repeat a 2-row by 3-column tile; example 1 repeats a 3-row by 2-column
tile. The two queries visibly have the same types of repetition.

## Revision 1: smallest consistent repeating tile

Hypothesis: zeros are erased pattern cells. Infer row and column periods using
all surviving nonzero cells, selecting the smallest tile area consistent with
them and with every tile position represented by a surviving cell. Fill only
zeros; keep all nonzero cells intact. Equal-area candidates are ordered by row
period, then column period for deterministic behavior.

Probe: ran an inline Python script from the packet root which read only
WORK/solve-blind/challenge.json, enumerated periods, and compared reconstructed
training grids to visible outputs. It exited 0. All three visible training
outputs matched exactly; inferred periods were (2, 3), (3, 2), and (2, 3).
Query periods inferred as (3, 2) and (2, 3). Their labels are withheld, so no
query correctness claim follows from this probe.

Implemented that hypothesis in solution.py. No failed hypothesis or prior
solution revision was attempted. A row-only repair would also fit some examples,
but the rectangular tile inference expresses the shared evidence across all
examples and both orientations of the erased segment.

Limitations: the evidence treats zero as damage, not a genuine tile color. A
pattern with fully erased residue classes or ambiguous periods may not be
uniquely inferable. The code returns an unchanged copy if no complete consistent
tile is supported. Private query correctness remains unknown.

Validation requested with:
python3 review.py blind check --intent solve --note 'Infer the smallest complete rectangular tile consistent with nonzero cells; the direct public-data probe matched all three training outputs.'

The checker exited 0, with execution_status completed, visible_passed 3,
visible_total 3, and reported_label unknown. No solution revision was necessary.
I stopped because this rule explains and reproduces all visible demonstrations,
and the query grids show the same repetition. Query correctness is withheld.

Finish command:
python3 review.py blind finish --earlier-exposure no --reference-consulted no --reason 'The smallest consistent rectangular tile restores all three visible demonstrations; query execution completed and private correctness remains withheld.'
