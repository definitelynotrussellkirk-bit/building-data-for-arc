# Visible-only solve notes

## Observations

- Row 0 begins with three nonzero colors; their left-to-right order behaves as a priority list.
- Cyan (`8`) cells below row 0 form closed walls. The non-cyan cells inside each connected chamber are the units transformed.
- Each chamber contains one or more seeds selected from the three legend colors.
- The output leaves the legend and every cyan wall unchanged, while replacing every cell in a chamber with the earliest legend color present in that chamber.

Examples supporting the hypothesis:

- Train 0 legend `[6, 5, 1]`: the upper-left room contains `6` and `5` and becomes `6`; the upper-right contains only `5` and becomes `5`; both lower rooms contain `6` (one also has `1`) and become `6`.
- Train 1 legend `[9, 4, 7]`: the upper room contains `4` and `7` and becomes `4`; the lower room contains `9` and `7` and becomes `9`.
- Train 2 shows three vertical rooms and confirms that wall connectivity, rather than fixed quadrants, defines the regions.

## Implementation

Flood-fill every four-connected non-cyan region below the legend row. For each region, scan the legend left to right and paint the whole region with the first color that appears in it. Preserve row 0 and all cyan walls.

## Expected queries

- Query 0 legend `[2, 3, 1]`: the upper room contains `2` and `3`, so it should become `2`; the lower room contains `3` and `1`, so it should become `3`.
- Query 1 legend `[5, 9, 3]`: the upper room contains only `9`, so it should become `9`; the lower room contains only `3`, so it should become `3`.
