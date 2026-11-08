# Working notes: c21f2ce8fb20

## 2026-10-03 review repair

The imported v2 generator encoded a different, much smaller family: exactly two full-height chambers separated by one vertical wall, always with a fixed 3-vs-1 seed pattern. Its validator also required exactly two chambers, so it rejected every one of the five canonical inputs. The public axis metadata advertised controls that generation did not honor, `RULE_HASH` was not pinned, and the selected base-bank `target_code` differed textually from the executed canonical authority.

Version 3.0.0 replaces that shortcut with a deterministic four-profile curriculum over three/four separated rectangular chambers. It owns all canonical inputs, honors the full declared override cross-product, and includes deliberate witnesses against the canonical-fit `prefer_exactly_three` shortcut plus largest-room and density shortcuts. The Racket rule behavior did not change; only the selected base-bank `target_code` text was synchronized byte-for-byte with the canonical/raw source.

Reusable independent checks live in `workspace/reference_probe.py`; regression tests live in `tests/test_generator_c21f2ce8fb20.py`. Final generator SHA-256: `999a65888862995bc9a4b69dbef1e8d2d79db2bd2ad41cdaaaf6877f8cd8ec20`.
## Current reviewer considerations

Source SHA-256: `999a65888862995bc9a4b69dbef1e8d2d79db2bd2ad41cdaaaf6877f8cd8ec20`.

# Decisions for `c21f2ce8fb20`

## D1 — Treat the baseline as the wrong family, not a small tuning defect

**Evidence.** The baseline generated exactly two giant chambers with a fixed 3-vs-1 seed count, while the five canonical inputs contain three or four separated chambers with varied geometry and winner placement. Its `self_check` explicitly rejected every canonical puzzle because it required exactly two regions. The before battery failed six of twelve stages (`checks/before-full/checks/c21f2ce8fb20_before_battery_summary.json`).

**Decision.** Replace the selected task generator rather than patching random dimensions around the two-room construction.

**Rejected alternative.** Keeping the divider template and randomizing seed positions would remain a different task distribution and continue teaching “left/full-height room” and “three seeds” shortcuts.

## D2 — Preserve the selected Racket behavior

**Evidence.** The rule smoke test already showed valid behavior. Independent parsing of all five canonical pairs agreed with the selected Racket authority. The authority-sync failure was textual drift among selected copies, not output disagreement.

**Decision.** Keep rule hash `b86be3a37a68` and its semantics unchanged. Synchronize only the selected base-bank `target_code` text with the canonical/raw authority. Final authority sync is exact and execution parity passes (`checks/after-full/checks/c21f2ce8fb20_after_authority_sync.json`).

**Rejected alternative.** Editing tie-breaking or narrowing the Racket rule to the generated domain would create unnecessary reference churn. Generated lessons use a strict seed maximum, so tie behavior is not part of the curriculum.

## D3 — Use a four-profile deterministic curriculum

The profile schedule is indexed by `sample_index % 4`:

1. `canonical_three_room` supplies canonical-sized three-room layouts and a two-seed winner.
2. `canonical_four_room` supplies canonical-sized four-room layouts and a three-seed winner.
3. `count_above_three` supplies a four/five-seed winner and a three-seed losing chamber.
4. `size_density_decoys` supplies a winner that is neither the largest nor the densest chamber.

**Why deterministic.** A short, periodic schedule lets every four-example lesson contain the complete teaching set, independent of seed luck. It also makes all cyclic windows testable and reproducible.

**Rejected alternatives.** Pure random mixture gives only frequency evidence and can produce entire lessons without the critical rival witness. Embedding every rival in every single grid would make inputs artificial and reduce geometric diversity.

## D4 — Restrict generation to three/four separated rectangular chambers

**Decision.** Start with an all-gray grid and carve one rectangle in three or four of four spatial slots. Rooms remain disconnected, retain gray margins, include at least one red seed and one blank, and move across all quadrants.

**Rationale.** This owns all canonical examples while keeping chamber identity unambiguous. Rectangular rooms permit strong structural validation, exact controls, and clean counterexamples without teaching accidental maze traversal complexity.

