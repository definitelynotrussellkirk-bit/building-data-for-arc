# Working notes: 6ccc3318a707

## 2026-09-28 review

The imported v2 generator described and generated a *symmetry completion* task: it placed cells only above the anti-diagonal and said originals remained while mirrored copies were added. The selected canonical rule is instead the bijection `(rotate-180 (transpose g))`: every grid cell moves across the anti-diagonal. The old `self_check` therefore rejected all three canonical inputs and the old distribution never exercised fixed points, cells from both sides, or occupied mirror-pair collisions.

Version 3.0.0 rewrites the input curriculum without changing the canonical Racket authority. Every ordinary draw has:

- square size 6..8 and exactly four nonzero colors, matching every canonical profile;
- one or two occupied anti-diagonal fixed points;
- one or two occupied mirror pairs with different endpoint colors, forcing a real swap;
- two or three singleton mirror orbits, proving cells move rather than remain as copies;
- at least one repeated color and one uniquely colored singleton, separating geometry from color frequency and anti- from main-diagonal reflection.

Exact axes are `grid_size`, `diagonal_marks`, `mirror_pairs`, and `singletons`; `observe_overrides()` reconstructs all four. Unknown axes and invalid difficulty values fail loudly. Difficulty selects a separate deterministic layout stream while preserving the same rule manifold and canonical-profile support.

The semantic contract names five rivals and five positive counterexample witnesses. Two rivals—`keep_occupied_pairs` and `reflect_only_unique_colors`—fit all three canonical train/test pairs, so they are declared in `CANONICAL_SHORTCUTS`. Generated occupied pairs and repeated colors refute them on every ordinary draw.

Evidence:

- focused regression suite: `checks/focused_pytest.log` (14 passed);
- before battery: `checks/before_full/6ccc3318a707_before_battery_summary.json` (5 failed stages, 1 advisory);
- after battery: `checks/after_full/6ccc3318a707_after_battery_summary.json` (12/12 green);
- semantic gate: 600/600 strict, 5/5 witnesses, 5/5 rival claims, 12/12 identifiable lessons;
- canonical profile: 60/60 exact profile, all 3 canonical inputs accepted;
- override contract: 3,780 accepted draws across 42 cases and 3 bands.
## Current reviewer considerations

Source SHA-256: `1ca86f8326393efed63bc8bf541b888ae50e49694013aa85f819fadbb14c748f`.

# Decisions: 6ccc3318a707

## D1. Keep the canonical Racket rule unchanged

**Choice.** Retain `(rotate-180 (transpose g))` and pin `RULE_HASH = "ea62a41435bf"`.

**Original rationale.** The imported generator had no trustworthy rationale for its conflicting overlay description. The canonical written solution, all three canonical pairs, rule smoke, Racket lint, and authority-sync evidence agree on full-grid anti-diagonal reflection.

**Alternatives considered.** Change the Racket rule to symmetry completion; reinterpret the task as reflecting only nonzero cells from one triangle. Both contradict canonical outputs, where source locations are cleared and cells may originate on either side.

**Probe.** Apply `rule_mirror` to all canonical inputs and compare exact matrices; all match. Rule smoke and authority sync pass.

**Failure modes / limitations.** The Python mirror is diagnostic only; Racket remains authoritative. A future canonical rule change must update the hash and tests.

## D2. Match the canonical profile on every ordinary draw

**Choice.** Use square sizes 6..8 and exactly four distinct nonzero colors.

**Original rationale.** The old 6..9 / arbitrary-color distribution appears inherited rather than evidence-based. Canonical inputs are 6×6, 7×7, and 8×8, each with palette size 5 including background.

**Alternatives considered.** Keep 9×9 exploration; add occasional exact-profile anchors; vary foreground palette cardinality. Those broaden reach but preserve an avoidable scale/palette shortcut and reduce exact support.

**Probe.** Canonical-profile gate reports 60/60 exact hits and all three bands supported.

**Failure modes / limitations.** This intentionally favors canonical fidelity over larger-grid extrapolation. Geometry still varies substantially within the profile.

## D3. Force semantic counterexamples in every generated input

**Choice.** Every draw includes 1..2 anti-diagonal fixed points, 1..2 differently colored occupied mirror pairs, and 2..3 singleton mirror orbits. Four colors are assigned so at least one repeats and one singleton color remains unique.

**Original rationale.** Unknown. The old one-triangle layout made the wrong copy/overlay rule indistinguishable and excluded fixed points/collisions entirely.

