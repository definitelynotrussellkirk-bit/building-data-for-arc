# 2243e48c880b

Generate an 8–12 by 9–14 background-0 grid containing exactly three
monochromatic 4-connected components. Component sizes are 2–6 cells and may be
distinct or tied. Input colors are irrelevant and may repeat across disconnected
components. The selected authority discovers components in row-major order,
stably sorts them by cell count, clears the canvas, and recolors the ranked
components 2, 4, and 8. Therefore equal-size ties are resolved by row-major
component discovery order.

The default three-slot curriculum alternates two direct shortcut
counterexamples (smallest-size tie and largest-size tie, each with two input
colors) with one three-color canonical-profile anchor. Exact controls expose
grid height, grid width, size relation, and palette size, including lawful
one-color and all-tied cases.

Kind: `per_puzzle`. Selected generator version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.

Current accepted generator version: `3.1.0`. The selected source/rule approval is reviewer-reported; finite test and curriculum claims are in its task-owned notes.
