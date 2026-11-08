# Working notes: a0444de97675

## Current design

- **Authority:** canonical rule hash `e92da57c2394`; the Racket rule was not changed.
- **Final generator SHA-256:** `b7dd9f1c48c9bb5f3421ec8182c1f68eb26f180e6001017c4b800d56663a51ec`.
- **Intended rule:** count cells of color 1 in row 0; among rows 1+, segment monochrome 4-connected objects; select the unique object whose area equals that count; crop the original grid to its bounding box and scale the crop 2×.
- **Generated domain:** rectangular 8–14 by 9–14 grids, three body objects, exactly one area-matched target, color 1 reserved for the header, target area 3–6, optional non-1 header distractors, and optional edge contact between the target and a differently colored object.

## Repair decisions

1. **Connectivity semantics corrected.** The previous validator merged touching different-colored cells into one component. This rejected canonical examples and the retained audit input even though the authority's `(objects work 0)` semantics are monochrome. `_body_objects` is now color-sensitive by default; the old behavior remains only as an explicit rival.
2. **Authority pinned.** Added `RULE_HASH = "e92da57c2394"` and a pure Python mirror covered against all five canonical pairs and the retained Racket-labelled audit input.
3. **Exact controls made observable.** Replaced dead/overlapping declarations with six exact axes: `grid_h`, `grid_w`, `target_size`, `header_distractors`, `touching_mode`, and `target_color`. Unknown keys and invalid scalar types fail loudly; `observe_overrides` reports realized values.
4. **Teaching schedule strengthened.** Four cyclic profiles cross two distinctions missing from the canonical demonstrations: non-1 header distractors (only color 1 counts) and differently colored edge-touching objects (connectivity is color-sensitive). Every consecutive three-profile demonstration set refutes both declared rivals.
5. **Canonical support restored.** Profiles 0 and 2 use 8×9 inputs; this raises canonical-size/palette support above the profile-floor threshold without removing either teaching contrast.
6. **Body color 1 prohibited.** A strict defect probe showed that an all-blue body could masquerade as an area match. `self_check` now reserves color 1 for row 0.
7. **Portable regression fixture.** The first task-test snapshot showed that an old nested audit directory is not copied into the isolated runtime. The exact retained input and Racket output are now self-contained in the task test; the failed snapshot is preserved under `checks/task-tests/`, and the corrected snapshot passes under `checks/task-tests-2/`.

## Evidence

- Final 12-stage battery: `checks/after/checks/a0444de97675_after_battery_summary.json` — 12 green, 0 advisory, 0 failed.
- Portable task tests: `checks/task-tests-2/` — 8 passed.
- Lesson census: `checks/lesson-census.json` — 300/300 lessons materialized, 0 production ambiguities; 1,200/1,200 query rotations scored, 0 ambiguous; 1,200 unique inputs.
- Strongest shortcut witness: `checks/shortcuts/a0444de97675/`. The canonical-fitting `count_all_header_nonzero` rival disagrees with the pinned Racket output on generated seed `20261012`, sample index `1`, difficulty `easy`.
- Focused cyclic-start coverage is in `tests/test_generator_a0444de97675.py`.

## Known limits

- The semantic checks cover two declared plausible rivals; they do not prove uniqueness against every conceivable rule.
- The 300-lesson census samples production lessons and rotates each materialized query; the focused test exhausts the four schedule residues for several starts, but neither establishes all-seed universal induction.
- The generated target is deliberately bbox-open so output shape/content is informative. Solid canonical or audit targets remain accepted by `self_check`; generation does not currently sample them.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-d50e23a8ffe7b31e:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `25d9418bf77216b2ee5f20f189732e759c1a0e353d0cab5c4d2686e938576511`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Exact prior9x12 witness matches embedded literal regression (static equality observed), monochromeobjects/4x4expected asserted;8portabletests reviewerreported, no agentrerun. Exact-source repair accepted with reviewer-reported evidence. Finite declared-rival/regression evidence; root must explicitly dispose source-bound audit.

### Assessment or prior finding

## a0444de97675

**Reproduced validator/rule mismatch; no source was modified.** Audited generator
SHA-256:
`25d9418bf77216b2ee5f20f189732e759c1a0e353d0cab5c4d2686e938576511`.
Catalog state at execution was unapproved / `unverified`; executed rule hash was
`e92da57c2394`.

