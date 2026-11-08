# Post-repair public-example solve notes

## Evidence boundary and exposure disclosure

For this main-target solve I independently read only WORK/solve/README.md and WORK/solve/challenge.json. I have not opened the generator, Racket rule, canonical task data, private .review material, prior main-target source or solution notes, or a reference solution tool. I will use only this public challenge, my newly written solution and notes, and visible checker feedback.

The team/root agent had earlier main-rule authoring exposure before this solve. Therefore the finish declaration must be earlier-exposure YES even though this solving agent independently saw only the present public challenge for the main target. No reference was consulted during this solve. I previously completed a different public-only blind episode, but have not read any of its files for this main-target solve.

The parent supplied the prepare-bound generator SHA as 7a43eacd6626e8c595ea24c4a7c75874d6e40993598f3cc75dfc3b58ffdb3a3b. That is provenance metadata, not rule evidence; I have not opened the generator to inspect or hash it.

## Observations and first hypothesis

Each input has a solid one-cell border on one side and many hollow 3 by 3 squares. The square centers are zero and the eight boundary cells all have one color. The squares lie on a regular lattice with a four-cell step. Reading each square as one cell yields a smaller grid with spaces between some colored cells.

The output preserves the number of squares of each color: the 56 input cells of color 9 correspond to 7 output cells, the 56 of color 2 correspond to 7, and the 120 of color 8 correspond to 15. The 30 border cells disappear. This supports reducing each hollow square to one colored cell rather than treating each individual input pixel as an object.

The border indicates a packing direction obtained by moving clockwise around the four sides: top means right, right means down, bottom means left, and, by the same cycle, left means up. Within every affected row or column, remove zeros, retain the order of the colors, and align the remaining cells to that side. Crop the unused extent on the packed axis to the largest occupied row or column count.

- Example 0 has a top border. Its decoded rows contain 3, 4, 6, 2, 6, 4, and 4 colored cells. Packing them right produces a 7 by 6 output. For instance, the top decoded row contains a 9 followed by two 8s, and becomes [0, 0, 0, 9, 8, 8].
- Example 1 has a right border. Packing its decoded columns down produces the displayed 6 by 7 output while preserving each column's color order.
- Example 2 has a bottom border. Packing its decoded rows left produces the displayed 7 by 6 output. Its first decoded row has two 8s followed by a 9, which becomes [8, 8, 9, 0, 0, 0].

Query 0 has a left border, so the cyclic rule predicts upward packing. Query 1 has a top border, so it predicts rightward packing; the color-3 group must retain color 3. These are hypotheses from visible inputs, not private-label observations.

## Scope assumptions

The code detects the uniform nonzero border rather than requiring a particular border color. It detects the hollow-square pattern and infers lattice steps from the greatest common divisor of observed row/column gaps. The public data establish only 3 by 3 hollow cells on a regular lattice and a single complete border; handling other encodings is not established by these examples. All visible square positions are compatible with the inferred steps.

## Genuine attempt log

Attempt 1 implements hollow-square decoding followed by stable packing in the clockwise border direction. I will test it because it accounts for the output color counts, color order, dimensions, and all three shown border orientations. No failed attempt has been suppressed or fabricated.
