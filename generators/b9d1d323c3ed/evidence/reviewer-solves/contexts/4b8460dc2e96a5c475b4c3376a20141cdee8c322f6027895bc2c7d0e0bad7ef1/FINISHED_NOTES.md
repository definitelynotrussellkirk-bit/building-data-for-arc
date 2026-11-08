# Post-repair visible-example solve log

This is a human work log based only on `solve/challenge.json`. I had already seen the task rule while repairing the generator, so this episode is exposed rather than blind; I did not reopen the generator, Racket source, reference solution, or private labels during this solve.

## Hypothesis

Each training output is the tight rectangular crop around all nonzero cells, concatenated with an identical copy to its right:

- Train 1 has a 3×3 occupied bounding box and a 3×6 output formed by repeating those three cropped columns.
- Train 2 has a 2×2 bounding box and a 2×4 repeated output, ruling out a fixed 3×3 crop.
- Train 3 again has a 3×3 bounding box and a 3×6 repeated output.

The implementation therefore finds all nonzero coordinates, crops their bounding box, and returns every cropped row twice. The first test visibly exercises a tall 15×5 crop; the second exercises a sparse 3×3 crop.
