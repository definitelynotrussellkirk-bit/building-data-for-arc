# Working notes: cadfb7a1ae72

## 2026-10-02 review repair

The imported `2.0.1` generator implemented a different problem: it created several motifs for a winner-selection/cropping rule. The selected canonical Racket rule instead computes an ordered pairwise feature-relation matrix. The old generator therefore had the wrong output task even when its scenes executed without crashing.

The generator was replaced rather than incrementally patched. Version `3.0.0` established the correct task family and:

- pinned canonical rule hash `b8842d5039be`;
- constructed 3–5 separated, distinct-color connected objects;
- computed exact row- and column-reflection bits and enclosed-hole-region count;
- mirrored the unchanged Racket relation precedence (`1`, then `8`, then `4`, then `0`);
- exposed only three exact, observable axes: `grid_h`, `grid_w`, and `profile`;
- rejected unknown and out-of-range overrides;
- scheduled four semantic profiles by `sample_index mod 4`; and
- added structural validation, semantic witnesses, task-local tests, and a feature inspector.

## 2026-10-02 second-round shortcut audit

A broader hypothesis search found that the first repaired curriculum still permitted a plausible projection shortcut: infer reflection class from palindromic row and column occupancy counts rather than exact reflected cells. That shortcut fit all official pairs. A retained replay against the frozen first-round generator (SHA-256 `0d385ce57f2fab2b474df74999bc7f43e403813b495f13e97feccab6eb25c983`) found it survived 639 of 1,440 four-demonstration windows (5,760 draws) under the pinned seed schedule documented in `checks/round2/projection_leak_round1_replay.json`.

Version `3.1.0` closes that and two adjacent ambiguities with guaranteed structural collisions rather than seed-dependent luck:

- `hole_priority` now contains two connected masks with identical ordered row/column projection vectors but different exact reflection classes. Projection-only models must disagree with the authority.
- `binary_holes` now pairs one enclosed two-cell region with two enclosed one-cell regions. Total enclosed area is equal while connected hole-region count differs.
- `canonical3` uses descending colors in top-left order, separating spatial order from the ascending-color coincidence in the official examples.

The semantic registry now contains six atomic rivals. `workspace/audit_curriculum.py` verifies declared canonical-fit status and tests every rival across sliding lesson windows. `workspace/audit_hypotheses.py` crosses three symmetry encodings, three hole encodings, two orderings, and two precedence rules. It first filters to the 30 hypotheses that fit all three official pairs, then tests all 29 non-authority alternatives against generated four-example windows.

## Curriculum profiles

- `canonical3`: 10×16, three objects, with descending colors in top-left order to force the ordering contract.
- `canonical4`: 11×17, four objects, preserving canonical-scale support and row-only/column-only contrast.
- `hole_priority`: five objects including duplicate `(holes=1, symmetry=both)` signatures plus the exact-projection collision. It separates symmetry precedence, exact axis orientation, and cellwise reflection from projection statistics.
- `binary_holes`: five objects including a one-region/two-cell ring and a two-region/two-cell object. It separates exact connected-region count from both hollow/solid and enclosed-area shortcuts.

## Iteration evidence

The first replacement draft passed semantic tests but the standalone lint probe reported only 38 distinct outputs over 144 pairs (26%) and warned that a local identifier echoed a Racket primitive. The profiles were expanded, and local names were made more specific. The next lint probe reported 54 distinct outputs over 144 pairs (38%) with no warnings. Those first-round probes remain in the review evidence.

Round two uses red-green regression evidence for the projection collision, hole-cell collision, composed-hypothesis auditor, and stricter audit certification. Final hashes and stress-run counts are recorded in the returned `REVIEW.md` and `RESULTS.json`.

## Remaining bounds

The shape bank is deliberately finite and hand-audited: object bounding boxes are at most 5×5 and hole counts are 0–2. The curriculum does not attempt all possible object geometries, same-color multi-component scenes, touching objects, or more than five objects. The hypothesis auditor covers a documented plausible family, not every mathematically inventable rule that can interpolate finite examples. These are explicit distribution and audit-scope limits, not known semantic failures for the generated grammar.
## Current reviewer considerations

Source SHA-256: `ee9d5586093a9d71d6678f667b7053e367136ab1156d5a26d2e511999d7b88cb`.

# Decisions for `cadfb7a1ae72`

Final generator SHA-256: `ee9d5586093a9d71d6678f667b7053e367136ab1156d5a26d2e511999d7b88cb`.

## D1 — Keep the round-one replacement, not the original generator

