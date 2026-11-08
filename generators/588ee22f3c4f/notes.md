# Working notes: 588ee22f3c4f

## Current decision — review-a5e9db7acb965a8a

**Base defect → repair.** The exact canonical program mirrors the motif across
the full-grid row axis when the two guides share a row, and across the full-grid
column axis when they share a column. The selected generator placed motifs on
the opposite, guide-relative side and therefore taught a different rule.
`generator.py` 3.0.0 now places same-row motifs strictly in the top half and
same-column motifs strictly in the left half, leaves reflected partners empty,
uses strict controls, and supports 7×7 through substantive 30×30 scenes. The
canonical Racket program remains unchanged (`RULE_HASH = 6f11c3f4c1e7`).

**Parametric family.** `followup ∈ {canonical, mirror_bridge}` is fixed for an
episode. The default returns the exact canonical full-grid reflection.
`mirror_bridge` uses the reflected partners Stage A creates to derive every
source-to-partner span, then fills the background strictly between each pair.
The protected counterfactual extends each source by only one cell; every audited
scene separates it from the full bridge.

**Teaching/export contract.** The adapter supports 2–6 demonstrations and four
distinct controller-side queries on matched inputs. Both reflection orientations,
multiple span lengths and motif counts, stable query prefixes, and one-query
private-safe public projection are exercised.

**Retained evidence.** Five original labels and two ordinary base draws passed
the source-bound authoring preflight. Four parametric jobs (both settings,
seeds 0 and 17) passed protected Racket and demo-only setting identification.
The reusable audit covered 32 seeds, 8,320 labeled pairs, 320 causal
separations, 40 protected family labels, and 20 protected counterfactual labels,
including a 30×30 bridge case. The final staged task suite is 14/14 green; the
public projection has 16 one-query views, four first-turn checks, and 24
private-field invariance mutations with no findings.

**Packet compatibility.** The immutable record stores `test` as a singleton
pair object, while the bundled base preflight assumes a list. The tested
`preflight_compat.py` launcher normalizes only that in-memory iteration, leaves
the catalog untouched, and delegates source binding, drift checks, native
execution, and receipt writing to the bundled implementation.

**Remaining gate.** This is reviewer-ready authoring evidence only. The owner
must integrate these exact bytes, inspect the repaired base, run fresh native
qualification, and accept the exact source. No training admission occurred.
