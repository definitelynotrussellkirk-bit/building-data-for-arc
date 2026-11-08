# Post-repair exposed solve work log

This is an authored work summary, not a captured token-level model trace. Earlier rule exposure: **yes**: I repaired this task before preparing this episode. Reference consulted during this solve: **no**. During this phase I opened the public solve README/challenge and wrote Python experiments; I did not open generator source, the Racket rule, previous solution notes, private labels, or query answers.

## Visible hypothesis and experiment

The visible grids suggest two header symbols and two body motifs. I treat the leftmost monochrome connected body object as the first operand, transform its cropped shape, align both cropped operands to a common local top-left origin, combine membership, paint retained cells 8, and trim empty output borders. Header position and body color vary in the visible examples, so neither determines operand roles.

I wrote `infer_keymaps.py` using only the visible nine training pairs. It evaluates all 13,824 mappings from the three transform keys to eight square symmetries and the three operation keys to union/intersection/XOR, without assuming either mapping is injective. Exactly one mapping survives under the stated parsing/alignment hypothesis: 1 = clockwise quarter-turn, 2 = left/right flip, 3 = up/down flip; 4 = union, 5 = intersection, 6 = XOR. The scope assumptions and each example's candidate set are retained in `visible_keymap_probe.json`. This finite search is supporting evidence, not an independent blind rediscovery or proof against every possible rule.

## Actual solution revision 1

`solution.py` independently implements connected components, matrix transforms, Boolean combination and shape-safe crop using ordinary lists. It imports no repository/reference code. The first actual submitted solution uses the surviving mapping; there were no deliberately wrong solutions or fabricated failures.

The two query input dimensions are 8 rows × 12 columns and 8 rows × 14 columns. Their outputs are unknown to this review phase. I will stop after visible checks pass; this episode cannot establish private query correctness.

## Result and stopping reason

The actual revision-1 check completed successfully and passed all 9 of 9 visible training pairs. Both query predictions executed, but the checker reports their correctness as unknown. I stopped with this first solution; no changes to the generator occurred during the episode. The solve summary binds the final generator SHA-256 `f2e3e653f292273c18c65d7b453f082cc1763786c23874de1e85fff1b22e3b5e`.
