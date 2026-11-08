# Native selector-row rotational-equivalence family for `95be702ec4db`

The default `matrix_view=full_matrix` is the byte-exact canonical rule: normalize every framed shape, compare all pairs up to quarter-turn rotation, and emit the full cyan equivalence matrix.

The alternative `matrix_view=selector_row` adds an input-dependent selector relay. A single value in the otherwise blank top row is a one-based frame selector. Step A computes the complete canonical equivalence matrix. Step B consumes that matrix and returns only the selected frame’s relation row. The first two demonstrations select indices 0 and 2 in different nontrivial partitions, so always-first, always-last, neighboring-row, diagonal-only, and ignore-the-selector shortcuts fail.

The family supports 2–6 demonstrations and 1–4 prefix-stable queries. Frame rows, shape rotations, colors, selectors, partition structures, and gallery sizes vary while the episode rule stays fixed. The fourth query is a substantive 30×30 five-frame diagonal gallery spanning rows 1–29 and columns 0–28. Settings, programs, query order, future queries, and answers remain private; `public_turn` reveals one query input only.

`audit.py` checks a finite rival set, protected-Racket labels, and a wrong-next-selector counterfactual. Owner source review, native qualification/acceptance, and training admission remain separate.