**Observed baseline.** Version `2.0.1` generated several motifs, chose a winner by holes/symmetry/area/location, then cropped and recolored it. The canonical task emits an `N × N` pairwise feature-relation matrix.

**Decision.** Preserve the round-one full replacement as the foundation. The original problem was task identity, not a parameter bug.

**Rejected alternative.** Keep the old scenes and relabel them through Racket. That would retain misleading axes and scenes not designed to identify the relation.

**Evidence.** `checks/round1/before/` and the baseline-to-final `patches/source.patch` produced by packaging.

## D2 — Preserve Racket authority

**Decision.** Do not edit canonical or archival Racket. Keep `RULE_HASH = "b8842d5039be"`; use the Python mirror only for testing, diagnostics, and rival construction.

**Why.** The selected Racket rule solves all official pairs. The defects were in generation and curriculum identifiability.

**Rejected alternative.** Change the authority to match either the original generator or a projection-based shortcut. That would redefine the task.

**Evidence.** Final rule smoke gives 120/120 mirror parity. Authority sync reports selected sources synchronized and all authority variants execution-equivalent on the canonical pairs.

## D3 — Keep the isolated distinct-color object grammar

**Decision.** Generate 3–5 separated 4-connected objects, one distinct nonzero color per component, sorted by top-left coordinate.

**Why.** The official examples use color as a segmentation/identity cue, while the relation depends on shape topology. This grammar isolates the intended reasoning from unnecessary segmentation ambiguity.

**Rejected alternatives.** Same-color disconnected objects, touching objects, two-object scenes, and more than five objects. Each adds complexity or removes branch coverage without evidence that it is central to this task.

**Known bound.** This is a curriculum choice, not a claim that the rule is undefined outside it.

## D4 — Keep a hand-audited finite shape bank

**Decision.** Use connected masks whose exact `(hole-region count, reflection class)` signatures are recomputed and asserted. Axis flips provide controlled variation.

**Why.** The curriculum requires deterministic feature collisions. Rejection-sampled random polyominoes make rare signatures and lesson guarantees fragile.

**Rejected alternative.** Unbounded procedural growth. It broadens geometry but weakens exact guarantees and makes failures difficult to reproduce.

**Known bound.** Bounding boxes are at most 5×5 and hole-region counts are 0–2.

## D5 — Treat exact reflection as cellwise equality

**Authority feature.** Row reflection and column reflection are checked by mapping every occupied cell to its reflected coordinate. The two booleans form classes `0..3`.

**Round-two finding.** A cheaper rule can instead check whether the sequence of row counts and the sequence of column counts are palindromes. It fits every official pair and survived 639/1,440 pinned first-round lesson windows.

**Decision.** Add two connected 3×3 masks whose ordered row and column counts are both `((2,3,1),(2,2,2))`, but whose exact reflection classes are `0` and `2`. Pin both into `hole_priority`.

**Rejected alternatives.** Merely add more random asymmetric shapes or declare the rival in metadata. Neither guarantees that every four-example lesson refutes it.

**Evidence.** `workspace/example_projection_report.json`, `checks/round2/projection_leak_round1_replay.json`, and the deterministic projection-trap tests.

## D6 — Count connected hole regions, not enclosed area

**Authority feature.** Count 4-connected zero regions inside the normalized object box that do not touch the box border.

**Round-two ambiguity.** Total enclosed-zero-cell area is a plausible substitute and fits all official pairs.

**Decision.** Pair a 3×4 ring containing one two-cell enclosed region with an object containing two one-cell enclosed regions. Both have enclosed area two; their region counts are one and two.

**Rejected alternatives.** Add a larger hole without equalizing area, or rely only on one-hole versus two-hole examples. Those distinguish binary hollowness but not region count from area.

**Evidence.** `workspace/example_binary_holes_report.json` and `checks/round2/verify_counterexamples.json`.

## D7 — Break the color-order coincidence

**Finding.** In the official examples, sorting objects by color can coincide with sorting them by top-left position. This rival fits every official pair.

**Decision.** Recolor `canonical3` so colors descend in top-left order. The geometry and canonical dimensions remain unchanged, while color-order output rows/columns are wrong.

**Rejected alternative.** Random colors alone. Randomization gives no bounded guarantee that the order differs.

**Evidence.** The `color_order` rival survives 0/3,000 final windows and is deterministically tested.

## D8 — Preserve relation precedence and overlapping matches

**Decision.** Continue emitting diagonal `1`, then exact-symmetry equality `8`, then equal hole-region count `4`, otherwise `0`. Keep two different objects that match both symmetry and holes.

