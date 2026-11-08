# 8f10b83435aa — three-panel majority merge

Three aligned width-4 panels are separated by full-height color-5 columns at input columns 4 and 9. At each panel-local position, the output is color 8 exactly when at least two of the three panels are occupied; otherwise it is 0. Output shape is the common panel height (6 or 7) by 4.

Generator `2.1.0` constructively includes both sides of the threshold in every grid: 3–9 one-panel negatives, 6–10 majority positives, at least three pair-only positives covering all panel pairs, and 1–3 triple positives. Each panel has a singleton temptation, so union, all-three-only and any single-panel-copy shortcut is contradicted locally. Fixed role colors and the 14-column layout remain canonical constraints.

Public exact axes are `panel_h`, `n_majority`, `n_singletons` and `n_triples`; every value is recoverable from pixels and legal in every band. Difficulty rotates complete default choice lists rather than narrowing domains. Unknown/invalid controls fail loudly. The semantic contract declares a Python rule mirror, strict teaching validator, five rivals/witnesses and a two-demonstration lesson hook with arbitrary query rotation.

Canonical Racket rule hash `bd5f126e874d` is unchanged. Final generator SHA-256 is `a435a00bc4b849d31965afb03b669f2d60df069f84b43f79f1fd9c6225f80b08`. The final 12-stage battery and 23 portable task tests pass; a 300-lesson/900-rotation census found no ambiguity among declared rivals. See root `REVIEW.md`, task `notes.md`, tests and `workspace/README.md`. Approval remains derived by catalog intake; this summary is not approval.
