# Native parametric family: anchor area → selected rectangle outline

`outline_mode=all_rectangles` is the exact canonical rule: pair same-color
diagonal endpoints and draw every implied rectangle border.

`outline_mode=anchor_area_select` adds a genuine selector relay. Rectangles are
ordered by their input-derived top-left coordinates; the first rectangle is the
anchor. Its area `A` selects candidate `(A-1) mod n`, and only that selected
candidate is outlined in its own color. The downstream border and color cannot
be fixed until the anchor rectangle has been reconstructed and measured.

Inputs are matched across settings and support 2–6 demonstrations plus 1–4
prefix-stable queries. The first three demonstrations force selector indices
0, 1, and 2 while varying colors and diagonal slants. Query four is a real
30×30 scene with six rectangles and endpoint contact on all four boundaries.

`audit.py` checks finite shortcut rivals, public masking, protected-Racket
labels, and an off-by-one area counterfactual. Native qualification and exact
owner acceptance remain separate; training admission is false.
