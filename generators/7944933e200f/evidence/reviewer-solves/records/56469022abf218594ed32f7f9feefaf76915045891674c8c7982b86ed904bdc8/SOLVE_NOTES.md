# Final-source exposed solve work log

This new episode is bound to generator version 3.1.1, SHA256 `a0ccc92d7b4cb372cbd538f12851b45efdb78245fb5666af31965714424ad7cd`. The earlier version's completed solve remains retained under `checks/prior-solve/a36a0ee10784/`. I previously worked on the rule and generator, so earlier exposure is yes. During this new solve phase I read only the current public presentation; I did not open the generator, Racket rule, reference solutions, private answers or earlier solution explanations. This is an actual concise work log, not a token-level model conversation.

## Visible observations

Example 0: Input 9 rows × 14 columns. Output 4 rows × 4 columns. Colors 5, 7 and 8 each occur 13 times, while color 4 occurs 14 times. The 7 component begins at (2,3), before the other minimum-frequency colors, and its four-by-four ring crop preserves interior 4, 8, 5 and 0. The detached diagonal 7 at (6,7) is excluded from the component box. Neither extreme numeric tied color selects 7.

Example 1: Input 11 rows × 9 columns. Output 1 row × 1 column. Color 4 occurs 9 times and color 9 occurs 19 times. The first isolated 4 at (0,2) gives the output. This contradicts choosing a visible ring regardless of global frequency.

Example 2: Input 9 rows × 11 columns. Output 5 rows × 5 columns. Colors 1, 6 and 8 each occur 17 times; color 2 occurs 18 times. The first 6 component starts at (3,2), before the other tied colors, and its five-by-five original crop matches the output with all interior content retained.

## Hypothesis and first implementation

Use global nonzero color counts to rank monochromatic four-connected components; choose the first component in row-major order at the lowest population, then return its original unmasked bounding-box crop. The first visible example rejects singleton-only, smallest local component, first object, masked crop, whole-color bounding box, numeric extreme tie breaking and eight-connectivity. The two rich examples are compatible with other artificial hypotheses; this exposed solve is not a claim of unique induction or independent rediscovery.

I wrote a standalone Python depth-first component traversal and global Counter. Strictly lower frequency replaces the winner; equal frequency preserves the earlier row-major component. No generator or canonical-data imports are used. This is the first attempted program on this freshly prepared episode. No failed attempt is fabricated.

Masked query 0: Input 7 rows × 9 columns. Output unknown. Masked query 1: Input 11 rows × 10 columns. Output unknown.
