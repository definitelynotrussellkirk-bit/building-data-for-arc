# Solve work log

## Earlier exposure

I had not opened this task's generator, canonical rule, reference solution, private query labels, audit records, or earlier solution explanations. I used only the visible examples produced by `blind prepare` and local tests against those examples.

## Hypothesis

The only non-background object is a 2×2 block containing red (`2`) and one paint color. A red cell selects the diagonal associated with its corner of that block: top-left selects northwest, top-right northeast, bottom-left southwest, and bottom-right southeast. The output replaces the seed with the paint color and repeatedly stamps a solid 2×2 paint-colored square one cell farther along every selected diagonal. Overlapping stamps form a three-cell-wide diagonal trail; stamps are clipped at the grid boundary.

This accounts for all three examples:

- one red top-right corner produces only a northeast trail;
- red top-right and bottom-left corners produce the two halves of one northeast–southwest trail;
- three red corners produce three branches, while their shared initial 2×2 stamp merges at the source.

## Probe and implementation

I first wrote a visible-example regression script that imported the untouched skeleton and confirmed it failed with `NotImplementedError`. I then implemented the corner-to-direction mapping, located the 2×2 seed by the nonzero bounding box, selected the unique non-red paint color, and stamped solid 2×2 blocks along each chosen diagonal until the stamp was fully outside the grid.

Remaining uncertainty is limited to malformed inputs outside the demonstrated task contract (for example, a seed not exactly 2×2 or multiple non-red colors). The two visible queries follow the same contract.
