# Visible-only solve work log

This is a reviewer-authored work log, not a captured token-level model trace. There are no recorded token probabilities. I previously read the generator and Racket authority during the repair phase, so this attempt is **not blind**. After `solve_episode.py prepare`, I read only `solve/challenge.json` for puzzle evidence, wrote the files in this directory, and ran the visible-only checker. I did not consult the generator, reference solutions, private query labels, or previous explanations during this solve phase.

## Revision 1 — row-wise propagation with a persistent final column

The first visible demonstration has a source 4 at row 1, column 0 of a 3×3 grid. The output extends 4 rightwards, then down the final column. The second has several differently colored sources in a row: its output retains the changes from 5 to 2 to 6, and the following occupied row changes the final-column carry to 8. The third has two sources of color 3 in separate rows, and both rows extend horizontally.

The candidate therefore scans each row left-to-right, carrying the latest nonzero color. The final column also carries the most recent occupied row's last source color downwards. The implementation does not modify its input and accepts arbitrary rectangular dimensions rather than memorizing the examples' sizes.

`visible_experiments.py` compares this candidate with two **intentional teaching negatives**, not accidental unsuccessful revisions: retaining only the first source in a row, and retaining only the first occurrence of a color. These probe why the second and third demonstrations matter. The exact visible-match vectors are saved in `visible_experiments.json`. Additional tiny checks exercise an empty background, propagation below a source, and input immutability; these are inferred-rule sanity checks, not hidden-label evidence.

Only one submitted solution revision was needed. The official checker reports visible training agreement and query execution, not private query correctness. I stopped after the visible examples passed and both queries executed. Earlier exposure: yes. Reference consultation during this phase: no. Hidden query accuracy remains unscored here.