**Why.** If feature matches never overlap, a holes-first implementation can interpolate all examples.

**Rejected alternative.** Avoid overlap to simplify generation. That would make precedence unidentifiable.

## D9 — Retain four deterministic profiles

**Decision.** Keep `sample_index mod 4` and `EXAMPLES_NEEDED = 4`:

| Profile | Main role |
|---|---|
| `canonical3` | exact canonical scale and color-order collision |
| `canonical4` | exact canonical scale and row-only/column-only contrast |
| `hole_priority` | precedence plus projection collision |
| `binary_holes` | binary-holes and equal-area/different-region collision |

**Why.** Every sliding four-example window contains one of each profile independent of seed and difficulty.

**Rejected alternatives.** Random profile choice, one overloaded profile, or three-example lessons. Each weakens the bounded coverage guarantee.

## D10 — Keep only exact observable overrides

**Decision.** Expose `grid_h` 10–20, `grid_w` 16–24, and `profile`; reject unknown keys and invalid values; recover every declared axis via `observe_overrides`.

**Why.** These axes materially affect the returned instance. Decorative palette/texture axes from the original generator were misleading or inert.

**Evidence.** 18,360/18,360 lawful override draws accepted with zero findings and the unknown-key probe rejected.

## D11 — Separate lawful grammar from strict canonical likeness

**Decision.** `self_check` validates the generated grammar. `strict_canonical_like` measures narrower canonical-scale support. Do not make all lawful generalized examples satisfy exact canonical dimensions.

**Why.** One hook cannot cleanly mean both structural validity and distribution proximity.

**Evidence.** All 3 canonical inputs pass; strict rate is 307/600, above the declared 40% floor.

## D12 — Expand the semantic registry from three to six rivals

**Decision.** Register:

- `hole_priority`;
- `binary_holes`;
- `axis_count`;
- `projection_symmetry`;
- `enclosed_hole_cells`; and
- `color_order`.

Map each to a witness, expose all as lesson competitors, and mark the five that fit every official pair as canonical shortcuts.

**Why.** The semantic gate should know what each generated profile is intended to disambiguate.

**Rejected alternative.** Put the claims only in notes. Unexecutable claims go stale.

## D13 — Certify canonical-fit metadata

**Finding.** An auditor that only checks generated disagreements can pass even when a rival labeled “canonical shortcut” no longer fits the canonical pairs.

**Decision.** `audit_curriculum.py` independently runs each `CANONICAL_SHORTCUTS` function on all official pairs and fails if any label is false.

**Evidence.** Red-green logs in `checks/round2/tdd/`; final report has `all_canonical_shortcuts_fit=true`.

## D14 — Add a composed-hypothesis audit

**Decision.** Enumerate the Cartesian product of:

- symmetry: exact, axis count, projection-derived;
- holes: connected regions, binary hollowness, enclosed-cell count;
- order: top-left, ascending color; and
- precedence: symmetry first, holes first.

This yields 36 hypotheses. Filter them by exact fit to all official pairs, then test each remaining non-authority hypothesis against every generated lesson.

**Why.** Atomic rivals can all fail while a combination of two wrong choices survives.

**Rejected alternatives.** Exhaustively search arbitrary programs, which is not tractable or interpretable; or audit only one changed feature at a time, which misses interactions.

**Result.** 30/36 fit all official pairs. All 29 non-authority canonical-fit hypotheses survive 0/1,500 windows.

## D15 — Keep the audit family finite and explicit

**Decision.** Treat the composed family as a reusable high-value probe, not a theorem of unique induction.

**Why.** Finite data always permits contrived interpolants. The practical goal is to defeat simple, structurally motivated alternatives a learner is likely to adopt.

**Remaining limitation.** Rules outside the declared family may exist. The final docs state this explicitly.

## D16 — Extend the feature inspector

**Decision.** Report exact reflection class, projection-derived class, connected hole regions, total enclosed zero cells, object ordering, intended output, all rival outputs, and first disagreements.

**Why.** Matrix errors are hard to diagnose by looking at a grid. A structured report makes the disagreement auditable and reusable by future agents.

**Artifacts.** `workspace/example_projection_report.json` and `workspace/example_binary_holes_report.json`.

## D17 — Preserve red-green evidence for each second-round change

**Decision.** Retain failing and passing logs for projection rivals, deterministic collisions, inspector fields, both auditors, and audit certification.

**Why.** A passing final test alone does not show that the test would have caught the missing behavior.

