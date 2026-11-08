# Working notes: a85f5274d2ae

## Current selected rule

A modal-7 grid is divided into a 3×3 panel layout by two full zero rows and two full zero columns. A single 9 sits at the center of a 3×3 ring of 5s in the middle panel; a single 6 is the target. Restore the old 9 cell to 5, place a 9 one signed cell toward 6 on each axis whose absolute delta is greater than one, and recolor the 6 cell as 9.

Selected rule hash: `bba3b44960f2`. Version: `4.1.0`. The selected Racket text is byte-identical to canonical; archival `raw_code` is intentionally preserved. No rule-semantic change was made in this review.

## Production curriculum

`EXAMPLES_NEEDED=3`, `LESSON_SCHEDULE_PERIOD=4`:

1. `threshold_witness_a` — target stays in a central separator band but is more than one cell away on an axis;
2. `public_anchor` — exact canonical/public input;
3. `threshold_witness_b` — second independent threshold witness;
4. `broad` — varied general profile.

Production uses three consecutive demonstrations and the next pair as query. Any hold-one-out rotation of a four-pair window leaves at least one threshold witness in the demonstrations. Explicit `scene_profile` overrides bypass the schedule and remain exact.

## Semantic contract

The strongest known canonical-fitting shortcut is `panel_direction_only`: move according to target panel rather than distance. It fits 4/4 labeled canonical pairs. `same_panel_far_axis` is an executable witness, and `lesson_identifiable` rejects lessons where the rival survives. The retained production counterexample is `counterexamples/panel-direction-only/reproducer.json` (seed 913, sample 0, hard), backed by a live Racket receipt under `checks/counterexample-panel-direction-only/`.

Final evidence: strict support 600/600; exact profile 16/60; envelope 35/60; semantic smoke 12/12 lessons and 48/48 rotations; 300-lesson census and 1,200 rotations with zero declared-rival ambiguities. These finite checks do not prove universal identifiability.

## Request validation

`seed` and `sample_index` must be exact integers; bool/float/string values are rejected, and `sample_index` must be nonnegative. This avoids silent request aliasing.

## Native parametric family

The current entrypoint is `workspace/parametric/adapter.py`, backed by `native.py`
and `promotion.json`. `axis_tolerance` is0,1,2 or `target_panel_count`; default1
is exact canonical source. The composed setting selects the6 target's panel,
counts its distractor cells, then consumes that count as the per-axis threshold.
Sampled selected counts are0–2; other panels carry varied clutter.

Four constructive demonstrations now teach both axis boundaries and both motion
signs, plus independent panel-count gating. Three left hard-coded direction and
inactive-axis shortcuts, so native requests support4–6 demos and exactly4 novel
queries. Matched inputs and independent RNG streams prevent setting-dependent
input sampling; queries are invariant to requested demo count. Queries include
8×8 and substantively populated30×30. The retained legacy prototype gallery is
provenance, not this native teaching API.

The predecessor global-dead-zone ambiguity and native three-demo direction
regression are retained in the review checks. Current native review uses20
executable shortcuts for fixed settings and32 for the dynamic setting, fitted
on demos only. Qualification, causal witness, and current bounded execution
scope are in the return and task-local native-current evidence. Owner native
acceptance remains pending; no training admission or production change.

## Known limits and open item

The default schedule deliberately repeats exact public anchors, trading some input uniqueness for guaranteed canonical-profile support. The semantic contract currently names one task-specific rival. The official task-test stage is blocked by an immutable baseline fixture that assumes a fixed source-tree depth; the portable new regression file passes, but maintainer migration of the frozen fixture is still required.

## Current owner source and evidence limits

Accepted version4.1.0 exact scalar validation, canonical selected-text synchronization and a four-role witness/anchor curriculum. Signed integer seeds remain allowed; sample indices must be nonnegative exact integers. The canonical Racket rule is unchanged, selected text is byte-identical and archival raw_code is preserved. The reviewer reports 12 green battery stages, 600/600 strict support, 16/60 exact and 35/60 envelope support, 300 lessons with 1,200 clean query rotations and 904 unique inputs. Exact anchors reduce input diversity. Six focused tests pass, while the aggregate task-test stage exits2 before pytest because the unchanged frozen fixture uses fixed-depth canonical lookup. Keep that blocker open. The axis_tolerance0/1/2 prototype changes only per-axis movement thresholds; default1 is exact canonical source. Three complete episodes identify settings through live Racket labels and mirror parity. Separately, the owner replaced setting-bearing directories with opaque challenge identifiers and a separate public-only directory, passed8 focused tests and regenerated all three episodes. Original reviewer source/gallery remain preserved. No full battery rerun, production parameter API, variant approval or training admission.
## Current reviewer considerations

Source SHA-256: `b0684ae96d7c1ddd870d8ad3659e65d9acf363ecbb197b1e5d1ff8fb53daee9e`.

# Decisions — a85f5274d2ae

## D1 — preserve canonical semantics and synchronize only selected text

**Decision.** Keep rule hash `bba3b44960f2` and its behavior. Use the supported selected-only authority synchronization so `target_code` is byte-identical to canonical while historical `raw_code` remains unchanged.

**Original rationale.** The pre-repair exact-text divergence was undocumented; execution parity suggests formatting/history rather than an intended semantic fork.

**Alternatives rejected.** Rewriting the Racket logic was unjustified because rule smoke passed and normalized texts agreed. Overwriting archival raw text would destroy provenance.

**Evidence and limits.** `checks/authority-sync/a85f5274d2ae-selected.json` and final authority sync. Exact synchronization does not itself approve training or variants.

## D2 — reject invalid request identity at the public boundary

