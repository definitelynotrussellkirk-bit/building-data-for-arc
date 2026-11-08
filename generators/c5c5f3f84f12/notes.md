# Working notes: c5c5f3f84f12

## 2026-10-04 source-bound repair

Baseline SHA: `718bbc8227d9986505b838096ae3d0710260b719984688d7eeeebda347543195`
Final SHA: `c4200c63da1349b84e8233479b142004d2422c5f527204e53b30d01b9940940f`

The baseline omitted the canonical non-blue corner distractor, generated only three-color scenes, rejected canonical inputs, exposed non-exact axes, and lacked a semantic contract. Version 2.0.0 restores the exact source rule and canonical nuisance role, narrows the public surface to five observable controls, schedules all four control codes per lesson, and adds an independent oracle plus four executable rivals.

Final evidence: 12/12 inherited stages green; 26/26 portable task tests; 300/300 shared census lessons with no declared ambiguity; 384/384 cyclic/query-position lessons and 24/24 exact boundary overrides in the workspace probe. The selected Racket behavior did not change; the selected bank target text was synchronized exactly to its existing raw/canonical text.

The shape grammar intentionally uses connected asymmetric 3–8-cell polyominoes in a 4×4 envelope. This makes rotation observable but is not a proof against all unknown shape-specific shortcuts. Re-run the full battery, lesson census, and `workspace/probe_curriculum.py` after any schedule, axis, or semantic-hook edit.
## Current reviewer considerations

Source SHA-256: `c4200c63da1349b84e8233479b142004d2422c5f527204e53b30d01b9940940f`.

# Decisions for `c5c5f3f84f12`

## D1 — Pin the rule before changing the distribution

**Observed baseline:** the canonical and selected base rule both say that blue (`1`) is the control, the other corner singleton is irrelevant, the red (`2`) object is rotated by the blue corner, and the result is cropped/recolored cyan (`8`). The baseline generator instead varied corner aliases and rejected the canonical nuisance marker.

**Decision:** set `RULE_HASH = "148139dec0ec"`, implement an independent Python mirror, and make canonical examples the first regression. The selected Racket rule behavior was not edited.

**Rejected alternatives:** reinterpret all corner colors as controls; preserve the three-color generator and weaken canonical validation; patch the authority to match the generator. Each would train a different task.

**Failure mode guarded:** a generator can execute and look diverse while teaching a simpler, answer-incompatible rule.

## D2 — Make the non-blue corner marker mandatory

**Observed baseline rationale:** no retained task note explained why the nuisance marker had been removed. The likely intent was palette variation, but it deleted the exact feature that distinguishes “blue controls rotation” from “the only corner marker controls rotation.”

**Decision:** every lawful generated grid has exactly four colors: background `0`, blue control `1`, red object `2`, and one distractor color `3..7` in another corner.

**Probe:** all five canonical inputs pass `self_check`; `use_distractor_corner` is refuted in every final census/probe lesson.

**Rejected alternatives:** make the distractor optional; permit it in the interior; use the same color as the control. Those erase the role distinction or leave an uncanonical ambiguity.

## D3 — Replace aliases and singleton controls with five observable axes

**Observed baseline:** palette/texture aliases were dead or contradictory, exact overrides failed, and unknown keys could slip through. Some controls described implementation labels rather than pixel-observable facts.

**Decision:** retain only dimensions, blue-corner position, distractor color, and red-cell count. Validate type/range before constructing `GenCtx`; reject unknown keys; recover all accepted values from pixels.

**Probe:** final inherited override stage is green; the task-local probe exercises 24 cross-band lower/upper boundary cases; invalid booleans, strings, values, and keys are regression-tested.

**Rejected alternatives:** keep compatibility aliases, publish diagnostic-only axes, or infer override success from lack of exceptions. Exact observability is simpler and safer.

## D4 — Use two independent schedules

**Decision:** use `sample_index mod 4` for control-corner coverage and `sample_index mod 5` for canonical profile anchors. This guarantees every four-demo lesson sees all rotation codes while canonical-scale profiles recur in every band.

**Why not random:** a random control corner makes lesson identifiability probabilistic and allows entire lessons to omit one or more transforms.

**Why not one combined period:** coupling all choices to a single short period would create stronger correlations among corner, size, palette, and blob size. Separate periods reduce that shortcut while preserving deterministic coverage.

**Measured result:** the shared census materialized 300/300 lessons; the custom cyclic probe tested 384/384 lessons with uniform start and query-corner counts.

## D5 — Require connected asymmetric red objects

**Decision:** generate 3–8-cell connected polyominoes with four distinct rotation signatures. Use finite attempts plus a validated fallback bank to avoid rejection loops.

**Reason:** symmetric shapes can make 90°/180° distinctions unobservable, allowing fixed-identity or wrong-direction rules to survive a lesson.

**Rejected alternatives:** arbitrary rectangles, disconnected point clouds, and unconstrained random walks. Rectangles are often rotationally ambiguous; disconnected shapes alter object semantics; unconstrained walks can fail unpredictably.

**Limit:** the 4×4 envelope is a teaching grammar, not a claim that the canonical rule only applies to those shapes.

## D6 — Declare semantic rivals instead of relying on diversity statistics

**Decision:** add four executable competitors, witness predicates, `WITNESS_RIVALS`, and `lesson_identifiable`. The workspace probe discovers these dictionaries dynamically rather than copying a rival list.

**Why:** color/shape diversity does not prove that the intended control variable is identifiable. A model can fit all examples with a wrong causal rule unless a lesson contains a counterexample.

**Probe:** every rival is refuted in all 300 census lessons and all 384 cyclic lessons. The probe also verifies every declared canonical shortcut against canonical pairs; none are declared for this task.

## D7 — Synchronize exact authority text without changing behavior

**Observed baseline:** selected `target_code` contained comment-only expansion while `raw_code` and canonical source were already behaviorally equivalent. Strict authority sync therefore failed on text identity.

**Decision:** set selected `target_code` exactly equal to its existing `raw_code`. No executable Racket token or canonical row changed.

**Probe:** final authority-sync report is `synchronized` with execution parity `PASS`; focused tests compare exact text and normalized rule hash.

## D8 — Retain failures and add a reusable probe

**Decision:** preserve the 20-failure red test run, the interrupted long battery invocation, the complete green battery, and the first exposed solve's genuine iterator failure. Build `workspace/probe_curriculum.py` to cover the shared census's stated cyclic-query limitation.

**Reason:** deleting failed attempts hides which regression detects which defect and makes future review slower. The probe makes the central teaching guarantee replayable without another bespoke analysis.

## D9 — Audit targets remain finding-only

`699479899861` and `9733a2d68593` were inspected and executed but not patched. The former has a portable-test path defect despite 36/36 sampled semantic parity. The latter has a documented degenerate generator path accepted by `self_check` that crashes the Racket authority, plus broad gate failures. Those findings belong in `AUDIT.md`, not in this selected task delta.
