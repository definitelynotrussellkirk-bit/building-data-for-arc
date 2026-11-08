# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, canonical rule, reference solution,
private labels, prior solve notes, or any assigned generator source. I used only
the visible presentation produced by `python3 review.py blind prepare` and local
experiments derived from those grids.

## Revision 1 — cumulative transformation program

The upper-left contiguous nonzero run behaves like a sequence of commands, while
the distant monochrome component is the payload picture. The output begins with
the tightly cropped original picture, then appends the result after each command,
with one zero column between states. All states are top-aligned in a canvas whose
height is the tallest state.

I segmented the visible outputs at all-zero columns and compared each segment to
the input component. This gives the command table:

- color 1: rotate 90 degrees clockwise;
- color 2: rotate 180 degrees;
- color 3: rotate 90 degrees counter-clockwise;
- color 4: reflect left-to-right.

The transformations are cumulative, not independent. For example, the first
training case applies clockwise rotation twice and then reflects the already
180-degree-rotated shape. The third case's first two transitions are original →
clockwise → original, confirming that command 3 undoes command 1.

The implementation reads the command prefix, crops the separate payload,
materializes the initial and cumulative states, and concatenates them. I left
unseen command colors as an explicit error rather than silently inventing a
meaning. Remaining uncertainty is limited to layouts not represented in the
visible examples (for example a payload touching row 0), but the generated format
consistently separates the command row from the payload.
