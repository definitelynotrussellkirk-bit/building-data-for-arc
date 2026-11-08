# Solve notes — ef02aedbac38

This is a human work log based on `solve/challenge.json`. I had already seen the task's intended rule while reviewing its generator, so this episode is exposed rather than blind; I did not consult the Racket source, private labels, reference solutions, generator code, or earlier solution explanations during this solve phase.

## Visible-example observations

- Every output has exactly the same dimensions as its input.
- Each input uses color `5` and exactly one other color `X`.
- At every position containing `5`, the output contains `X`.
- At every position containing `X`, the output contains `0`.
- This explains both sparse-5 examples and the 25×4 example where `5` is the dense/background-looking color, so the operation is keyed to the literal value `5`, not to foreground density.

## Hypothesis and implementation

Transform each cell independently: `5 -> X`, and `X -> 0`, where `X` is the sole non-5 input color. The implementation derives `X` from the current grid and rejects inputs that do not contain exactly one such color. No alternate hypothesis was needed because the same cellwise mapping accounts for every visible training cell without exceptions.