**Evidence.** `checks/round2/tdd/`.

## D18 — Retain rather than rerun the fresh solve

**Decision.** Keep the first-round solve unchanged.

**Why.** The canonical rule and visible-example semantics did not change; only generated curriculum identifiability improved. Rewriting the solve would destroy the honest chronology, and rerunning after additional source exposure would not be a cleaner blind solve.

**Disclosure.** Earlier rule exposure remains `yes`; reference consulted during solve remains `no`; masked correctness remains unknown.

## D19 — Do not treat output repetition as semantic failure

**Observation.** The generic diversity probe reports 22% unique outputs over 300 pairs and labels repeated matrices. The linter reports 54 distinct outputs over 144 pairs and no warning.

**Decision.** Keep the finite relation-matrix distribution and document the generic diagnostic rather than corrupt semantics to create artificial output diversity.

**Rejected alternative.** Randomly permute output rows/columns independently of top-left object order. That would create diversity by making labels wrong.

## D20 — Stop after all declared alternatives are structurally eliminated

**Stopping rule.** Stop when the final source has: a green official battery, passing task tests, exact Racket counterexample replay, zero surviving atomic rivals in the stress audit, zero surviving non-authority composed hypotheses, and package validation.

**Why.** Broader geometry would be a new coverage project rather than a repair to the demonstrated shortcut defects.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-c6237723b7a5b3a1:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `ee9d5586093a9d71d6678f667b7053e367136ab1156d5a26d2e511999d7b88cb`. At disposition, audited bytes match the current source.

### Current decision

Audited source repo/generators/cadfb7a1ae72/generator.py SHA256 ee9d5586093a9d71d6678f667b7053e367136ab1156d5a26d2e511999d7b88cb. Fresh evidence:

- All 15 task-local tests pass: `checks/audit/cadfb7a1ae72/pytest.log`.
- `checks/audit/cadfb7a1ae72/curriculum.json` tested 600 sliding
  four-demonstration windows / 2,400 draws across easy, medium, and hard. Every
  one of the six declared rivals had zero surviving windows; all declared
  canonical shortcuts still fit the three official pairs.
- `checks/audit/cadfb7a1ae72/hypotheses.json` crossed 36 composed hypotheses.
  Thirty fit all official pairs, leaving 29 non-authority alternatives; none
  survived any of the same 600 generated windows.

This is a finite audit of the documented hypothesis family and finite shape
bank, not a proof against every possible interpolation rule. I found no concrete
current-source defect, canonical mismatch, inert declared control, or surviving
shortcut within that scope.

 Bounded reviewer-reported finding, no owner rerun or target repair. Evidence: `checks/audit/50b436f101bb/audit.py` `checks/audit/cadfb7a1ae72/curriculum.json` `checks/audit/cadfb7a1ae72/curriculum.log` `checks/audit/cadfb7a1ae72/curriculum.status` `checks/audit/cadfb7a1ae72/hypotheses.json` `checks/audit/cadfb7a1ae72/hypotheses.log` `checks/audit/cadfb7a1ae72/hypotheses.status` `checks/audit/cadfb7a1ae72/pytest.log` `checks/audit/cadfb7a1ae72/pytest.status` `checks/audit/cadfb7a1ae72/source.sha256`

### Assessment or prior finding

## cadfb7a1ae72

**No issue found in the bounded current-source audit.** I checked generator
SHA-256 `ee9d5586093a9d71d6678f667b7053e367136ab1156d5a26d2e511999d7b88cb`,
including the object-order contract, exact cellwise reflection versus projection
statistics, connected hole-region count versus enclosed area/binary hollowness,
branch precedence, declared controls, and the task's retained adversarial tools.

Fresh evidence:

- All 15 task-local tests pass: `checks/audit/cadfb7a1ae72/pytest.log`.
- `checks/audit/cadfb7a1ae72/curriculum.json` tested 600 sliding
  four-demonstration windows / 2,400 draws across easy, medium, and hard. Every
  one of the six declared rivals had zero surviving windows; all declared
  canonical shortcuts still fit the three official pairs.
- `checks/audit/cadfb7a1ae72/hypotheses.json` crossed 36 composed hypotheses.
  Thirty fit all official pairs, leaving 29 non-authority alternatives; none
  survived any of the same 600 generated windows.

This is a finite audit of the documented hypothesis family and finite shape
bank, not a proof against every possible interpolation rule. I found no concrete
current-source defect, canonical mismatch, inert declared control, or surviving
shortcut within that scope.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