`self_check` groups all touching nonzero cells into color-agnostic components,
whereas canonical Racket `(objects work 0)` partitions touching cells by color.
The exact accepted 9×12 input has header `K=4`, color-agnostic component sizes
`4,5,3`, and monochrome object sizes `2,2,4,1,3`. Thus the validator sees exactly
one size-4 component, but the rule selects a different monochrome size-4 object
inside the color-agnostic size-5 cluster.

The target validator returns no errors. Canonical Racket outputs a 4×4 all-color-4
grid; the validator-implied color-agnostic selection produces a different 4×6
mixed-color grid. Evidence:

- `checks/audit/a0444de97675/input.json`
- `checks/audit/a0444de97675/precheck.json`
- `checks/audit/a0444de97675/racket.json`
- `checks/audit/a0444de97675/color_agnostic_validator_output.json`

The supported `arcpuzzles apply` command exited 0 and the Racket report records
matching catalog/executed rule hashes. This is a concrete domain mismatch, not
only a suspicion. Separate lint diagnostics also report a missing `RULE_HASH`
and unprobed single-token axes under
`checks/audit-diagnostics/a0444de97675/`, but the connectivity mismatch is the
stronger semantic finding. No repair was requested for this audit target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-d50e23a8ffe7b31e-v0001/audit_assets.json), manifest SHA-256 `69fb386a878455fadc21f2981391eb1d7289c3e67dc884c5d0451e96ccafed24`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `b7dd9f1c48c9bb5f3421ec8182c1f68eb26f180e6001017c4b800d56663a51ec`.

# Decisions: repair of a0444de97675

## D1 — Use monochrome connectivity, not color-agnostic occupancy

- **Original choice:** the baseline `_body_components` connected any nonzero orthogonal neighbors, regardless of color.
- **Why it failed:** three canonical inputs and the retained audit input contain differently colored edge-touching cells that the authoritative object primitive keeps separate. The baseline validator merged them and rejected lawful inputs.
- **Alternatives considered:** preserve occupancy connectivity and special-case canonical grids; loosen the validator without changing the internal object model; or match authority throughout. The first two would leave generated labels, validation, and shortcut analysis inconsistent.
- **Decision:** make monochrome 4-connectivity authoritative everywhere; retain color-agnostic connectivity only as an executable rival.
- **Evidence:** canonical/Racket regression tests in `repo/generators/a0444de97675/tests/test_generator_a0444de97675.py`; retained original evidence under the generator's `counterexamples/` tree.

## D2 — Preserve the Racket rule and pin its hash

- **Rationale:** the canonical examples and retained audit output agree with the existing rule. The defect was in generator-side interpretation, not authority.
- **Decision:** add `RULE_HASH = "e92da57c2394"`; no Racket source change.
- **Failure mode avoided:** a repair silently drifting to a different authority.
- **Evidence:** all five canonical pairs match the Python mirror; `rule_smoke` and `authority_sync` are green in `checks/after/`.

## D3 — Replace dead axes with six exact, observable controls

- **Original choice:** baseline axes included single-token/dead declarations and overlapping texture controls.
- **Alternatives:** mark them diagnostic, retain them as aliases, or replace them with directly observable semantic controls.
- **Decision:** expose `grid_h`, `grid_w`, `target_size`, `header_distractors`, `touching_mode`, and `target_color`; reject unknown keys and invalid types; implement `observe_overrides`.
- **Limit:** the generator intentionally always has three objects; object count is an invariant, not an advertised axis.
- **Evidence:** override stage green; exact round-trip and invalid-control tests pass.

## D4 — Teach two canonical blind spots with a four-profile cycle

- **Plausible rivals:** (1) count all nonzero header cells; (2) merge differently colored touching cells into one object.
- **Options:** random independent witnesses, forced witnesses in every example, or a cyclic schedule.
- **Decision:** use four profiles crossing header distractor present/absent with target touching/separated. `EXAMPLES_NEEDED=3`; every consecutive three-profile window contains both kinds of refutation while retaining variation.
- **Why not force both in every example:** that would make distractors and touching perfectly correlated with the task and unnecessarily narrow the distribution.
- **Evidence:** exhaustive cyclic-start focused test; `checks/lesson-census.json` reports 300 materialized lessons, 0 production ambiguities, and 1,200 rotations with 0 ambiguities.

## D5 — Raise canonical-profile support without weakening teaching

- **Initial repair choice:** only profile 0 was fixed at 8×9. The profile-floor gate measured 12/60 canonical-envelope draws (20%), below the required 25%.
- **Alternatives:** make all profiles canonical-sized; change palette/object structure; or make the second no-header profile canonical-sized.
- **Decision:** profiles 0 and 2 use 8×9. This yields canonical support in every band while retaining both touching states and both header-cue states.
- **Evidence:** preserved failure under `checks/profile-floor/`; passing rerun under `checks/profile-floor-2/` and final battery.

