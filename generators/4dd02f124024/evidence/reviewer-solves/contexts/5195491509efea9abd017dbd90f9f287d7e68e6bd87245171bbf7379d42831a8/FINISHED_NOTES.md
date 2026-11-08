# Solve work log

## Prior exposure disclosure

Before this isolated solve episode, I had already inspected the task's implementation and Racket authority while repairing its generator. I therefore mark earlier rule exposure **yes**. After `solve prepare`, I did not reopen the generator, Racket rule, reference solution, private labels, or earlier solution notes; this implementation was reconstructed from the visible examples in `challenge.json`.

## Revision 1 — rectangular-frame consistency filter

The only changed cells in all four demonstrations are occupied cells strictly inside monochrome rectangular borders. Borders and background remain fixed. The examples support this rule:

1. Find each nonzero monochrome rectangular frame.
2. Inspect its nonzero interior cells.
3. Keep the interior when every occupied interior cell has the frame's color.
4. If any occupied interior cell has another color, erase **all** occupied cells inside that frame, including cells that match the border.
5. Apply the test independently to every frame.

Evidence against nearby alternatives:

- "Erase only foreign cells" fails train examples 1–3: an interior contains both its own color and a foreign trigger, yet the output removes both.
- "Erase every interior" fails the 7-frame in example 0, the 4-frame in example 1, the 3-frame in example 2, and the 4-frame in example 3; matching-color interiors survive.
- "Repair only one bad frame" fails examples 1–3, which each contain multiple independently erased frames.

I implemented a shape-independent scan for uniform rectangular borders rather than relying on component positions or the example dimensions. For each detected frame, the code tests the currently occupied interior and clears it only after a foreign-color witness. Remaining uncertainty before checking: the visible layouts use separated frames, so overlapping-frame precedence is not strongly identified; scanning the rectangles deterministically is the least specialized extension.
