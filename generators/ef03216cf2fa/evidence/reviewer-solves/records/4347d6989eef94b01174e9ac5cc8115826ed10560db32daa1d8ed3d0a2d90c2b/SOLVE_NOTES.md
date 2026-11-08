# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Exposure and observations

No earlier rule exposure to this new target. I read only this episode's public
README.md, challenge.json, solution.py, SOLVE_NOTES.md, and public feedback. I
did not consult a generator, canonical/reference rule, private labels, audits,
other task files, previous solution notes, or answer-return metadata. This is a
concise model-authored work log, not a purported raw conversation transcript.

Each demonstration contains separated monochrome shapes. Outputs preserve each
shape's colored cells, crop surrounding background, rotate tall shapes 90
degrees clockwise, and stack shapes with one zero row between them. Horizontal
and square shapes retain their orientation. The output width equals the widest
oriented shape; shorter rows receive zeros on the right.

## Revision 1: crop, orient, sort, stack

Hypothesis: group nonzero cells by color, crop each group's bounding rectangle,
rotate it clockwise if taller than wide, sort by decreasing oriented width,
then by decreasing colored-cell count, then reading position, and stack.
Width is supported by the equal-count shapes in example 2: the width-4 shape
precedes the width-3 shape. Cell count resolves the equal-width shapes in
example 1. Pure count sorting with a suitable tie-breaker also fits the visible
evidence; the precise general ordering is not uniquely established.

Probe: ran WORK/.venv/bin/python3 with an inline Python experiment reading only
WORK/solve-blind/challenge.json. It exited 0 and matched all three visible outputs
exactly. Orders were [8,7,9], [2,4,1,8], [6,7,9], with shapes (8,4), (12,4),
(8,4). Both query inputs executed under the hypothesis, yielding shapes (8,4)
and (12,4); query correctness remains withheld. Implemented this tested rule in
solution.py. No failed attempt or earlier actual revision occurred.

Limitations: same-colored disconnected objects, wider but less-populated shapes,
and equally ranked shapes are not demonstrated. Grouping by color and the final
reading-position tie-breaker are assumptions. No private correctness claim.

Requested public check:
WORK/.venv/bin/python3 review.py blind check --intent solve --note 'Crop each color, rotate tall shapes clockwise, sort by oriented width then cell count, and stack with blank rows; the public-data experiment matched all three demonstrations.'
