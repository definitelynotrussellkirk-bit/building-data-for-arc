# Solve work log

## Prior exposure

I had already inspected and repaired this task's generator before this fresh solve, so this is **not blind** and `earlier-exposure` must be recorded as `yes`. During the solve itself I did not reopen the generator, Racket rule, reference solutions, prior solution explanations, or private labels. I used only the visible examples printed by `solve_episode.py prepare` and the visible-only checker.

## Visible structure

Every input is a 4×7 grid with:

- a single command digit in cell `(0, 3)`;
- a 3×3 nonzero shape in rows 1–3, columns 0–2;
- a second 3×3 nonzero shape in rows 1–3, columns 4–6;
- zero separators around the command and between the panels.

Every output is a 3×3 binary mask colored 8. This suggests comparing the two panel shapes after a command-selected transform.

## Hypothesis derivation

I represented each panel by occupied/nonzero cells and tested simple transforms of the right panel against the left panel.

- Command 1 (train 3): the output is exactly `left ∩ right`, so command 1 is identity.
- Command 2 (train 0): rotating the right mask 90° clockwise, then intersecting with the left mask, gives exactly `(0,2)` and `(1,2)`.
- Command 3 (train 1): reflecting the right mask left-to-right, then intersecting, gives exactly `(1,1)`, `(1,2)`, and `(2,1)`.
- Command 4 (train 2): rotating the right mask 180°, then intersecting, gives exactly `(1,0)` and `(2,0)`.

The rule is therefore:

1. extract occupancy masks from the left and right 3×3 panels;
2. transform the right mask according to the command: `1=identity`, `2=clockwise 90°`, `3=left-right reflection`, `4=180°`;
3. output color 8 where the transformed right mask overlaps the left mask, and 0 elsewhere.

## Query predictions from the hypothesis

- Query 0 uses command 2. The predicted overlap is `(1,1)`, `(2,1)`, `(2,2)`, producing rows `000 / 080 / 088`.
- Query 1 uses command 3. The predicted overlap is `(2,0)`, `(2,1)`, producing rows `000 / 000 / 880`.

## Revision 1

Implemented the transform table and mask intersection directly. No alternative was needed after the four visible examples independently fixed all four command meanings. Remaining uncertainty is only the masked query score, which the packet intentionally withholds; the rule has no visible-example mismatch.
