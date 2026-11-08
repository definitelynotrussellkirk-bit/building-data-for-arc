# Working notes: 3d48e913ef07

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `083c42f670fc323018502eca4840c292a0f56b3ecd394da49e1303c479b95067`.

# Decisions for `3d48e913ef07`

## D1 — Preserve the Racket authority; pin it in Python

**Choice.** Keep the canonical/base Racket program byte-identical and add `RULE_HASH = "4d5171afc86a"` to the generator.

**Original rationale.** The baseline documentation already described the correct transformation, but the code did not bind itself to the authority. The exact reason the hash had been omitted is unknown.

**Alternatives considered.** Rewriting or simplifying the Racket rule was rejected because all canonical outputs already matched it and the defect was entirely in sampling/contracts. Deriving the hash dynamically at import time was rejected because the generator should remain standalone and the explicit pin makes drift reviewable.

**Probe.** The authority-sync/rule-smoke stages passed, all four canonical pairs matched the independent oracle, and 53/53 retained inputs matched real Racket.

**Failure mode/limit.** A future legitimate Racket change requires an intentional hash update and new parity evidence.

## D2 — Replace the advertised axis set instead of pretending inherited controls work

**Choice.** Expose only `grid_h=10..18`, `grid_w=14..20`, and `n_objs=3..5`; reject unknown keys, booleans/non-integers, and out-of-range values. Declare no incompatible Cartesian tuples.

**Original rationale.** The old `palette_kind`, `density`, and `texture` controls came from a generic template. Their task-specific rationale is unknown, and several were inert or diagnostic-only.

**Alternatives considered.** Keeping the old names and manufacturing superficial visual effects was rejected because they would not represent independent semantic controls. Keeping wide dimensions with failure-prone placement was rejected. Retaining degenerate textures was rejected because production lessons should consistently demonstrate both palette and object-order branches; deliberate negatives belong in tests/probes.

**Probe.** The final override audit accepted and observed 11,970/11,970 draws across 133 cases and rejected the unknown-key probe.

**Failure mode/limit.** The honest domain is narrower than the baseline's aspirational text; it is intentionally restricted to dimensions that support the constructive grammar.

## D3 — Use a six-slot constructive layout

**Choice.** Partition the object canvas into two row bands × three column bands and place one connected polyomino per selected slot, with no rejection loop or fallback.

**Original rationale.** The baseline had been rewritten once to improve diversity, but still used random motif growth and bounded placement attempts. Its comments focused on average diversity, not exact requested behavior.

**Alternatives considered.** Increasing retry counts was rejected because it does not make overrides exact. A solver/backtracking placer was unnecessary for this small grammar. A bank of fixed grids was rejected because it would collapse variability and invite memorization.

**Probe.** No generation crash or validator failure occurred in 600 semantic-gate draws, 11,970 override draws, 1,000 independent draws, or the lesson census. Each independent band produced 250/250 distinct inputs.

**Failure mode/limit.** Objects are confined to 4×3 local shape support and areas 3–8; the constructor is not intended to cover arbitrary polyomino sizes.

## D4 — Couple canonical morphology through a deterministic five-profile schedule

**Choice.** Use four linked canonical profiles plus one broad profile, selected by `sample_index mod 5`; set `EXAMPLES_NEEDED=3`.

**Original rationale.** The baseline sampled dimensions/counts independently and did not guarantee any canonical joint profile. The original reason for its difficulty ranges is unknown.

**Alternatives considered.** A random 25% canonical prior was rejected because complete lesson composition would remain probabilistic. Using only canonical profiles was rejected because it would overfit dimensions/morphology. More than five residues was unnecessary for the known branches.

**Probe.** The profile floor hit exact canonical profiles 51/60 times and at least once in every band. The independent probe tested all five cyclic query starts for 100 cycles in each of four bands (2,000 lessons) with no failures.

**Failure mode/limit.** The schedule is intentionally visible to audit tools; a learner could potentially detect residue-specific distribution cues, although every residue remains governed by the same transformation and cyclic lesson checks found no declared-rival leak.

## D5 — Deliberately separate area, position, bounding boxes, and palette order

