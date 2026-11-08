# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure before this blind solve: none to task `c5dd8036311b`; I opened only
this episode's visible `challenge.json` after preparation.

Hypothesis: the nonzero horizontal row is a blue baseline.  Every non-blue marker
raises a vertical pole upward.  The pole's cap retains the marker color and its
interior is blue.  Across all visible examples, red (2) has height four above the
baseline and azure (8) has height three; adjacent markers create adjacent poles.
The first two examples isolate red height and run behavior, while the third
contains both colors and distinguishes their heights.  The tests contain only
azure markers, so each should add an azure cap three rows above the baseline and
two blue cells between cap and baseline.

Implementation copies the grid, handles each 2/8 marker independently, and clips
at the top rather than allowing Python negative-index wraparound.  Remaining
uncertainty: the unseen generator may define more marker colors, but the visible
training evidence supports exactly the two observed mappings and the queries use
only 8.
