# Current notes: 9a7579840f41

## Intended rule

Normalize the single connected color-4 template to a top-left origin. Starting from the sole color-7 marker, trace the unique connected nonbranching color-1 wire in order. At every internal wire cell where the incoming and outgoing directions differ, stamp the normalized template with that turn cell as the stamp's top-left anchor on a fresh zero grid.

The selected Racket authority and `RULE_HASH = 7dd342fe1468` were not changed in this review.

## Current generation choices

- Exact observable axes remain `grid_h`, `grid_w`, `n_turns`, `template_size`, and `start_axis`; removed metadata-only controls remain rejected.
- Both staircase and direction-reversing path families remain in support.
- The default-only 30% prior over the three official linked profiles remains unchanged.
- Version 3.3.0 moves the marker from the old collinear extension to either perpendicular side of the first wire cell. The marker must touch exactly that first cell.
- A candidate layout is retained only when stamping the template at the first wire cell would add at least one cell outside the true turn-stamp answer. Thus every generated example distinguishes the wrong rule that treats color 7 as another wire pixel and stamps every local corner.
- `self_check` and `strict_canonical_like` now reject collinear marker entry. The executable semantic contract exposes the marker-inclusive rival, its counterexample witness, and a lesson-identifiability check.

## Evidence and decisions

The concrete repair lead was prior audit `review-d83e98f966e5d70f:v0001`: baseline version 3.2.1 always placed color 7 collinearly, so the marker-inclusive local-corner rival matched generated lessons while failing all three canonical inputs. The retained historical reproducer is under `counterexamples/review-d83e98f966e5d70f-v0001/`.

New regression tests first reproduced the collinear entry and an exact generated case where a perpendicular marker still failed to produce a visible rival disagreement. The final tests require both perpendicular sides, collinear rejection, canonical agreement of the Python mirror, and rival disagreement on every sampled generated input. The final generator also passed an exhaustive 2,800-case cross-product over all declared exact-axis values.

The strongest canonical-fitting rival found is different: ignore color 7 and stamp at every local orthogonal corner of every color-1 component. It matches all 3 canonical labels and 300/300 current generated draws, because the accepted grammar contains one connected, nonbranching, non-self-touching wire, making local corners answer-equivalent to ordered internal turns. An exact separator adds a disconnected L-shaped color-1 component; the public Racket authority ignores it while the rival adds three cells. That input is rejected by `self_check` and is not emitted. Current-source evidence is in `counterexamples/current-shortcuts/evidence.json`.

## Known limits

- Declared rival checks and finite censuses are evidence against named shortcuts, not proof of unique induction against every possible program.
- The accepted one-component wire grammar cannot demonstrate that color 7 is causally needed to choose among multiple color-1 components. Supporting that distinction would require a deliberate domain/rule expansion, not a sampler-only change.
- Inputs outside the Python teaching grammar can be partial or unsupported for the Racket program; malformed examples are not training candidates.
- This return is a candidate repair and does not itself grant training approval.
## Current reviewer considerations

Source SHA-256: `150ecbcf84e65e58c370e666f454a3a142486fe853e1eae26482bc8b507d5fd7`.

# Decisions for review-919bd811fa2df3e2

## D1 — Keep the selected rule; repair the teaching distribution

**Original state:** The selected generator used the correct canonical Racket rule but always placed color 7 as a collinear extension of the first color-1 segment.

**Decision:** Leave the Racket authority and `RULE_HASH` unchanged. Repair only the input sampler, validators, semantic contract, tests, and evidence.

**Rationale:** Public-Racket checks and the prior audit showed correct labels. The defect was that generated inputs taught a wrong shortcut, not that the authority computed the wrong output.

**Alternative rejected:** Rewriting the Racket program or changing the task domain. That would alter authority semantics without evidence of a rule defect.

**Failure mode considered:** A sampler-only change that makes some exact axis combinations impossible. A complete 2,800-case declared-axis cross-product was generated and checked after the repair.

