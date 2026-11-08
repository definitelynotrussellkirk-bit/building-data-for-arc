# Solve work log

I had no earlier exposure to task `c21f2ce8fb20`, its generator, its Racket rule,
private labels, reference solution, or prior solution notes. I used only
`solve-blind/challenge.json` and a local component-counting probe.

## Revision 1 — choose the compartment with the most red cells

The gray `5` cells partition every input into rectangular non-gray compartments.
The output erases the dividers and all unselected contents to `0`, then fills one
whole compartment with azure `8`.

I enumerated the 4-connected non-`5` compartments and counted red `2` cells. The
selected compartment was the unique maximum in every visible training example:

- train 0: counts `1, 2, 1`; selected count `2`
- train 1: counts `1, 3, 2, 1`; selected count `3`
- train 2: counts `1, 2, 4, 3`; selected count `4`
- train 3: counts `3, 1, 2, 1`; selected count `3`

Alternatives based on room area, aspect ratio, red-cell connectivity, or a fixed
red shape do not fit all four examples. I therefore implemented: find all
4-connected cells not equal to `5`, select the component with the greatest count
of `2`, return an all-zero grid with every cell of that component changed to `8`.
The visible tests have a unique maximum; tie behavior remains unspecified.
