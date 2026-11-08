# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Initial observations and hypothesis

- Earlier exposure to this task's hidden rule: none known. I have not opened its generator, Racket rule, reference solution, private labels, or prior notes.
- Across all three visible training examples, the output differs only by inserting color 6 immediately before and after maximal horizontal runs of exactly three color-4 cells.
- Runs of color 4 with lengths 2, 4, or 5 remain unchanged. Horizontal runs of length 3 in colors 5 or 7 also remain unchanged. A qualifying run can be part of a larger vertically connected color-4 object, so connected-component size is not the selector.
- Proposed algorithm: copy the grid; scan each row for maximal contiguous runs of color 4; for a run of length exactly 3, recolor the background cell immediately to each side as 6 when that side exists and is zero.
- Main alternative considered: mark the top row of a gray object. Train example 1 rejects that because isolated gray triples are marked, while train example 2's bottom isolated triple is also marked. The exact horizontal-run interpretation covers every visible change more directly.
- Remaining uncertainty: visible examples place qualifying triples with zero-valued cells on both sides. I will conservatively write caps only into in-bounds background cells rather than overwrite another object.

## TDD probe

Before implementing, I added `test_solution_visible.py`. Its first test replays all visible examples; its second prevents a sliding-window bug that would incorrectly treat a length-4 run as containing length-3 runs. The production change each test catches is respectively an incorrect selector/cap placement and failure to require maximality.

## Implemented revision

Implemented the maximal-run scan without connected-component assumptions. The local visible-example tests now pass, including the explicit length-4 negative case. The implementation reads run boundaries from the original row and writes only to a copied grid, so newly added caps cannot create or alter later gray runs.