## D2 — Use perpendicular marker entry on both sides

**Prior choice:** `start = path[0] - first_step`, forcing color 7 to be collinear with the first segment.

**New choice:** Place color 7 at either perpendicular neighbor of the first wire cell, subject to touching exactly that wire cell. Random layout shuffling exposes both sides.

**Rationale:** All three canonical inputs use perpendicular entry. This makes treating colors `{1,7}` as one wire create a false local corner at the initial color-1 cell.

**Alternatives rejected:**

- Merely varying grid size, path family, turn count, or first axis: none changes the missing entry-corner branch.
- Always using one perpendicular side: valid, but unnecessarily leaves a fixed orientation shortcut.
- Adding a new public axis for marker side: the side is observable but not needed as a user control; sampling both sides is sufficient and avoids expanding the API.

**Evidence:** `checks/tdd-red-entry`, `checks/tdd-green-entry`, and the focused two-side regression test.

## D3 — Guarantee visible rival disagreement, not just perpendicular geometry

**Observed failure:** A perpendicular marker alone was insufficient in rare layouts because the false stamp at the first wire cell could be clipped or fully overlap true turn stamps. Fixed case: seed `991083`, sample index `1414`, difficulty `easy` before the final filter.

**Decision:** Reject layout candidates unless the in-bounds false start stamp has at least one cell outside the true answer.

**Rationale:** Every emitted example should directly falsify the named marker-inclusive local-corner shortcut, rather than relying on a probabilistic lesson schedule.

**Alternative rejected:** Define the semantic witness only on the subset that happens to disagree. That would make the contract pass while leaving occasional individually ambiguous training examples.

**Evidence:** `checks/tdd-red-guarantee`, `checks/tdd-green-guarantee`, and `SEMANTIC_WITNESSES` firing on 600/600 semantic-gate samples.

## D4 — Make the canonical entry geometry part of validation

**Decision:** `self_check` and `strict_canonical_like` reject collinear entry.

**Rationale:** The sampler, canonical inputs, declared invariant, and validation should describe the same manifold. The old validator accepted the exact marker-only mutation that exposed the teaching gap.

**Alternative rejected:** Keep `self_check` broad and enforce perpendicularity only in the sampler. That would preserve a hidden mismatch between documented grammar and actual support.

## D5 — Add an executable semantic rival and lesson contract

**Decision:** Add a Python rule mirror, the `marker_inclusive_local_corners` rival, a counterexample witness, and `lesson_identifiable` with three demonstrations.

**Rationale:** Future batteries can now test the exact shortcut mechanically instead of relying on narrative audit notes.

**Limit:** This contract covers one strong wrong rule. Passing it does not prove universal identifiability.

## D6 — Do not declare the color-1-only local-corner rival as a generated counterexample target

**Finding:** Ignoring color 7 and stamping every local corner of every color-1 component fits 3/3 canonical pairs and 300/300 current generated draws.

**Decision:** Document it as an in-domain answer-equivalent shortcut, not as a `CANONICAL_SHORTCUTS` claim that the current sampler can refute.

**Rationale:** On the declared single connected nonbranching non-self-touching wire domain, local corners and ordered internal turns coincide. The exact separating input requires a disconnected extra component, which `self_check` rejects and the generator does not emit.

**Evidence:** `repo/generators/9a7579840f41/counterexamples/current-shortcuts/evidence.json`.

## D7 — Preserve existing exact axes and canonical-profile prior

**Decision:** Keep the five exact structural axes and the default-only 30% linked-profile prior unchanged.

**Rationale:** They were already observable and validated; unrelated API or curriculum changes would add risk without addressing the audited defect.

## Current audit assessment

The source-bound reviewer audit found no issue in its finite checked scope. See `evidence/current-audit-assessment.json` for source identity, scope and reviewer-reported evidence basis. The current audit is explicitly closed as `no_issue`; this does not certify all inputs or undeclared rivals.
