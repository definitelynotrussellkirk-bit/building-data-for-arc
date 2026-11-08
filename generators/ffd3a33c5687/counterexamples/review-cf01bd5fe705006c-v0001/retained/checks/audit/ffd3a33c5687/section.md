## ffd3a33c5687

**Status: reproduced teaching ambiguity — A1-NUMERIC-RANK.** Findings-only audit; the audited target and shared sources are unchanged.

Audited generator SHA-256: `419d368c4fae796aaeaa52c5d2ee1965b106960f53e73f8a9980208d6a900ae7`. Canonical rule hash: `4276b16a10bb`; exact ledger-source SHA-256: `a963032e344c5c1d07c4a3ec260fb5e69dccae3c2728fba2f5c8fe65836b10aa`. The public Racket receipt separately binds the executed callable SHA-256 `72fe4596006bb59ff77b1e6dc85bdcc9b4d29cf540b1685e3dd5a42702acb826`.

**Reproduction.** Generate the ordinary medium-band lesson with seed `0`, no overrides, and consecutive sample indices `0, 1, 2, 3`; use the first three pairs as demonstrations and the fourth as query. The undeclared rival “complete each mirror orbit using its numerically smallest nonzero color” matches every demonstration but changes the query:

| Pair | Left/right conflict colors | Racket winner | Numeric-minimum winner |
|---|---|---|---|
| Demonstration 0 | 2 / 7 | 2 | 2 |
| Demonstration 1 | 8 / 9 | 8 | 8 |
| Demonstration 2 | 2 / 5 | 2 | 2 |
| Query 3 | 4 / 3 | 4 | 3 |

The query differs at zero-based cells `(1, 0)` and `(1, 8)`: Racket returns `4`, the rival returns `3`. All four generated inputs are distinct, pass the current validator, and produce nonidentity Racket outputs. Both numeric-minimum and numeric-maximum rivals also fit all **4/4 labeled canonical pairs**. The existing two declared rivals each match **0/3** demonstrations, while `lesson_identifiable` returns `[]`; its finite contract omits the numeric-rank ambiguity.

**Measured evidence.** A bounded Python search stopped after six lesson candidates and 12 generated positions. One `Catalog.apply(..., reference="canonical", check_generator_domain=True)` invocation then executed the four generated inputs and four labeled canonical inputs: **8/8 valid Racket outputs**, all generator-domain checks valid. Exact inputs, actual outputs, rival outputs, seeds, hashes and differing cells are retained in `checks/audit/ffd3a33c5687/finding.json`, with the source-bound execution receipt in `checks/audit/ffd3a33c5687/racket.json`. Reusable search/verification code is `checks/audit/ffd3a33c5687/probe_numeric_rank.py`; command records are `checks/audit/ffd3a33c5687/commands.json`.

**Suggested follow-up.** Add numeric-minimum and numeric-maximum conflict rivals, then provide demonstrations with opposing numeric conflict orderings under the intended lesson and query-rotation policies. This audit supplies the counterexample and makes no task repair.

**Limits and retained failure.** This is one exact default-generated consecutive lesson, not an incidence estimate or exhaustive induction result; no canonical-label defect was found. The first evidence wrapper exited 1 after incorrectly comparing ledger-source and wrapped-callable hashes, although all eight Racket executions had completed. `checks/audit/ffd3a33c5687/verify-attempt-1.json` and the original wrapper preserve that failure. Corrected receipt verification exited 0 and reused the same Racket outputs. No solve directories, hidden solve labels, full batteries or further assignment draws were used.
