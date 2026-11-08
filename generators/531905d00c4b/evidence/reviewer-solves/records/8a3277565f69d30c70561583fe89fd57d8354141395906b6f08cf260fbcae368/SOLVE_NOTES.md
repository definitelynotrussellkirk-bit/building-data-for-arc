# Solve notes — 531905d00c4b

This is a human work log. I had seen the task rule during the earlier generator review, so this is **not blind**. After `solve_episode.py prepare`, I consulted only `solve/challenge.json` and used Python experiments derived from that visible file; I did not reopen the generator, Racket rule, reference solution, or private labels.

## Visible-example observations

1. Every input has a top region followed by a first all-zero row and then a small lower color matrix, sometimes surrounded by blank padding.
2. The top region contains one four-connected monochrome object per color. Their bounding boxes have unequal sizes.
3. Output dimensions equal `(cropped lower height × maximum prototype crop height)` by `(cropped lower width × maximum prototype crop width)`:
   - train 0: lower `3×3`, common tile `3×3`, output `9×9`;
   - train 1: lower `4×3`, common tile `4×3`, output `16×9`;
   - train 2: lower `3×3`, common tile `4×3`, output `12×9`.
4. In train 1, the color-7 prototype starts one row below the other library objects, but its output tile begins at the top. Therefore each prototype is cropped independently; absolute library row placement is not retained.
5. In train 2, the lower matrix begins after two blank rows and one blank column, but the output has no corresponding blank tile border. Therefore the lower nonzero rectangle is cropped.
6. The maximum tile height changes from 3 to 4 across examples, so a fixed `3×3` substitution rule is false.

## Hypothesis and probe

Hypothesis: split at the first all-zero row; find same-color four-connected prototype objects above it; crop each object to its own bounding box; top-left pad all crops to the largest height and width; crop the nonzero lower index rectangle; replace each index color by its padded prototype tile without gaps.

I ran a challenge-only Python geometry probe that reported prototype bounding boxes, lower bounding boxes, and predicted output dimensions for all three visible training pairs. The dimensions matched all outputs, including the shifted prototype and padded lower matrix cases above.

## Implementation

`solution.py` implements the hypothesis directly with standard Python. Components are detected independently of their absolute library placement, prototype padding is top-left aligned, and lower layout padding is removed before tiling. No fallback or task-source lookup is used.

There was one genuine solve revision: the implementation below. I did not manufacture a failed attempt or teaching negative because the visible examples already distinguish the main rival rules.
