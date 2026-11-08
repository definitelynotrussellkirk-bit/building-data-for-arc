# Workspace

The selected implementation is ../generator.py. Workspace tools are diagnostics
and are never automatically selected as generators or label authorities.

## Reusable tool

probe_minimal_impostors.py reproduces the five named minimal-shape mutations
used by the shared linter, preserves every exact input and validator result,
and obtains actual reference outputs for accepted mutants through public
Catalog.apply. It accepts a task ID, so it can help review other generators.
Read MINIMAL_IMPOSTORS_USAGE.md for the bounded command, report contents,
and limits. It never suppresses lint or grants approval.

## Tests and retained reports

../tests/test_header_repeat.py uses reviewer_support.find_root and canonical_pairs
for both checkout and portable-runtime layouts. Its independent row-slice oracle
is anchored to the three canonical labeled pairs. Focused tests cover exact
controls, malformed and lawful edge cases, output-size boundaries, the actual
rival declarations, and all five cyclic lesson starts.

The review return contains before, intermediate, and final receipts under checks/,
including the 300-lesson Racket census and minimal-impostor evidence. Root reports
REVIEW.md, DECISIONS.md, QUESTION_ANSWER.md, and FEEDBACK_TO_CODEX.md explain
the repair, rejected alternatives, finite-coverage limits, and retained warning.
