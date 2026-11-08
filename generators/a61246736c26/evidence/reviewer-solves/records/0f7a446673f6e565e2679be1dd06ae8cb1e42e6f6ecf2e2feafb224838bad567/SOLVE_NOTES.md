# Post-repair visible-only solve work log

## Exposure and scope

This is an exposed post-repair solve. I inspected task-authoring material earlier in the overall review, so the finish declaration must be **earlier exposure: yes**. After entering this solve phase I kept the generator, Racket rule, reference solutions, private labels, and prior solution explanations closed. I read only the freshly prepared solve README and public challenge, then wrote the solver below from the visible grid relationships. **Reference consulted during solve: no.**

These notes are an assistant-authored work log of observations, hypotheses and actual experiments. They are not a captured model-token conversation, token-level trace, or log-probability record.

## Visible observations

The five demonstration dimensions are independently read from their input and output arrays:

| Example | Input | Output |
|---|---|---|
| 1 | 22 rows × 22 columns | 6 rows × 20 columns |
| 2 | 19 rows × 19 columns | 5 rows × 17 columns |
| 3 | 22 rows × 22 columns | 6 rows × 20 columns |
| 4 | 19 rows × 25 columns | 5 rows × 23 columns |
| 5 | 22 rows × 29 columns | 6 rows × 27 columns |

Query 1 input: 19 rows × 25 columns. Output: unknown.
Query 2 input: 19 rows × 19 columns. Output: unknown.

Complete color-8 rows and columns separate the input into tile rows and tile columns. The first tile-column region has an additional left-hand swatch strip. Within each tile column, two tiles have the same 1/2/8 pattern, while the remaining tile has a uniform colored interior. The output retains one pattern tile per input column and a single color-8 separator between adjacent output tiles.

The working recoloring hypothesis is: replace the pattern's 2s by the solid tile's interior color, replace its 1s by the left-hand swatch in the solid tile's row, and retain its 8s. Read swatches from the actual input; their order varies between examples.

Visible cross-checks supporting that hypothesis:

- Example 1 puts all three solid tiles in the bottom band, whose swatch is 9. All three output borders are 9, with separate fill colors 3, 4 and 7.
- Example 2 has row swatches 0, 9 and 5. The three solid cues occur in the top, bottom and middle bands, respectively; the output borders are 0, 5 and 9.
- Example 4 puts all four solid cues in the top band, whose swatch is 9, and all four output borders are 9.
- Example 5 mixes top-band solid cues with a bottom-band cue. The first three output borders are 9, while the last is 0. This supports an independent lookup for each tile column.

## Revision 1

Created `solution.py` with a fresh `solve(grid)` implementation. It locates separators from the grid, extracts the row swatches, identifies each solid cue, verifies the duplicate patterns, recolors the pattern, and joins the output tiles. It has no generator, reference, private-answer or earlier-solver imports and contains no stored example/query answers.

The first official check will test this actual revision against the visible demonstrations and record query execution without exposing private query correctness. No deliberately wrong revision was constructed.
