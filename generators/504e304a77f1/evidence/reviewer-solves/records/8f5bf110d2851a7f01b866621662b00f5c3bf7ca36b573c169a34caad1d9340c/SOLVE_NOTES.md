# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — ranked object relocation

Visible evidence suggested that each non-background loose component is moved into one hollow rectangular frame while preserving its color, orientation, and exact cell pattern. I classified full monochromatic rectangle borders as frames, ranked loose objects by occupied-cell count, ranked frames by interior area, paired them in ascending order, erased the loose originals, and centered each object's bounding box in the assigned interior using floor offsets for odd slack.

Probes:
- Added `test_solution_visible.py` against all three public training pairs.
- Confirmed the test first failed on the untouched `NotImplementedError`.
- Implemented monochromatic 4-connected component extraction and exact hollow-border recognition.
- `python3 -m pytest -q WORK/solve-blind/test_solution_visible.py` then passed (1 test).

Alternatives considered: matching solely by bounding-box dimensions or nearest spatial frame. The examples instead consistently support ordinal matching by object cell count and frame interior capacity; spatial proximity is contradicted by several pairs. Remaining uncertainty is tie-breaking if two objects have equal cell counts, which the visible examples do not exercise.