## D6 — Reserve color 1 for the header

- **Probe:** strict defect lint constructed a small grid whose body also used color 1; the validator accepted it as the target.
- **Decision:** reject any body color-1 cell. Generated colors already used 2–9, so this tightens validation without reducing intended generated support.
- **Evidence:** red regression `checks/tdd/red-body-one.txt`; final focused test passes.

## D7 — Keep the historical counterexample test portable

- **First attempt:** read a deeply nested retained audit file at test runtime.
- **Failure:** isolated `task_tests` copies task tests and selected source, not that nested historical return; the snapshot failed with `FileNotFoundError` (`checks/task-tests/`).
- **Decision:** embed the exact small input and expected Racket output in the regression test. The original evidence remains retained separately.
- **Evidence:** corrected isolated run `checks/task-tests-2/` passes 8/8.

## D8 — Scope of claims

The final checks establish consistency with the pinned authority, exact override behavior, support for the declared profiles, and separation from two concrete rivals. They do not prove that every possible human hypothesis is excluded or that every random seed yields an equally easy puzzle. Those remain explicit limits rather than inferred guarantees.

## D9 — Prove the source delta replays cleanly

- **Risk:** a valid-looking return can contain a patch that applies from the wrong Git root, omits a newly added file, or does not reconstruct the bytes that were tested.
- **Decision:** extract the original packet afresh, initialize Git at its exact `WORK/` directory, run `git apply --check` and `git apply` on the builder-generated patch, hash every changed path, compare all three files byte-for-byte with the active workspace, and rerun the portable focused suite.
- **Evidence:** `checks/fresh-replay/replay.json`; reconstructed generator SHA-256 `b7dd9f1c48c9bb5f3421ec8182c1f68eb26f180e6001017c4b800d56663a51ec`; 8/8 focused tests pass.


## Native parametric scaling: reviewer-ready, owner acceptance pending

The separate `workspace/parametric/` adapter adds episode-fixed scales 1, 2 and 3;
scale 2 preserves the exact canonical Racket source. The production generator
and authority remain unchanged. Ordinary use is three demos/four queries;
independent bounds are 2–6 demos and 1–4 queries. The single-query request exists
to verify identical first-turn projection. Settings, programs and query answers
stay private, with public identities computed solely from visible bytes.

The sampler grows to substantive 30×30 scenes with additional objects and area,
plus rectangular boundaries. Its first two demos now include both a foreign-cell
crop and a clean crop, and vary the selected object's area rank. Independent
review found that the initial two-demo lesson admitted a larger-multicolor-group
shortcut and a fixed-size-rank shortcut. Both were reproduced, retained with
18 protected Racket evaluations, and repaired without increasing demo count.
`counterexamples/parametric-teaching-gap/` preserves the original lesson/rivals;
the new regression covers seeds 0 and 17. The frozen lesson's capture-time pending
text is historical; `racket-replay.json` records completed execution and pins it.

Final evidence: 31 direct and 31 staged portable tests passed; 60/60 bounded
Python episodes had no ambiguity against the 26 declared rivals (including the
chosen scale), with at most one extra demo draw. `workspace/parametric/evidence/verified/`
contains six four-query examples, 48 executed labels, five canonical pairs,
boundary cases and executable shortcut predictions (125 Racket evaluations).
Native qualification separately passed all three settings at seeds 0/17 with
three demos/four queries: 42 labels and 78 Racket evaluations. The inventory is
`workspace/parametric/evidence/manifest.json`; returned qualification and causal
replay are under `checks/a0444de97675/`.

Causal dependency: count the blue header to obtain K, then choose the area-K
monochrome body object and crop it. The retained protected-Racket witness changes
K=10 to the incorrect all-nonzero count 11, selecting another lawful object and
changing the output. This establishes the named input-derived selection dependency
on that witness, not iterative simulation or universal algorithmic depth.

Limits: finite rivals/seeds only; slot-based sampling is narrower than the full
canonical domain. Large output crops are capped at 10×10 before scaling. No
measured learning benefit, owner acceptance, training admission or allocation
change is claimed. After integrating these exact source bytes, the owner must
perform fresh native qualification and acceptance. Reuse `verify.py` for future
focused evidence and update the source inventory after any implementation edit.
