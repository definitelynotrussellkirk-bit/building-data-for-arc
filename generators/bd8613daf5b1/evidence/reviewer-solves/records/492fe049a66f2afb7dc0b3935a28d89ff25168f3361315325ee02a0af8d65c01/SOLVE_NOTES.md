# Blind solve notes

This is a concise work log of observations, hypotheses, and executed probes. It is not a token trace. Puzzle information came only from `solve-blind/challenge.json`; no reference, generator, rule source, private query result, prior solution, or prior notes were consulted.

## Observations

- There are three visible input/output pairs and two query inputs without outputs.
- Each visible output is the tight bounding rectangle of all nonzero input cells: 6 by 6, 6 by 6, and 5 by 5.
- Zeros within that rectangle remain zero. Original nonzero colors disappear; differently colored touching cells form one occupied shape.
- The exposed cells have value 1. Interior cells have value 2, with a central 3 in the third example. This suggests successive layers measured from the background.

## Hypothesis and visible-only probe

Hypothesis: crop to the bounding rectangle of all nonzero cells, then replace every nonzero cell with its shortest orthogonal distance to a zero cell, including the background just outside the crop.

Executed an inline `python3 -` probe that loaded only the challenge JSON and compared multi-source distance transforms against all three visible outputs. It tested orthogonal adjacency and eight-neighbor adjacency separately. Exit code: 0.

- Orthogonal adjacency matched all three visible examples exactly.
- Eight-neighbor adjacency disagreed in 4, 3, and 2 cells respectively. In the third example it gave the central cell 2 instead of the observed 3.

This probe distinguishes the two distance metrics; it was not a submitted solver attempt. There was no reason to add special behavior for individual input colors or separate connected components.

## Solver revisions and episode checks

Revision 1 implements the orthogonal distance rule with a padded zero frame and breadth-first propagation from every background cell. An all-zero input returns an empty crop; this case is absent from the visible examples.

The required episode check and its actual outcome will be recorded below after execution. No failures or revisions have been invented.
