# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — starter baseline

- Earlier exposure before this solve: none to this task's rule, generator, private labels, or prior solution notes.
- Probe: ran the visible-only checker on the untouched starter.
- Observation: `NotImplementedError`; 0/3 visible examples executed successfully. This was a diagnostic baseline, not a candidate rule.

## Revision 2 — row-local color key

- Observation: every non-footer row contains exactly one color other than background `0` and gray `5`. Most keys are at column 0; a row crossing the gray payload may place the same key farther right. The last row is entirely gray.
- Hypothesis: preserve `0` and the embedded key. Replace every gray cell in an ordinary row with that row's key. The special first row starts `[0, key, ...]` and acts as a legend/header, so its gray cells erase to `0`. Preserve the all-gray footer literally.
- Alternatives considered: connected-component flood fill cannot explain the examples because gray areas of differently colored row bands are vertically connected; carrying a color from the first column also fails on rows whose key is embedded inside gray cells.
- Implementation: derive the unique non-`{0,5}` value independently for each row, handle the encoded header and footer explicitly, and otherwise recolor only gray cells.
- Remaining uncertainty: unseen malformed rows with zero or multiple keys are left unchanged; the visible tasks consistently have one key per payload row.
