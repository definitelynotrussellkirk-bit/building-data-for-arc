# Solve notes

This is a human work log. I had seen the task rule earlier while repairing the generator, so this is an exposed post-repair solve, not a blind solve. During this solve I kept the generator, Racket source, reference solutions, private labels, and previous solution explanations closed and used only `solve/README.md`.

## Hypothesis

Each symbol is a hollow red diamond: its center is a background cell with red cells immediately above, below, left, and right. The output preserves all input cells and paints blue through background cells between consecutive diamond centers that share a row or a column.

Evidence from the visible demonstrations:
- Example 1 has two centers in the top row-alignment and two in one column; exactly those gaps become blue.
- Examples 0 and 2 show long horizontal spans and a vertical span, while red arm cells are preserved rather than overwritten.
- The centers themselves are part of the connecting span only when they lie strictly between another aligned pair; ordinary endpoint centers remain background.

I implemented exact four-arm detection, grouped centers by row and column, sorted each group, and filled only zero-valued cells between consecutive centers. I considered a looser partial-marker interpretation, but the demonstrations consistently support complete four-arm diamonds and crowded inputs can create misleading three-arm patterns, so the implementation deliberately requires all four arms.
