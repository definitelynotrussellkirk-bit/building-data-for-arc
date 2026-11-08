# Native parametric family: largest blue component → indexed header color

`selection_mode=first_header_all` is the exact canonical rule: take the first
nonzero header color, recolor every blue body cell, and clear everything else.

`selection_mode=largest_component_indexed_header` adds a non-collapsing relay:
segment the blue body, retain the unique largest component, use its cell count
`k` to select header marker `(k-1) mod 3`, then paint only the retained component
with that selected color. The selected object supplies both the output mask and
the color index; the downstream paint cannot be chosen before segmentation and
ranking.

Inputs are matched across settings, deterministic, distinct, and prefix-stable
for 2–6 demonstrations and 1–4 queries. The first three demonstrations rotate
all three header-index branches while moving the largest component through
multiple spatial slots. Query four is a substantive 30×30 scene with eight blue
components, 53 blue cells, three header markers, and boundary contact.

`audit.py` checks executable finite rivals, public masking, protected-Racket
labels, and a smallest-component wrong-intermediate counterfactual. Native
qualification and owner acceptance remain separate; training admission is false.
