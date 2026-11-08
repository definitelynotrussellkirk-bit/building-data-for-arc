# Working notes: 196d5de2ea8c

## Current review decision

Version 4.1.0 keeps the selected canonical Racket rule and `RULE_HASH=4af43de85dfe` unchanged. The generator source moved from SHA-256 `2427e6665c70cb388c6767096ea580209c281c390eb04605de1df07f43fba3ba` to `96e132c120dfd18cf4af855893951afff1373f4bdcfd5a339c9f3a0ba33fe806`.

## Repaired defects

- Reject non-literal or negative `seed`/`sample_index`, invalid difficulty, and unknown overrides before drawing.
- Restore canonical 19×19 support through a one-in-three generalized scale branch; final pinned support is 18/60 with every band represented.
- Declare executable rivals for including the outer border, sampling region corners, and using one global mode.
- Treat `include_outer_border` as a canonical shortcut: it fits all 8 canonical labels.
- Alternate a forced ignored-border counterexample with broad family coverage so every three-demo/one-query window and query rotation refutes all declared rivals.

Final strict battery: 12/12 green. Fixed-seed period census: 6 lessons and 24 rotations, zero ambiguity/errors. Wider census: 300 lessons and 1,200 rotations, zero ambiguity/errors.

## Proposed parametric extension

`workspace/parametric/` contains an isolated `border_policy` prototype with `exclude_outer` (canonical default) and `include_outer`. Both complete episodes are labelled by executed Racket and distinguish the setting. It is proposed authoring evidence only; production remains canonical.

## Retained blocker

The inherited frozen test `tests/test_generator_196d5de2ea8c.py` uses a fixed `__file__.parents[...]` canonical-data path and fails portable preflight before pytest. Packet rules forbid editing it. Maintainer migration should use `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`; until then the review completion state is blocked even though the reviewer-owned 23 tests pass.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`; `GNOTE-000022` was used only as a lead and all conclusions above were remeasured.
## Current reviewer considerations

Source SHA-256: `96e132c120dfd18cf4af855893951afff1373f4bdcfd5a339c9f3a0ba33fe806`.

# Decisions for `196d5de2ea8c`

## D1 — Preserve the canonical authority

The canonical Racket rule already matches the intended task, all 8 canonical labels, and the generator’s mirror. I therefore kept `RULE_HASH=4af43de85dfe` and source SHA `82af978f86f5a43424151559a8c2911316aba0eab6f2a935ca018651bd5ee4b1` unchanged. Changing authority to accommodate the sampler would have converted an authoring defect into a semantic fork.

## D2 — Reject malformed calls before any draw

`type(value) is int and value >= 0` is required for `seed` and `sample_index`, so booleans do not pass through Python’s `bool <: int` relationship and floats/strings are not coerced. Invalid difficulty and unknown overrides remain closed. The alternative—letting the context layer normalize these inputs—was rejected because it silently aliases curriculum positions and was the baseline hard failure.

## D3 — Restore canonical-scale support without narrowing the family

Generalized profiles choose 19×19 through `ctx.draw_choice("scale_profile", (True, False, False))`; otherwise they use the existing band ranges. This one-in-three branch, combined with retained public profiles, measured 18/60 exact canonical-envelope draws and support in every band. I rejected both “force every draw to 19×19” and larger scale weights: they clear the floor more easily but erase useful size diversity. Exploratory alternatives are retained under `checks/exploration/`; the accepted choice is bound by the final profile-floor report.

## D4 — Treat border inclusion as a real canonical shortcut

The “include row 0/column 0” rule fits all 8 canonical pairs, so it is declared in `CANONICAL_SHORTCUTS` rather than merely mentioned in prose. The generator’s existing `close_runner_up` profile was strengthened so its runner color fills the excluded border, yielding a direct answer-changing witness. Whitelisting the public examples or adding a witness that appears only in the query was rejected because neither teaches the distinction from demonstrations.

## D5 — Use a finite two-slot lesson schedule

The default schedule alternates `ignored_border_counterexample` and `broad_mix`, with `EXAMPLES_NEEDED=3`. Any four consecutive pairs therefore contain two forced border witnesses, and every legal held-out-query rotation still leaves at least one in the demonstrations. A longer profile-by-profile schedule was rejected as unnecessary: the two-slot period can be exhaustively enumerated, while the broad slot already samples the full family.

## D6 — Keep the semantic contract executable and finite

The repair declares pure rivals, witness-to-rival mappings, strict-family validation, and `lesson_identifiable`. This lets the shared gate check canonical fit, generated counterexamples, production lessons, and rotations. The claims are deliberately limited to the named rivals plus the shared generic search; the 300-lesson census is strong empirical evidence, not a universal identifiability proof.

## D7 — Isolate the rule-changing parameter

The nearby meaningful parameter is whether row 0/column 0 participate in regional modes. `border_policy={exclude_outer,include_outer}` preserves divider detection, regional mode aggregation, and 3×3 output composition; only three region starts change. It lives under `workspace/parametric/`, is labelled **proposed**, and is not connected to production generation or approval. Cosmetic parameters such as colors or dimensions were rejected because they do not change the executed transformation.

## D8 — Preserve the frozen test blocker

The inherited test’s fixed parent-depth lookup fails in the relocated runtime. Packet rules explicitly forbid patching a frozen fixture, so I did not copy data into the guessed location or edit the test. Completion is `blocked` until the maintainer migrates that fixture to `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`; the reviewer-owned 23-test suite remains independently green.

## D9 — Use prior notes only as leads

Associated note `GNOTE-000022` was treated as a lead, not proof. The baseline battery, canonical-shortcut check, schedule census, large lesson census, and Racket executions were rerun against the packet’s exact source bytes before any conclusion was recorded.