**Alternatives considered.** Make witnesses rare scheduled profiles; rely on multiple examples to accumulate coverage; random sparse placement without structural guarantees. All leave a measurable chance that a lesson teaches a shortcut.

**Probe.** The strict semantic census found every one of five witnesses in 600/600 draws, with each rival claim verified on 60 sampled firings. The shortcut probe confirms all rivals disagree on 12/12 sampled inputs.

**Failure modes / limitations.** The synthetic curriculum is deliberately more diagnostic than the sparse canonical examples. `self_check` remains broader, so not every externally supplied lawful input has all witnesses.

## D4. Treat occupied-target behavior as the primary canonical ambiguity

**Choice.** Declare `keep_occupied_pairs`: move singleton cells, preserve fixed points, but leave an already occupied anti-mirror pair unswapped.

**Original rationale.** None was documented. All canonical inputs avoid occupied off-diagonal mirror pairs, so this rival fits every canonical train/test pair.

**Alternatives considered.** “Erase anti-diagonal cells” fits the two training demonstrations but is refuted by the canonical test fixed point; “keep originals and copy” is refuted by every canonical singleton. `keep_occupied_pairs` survives more evidence and is therefore stronger.

**Probe.** Canonical ambiguity gate confirms it fits 3/3 canonical pairs; generated `occupied_pair_swaps` witnesses refute it. `checks/shortcut_probe.json` contains an exact matrix and both outputs.

**Failure modes / limitations.** This is one plausible collision policy, not an exhaustive enumeration of all programs consistent with three examples.

## D5. Expose only exact, observable axes

**Choice.** Declare `grid_size`, `diagonal_marks`, `mirror_pairs`, and `singletons`; implement `observe_overrides`; reject unknown keys.

**Original rationale.** The legacy axis list mixed aliases, dead knobs, fake metadata, and unobservable semantics. No defensible rationale was retained.

**Alternatives considered.** Preserve compatibility aliases (`grid_h`, `grid_w`, palette kind, texture); mark dead axes diagnostic; add a palette override. These increase surface area without adding task semantics.

**Probe.** Focused tests exhaust both boundaries of every axis across all three bands. Override gate accepted 3,780/3,780 draws over 42 cases and rejected the unknown-key probe.

**Failure modes / limitations.** Palette identity varies but is intentionally not caller-overridable; palette *cardinality* is fixed by the canonical profile.

## D6. Separate broad validity from teaching strength

**Choice.** `self_check`/`strict_canonical_like` accept every canonical-shaped instance with 4..9 cells and exactly four foreground colors, while `generate` guarantees stronger witnesses.

**Original rationale.** The old validator encoded the generator’s one-sided sampling choice and therefore disowned the task.

**Alternatives considered.** Require fixed points and collisions in `self_check`; accept any nonempty square ARC grid. The first rejects canonical training examples; the second admits blank/minimal impostors and weakens mutation detection.

**Probe.** All three canonical inputs pass; 60 generated defaults pass; blank, dropped-color, invalid-value, ragged, and non-square cases fail. Mutation sensitivity is 48/60.

**Failure modes / limitations.** Some destructive row/cell mutations can still land inside the broad lawful manifold. That is expected when the mutation accidentally preserves shape, counts, and palette.

## D7. Make difficulty affect layout, not semantics

**Choice.** Keep the same axis ranges and canonical support in all bands, but use a band-keyed deterministic layout RNG stream.

**Original rationale.** Initially difficulty was validated but did not enter any draw. The defect linter correctly reported all bands byte-identical.

**Alternatives considered.** Assign sizes 6/7/8 by band; increase witness counts by band. Those would starve some bands of canonical profiles or make override behavior band-dependent.

**Probe.** A failing regression was added first; after the change, 12 sampled indices differ across bands while all remain valid exact-profile inputs. Defect lint is green.

**Failure modes / limitations.** Difficulty changes spatial arrangement rather than an intrinsic reasoning depth; this task has little natural complexity scaling without changing the rule.

## D8. Add reusable tests and a shortcut probe

**Choice.** Add a focused pytest module and `workspace/shortcut_probe.py`.

**Original rationale.** No task-local tests or concrete rival reproducer existed.

**Alternatives considered.** Rely solely on the generic battery; document matrices manually. The battery is broad but slower and less convenient for future edits; manual calculations are easy to drift.

**Probe.** 14 tests pass, the probe emits machine-readable JSON, and packaging includes both as task-local artifacts.

**Failure modes / limitations.** The test loader targets this packet’s source layout; an integrated runtime may prefer ordinary package imports.
