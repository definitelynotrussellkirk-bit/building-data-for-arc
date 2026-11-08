# Fresh release visible-only solve

## Exposure and episode reset

The root reviewer inspected the generator and its canonical rule earlier during
repair, so earlier rule exposure is **yes**. During this fresh solve I read only
the newly prepared public challenge and command feedback. I did not consult the
reference rule, generator, private query labels, or previous solution notes in
this episode. Reference consulted during solve: **no**.

Prior public episodes and a genuine setup/finish collision remain archived under
checks/prior-solve/. This directory was cleared, officially prepared again, and
verified to have zero attempts and no finished-notes snapshot before this candidate.
The source hash printed by prepare is
5de19b883ae5a9875abc09824ca005cdae155d345506898b60b2f0df382bf76d.

## Visible observations

The four visible pairs have input/output dimensions 8×10, 8×7, 8×9 and 5×7.
Each preserves the existing colored cells and the single 9. In example 0, the
plus centered at (6,1) is copied to center (6,7), opposite the 9 at (6,4).
Example 2 moves its plus from center (1,6) to (5,4), opposite (3,5).
Examples 1 and 3 supply asymmetric shapes and boundary cases: visible target
cells remain when other reflected positions fall outside the existing grid.

## Candidate and check

The first candidate in this clean episode preserves the input and maps every
nonzero, non-9 source cell (r,c) to (2*ar-r,2*ac-c), adding only targets within
the existing dimensions. Color is preserved. I compared the candidate against
all four public labels before the official check; all four matched. No revised
hypothesis or fabricated negative candidate was needed.

The official check below records execution and visible-example results. The two
masked queries remain unknown; I did not inspect or score their private answers.
Stopping is justified by the visible matches and completed execution, not by a
claim of masked-query correctness.
