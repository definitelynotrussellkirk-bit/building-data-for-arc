# Working notes: db4cb6bcf6fe

## Reviewed rule

Each nonzero color is one object. Close its cells in this order:

1. For each occupied row, fill from that row's minimum to maximum occupied column.
2. In the row-closed result, for each occupied column, fill from that column's minimum to maximum occupied row.
3. Normalize the completed cells by translation.

Sort objects by color and emit the equality matrix (`5` diagonal, `8` equal, `0` unequal). The selected Racket authority was retained and pinned by `RULE_HASH = 38e335f43e6f`.

## Baseline defect

Version `2.3.0` emitted only four-corner rectangles. The closure step did not distinguish any lesson from three simpler rules:

- normalized raw-marker equality;
- bounding-box equality;
- completed-area equality.

It also had eleven unreliable axes, dead textures, ordinary-domain negative fixtures, unknown-key acceptance, no semantic contract, and no exact canonical-profile coverage.

## Reviewed construction

- Exact scene profiles: `canonical_9x12` and `canonical_10x14`.
- Exactly four colors and four raw cells per color.
- Four completed-shape classes, each with three distinct raw realizations.
- Every completed class has bounding box `3x5` and area `7`.
- Relation schedules: `2+2`, `2+1+1`, and `3+1`.
- Nuisance variation: colors, placements, class labels, raw variants, and whole-scene flips/180° rotation.
- Unknown or invalid overrides fail loudly.

## Executable review claims

`CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `strict_canonical_like`, and `lesson_identifiable` encode the semantic claims. `EXPECTED_OUTPUT_CODOMAIN = 13` records the complete nontrivial equality-matrix language for four labeled objects.

Run the focused regression suite from `repo/`:

```bash
PYTHONPATH=shared/runtime pytest -q generators/db4cb6bcf6fe/tests/test_generator_db4cb6bcf6fe.py
```

The deterministic counterexample used in `QUESTION_ANSWER.md` is seed `0`, sample index `0`, difficulty `easy`.

## Remaining scope

The generator intentionally fixes four objects and excludes all-equal/all-distinct relation partitions so each ordinary lesson contains both a positive and negative comparison. It does not claim to teach arbitrary matrix cardinality or rotation-invariant shape equality.
## Current reviewer considerations

Source SHA-256: `ef5e4911ca717c3fffbdbe9748afb6dc85c1def529bec0a6f9a120a3d6e3ce26`.

# Design decisions for `db4cb6bcf6fe`

## D1. Keep the authoritative rule unchanged

**Original rationale:** Unknown from the imported generator notes.
**Observed evidence:** The canonical rule passes all canonical examples, 120/120 generated executions, re-entrancy, and 120/120 agreement with an independently written Python mirror.
**Alternatives considered:** Rewrite or cosmetically normalize the Racket program; select the divergent archival text.
**Decision:** Keep the selected canonical Racket authority unchanged and pin it with `RULE_HASH = "38e335f43e6f"`.
**Probe:** Rule-smoke, authority-sync execution parity, and direct execution of the exact shortcut counterexample.
**Failure mode controlled:** A generator silently drifting away from the rule it supposedly teaches.
**Limitation:** One archival source remains textually divergent, although execution parity passes.

## D2. Use exact canonical canvas profiles

**Original rationale:** The prior generator chose larger, difficulty-dependent grids; no reason was retained for departing from canonical dimensions.
**Alternatives considered:** Preserve broad `grid_h`/`grid_w` axes; use only one canonical size; opt out of the profile floor.
**Decision:** Expose one `scene_profile` axis with exact `9x12` and `10x14` profiles and alternate them deterministically.
**Probe:** `observe_overrides`, profile-floor sampling, and focused override tests.
**Failure mode controlled:** Training on a visibly different task family or silently clamping requested dimensions.
**Limitation:** The public surface intentionally does not support arbitrary dimensions.

## D3. Fix object and palette cardinality at four

**Original rationale:** The imported code declared four pairs while also carrying misleading cardinality axes. The canonical task has four nonzero colors in each example.
**Alternatives considered:** Vary from three through five objects; retain `n_pairs`, `n_classes`, and palette-size axes.
**Decision:** Emit exactly four colors, four marker cells per color, and a `4x4` output.
**Probe:** Self-check, canonical profile checks, and exact output-codomain enumeration.
**Failure mode controlled:** Axes that claim variability but cannot be honored consistently or change the task interface.
**Limitation:** It does not teach generalization to other matrix sizes.

## D4. Replace rectangle corners with closure-sensitive sparse motifs

**Original rationale:** Rectangle corners were apparently chosen as an easy way to make row/column closure visible, but they make closure-equivalence identical to raw-marker equivalence.
**Alternatives considered:** Random point clouds with rejection sampling; rectangles of varied dimensions; hand-authored adversarial motifs.
**Decision:** Use a small audited motif grammar. Each class has three distinct four-point raw variants that map to one closure, while every class shares a `3x5` bounding box and completed area `7`.
**Probe:** Exhaustive motif assertions in the focused suite and 600 draws per semantic witness.
**Failure modes controlled:** Raw-marker equality, bounding-box equality, completed-area equality, unstable rejection sampling, and accidental empty/one-dimensional objects.
**Limitations:** The grammar is deliberately finite and uses only four closure classes.

## D5. Schedule relation structures instead of sampling them accidentally

**Original rationale:** The prior implementation tried to create repeated and unique signatures through several coupled random axes.
**Alternatives considered:** Random class labels with rejection; always use two equal pairs; enumerate every set partition directly.
**Decision:** Cycle among `2+2`, `2+1+1`, and `3+1`, then shuffle symbolic labels across colors and closure classes.
**Probe:** Every output must contain both `8` and `0`; all thirteen labeled matrices must be realized.
**Failure modes controlled:** All-equal lessons, all-distinct lessons, a collapsed output alphabet, or one memorized relation layout.
**Limitation:** The all-equal and all-distinct partitions are excluded because the reviewed training manifold requires both positive and negative comparisons in every lesson.

## D6. Vary only nuisance factors that preserve the rule

**Original rationale:** The imported generator exposed many nominal axes, several of which were dead or semantically overlapping.
**Alternatives considered:** Keep texture/palette/density controls; add rotations per object; use arbitrary color permutations.
**Decision:** Randomize colors, class-label assignment, disjoint slot assignment, offsets within canonical profiles, and one whole-scene transform (`identity`, row flip, column flip, or 180° rotation).
**Probe:** Determinism test, global-RNG-state test, semantic witness suite, and rule-smoke mirror comparison.
**Failure modes controlled:** Per-object transformations changing equivalence unexpectedly, object overlap, position leakage, and color-order leakage.
**Limitation:** No 90° rotation is used because the task compares orientation-sensitive normalized shapes rather than shapes modulo rotation.

## D7. Expose one truthful override axis

**Original rationale:** The previous eleven-axis surface included singleton domains, dead textures, difficulty-clamped ranges, and negative fixtures in ordinary domains.
**Alternatives considered:** Repair every legacy axis; mark nonfunctional axes diagnostic; retain negative texture overrides.
**Decision:** Remove the misleading surface and expose only `scene_profile`, which can be generated exactly and inferred exactly from a returned grid. Reject unknown keys and invalid values.
**Probe:** 270-draw override battery plus focused round-trip and typo tests.
**Failure mode controlled:** False claims that an override changed data when it was ignored, clamped, or incompatible.
**Limitation:** Review tools that expected the legacy axis names must use the simplified contract.

## D8. Make shortcut resistance executable

**Original rationale:** The baseline had no semantic contract, so generic checks could validate syntax and diversity without knowing that closure itself was unidentifiable.
**Alternatives considered:** Document rivals only; rely on visual review; add one generic `strict_canonical_like` hook.
**Decision:** Declare three named rivals, three mapped witnesses, a strict-canonical hook, and a lesson-identifiability function that rejects demonstration sets still solved by a rival.
**Probe:** Canonical tests prove all rivals fit the demonstrations; generated tests prove every ordinary case refutes each rival; semantic gate independently checks all hooks.
**Failure mode controlled:** A future edit making the task solvable through a simpler canonical-fitting heuristic.
**Limitation:** No finite rival list proves uniqueness against every imaginable program; it covers the strongest observed local shortcuts.

## D9. Declare the finite output codomain

**Original rationale:** Generic diversity lint saw a small output alphabet and could not know whether that was intrinsic.
**Alternatives considered:** Waive the warning; generate arbitrary object counts to inflate outputs; document the bound only.
**Decision:** Declare and test `EXPECTED_OUTPUT_CODOMAIN = 13`. For four labeled objects with at least one equal and one unequal pair, the allowed partitions are three `2+2`, six `2+1+1`, and four `3+1` matrices.
**Probe:** Enumerate outputs over bands, seeds, and indices and require exactly thirteen distinct matrices.
**Failure mode controlled:** Mistaking mathematically complete finite coverage for deficient diversity, or silently losing one relation structure.
**Limitation:** The declaration depends on the deliberate four-object and mixed-relation manifold.
