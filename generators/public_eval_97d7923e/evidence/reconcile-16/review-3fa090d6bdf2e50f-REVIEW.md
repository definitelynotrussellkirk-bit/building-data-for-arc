# Review — `review-3fa090d6bdf2e50f`

- **Sources:** new `public_eval_97d7923e` and `public_eval_da515329` homes; generator versions `1.0.0`.
- **Defect → repair:** both public parents lacked general Racket rules and native parametric families; both now have standalone generators, exact canonical references, adapters, tests, audits, and replay tooling.
- **Official labels:** **8/8** matched protected Racket—four for each parent.
- **Focused verification:** **10/10** final tests passed.
- **Authoring preflight:** **8/8 jobs** passed across both settings and two fresh seeds per family.
- **Adversarial support:** **48 jobs**, **368 pair claims**, and **18 declared rival rules** with zero survivors.
- **Sequential exports:** **1,024 views**, **1,024 hidden/future-field mutations**, and **256 positive controls** passed.
- **Causal replay:** both source-bound witnesses are `reviewer_replayed`; counterfactuals changed 50 and 244 final cells.
- **Reference changes:** both `reference.rkt` files are newly authored general rules; each default `canonical.rkt` is byte-identical.
- **Needs attention:** these are reviewer-ready prototypes only—owner registration, unchanged native qualification, exact-source acceptance, and training admission remain pending.
- **Review strength:** final source review was an author self-review; finite rival checks do not prove universal rule uniqueness.

## `public_eval_97d7923e` — legend-ranked rods

The canonical rule finds vertical rods whose equal-colored endpoints surround a uniform payload. Detached legend multiplicities select the corresponding endpoint-colored rod by descending payload length, then recolor the selected payload to its endpoint color. The alternate performs that selection first, derives the selected rods and their lengths, then recolors the unique longest selected complete rod to color 9.

A retained regression closes a top-row-only legend shortcut by spreading every repeated legend color across rows while keeping legend columns disjoint from rod columns. Every retained episode supports 2–6 demonstrations and four distinct private queries; the final query is exactly 30×30. The causal case deliberately makes the globally longest raw rod unselected, so replacing the selected-set intermediate changes 50 cells under protected Racket.

Key evidence: `checks/public_eval_97d7923e/preflight/preflight.json`, `checks/public_eval_97d7923e/audit-final.json`, `checks/public_eval_97d7923e/export-audit-final.json`, and `checks/public_eval_97d7923e/causal/witness.json`.

## `public_eval_da515329` — cropped four-arm square spirals

The canonical rule identifies a zero center with four equal color-8 arms, grows a north-seeded square-spiral branch on the infinite lattice, rotates that branch through all four orientations, unions the branches, and crops to the original canvas. The alternate derives the four visible in-bounds branch populations after that construction and recolors the unique largest visible branch to color 9.

A retained regression closes a fixed-direction shortcut by forcing different unique winners in the first two demonstrations. The constructive sampler covers arm lengths 1–6, varied canvas placement, 2–6 demonstrations, four distinct private queries, and an exact 30×30 stress case. Replacing the input-dependent visible-count intermediate with a fixed north branch changes 244 cells under protected Racket.

Key evidence: `checks/public_eval_da515329/preflight/preflight.json`, `checks/public_eval_da515329/audit-final.json`, `checks/public_eval_da515329/export-audit-final.json`, and `checks/public_eval_da515329/causal/witness.json`.

## Reusable verification tools

- `checks/build_public_witnesses.py` executes both correct and counterfactual programs under protected Racket and emits package-compatible source-bound witnesses plus fresh replay records.
- `checks/verify_handoff.py` re-hashes every preflight-bound source, checks canonical/reference byte identity, validates all retained receipts, verifies relocated ordinary generators, and rejects owner/training overclaims.
- `checks/final-handoff.json` is the compact final result of that verifier.

## Remaining limits

No catalog, canonical authority, approval, or shared runtime was changed. The preflights are authoring evidence, not owner qualification. The owner must register each exact source/provenance record, reconcile any source collision, accept the source review, run unchanged native qualification, and perform fresh acceptance separately for both families.
