# Blind solve work log

This is an authored work log, not a captured token-level conversation.
No generator, Racket rule, reference solution, audit record, or private label was opened.
Only challenge.json and the public preparation output were used.

## Observations and rejected hypotheses

Visible examples 0 and 1 suggest replacing black pockets inside gray outlines with yellow while preserving every gray pixel. Example 0 has an irregular pocket caused by an extra gray pixel, so filling the whole bounding rectangle would overwrite a given pixel.

Example 2 refutes a conventional flood fill that preserves every component touching the canvas edge: its one-cell left notch and three-cell right notch become yellow. It also refutes filling every zero component except the largest: several large background regions stay black. A component census using only visible inputs and outputs found filled components of sizes 1, 3, 10 and 4, and unchanged components of sizes 20, 6, 47, 36, 14 and 19.

## Attempt 1

Hypothesis: fill each four-connected zero pocket whose bounding rectangle has complete gray caps immediately above and below and complete gray side walls wherever those walls lie inside the canvas. A side may be clipped by the canvas edge; top/bottom caps remain necessary. This distinguishes the right-side three-cell pocket from the irregular fourteen-cell background region: the latter has a gap in its bounding rectangle's top cap. The top-edge six-cell region lacks a top cap and stays black.

Implementation enumerates zero components, tests their surrounding caps/walls, and recolors only original zero cells. It uses no size threshold, component rank, query outputs, or source imports. Query output correctness is unknown and must be scored independently.
