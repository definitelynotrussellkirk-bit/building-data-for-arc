# Blind solve notes — 061566027b67

## Observations

Each 16×16 input is mostly isolated colored noise plus one conspicuous solid,
axis-aligned, nonzero rectangle.  The output erases everything except the
largest fully monochromatic rectangle:

- train 1: color 9, rows 2–3 and columns 4–9 (2×6, area 12)
- train 2: color 2, rows 8–10 and columns 1–3 (3×3, area 9)
- train 3: color 6, rows 4–7 and columns 4–6 (4×3, area 12)

The surrounding same-colored cells are distractors and are not included unless
they belong to the complete rectangle.  For example, train 3 has an extra 6 at
row 4, column 7, but the lower rows do not support that fourth column.

## Hypothesis

Return a same-sized black grid containing only the maximum-area solid rectangle
of one nonzero color.  Require both height and width to be at least two so a
long accidental run in the random noise cannot defeat the intended 2-D object.

## Probe

I enumerated all row intervals.  For each interval I found consecutive columns
whose cells all share one nonzero color.  The largest eligible candidates were
unique and exactly matched all three visible outputs.  The two test candidates
were respectively a 3×3 block of color 3 at rows 4–6, columns 6–8, and a 3×3
block of color 4 at rows 10–12, columns 6–8.

## Implementation

`solution.py` performs that enumeration and reconstructs only the best rectangle.
Tie-breaking is deterministic, but no visible example has a top-area tie.
