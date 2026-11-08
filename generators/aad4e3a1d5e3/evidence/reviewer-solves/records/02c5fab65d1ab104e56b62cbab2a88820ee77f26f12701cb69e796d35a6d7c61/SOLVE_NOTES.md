# Visible-only solve notes

All four visible demonstrations preserve the gray/guide cross and replicate the two-color motif into the other three guide-defined quadrants. The horizontal axis is the row containing all color 6 except that the crossing cell may be 5 or 6; the vertical axis is similarly the column of color 5 with at most the crossing cell changed to 6.

Hypothesis: for each cell whose color is not 0, 5, or 6, keep the original and write the same color at its reflection across the vertical guide, across the horizontal guide, and across both guides. The output keeps the same dimensions and never recolors the guides.

The visible examples cover motifs initially in all four quadrants and show both possible crossing colors, so the guide is detected by its near-full line rather than requiring an unbroken line of one color. I implemented that rule directly and did not inspect the reference rule during this solve episode. Earlier rule exposure is necessarily yes because this is the assigned generator I just repaired.
