# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Exposure and scope

The supervising reviewer has earlier exposure through the authorized repair;
the finish flag must therefore say earlier-exposure yes. My isolated solve
context contains only these public examples and public feedback, not the main
task semantics, generator, rule, canonical/reference files, tests, private
labels, review summaries, or previous solution notes. I did not consult a
reference during this solve. This log is a concise model-authored record, not
a purported full raw conversation trace.

## Visible inference and revision 1

Outputs retain input dimensions and contain only zero and color 8. The moved
shape is the largest orthogonally connected color-3 component; diagonal contact
does not join components. Other colors and smaller color-3 components disappear.
The movement vector is the position of marker 1 minus the position of marker 2.
Paint the moved component color 8, clipping cells outside the original bounds.

For example 0, the selected component is the four-cell bent line at rows 6/7;
the two cells at (4,2)/(5,2) touch it only diagonally and are excluded. Moving
by (-3,+3) gives the displayed output. Example 1 establishes the opposite-sign
direction with (+3,+3). Examples 2 and 6 demonstrate partial clipping; examples
3 and 7 move every selected cell off the grid and give completely zero outputs.

Probe: ran WORK/.venv/bin/python3 with inline Python reading only challenge.json,
using this component/vector rule. Exit 0. All eight visible outputs matched.
Selected component sizes were [4,6,8,4,8,6,6,5]; visible retained sizes were
[4,6,7,0,8,6,3,0]. Both query inputs executed; their correctness is withheld.
Implemented this tested hypothesis in solution.py. There were no prior actual
revisions and no failed probe/check attempts.

Limitations: the demonstrations use exactly one marker of each color and a
unique largest color-3 component. Equal-size ties and duplicate/missing markers
are not established. Ties use reading-order component discovery; missing
markers or components return a zero grid. No private query correctness claim.

Requested public validation:
WORK/.venv/bin/python3 review.py solve check --intent solve --note 'Select the largest orthogonally connected color-3 component, translate by marker 1 minus marker 2, recolor 8 and clip; the public-data probe matched all eight demonstrations.'