**Choice.** Make source object order differ from descending area, make palette order nonnumeric, and select compact/sparse shapes so cell area does not collapse to bbox area/width.

**Original rationale.** The baseline stated that areas and palettes varied, but did not encode counterexamples to plausible alternatives. Its exact lesson-design rationale is unknown.

**Alternatives considered.** Randomly hoping for counterexamples was rejected. Hard-coding a single witness was rejected in favor of production-wide structural conditions. Forcing bbox-area disagreement on every draw was unnecessary; the generator guarantees other strong witnesses and supplies bbox-area disagreements at substantial frequency.

**Probe.** Semantic-gate witness rates were 600/600 for source order, ascending area, bbox width, and numeric palette; bbox-area disagreement occurred on 363/600 draws. The independent audit reproduced 250/250 bbox-width and 150/250 bbox-area counterexamples per band.

**Failure mode/limit.** These are five plausible rivals, not an exhaustive hypothesis class.

## D6 — Classify `bbox_width` honestly as a canonical shortcut

**Choice.** Put only descending bbox width in `CANONICAL_SHORTCUTS`; keep all five rules in `SEMANTIC_RIVALS`/`LESSON_COMPETITORS`.

**Original rationale.** There was no prior executable shortcut declaration.

**Alternatives considered.** Labeling all rivals canonical shortcuts was rejected after checking the public pairs: only bbox width fits all four. Omitting bbox width because the generator refutes it was rejected because the question is whether public demonstrations admit it, not whether production data fixes it.

**Probe.** `checks/shortcut/witness.json` proves 4/4 canonical fit and gives a validator-clean input where independent Python equals Racket but bbox width disagrees. The semantic gate emitted a bbox-width counterexample on 600/600 draws.

**Failure mode/limit.** Another undiscovered public-pair shortcut may exist; the retained declaration is the strongest found, not a completeness proof.

## D7 — Make validation structural and observable

**Choice.** Validate rectangular integer grids, exact marker/object counts, separator/palette constraints, connected components, distinct areas, separation, and palette distinctness. Add `observe_overrides` and `strict_canonical_like`.

**Original rationale.** The baseline self-check only required at least one palette marker and one color-3 cell. Its permissiveness likely came from a smoke-test template.

**Alternatives considered.** Checking only generator metadata was rejected because returned pixels are the contract. Reusing generator placement internals in tests was rejected where an independent reconstruction was practical.

**Probe.** Canonical inputs pass, targeted mutations fail, final self-check/profile/override stages pass, and independent audits reconstruct observations from pixels.

**Failure mode/limit.** `strict_canonical_like` intentionally rejects broad-but-lawful profiles; it is a profile-measurement hook, not the generator-domain validator.

## D8 — Build a reusable independent probe alongside focused tests

**Choice.** Add 40 task-local regressions plus `workspace/reference_probe.py`, which independently reconstructs the rule, reads actual rival declarations, checks canonical-shortcut honesty, rotates schedule starts, and optionally executes Racket.

**Original rationale.** No task-local portable tests or reusable semantic probe existed.

**Alternatives considered.** Relying only on the general battery was rejected because it does not discover task tests automatically and its lesson census does not rotate every small deterministic schedule residue into the query. Copying rival names into the probe was rejected; it introspects the actual declarations.

**Probe.** Supported task stage: 40/40 passed. Independent command: 1,000 samples, 2,000 cyclic lessons, and 53 Racket checks, all clean.

**Failure mode/limit.** The tool is task-local and its independent oracle still mirrors a written interpretation; real-Racket parity mitigates but does not remove the need to review future rule changes.

## D9 — Freeze the final generator before the exposed solve

**Choice.** Prepare the post-repair solve only after the final generator hash was fixed; make no subsequent generator.py edit.

**Original rationale.** Required by the packet's source-bound solve protocol.

**Alternatives considered.** Reusing an earlier solve was rejected because it would not be bound to final bytes.

**Probe.** `solve/summary.json` records generator hash `083c42f...` and one visible-example-passing revision. Earlier exposure is `yes`; reference consultation during the solve is `no`.

**Failure mode/limit.** The packet intentionally withholds masked-query scoring; the record proves visible-example behavior and provenance, not private correctness.
