# Working notes: 78fd2bcdbb99

Review `review-b79217513dc660a0` repaired the base generator and added a native two-setting parametric family.

- Base defect: the previous curriculum was effectively LR/single-color, rejected canonical UD/multicolor inputs, and evaluated missing override defaults eagerly. The generator now validates exact types, schedules LR/UD plus 1–3 colors, and checks the axis actually selected by the canonical mismatch rule.
- Canonical authority: the executable canonical ledger program (SHA-256 `038edcc7127447e984bafa0c0cba02a66e7f43f9b838edcfeb56ddd824e8fc1f`) differs from the archival solution copy only in `for/sum` binder syntax. The native default is byte-identical to the executable ledger, which is what the protected worker enforces.
- Parametric family: `repair = fill | erase`; sampling is setting-independent. A counts LR/UD mismatches and selects the lower-mismatch axis (LR on ties); B fills missing mirrors or erases unmatched nonzeros on that selected axis.
- Coverage: 2–6 demos, 1–4 queries, both axes and multicolor scenes in the teaching prefix, distinct inputs, and a substantive boundary-spanning 30×30 query.
- Retained evidence: 15 final tests; four protected-worker jobs / 40 Racket labels; sole declared-setting survivor at seeds 0 and 17; protected wrong-axis causal replay; bounded shortcut audit; verified 16-view sequential public projection and first-turn privacy checks.
- Current status: reviewer-ready only. Owner source review, native qualification, and fresh acceptance remain mandatory; no training admission is claimed.
