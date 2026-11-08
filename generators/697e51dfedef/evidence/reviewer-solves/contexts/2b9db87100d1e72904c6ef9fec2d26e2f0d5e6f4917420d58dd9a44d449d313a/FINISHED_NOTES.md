# Solve notes

This is a human-authored visible-example work log. I had already seen the task rule during generator review, so this is an exposed post-repair solve; nevertheless I used only `solve/challenge.json` while preparing this revision and did not consult the generator, Racket source, reference solutions, private labels, or prior solve notes.

## Visible evidence

Each demonstration contains exactly three separated, single-color, 4-connected objects with distinct cell counts. The source colors vary and are discarded, while shape and location are preserved.

- Demonstration 1 has areas 1, 3, and 5, recolored 2, 4, and 8.
- Demonstration 2 has areas 2, 3, and 5, recolored 2, 4, and 8.
- Demonstration 3 has areas 2, 4, and 5, recolored 2, 4, and 8.

Hypothesis: rank the objects by area; recolor smallest to 2, middle to 4, and largest to 8. I implemented color-preserving 4-connected component extraction and retained every object's original cells.

The two visible queries satisfy the same three-object/distinct-area assumptions. One revision was sufficient because the hypothesis matches all three visible demonstrations exactly.