**Decision.** Require exact Python integers for `seed` and nonnegative `sample_index`; reject bools, strings, floats, and negatives before `gen_ctx`.

**Original rationale.** Unknown. The prior implementation delegated unchecked values and defect lint demonstrated accepted invalid requests.

**Alternatives rejected.** Coercion and clipping were rejected because they alias distinct caller errors to valid samples and weaken reproducibility.

**Probe/failure mode.** The new test first failed on the old implementation and now checks all invalid classes plus valid determinism. This validation does not attempt to constrain arbitrary-size valid integers beyond the runtime's existing behavior.

## D3 — use a four-role deterministic teaching schedule

**Decision.** Cycle `threshold_witness_a`, `public_anchor`, `threshold_witness_b`, and `broad` by `sample_index mod 4`.

**Original rationale.** The old source appeared designed for broad random layout coverage, but notes did not document a curriculum or a reason that random support was sufficient.

**Why.** Two witness roles guarantee that any 3-of-4 demonstration set refutes the canonical-fitting panel shortcut. The anchor guarantees exact public-profile support in each band. The broad role preserves general variation.

**Alternatives rejected.** Pure rejection sampling would make witness frequency probabilistic; all-public sampling would satisfy profile floor but overfit four fixed inputs; a single witness per cycle would fail the rotation requirement when that witness is held out.

**Limits.** The schedule is finite and task-specific. Any change to its length, demonstration count, or query policy requires rechecking every cyclic start and rotation.

## D4 — keep three demonstrations and support any query rotation

**Decision.** Declare `EXAMPLES_NEEDED=3`. Production uses three consecutive demonstrations and the next pair as query; authoring evidence also holds out each of four materialized pairs once.

**Why.** With two witness roles per four-pair cycle, three demos are sufficient for every rotation. The final semantic smoke checks 48 rotations; the larger census checks 1,200.

**Alternatives rejected.** Two demonstrations cannot guarantee a witness under this schedule. Requiring four demonstrations would be unnecessary overhead for the declared rival.

**Limits.** This sufficiency is relative to the current finite rival contract, not a universal minimum for human or model induction.

## D5 — make the strongest shortcut executable and retain an exact witness

**Decision.** Declare `panel_direction_only` in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; add `same_panel_far_axis`, `WITNESS_RIVALS`, and `lesson_identifiable`. Retain seed 913/sample 0/hard under `counterexamples/panel-direction-only/`.

**Why.** The rival fits every labeled canonical pair but disagrees whenever the target remains inside the marker's separator band while an axis distance is greater than one. This is a reference-lawful, plausible teaching ambiguity rather than a malformed-input trick.

**Output check.** The retained input was emitted by the production generator, passed strict validation, and was executed by the selected Racket rule. Python mirror and Racket output agree; the two differing cells are recorded.

**Limits.** A single executable rival is not a complete hypothesis space. Add future shortcuts as executable callables and focused witnesses.

## D6 — expose only the existing exact `scene_profile` control

**Decision.** Preserve `scene_profile` as the only advertised override. Explicit overrides bypass the teaching schedule and are validated exactly.

**Why.** The schedule is the default curriculum, while authors still need deterministic access to every public/general profile. Adding separate low-level dimensions or marker coordinates would expose combinations the constructor is not designed to honor.

**Alternatives rejected.** Silent fallback and clipped coordinates were rejected. New controls were unnecessary to repair the measured defects.

**Limits.** The special witness roles are curriculum roles, not public override values; they are generated through the default schedule.

## D7 — finish the prototype through the native adapter

**Decision.** Reuse fixed tolerance0/1/2 rules, preserve default1 exact bytes,
and add input-dependent target-panel cell count as a fourth setting. Use four
required teaching roles with deltas(1,4),(2,-4),(4,1),(-4,2) and counts0,2,2,1,
then apply one common dihedral transform and randomized scene construction.

**Why.** The earlier three-demo gallery admitted a global dead-zone rule.
An initial native three-demo proposal also admitted fixed direction and
never-move-one-axis rules. Random separated distractors then admitted a
connected-component count shortcut at seed24. Four roles now include a
connected same-color pair and a separated pair; they teach those distinctions,
including cell counting and count1 versus count2. This increases the minimum
teaching cost to four;5/6 remain supported. Simple fixed-threshold changes alone
did not supply the required substantive causal dependency.

**Evidence and limits.** Protected Racket executes labels and finite rivals;
a dynamic source-selection/count ablation supplies the causal witness. These
are bounded source-specific checks. Legacy gallery evidence is preserved,
production remains unchanged, and only owner native acceptance can promote it.

## D8 — do not edit the frozen legacy test fixture

**Decision.** Restore and preserve the baseline root fixture byte-for-byte even though its fixed-depth canonical path blocks portable task-test preflight.

**Why.** `DUTIES.md` explicitly assigns frozen-fixture migration to the maintainer. Editing it would create a misleading aggregate pass and violate patch scope.

**Alternative rejected.** A local path rewrite was tested during investigation but was reverted before final evidence. The new portable regression file uses `reviewer_support` and passes 6/6 independently.

**Limit/blocker.** Completion remains `blocked` until the maintainer migrates the frozen fixture. This does not negate the passing new tests or 12-stage battery.

## D9 — retain failures and source-bound audit conclusions

**Decision.** Keep the first semantic attempt that warned about unenumerated schedule starts, the official task-test preflight failure, and the initial 5b4 audit warning. Follow each with a stricter/new-path run rather than deleting or relabeling it.

**Why.** The warnings identified missing evidence, not source behavior to hide. The final main semantic battery enumerates the declared period; the final 5b4 semantic audit does the same.

**Limits.** Audit A1 is a finding only; no audit target was edited or approved.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a85f5274d2ae/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
