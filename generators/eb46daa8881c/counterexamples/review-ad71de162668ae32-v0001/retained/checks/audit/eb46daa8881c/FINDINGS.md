## eb46daa8881c

**Reproduced exact-control defect and existing shortcut coverage gap; findings only.**
Audited source SHA-256 `fb16f7f5f7e35c5b1aa7da30a12d192794c7075f8ac3416df5b570ed193e1671`;
executed canonical rule hash `bf2fe6881845`. No source was edited.

**A1 — Ignored exact color-count controls.** `generate(0, 0, difficulty="hard",
palette_size=1)` returns three nonzero colors and exactly the same grid as the
unoverridden call. `n_distinct_colors=1` has the same defect. Both are declared
integer controls with allowed range 1..8, and the resulting grid passes the
generator's hard validator. This is a direct generated-input API defect, not a
contrived off-domain input. Exact requests, grids and input hashes are in
`checks/audit/eb46daa8881c/probe.json`; Racket execution of the resulting grid is
entry 4 of `checks/audit/eb46daa8881c/racket.json`.

**A2 — Clean-diagonal shortcut remains supported by the corpus.** The rival
recolors a plus center only if all four diagonal neighbors are zero. It fits
all 3 canonical pairs and agrees with an independent Python rule mirror on
300 fresh default draws: seeds 0..99, sample index 0, in each of easy/medium/hard.
All 300 pass the corresponding validator. This is finite mirror-based coverage;
three representative generated draws were additionally executed in Racket.

The exact 5x5 counterexample keeps a color-4 plus at center (2,2) and adds a
color-6 diagonal cell at (1,1). The easy validator accepts it. Racket changes
the center to 8; the rival leaves it 4. This input is **validator-accepted but
outside the documented pure, separated-plus default distribution**. It
therefore witnesses an omitted rule distinction, not observed wrong labels in
default generation. The same-source unresolved audit
`review-50a65f644b693fed:v0001` was used as a lead; this run independently
reproduces its core concern and does not resolve or approve that finding.

**A3 — Missing verification contracts.** The source-bound combined audit exits
1: no task-local or frozen tests, and strict semantic gate exit 2 because no
semantic contract is declared. See
`checks/audit/eb46daa8881c/combined/result.json` and
`checks/audit/eb46daa8881c/combined/checks/eb46daa8881c_audit_semantic_gate.log`.
Missing tests are not a pass.

Reproducers: `checks/audit/eb46daa8881c/probe.py` and `verify.py`;
exact source/rule binding and counts: `checks/audit/eb46daa8881c/verified-summary.json`;
full command records: `checks/audit/eb46daa8881c/COMMANDS.json`.
The five retained Racket outputs are correct for the selected authority. This
audit makes no exhaustive-support, universal-identifiability or training claim.
