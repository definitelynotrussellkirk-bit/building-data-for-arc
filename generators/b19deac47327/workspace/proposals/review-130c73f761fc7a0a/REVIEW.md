# Review — b19deac47327
Task/version: `b19deac47327`, generator `2.1.0`, final SHA-256 `14284b3bd817e139cf615486973e192da5ec84a97f50c200832e23cd682551ed`.
Baseline defect: the current selected `2.0.0` source failed defect lint despite 11/12 green stages—24 strict-call findings plus a default `grid_h` span limited to 12–13 against declared/canonical support.
Repair: reject nonliteral seed/sample scalars and negative indices, and broaden default height support to 12–16 without weakening the four-slot lesson anchors.
Final battery: 12/12 green under fixed-seed exhaustive schedule enumeration; evidence: `checks/after-enumerated/checks/b19deac47327_after_battery_summary.json`.
Focused portable tests: 25/25 passed; evidence: `checks/final-task-tests/checks/task_tests.xml` and `checks/final-task-tests/result.json`.
Lesson policy: three demonstrations plus one query from a four-slot schedule; 300/300 lessons and 1,200 unique inputs had 0 production and 0 query-rotation ambiguities against declared rivals.
Parametric assessment: proposed, unapproved `projection_depth ∈ {1,2}` prototype; two retained episodes, six demonstrations, two queries, and 0 surviving parameter rivals.
Authority: no canonical Racket rule changed; `RULE_HASH` remains `2b2e46dd36cc`, and selected execution parity passed.
Remaining limitation: all induction claims are finite and only cover declared rivals, retained seeds, and the bounded prototype grammar.
Acceptance: routine.

## Maintainer finding table

| ID | Task/path | Finding or contribution | Evidence/reproducer | Patch status | Final result |
|---|---|---|---|---|---|
| R1 | `b19deac47327/generator.py` | Strict public-call validation and wider default height provenance | `checks/before/`, `checks/tdd-red-canonical/`, `checks/tdd-green-canonical-2/` | Patched | Final 12/12 battery green |
| R2 | `b19deac47327/workspace/parametric/` | Runnable episode-level `projection_depth` extension | `checks/parametric/projection-depth-v1/report.json` | Proposed only; canonical path unchanged | 2 settings covered; 0 parameter-rival survivors |
| R3 | `b19deac47327/tests/` | Regression tests for scalar validation, full strict height envelope, and parametric evidence | `checks/task-tests/checks/task_tests.xml` | Patched | 25/25 passed |
| A1 | `6f6c567e365b` | Three demonstrations admit an ignore-all-keys rival that changes the query | `checks/audit/6f6c567e365b/counterexample.json` | Audit only; unchanged | Reproduced defect |
| A2 | `3511f98c7b84` | Advertised override axes are inert or reject declared-valid values | `checks/audit/3511f98c7b84/override_counterexample.json` | Audit only; unchanged | Reproduced defect |

## Scope and prior evidence

I used approved return `review-a8e2e34d9efd7169:v0001` only as a lead for the already-selected v2.0 design and its unresolved assumptions. I did not treat its claims as current measurements. The current packet’s clean baseline, current-source tests, and protected Racket runs are the evidence reported here.

The assigned source already contained a strong canonical repair: exact observable axes, a four-profile lesson schedule, an independent Python rule mirror, witnesses/rivals, canonical-shortcut counterexamples, and a pinned canonical rule. This review therefore made the narrow current-source repair that the baseline exposed and built the missing parametric extension separately.

## R1 — canonical generator repair

### Reproduced baseline

The before battery bound to generator SHA-256 `e8eeb4702e21c23fbb5e01c317b5e8f27462f303295b0aa0c39ba9e00e94bd70` completed 11 green stages and failed only defect lint. The failure combined strict-call contract findings with a default height axis that was declared/canonically broader than the sampled 12–13 support. Evidence is retained at `checks/before/checks/b19deac47327_before_battery_summary.json` and the corresponding defect-lint log.

### Implemented repair

`VERSION` is now `2.1.0`. `_validate_public_call` rejects bools, floats, and strings for `seed` and `sample_index`, rejects negative sample indices, and validates difficulty before schedule indexing or generation. This prevents Python’s permissive scalar behavior from silently accepting values that violate the public contract.

Default height selection now uses profile-specific choices:

- `cross_horizontal`: 12 only;
- `tie_vertical`: 12–16;
- `cross_vertical`: 12 only;
- `tie_horizontal`: 13 or 15.

The two crossed canonical-shape profiles remain fixed because every query rotation needs at least one crossed shape among its demonstrations. Variation is placed on dimensions that do not destroy the profile’s semantic witness; odd heights are retained for the horizontal tie profile. The first broader attempt varied all profiles and failed three lesson tests, so it was rejected rather than rationalized; that intermediate failure is retained at `checks/tdd-green-canonical/`.

`counterexamples/canonical_shortcuts.json` was rebound to the final generator version/hash without changing its semantic cases.

### Verification

The final enumerated after battery used seed 0 and exhausted the declared four-slot schedule. It completed 12/12 stages green on final SHA-256 `14284b3bd817e139cf615486973e192da5ec84a97f50c200832e23cd682551ed`.

Measured final-source results:

- strict semantic support: 600/600 draws, 200 per band;
- profile floor: 31/60 exact canonical-profile hits and 60/60 envelope hits; exact support was present in every band (easy 10/20, medium 12/20, hard 9/20);
- override matrix: 849 cases and 76,410/76,410 accepted draws, with 0 findings and 0 warnings;
- fixed-seed schedule enumeration: 12/12 lessons, 48 pairs, 48 query rotations, 0 production ambiguities, 0 rotation ambiguities;
- broad production census: 300/300 materialized lessons, 1,200 pairs/unique inputs, 0 production ambiguities, and 0/1,200 rotation ambiguities.

Exact evidence is under `checks/after-enumerated/`, with the wider census companion at `checks/lesson-census.summary.json`.

## R2 — parametric extension

The separate prototype at `repo/generators/b19deac47327/workspace/parametric/prototype.py` adds one episode-level parameter, `projection_depth`, with values 1 and 2. Depth 1 is byte-for-byte the canonical Racket program (`18c042039414a6bd8745b9ffc3277879010959e3ce76d64d94d4d16925343dd8`); depth 2 uses Racket SHA-256 `6298af1e4528c6f2331e40466a2b61a16ae5809c87372540695cf5e1e27be7c9` and projects the matching border color two cells instead of one.

The parameter is selected once per episode, labels are produced by protected Racket execution, and an independent Python mirror is checked against every retained label. Public episodes omit the selected rule and private evidence retains the parameter, exact rule bytes, labels, hashes, and a distinguishing witness. The report covers two settings, two episodes, six demonstrations, two queries, 22 Racket applications, four canonical replays, and no surviving alternate-parameter rival.

This is explicitly `proposed_unapproved`. It does not alter the canonical generator, authority, rule hash, or training admission. Evidence and limits are in `checks/parametric/projection-depth-v1/report.json` and `repo/generators/b19deac47327/workspace/parametric/README.md`.

## Solve records

The mandatory blind task `019445e9b5a1` was solved before opening repair material. The first visible-only hypothesis passed all three demonstrations; the finish record declares no earlier exposure and no reference consultation. Evidence: `solve-blind/summary.json`.

The final-source exposed solve was prepared from generator SHA-256 `14284b3bd817e139cf615486973e192da5ec84a97f50c200832e23cd682551ed`. Its first visible-only implementation passed 3/3 demonstrations; earlier exposure is honestly marked yes and reference consultation during the solve is marked false. Evidence: `solve/summary.json`.

## Self-review

The new height variation was checked specifically for a new curriculum shortcut: crossed shape/orientation anchors remain fixed, tie profiles retain their required odd projection axis, and all four query rotations remain distinguishable against declared rivals. The variation is intentionally not claimed to eliminate every incidental correlation or undeclared hypothesis.

## Failed and intermediate evidence retained

- `checks/tdd-red-canonical/`: new canonical tests failed before implementation.
- `checks/tdd-green-canonical/`: an overbroad first implementation still failed three lesson tests.
- `checks/tdd-red-parametric/`: the prototype tests failed before the prototype existed.
- `checks/after/`: all nonsemantic stages passed, but semantic gate correctly failed because the declared schedule had not been explicitly enumerated.
- `checks/after-enumerated/`: fresh final-source battery with the required enumeration, 12/12 green.

No Racket authority or unrelated generator was modified.
