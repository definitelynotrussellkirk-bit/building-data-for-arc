## 615b0cf22405

**Classification: Racket-confirmed teaching defect; a canonical-fitting overlap-policy rival survives an ordinary lesson.** This findings-only audit leaves the target source unchanged. The audited v2.2.0 source SHA-256 is `046befc74b1d36f3e73167fef9dbc90823c1b3893b35bc98288260763ac07306`; the selected canonical Racket rule hash is `ed22871432d2`.

The generator only checks that newly placed endpoint cells are empty. It can therefore place two different-colored horizontal pairs on the same row with overlapping interiors, or the analogous vertical arrangement. The selected rule resolves multiple matching colors by choosing the **lowest numeric color**. None of the three labeled canonical examples exposes this same-direction tie. A rival that chooses the **highest numeric color**, while preserving the selected rule's vertical-over-horizontal and original-cell precedence, matches all **3/3 canonical labels**.

An ordinary production lesson already exhibits the ambiguity at `seed=0`, default difficulty, demonstration sample indices `0,1,2`, and query index `3`. All four inputs pass the target's `self_check`; their shapes are 18×16, 22×12, 26×13, and 19×11. The rival matches all three demonstrations but disagrees with the query at three zero-based cells:

| Cell | Authoritative output | Rival output |
|---|---:|---:|
| `(14,3)` | 2 | 8 |
| `(14,5)` | 2 | 8 |
| `(14,6)` | 2 | 8 |

In that query, color 2 has endpoints `(14,1)` and `(14,9)`, while color 8 has endpoints `(14,2)` and `(14,7)`. Their overlapping requested fills require a color-priority decision that neither the canonical examples nor the three generated demonstrations identify. The existing color-5 endpoint at `(14,4)` is preserved under both policies, so it is correctly absent from the disagreement list.

The probe executed the three canonical inputs and the four generated lesson inputs through supported `Catalog.apply`, using the selected canonical Racket authority. All **7/7** authoritative outputs matched the independent minimum-color pixel oracle. The receipt rule hash matches the catalog. The generator still declares no `RULE_HASH`, `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, or `lesson_identifiable` hook.

**Suggested owner action:** either exclude overlapping spans of different colors on the same row/column, preserving the canonical task's demonstrated geometry, or explicitly teach and check the minimum-color tie policy in every relevant demonstration window. If retaining these overlaps, declare minimum/maximum tie-policy rivals, add a same-direction overlap witness and a lesson check, and pin the selected rule hash. This is separate from the two existing unresolved reports about horizontal-versus-vertical crossing precedence: that older rival fits 0/3 canonical labels; the rival reproduced here fits 3/3. Those earlier findings were not cleared by this audit.

**Evidence and scope:** `checks/audit/615b0cf22405/evidence.json` retains the exact grids, Racket outputs, rival outputs, source identity, query differences, and per-input/output hashes. Reproduction code is `checks/audit/615b0cf22405/probe.py`; exact commands and runtime output are in `checks/audit/615b0cf22405/commands.json`, `checks/audit/615b0cf22405/probe.stdout.log`, `checks/audit/615b0cf22405/probe.stderr.log`, and `checks/audit/615b0cf22405/probe.exit`. The bounded search found this lesson after four generated pairs. No full battery was run, and this audit does not estimate ambiguity frequency or claim exhaustive coverage.
