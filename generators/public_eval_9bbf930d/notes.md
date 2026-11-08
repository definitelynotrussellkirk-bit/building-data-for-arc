# public_eval_9bbf930d — current design

Interpret the left magenta column as candidate moving markers, on orange
background. Launch only a marker whose first encountered upper/lower rail
pair is equal-colored. Scan across any leading empty margin (the originals
include a one-cell extra margin). Move through background in the current
heading. Matching perpendicular wall colors update the active guide color.
At a same-guide-color obstacle, take the uniquely open perpendicular turn;
stop at a different-color obstacle, a blocked/ambiguous turn, or the boundary.
Only the launch cell and final stopping cell change.

Variant `guide_update=entry` keeps the entry color instead of adopting the
colors of subsequently entered corridors. Default `local` is the exact new
reference. The non-collapsing intermediate is the traced heading and active
input-derived guide color; these determine whether a later obstacle turns or
stops the marker. The first two teaching examples require color handoffs after
different numbers of bends and include a black-wall foreign-obstacle probe.

Plan/checks: original four-label regression; deterministic multibend corridor
sampler; finite-rival lessons and count-prefix tests; strict public projection;
protected-Racket audit, authoring preflight, and guide-state causal replay.
Only assigned task-local source is changed. Owner registration and acceptance
remain separate; no training admission is asserted.

## Verified handoff

- Authored a stateful corridor-routing Racket rule and local/entry guide-color family; 4/4 original labels, 32 tests, protected audit and authoring preflight pass.
- Two settings, 2–6 demos and 1–4 source queries; full four-query banks
  are shuffled separately for one-query public turns.
- Self-audit: 64 protected Racket labels, 66 stress episodes, 16 public views.
- Preflight: both settings at seeds 17 and 43, two demos and four queries.
- Causal replay: 2 changed cells with an intentionally wrong intermediate.
- Combined final suite: 63/63. Cross-target final review: 168 episode requests
  across every supported count, plus current source/evidence hashes and
  first-turn invariance under changed private metadata and future queries.
- Historical red logs are deliberate missing-implementation tests; the second
  target also records a corrected test-fixture parameter typo. No current
  failing check remains. This is author self-review, not independent review.

Reproduce from a packet root with `python3 review.py run python3` followed by
`generators/public_eval_9bbf930d/workspace/parametric/self_audit.py --out ../checks/public_eval_9bbf930d/fresh-audit`.
After any source edit, use a NEW preflight destination and rebuild the causal
witness with `--preflight ../checks/public_eval_9bbf930d/preflight-v2/preflight.json --out NEW`.
The preflight receipt, execution, official-label report and causal witness are
authoring evidence only. Owner registration, source review, native qualification
and fresh acceptance are pending. Training admission remains false.

Current bound evidence uses preflight-v2, audit-v2 and causal-v2. Initial packaging exposed an exact-schema mismatch: the Racket marker must contain only backend/protected; full identity is now stored separately as racket_identity. The writer is fixed and both actual protected executions and source bindings were regenerated. The two owner-schema regressions now supplement the 63 task tests.

Owner worker API correction: use the existing worker input/findings contract. Earlier author checks used the incompatible return convention. Reference programs are unchanged; owner preflight and native acceptance determine current readiness. See evidence/owner-base-api-repair.json.

## Current repeated-parent reconciliation

Preserve exact local/entry programs and corrected dict-return ordinary generator. Add complementary route constructor; retain incumbent finite-rival teaching prefix and strict shuffled query projection. Alternative adaptive/initial semantics are represented by the retained programs on the checked domains, not new redundant settings. Current evidence resides in evidence/repeat-sixth-union. Private native acceptance and root publication are separate.
