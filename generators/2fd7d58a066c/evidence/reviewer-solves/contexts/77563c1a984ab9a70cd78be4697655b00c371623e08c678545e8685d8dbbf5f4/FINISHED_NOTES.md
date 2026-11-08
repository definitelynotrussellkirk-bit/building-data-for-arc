# Visible-only blind solve: 2fd7d58a066c

## Exposure and evidence

No earlier exposure to this task's rule is known. I have opened no generator,
canonical rule, reference solution, task notes, audit records, or private labels.
I used only the five displayed training pairs and two query inputs from this
episode. Their shapes are 10x8, 10x10, 11x8, 11x10, and 11x10 respectively;
each visible output keeps the input shape. Query output dimensions are unknown.

## Hypothesis before the first check

For each column containing any nonzero cells, recolor the inclusive interval
between the topmost and bottommost marked cells to 8. All other cells remain 0.
The marker's color does not determine connectivity or the output color.

Visible discriminators: example 0 has three vertical spans of different lengths;
example 3 connects differently colored endpoints (2 and 9) in column 1;
example 4 recolors the singleton at (7,3) and connects all three marks in column 5.
Thus same-color-only matching, retaining marker colors, and requiring exactly
two endpoints are inconsistent with the visible evidence. No failed solution
attempt was needed or manufactured.

## Revision 1

Implemented the columnwise min/max span directly. The check below will compare
only visible examples and execution. Masked-query correctness is not available.

The revision-1 checker completed and matched all 5/5 visible examples. I stopped
because the concrete mixed-color, multi-endpoint, and singleton cases support
the same simple transformation. Query outputs remain independently unscored.