**Rejected alternatives.** Reproducing exact canonical coordinates would overfit five layouts. Arbitrary polyomino chambers are compatible with the broad Racket flood-fill rule but unsupported by the canonical evidence and would substantially enlarge the hypothesis class.

**Limitation.** This is a documented curriculum boundary, not a universal characterization of every grid accepted by the selected Racket program.

## D5 — Advertise only controls with total joint support

**Decision.** Public axes are `grid_h=8..16`, `grid_w=11..20`, `n_chambers=3..4`, and `winner_seeds=2..5`. Overrides bypass scheduled defaults but still use the same lawful constructor. There are no declared incompatible combinations.

**Rationale.** Every advertised value and cross-product must be observable; metadata is a contract, not a hint. The final override audit exercised 21,600 draws with no finding or warning.

**Rejected alternatives.** Retaining old `texture` controls or wider dimensions would advertise cases with no honest semantic role or no guaranteed geometric construction. Silently clamping invalid overrides was rejected in favor of explicit errors.

## D6 — Make the canonical-fit shortcut executable

The strongest canonical-fit rival is `prefer_exactly_three`: choose a three-seed chamber when one exists, otherwise a two-seed chamber, otherwise the authority maximum. It matches all five canonical demonstrations because canonical winners have counts `[2, 3, 3, 3, 3]` and none contains a chamber above three seeds.

**Decision.** Declare it in `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`; verify that it really matches every canonical pair; schedule a four/five-versus-three disagreement case.

**Why this is stronger than “always choose three.”** The fallback to two explains the one canonical example whose winner has two seeds, so it fits the complete canonical set rather than four of five.

## D7 — Add independent area and density rivals

**Decision.** Retain `largest_room` and `densest_room` as executable competitors. The decoy profile assigns independent roles to the true seed-count winner, a larger one-seed loser, and a smaller but denser two-seed loser.

**Rejected alternative.** Ordinary random rectangles sometimes refute these rules, but frequency alone does not guarantee a complete lesson will. The dedicated profile makes the teaching obligation deterministic.

## D8 — Mirror the authority independently enough to detect drift

**Decision.** Keep a task-local Python flood-fill mirror with the selected Racket ordering, then cross-check retained inputs through the supported catalog Racket bridge. `workspace/reference_probe.py` contains a second implementation used for analysis and exact witness generation.

**Boundary.** Python mirrors are supplementary. The selected Racket execution is the authority; 37 retained inputs had 0 parity mismatches in the independent probe.

## D9 — Validate structure, not provenance

`self_check` examines only the supplied grid: rectangularity, palette, gray border, 3/4 connected rectangular chambers, red/blank composition, and unique maximum. It does not require hidden generation metadata. `strict_canonical_like` reuses the same structural contract.

**Rejected alternative.** Checking exact scheduled coordinates or profile labels would make canonical acceptance impossible and turn the validator into a provenance detector.

## D10 — Test lesson assembly, not only isolated witness frequency

The task-local suite checks every cyclic four-example window over 12 starts in every difficulty band and requires all declared rivals to be refuted. The shared 100-lesson-per-band census then measures production materialization. This separates “a witness occurs sometimes” from “each lesson actually teaches the rule.”

## D11 — Preserve genuine solve records

The required blind solve was completed before source inspection with one 4/4-visible revision and declared no earlier exposure. The post-repair solve was prepared from generator hash `999a...ec20`, completed in one 4/4-visible revision, and honestly declared earlier rule exposure because generator work had already occurred. Neither solve consulted a reference source during its solving phase.

## D12 — Leave adversarial audit targets unchanged

The two audit assignments are review-only. Exact Racket-backed counterexamples and rival outputs are retained under `checks/audit/`; no source outside the selected repair task was modified.

## Remaining uncertainty

The evidence establishes deterministic validity, authority parity, canonical ownership, full declared-axis support, and resistance to the named rivals across the tested schedule. It does not establish that no unimagined rival can fit all generated lessons, nor that arbitrary nonrectangular wall mazes should belong to this generator. Those are broader domain-design decisions, not hidden claims of this return.
