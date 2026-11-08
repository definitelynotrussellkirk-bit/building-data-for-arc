# Solve work log

## Exposure declaration

Before this post-repair solve I had already inspected the selected generator and canonical rule while repairing them, so this episode must be recorded with `earlier-exposure=yes`. During the solve itself I kept the generator, Racket source, reference implementations, prior solve notes, and private labels closed. I used only the visible examples in `README.md` / `challenge.json` and local execution against the three visible training pairs.

## Revision 0 — establish a real red check

I created `test_visible.py`, which imports `solution.py` and requires exact equality on all three visible training pairs. Against the prepared placeholder it failed with `NotImplementedError` (`red-test.log`, exit 1), establishing that the check could detect the missing solution.

## Visible-pattern hypothesis

Across the three demonstrations:

1. The input consists of a color-1 upper field, a color-6 lower band, and an irregular color-5 stencil flush with the left or right edge immediately above the band.
2. The output erases the source stencil to color 1 and copies the same occupied stencil cells to the opposite edge. The stencil is not replaced by a fixed pattern: demonstration 2 preserves its alternating filled and hollow rows.
3. Rows 0, 1, and 2 within the stencil bounding box remain aligned with the destination edge. Each later row shifts one additional column inward. Thus the inward displacement is `max(0, local_row - 2)`.
4. On the first color-6 row, color 9 fills the wake. For a source on the right (destination left), it runs from `final_shift + 1` through the right edge. For a source on the left (destination right), the symmetric prefix is colored 9. Here `final_shift = max(0, stencil_height - 3)`.

I considered two alternatives and rejected them from the visible pairs: horizontally mirroring the stencil (the asymmetric rows in demonstration 2 retain their local column arrangement), and stamping the five-column comb seen in demonstrations 0/1 (demonstration 2 has a different mask that is copied exactly).

## Revision 1 — implementation and visible verification

I implemented the geometric rule directly from color locations and the stencil bounding box, without relying on fixed dimensions, a fixed width, or a fixed mask. Running `python3 WORK/solve/test_visible.py` then matched all three visible training outputs exactly. The two query outputs are produced by the same rule; no private-label feedback was consulted.

Remaining uncertainty is limited to inputs outside the demonstrated grammar (for example, a stencil not flush with either edge); the solution raises a clear error for that unsupported case rather than silently guessing.
