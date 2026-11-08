# Solve notes — aea86d2776f1

This is a human work log from the visible generated examples. I had already seen the task rule while repairing its generator, so this episode is **exposed**, not blind; I did not consult the generator, Racket source, reference labels, or previous solution explanations during this solve phase.

## Visible structure

Every input is 5×11. Four isolated digits sit at row 0, columns 1, 3, 7, and 9. Two 3×3 colored templates sit at rows 2–4, columns 1–3 and 7–9. Every output is a 6×6 2×2 mosaic of four 3×3 tiles.

From the first visible example:

- command 3 produces a left-right reflection of the left template;
- command 2 produces a 90° clockwise rotation of the left template;
- command 8 produces a 180° rotation of the right template;
- command 5 preserves the right template.

The other examples support the complete codebook: 1–4 choose the left template and 5–8 choose the right; within each group the transforms are identity, rotate clockwise, reflect left-right, rotate 180°. The four commands map to output quadrants in row-major order.

## Implementation plan

Extract the two fixed 3×3 templates, decode each command into source and transform, transform a copied tile, and concatenate tiles 0/1 above tiles 2/3. I will submit this directly because all visible examples distinguish the relevant source and transform choices; no diagnostic negative is needed.
