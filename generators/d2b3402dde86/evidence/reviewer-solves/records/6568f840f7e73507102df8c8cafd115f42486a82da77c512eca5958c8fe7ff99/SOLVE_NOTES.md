# Exposed post-repair solve notes

This is a human work log from the visible examples. I had already seen the task's
rule during generator review, so this is **not blind**; I nevertheless used only
the prepared visible examples while implementing this solve and did not consult
a reference implementation during the solve phase.

## Hypothesis

1. Locate the minimal axis-aligned bounding box containing every nonzero cell.
2. Keep zeros inside that box; do not crop the prospective answer again.
3. Return the upper-left rectangle whose height is `floor(box_height / 2)` and
   width is `floor(box_width / 2)`.

## Checks against the visible examples

- Example 0 has a 5×9 content box and a 2×4 output. Its output is exactly the
  first two rows and first four columns of that box, including a fully blank top
  row.
- Example 1 has a 4×6 content box and a 2×3 output, again the upper-left half.
- Example 2 has a 7×9 content box and a 3×4 output, confirming independent floor
  division for odd height and width rather than rounding up or forcing a square.

The two queries should therefore use the same content-relative slicing. I made
one direct implementation and stopped after the visible-example checker passed.
