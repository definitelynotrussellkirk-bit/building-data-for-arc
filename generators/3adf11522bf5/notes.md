# Current review update — 2026-10-23 UTC

Final selected source SHA-256:
`73070905c812ef39c479df6bf80b47f68b21b9b94f391f48580906c48c80d7e7`.
Canonical `RULE_HASH` remains `a18583a5c8f2`; valid-call generation and the
canonical Racket rule are unchanged.

## Current repair

The pinned approved source passed 11/12 baseline stages. `defect_lint` found 33
strict-scalar violations: bool/float/string seeds and bool/float/string/negative
sample indices were accepted across easy, omitted, and hard difficulty. The root
cause was missing exact validation before context construction and later integer
coercion.

`generate` now requires a literal Python `int` seed and a nonnegative literal
Python `int` sample index. Eleven task-local regression cases cover the defect.
No version bump was made because all valid-call outputs must remain stable.

Final evidence: 12/12 battery stages green; portable task tests 25/25; override
matrix 33,300/33,300 accepted; profile floor 16/60 exact with every band
represented; 300/300 four-demo/one-query lessons and all 1,500 query rotations
have no surviving declared/searched rivals. Direct raw-repository pytest still
cannot collect the frozen fixture's portable import alias; this is retained as a
non-authoritative diagnostic, not hidden.

## Proposed parametric extension

`workspace/parametric/` contains an isolated prototype with
`minimum_disjoint_square_side ∈ {2,3}`, canonical default 2. The setting is
chosen once per episode and inputs do not depend on it. Two retained episodes
exercise both settings; 6 demonstrations refute the alternate threshold, both
queries differ, and four canonical labels are rechecked. Racket program hashes:

- threshold 2: `088344d6391d028058e85ddaced7431bca2921323758d2dda40e60a5d3b4a648`;
- threshold 3: `bbee6cfc3d3aab46d9fa3a995ec10f4a92eb45edc547aa373e8f4378d1323e8a`.

This remains proposed evidence only: no production axis, authority, approval, or
training-admission change. Finite rivals and two episodes do not prove universal
identifiability.

## Evidence leads

The previous approved repair `review-4d4db12e04cbfe1c:v0001` and bounded audit
`review-7f65e00a26f3126b:v0001` were used as leads, then remeasured against the
current packet policy. Detailed current rationale is in `WORK/DECISIONS.md` and
measurements are in `WORK/REVIEW.md`.

---

## Retained prior approved repair history

The relative evidence paths in this historical section belong to the earlier retained return, not to this packet's current `WORK/checks/` tree.

# Working notes: 3adf11522bf5

## Baseline diagnosis — 2026-10-04

The pinned v2.0.1 baseline failed 4/12 battery stages and had two advisory
findings. Evidence: `checks/before/checks/3adf11522bf5_before_battery_summary.json`.

1. `lint`: missing canonical `RULE_HASH`.
2. `defect_lint`: `self_check` accepted blank, full, singleton, and solid 2×2
   impostors; only 15/60 destructive mutations were rejected.
3. `override`: `AXES` advertised height 7–16 and width 8–18, but each difficulty
   called `draw_int` with a narrower range. The gate found 1,080 generation
   errors and accepted an unknown key.
4. `authority_sync`: the selected base `target_code` was a minified version of
   the canonical program. Execution and whitespace-normalized hashes agreed,
   but selected text was not synchronized exactly.
5. `profile_floor`: only 1/60 draws matched the 10×10/two-color canonical
   profile; easy and hard had zero support.
6. `semantic_gate`: no strict manifold, witnesses, rivals, or lesson contract.

The canonical examples establish two observable scene classes: maximum empty
square side 2 or 3. The strongest canonical-fitting shortcut is
`color_five_only`: all four canonical inputs use obstacle color 5, so a solver
that applies the true transform only for color 5 reproduces every canonical
answer. Generated non-5 scenes are therefore essential.

## Repair decisions

- Kept the Racket semantics unchanged and pinned `RULE_HASH = "a18583a5c8f2"`.
- Replaced difficulty-specific validity with full-range exact overrides in every
  band. Difficulty now only nudges density and rotates the default schedule.
- Added strict call validation, unknown-key rejection, observable overrides, and
  `INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()` because every Cartesian combination
  is constructive.
- Added a deterministic rejection sampler over exact obstacle counts. A
  `canonical2` scene has global maximum side 2; a `teaching` scene has maximum
  side 3 plus disjoint-smaller, overlap-exclusion, and tied-max witnesses.
- Added a 20-slot shape schedule with 25% exact 10×10 support in every band and
  a four-slot semantic cadence (`canonical2`, then three teaching scenes).
- Added an independent Python oracle and rival implementations in
  `workspace/reference_probe.py`; product code has its own `rule_mirror` so the
  tests compare two independently written implementations.
- Added task-local regression tests before implementation. The red run retained
  in `checks/task-tests-red/` failed all missing contracts; the final run passes
  7/7.
- Synchronized only `racket_target.target_code` in the selected base authority
  to the existing canonical text. `raw_code` remains the original minified
  archival source. No rule behavior or canonical row changed.

## Final measurements

- After battery: 12/12 green, zero advisories or failures.
- Override matrix: 33,300/33,300 draws accepted, 370 cases, all three bands,
  zero findings; unknown key rejected.
- Semantic gate: strict 600/600, canonical accepted 4/4, four witnesses firing,
  four rival claims verified, 12/12 smoke lessons identifiable.
- Canonical profile floor: 16/60 exact 10×10/two-color hits, with support in
  every band.
- Source-bound lesson census: 300/300 lessons, 1,500 unique inputs, zero
  production ambiguities and zero ambiguities across 1,500 query rotations.
- Post-repair exposed solve: revision 1 passed all 4 visible examples; earlier
  rule exposure was declared `yes` and no reference was consulted during solve.

## Limitations

The finite rival set is not a proof of universal identifiability. The generated
manifold intentionally limits maximum empty-square side to 2 or 3 and obstacle
density to 30–50%; this matches all canonical inputs while keeping exhaustive
semantic witnesses reliable. Difficulty changes density/order rather than rule
complexity. The rejection sampler is deterministic and passed the complete
advertised override matrix, but future axis expansion should re-run that matrix.
## Prior reviewer source binding (historical)

Source SHA-256 at that approved repair: `9c49f5db7d4f53fcaff2fe6f6a84407920a7b6ef73d9f371e1306f8782170790`.

# Decisions for `3adf11522bf5`

The canonical Racket law is fixed by `RULE_HASH = "a18583a5c8f2"`. The baseline
notes did not give a defensible rationale for its difficulty-specific dimension
bounds, Bernoulli obstacle sampler, weak validator, or lack of lesson witnesses;
where the original rationale was absent, it is recorded below as unknown rather
than reconstructed after the fact.

## D1 / R4 — Preserve rule semantics

**Choice.** Keep the canonical Racket program unchanged and synchronize only the
selected base `racket_target.target_code` to the already-existing canonical text.

**Rationale.** Canonical outputs, execution parity, and an independent Python
oracle all agreed. The blocker was exact selected-authority text divergence, not
rule behavior.

**Rejected alternatives.** Rewriting the Racket program would add semantic risk
without correcting a demonstrated semantic defect. Replacing archival `raw_code`
would erase provenance, so it remains minified and divergent by design.

**Probe and failure mode.** `authority_sync`, `rule_smoke`, the exact-text task
test, and canonical oracle parity all pass. A future canonical rule update must
change the pin and rerun every source-bound check.

## D2 / R1 — Make every advertised override exact in every band

**Choice.** Height 7–16, width 8–18, obstacle color 2–9, and both scene profiles
are legal Cartesian controls for `None`, easy, medium, and hard. Unknown keys,
wrong types, and out-of-range values fail before generation.

**Original rationale.** Unknown. The baseline advertised broad ranges while
calling narrower per-band `draw_int` bounds, which made its metadata false.

**Rejected alternatives.** Narrowing `AXES` to each difficulty would preserve
three incompatible contracts and reduce coverage. Declaring numerous
incompatibilities was unnecessary because every combination is constructible.

**Probe and failure mode.** The final override gate accepts 33,300/33,300 draws
across 370 cases and rejects an unknown key. Any added axis or widened domain
must rerun the complete override matrix, because deterministic rejection can
fail at extreme geometry/density combinations.

## D3 / R3 — Use a deterministic shape and color schedule

**Choice.** A 20-slot schedule contains five 10×10 slots and fifteen additional
shapes spanning the declared range; difficulty rotates order without changing
support. Obstacle colors cycle through 2–9 as a function of seed and index.

**Rationale.** The battery needs canonical-size/palette support in every band,
while training needs enough shape and color variation to defeat accidental
specialization. Keeping support equal across bands avoids an override being
valid in metadata but impossible in one band.

**Rejected alternatives.** Pure random dimensions gave weak and unstable
canonical-profile support. Always using 10×10 would pass the floor but create a
strong fixed-size shortcut. Always using obstacle color 5 would preserve the
strongest canonical shortcut.

**Probe and failure mode.** The battery sees 16/60 exact 10×10/two-color hits.
The reusable probe sees 16 shapes and all eight obstacle colors per band over 80
draws. The schedule is deterministic, so changing its period requires rechecking
all cyclic lesson starts.

## D4 / R2–R3 — Define two strict semantic profiles

**Choice.** `canonical2` has maximum all-zero square side 2 with tied maxima.
`teaching` has maximum side 3, tied maxima, a disjoint smaller-square witness,
and an overlap-exclusion witness.

**Rationale.** Canonical examples exhibit maxima of side 2 or 3. The two profiles
retain that observed complexity while making the subtle second clause of the
rule visible.

**Rejected alternatives.** Unconstrained Bernoulli noise can generate labels
that are correct but demonstrations that never distinguish `largest_only` or
`mark_all_square_cells`. Allowing arbitrary maximum side would broaden the rule
domain, but at the cost of expensive or unreliable constructive guarantees.

**Probe and limitation.** `self_check`, `strict_canonical_like`, named witnesses,
and the independent oracle enforce the profile. This is an intentional sampler
restriction, not a claim that side >3 inputs are unlawful for the canonical
program.

## D5 / R2 — Use 30–50% exact obstacle density

**Choice.** Draw an exact obstacle count in the 30–50% band, with a small
profile/area/difficulty-dependent target and deterministic jitter.

**Rationale.** Side-2 scenes generally need more obstacles than side-3 scenes;
exact counts make the validator and observed distribution stable. Difficulty
nudges density only and never changes legality.

**Rejected alternatives.** Independent Bernoulli placement produces unstable
density tails and can make exact overrides flaky. Hard-coded obstacle templates
would make witnesses reliable but introduce visible layout shortcuts.

**Probe and failure mode.** Every final semantic and override draw passes the
density check. The sampler uses at most 4,096 deterministic attempts; future
range expansion could exhaust that budget and must be measured, not assumed.

## D6 / R3 — Four-sample lesson cadence and four executable rivals

**Choice.** Every four consecutive samples contain one `canonical2` and three
`teaching` scenes. The declared rivals are `largest_only`,
`mark_all_square_cells`, `first_largest_only`, and `color_five_only`, each paired
with an executable witness; `color_five_only` is also a canonical shortcut.

**Rationale.** All canonical inputs use obstacle color 5, so a solver can fit all
four examples by applying the true transform only to color 5. The other three
rivals represent the main structural misreadings of union, disjointness, and ties.

**Rejected alternatives.** A single witness per long random run does not ensure
that any complete lesson teaches the distinction. Merely naming rivals without
executable predictions cannot verify that a witness actually changes the answer.

**Probe and limitation.** Task tests enumerate eight cyclic starts per band and
all five query rotations of each five-pair bundle; the reusable probe adds 300
rotations, and the production census checks 1,500 rotations. These finite rivals
do not exhaust all hypotheses a learner could invent.

## D7 / R2 — Strict self-check and observable reconstruction

**Choice.** `self_check` validates rectangular ARC grids, dimensions, exactly one
nonzero obstacle color in 2–9, density, and maximum side 2 or 3.
`observe_overrides` reconstructs all four controls and generation asserts exact
agreement.

**Rationale.** The baseline validator admitted blank, full, singleton, and
otherwise off-manifold grids. An exact observer turns each override promise into
a testable output property.

**Rejected alternatives.** Trusting generator internals or metadata would not
catch ignored overrides. A permissive validator would make strict-fraction
metrics meaningless.

**Probe and failure mode.** Destructive tests reject minimal impostors and a
second obstacle color. The observer intentionally classifies profiles from
maximum side; adding a third profile would require an unambiguous observable.

## D8 / R5 — Independent reviewer tooling

**Choice.** Keep an independent oracle/rival module separate from product code,
plus a standalone curriculum probe that dynamically reads the generator's rival
declarations.

**Rationale.** Comparing a generator mirror to itself can make a shared bug look
correct. Dynamic rival discovery prevents future declarations from silently
escaping the probe.

**Rejected alternatives.** Copying a fixed rival-name list into the probe would
become stale. Importing canonical labels into solve code would violate the solve
boundary.

**Probe and limitation.** `tests/test_generator.py` compares canonical pairs and
generated scenes against `workspace/reference_probe.py`; the production Racket
program remains final label authority. The Python oracle is still independently
written software, so Racket smoke/parity remains necessary.

## Current owner source and evidence limits

Accepted strict literal-integer seed/index and nonnegative-index guard;version3.0.0 and lawful deterministic sampler outputs unchanged. Canonical Racket unchanged. Reviewer12/12 battery,25 portable tests including fresh full99608-member replay,16/60 exact profile hits. Production4-demo/1-query census300 lessons/1500 unique inputs/1500 rotations has zero declared-rival ambiguities. minimum_disjoint_square_side2/3 prototype has two episodes,six demos,exact canonical default and live Racket rivals. Direct raw-repository pytest alias failure is a separate non-authoritative diagnostic;portable aggregate passes. Owner corrected seed-bearing public IDs and retained actual Racket export from passing naming tests. No production parameter API,variant approval,training admission or owner repair battery rerun.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-7f65e00a26f3126b:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `9c49f5db7d4f53fcaff2fe6f6a84407920a7b6ef73d9f371e1306f8782170790`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit bounded no_issue for the old valid-domain audit:32 generated/4 canonical reference cases and20 holdouts were clean. Its scope did not cover newer scalar policy;current repair separately fixes strict scalars. Finite assessment,not universal clearance.

### Assessment or prior finding

## 3adf11522bf5

**Verdict: No issue found in the bounded checks below.** This is a findings-only
audit of the selected source. No generator, rule, notes, or task tests were edited.
The current review index has no unresolved audit entries (`audits: []`).

All evidence filenames in this section resolve under `checks/audit/3adf11522bf5/`.

**Source binding.** Generator SHA-256:
`9c49f5db7d4f53fcaff2fe6f6a84407920a7b6ef73d9f371e1306f8782170790`.
The raw canonical `program_solution` text SHA-256 is
`088344d6391d028058e85ddaced7431bca2921323758d2dda40e60a5d3b4a648`.
The public Racket report records executed rule hash `a18583a5c8f2`, matching the
catalog, and runtime rule-text SHA-256
`519d72bc531bb981bc12dc0b2972e6c2b3e0c96fac1455efe3f569ec454fce48`.
The raw and executed text hashes describe their respective stored/runtime text;
they are not asserted to be identical.

**Targeted risk and valid-domain cases.** The deterministic rejection sampler has
a finite 4,096-attempt budget. I targeted its smallest teaching geometry, then
checked exact controls and the known teaching shortcuts:

- Sixteen default draws: seed 91, sample indices 0..7, easy and hard.
- Eight boundary draws: seed 407, index 1, easy/hard, each combination of
  7x8 or 16x18 and `scene_profile=canonical2|teaching`, `obstacle_color=7`.
- Eight additional smallest teaching draws: seeds 0..7, index 1, difficulty
  omitted, `grid_h=7`, `grid_w=8`, `scene_profile=teaching`.
- All four original canonical input/answer pairs.

All 32 generated requests succeeded, all returned grids passed `self_check`, and
independent exhaustive square-footprint enumeration observed exact requested
dimensions, obstacle color, and scene profile. Case-specific seeds, indices,
difficulty, overrides, density, maximum square side, tied maxima, and validation
results are retained in `metadata.json`. Actual input/output grids and their
hashes are retained in the public `racket.json` report. All 36 reference
executions succeeded; the four original canonical outputs matched exactly.

**Teaching checks.** Independent rival predictions are in `rivals.json`; actual
labels are exclusively the public Racket outputs. Among the 32 generated inputs,
Racket disagreed with `largest_only` on 24, `mark_all_square_cells` on 24,
`first_largest_only` on 32, and `color_five_only` on 29. The color shortcut uses
the Racket answer only in its color-5 branch and identity in its other branch.
Four five-pair default windows (starts 0 and 3 in easy/hard) were checked with
every pair exchanged into the query slot: all 20 four-demonstration lessons
returned no identifiability reasons from the public lesson hook.

**Reproduction.** Run these commands from
`/workspace/scratch/cdcdb519712b/review_work/WORK` (the wrapper runs payloads from
its `repo/` directory). Final commands each exited **0**:

```bash
python3 run_with_racket.py python3 ../checks/audit/3adf11522bf5/probe.py prepare
python3 run_with_racket.py python3 -m arcpuzzles apply 3adf11522bf5 --input ../checks/audit/3adf11522bf5/input.json --out ../checks/audit/3adf11522bf5/racket.json
python3 run_with_racket.py python3 ../checks/audit/3adf11522bf5/probe.py analyze
```

The `--out` destination must be absent when replaying public `apply`; choose a
fresh destination or remove only the replay's prior generated report.
Logs are `prepare.log`, `apply.log`, and `analyze.log`; machine conclusions and
20 lesson rotations are in `summary.json`, with command evidence in
`commands.json`.

**Scope.** No concrete valid-domain generation failure or surviving declared
teaching shortcut was found. This checks 32 draws, two explicit difficulty
bands plus eight difficulty-omitted cases, two boundary shapes, and four default
lesson windows. It does not exhaust all seeds, the medium band, or all lawful
Cartesian overrides, and it is not a full battery or a universal
identifiability claim. The documented maximum-square-side restriction to 2/3
was treated as the selected sampler contract.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-7f65e00a26f3126b-v0001/audit_assets.json), manifest SHA-256 `eac534940b23b4961fedf04b92ebf9f386687a4f12020ab685f0a64d2364daf8`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `73070905c812ef39c479df6bf80b47f68b21b9b94f391f48580906c48c80d7e7`.

# Decisions — `3adf11522bf5`

## D1 / R1 — validate public scalars before constructing the context

**Choice.** Require `type(seed) is int`; require `type(sample_index) is int` and
`sample_index >= 0`. Raise `ValueError` with the offending argument named.

**Original rationale.** Unknown. The selected source relied on downstream
coercion even though the current checker treats these fields as strict public
scalars.

**Alternatives rejected.** `isinstance(x, int)` would still admit `bool`.
Silently calling `int(x)` would preserve the defect for strings and floats.
Validation inside later draw helpers would be too late and inconsistent across
paths.

**Probe / failure mode.** Eleven task-local regression cases cover bool, float,
string, and negative-index inputs. A future public scalar addition should get an
exact type/range test at the same boundary.

## D2 / R1 — keep version, rule, and valid-call generation stable

**Choice.** Retain `VERSION = "3.0.0"`, `RULE_HASH = "a18583a5c8f2"`, all
sampling schedules, axes, profiles, and canonical Racket bytes.

**Rationale.** The measured defect concerned invalid calls only. Changing the
version would perturb context-derived randomness for every valid call and would
turn a contract repair into an unnecessary distribution migration.

**Alternatives rejected.** A version bump, sampler rewrite, or Racket edit would
create far more semantic and replay risk without addressing additional evidence.

**Probe / limitation.** The full after battery, authority sync, Racket smoke,
override matrix, profile floor, semantic gate, and lesson census all bind to
source SHA `73070905…`. The checker does not exhaust every valid seed/index.

## D3 / P1 — parameterize only the minimum side of disjoint squares

**Choice.** Proposed parameter `minimum_disjoint_square_side ∈ {2,3}`, with
canonical default 2.

**Original rationale.** The assignment requested a small original-family
parameter while preserving object roles and reasoning structure. The canonical
program exposes a natural lower bound in its final disjoint-square enumeration.

**Alternatives rejected.** Changing output color is a superficial palette
variant. Selecting only one tied maximum breaks the core union reasoning.
Changing overlap semantics or obstacle roles creates a different task family.
Allowing arbitrary thresholds exceeds the selected side-2/side-3 generator
manifold and weakens teachability.

**Probe / failure mode.** Exact Racket programs differ only in the lower bound.
Both settings have a full episode, demonstrations refute the alternate setting,
and the query differs. The evidence covers only one episode per setting.

## D4 / P1 — keep the parameterized family outside production

**Choice.** Store the runner, tests, examples, and source-bound evidence under
`workspace/parametric/` and `checks/parametric/`; do not add a production axis or
change selected authority.

**Rationale.** Parametric authoring priority does not grant training or source
approval. Isolation makes the proposal replayable without contaminating the
canonical generator.

**Alternatives rejected.** Adding `minimum_disjoint_square_side` to production
`AXES` would silently mix two label laws under one canonical task ID. Embedding
hidden settings in public JSON would leak the intended induction target.

**Probe / failure mode.** Public files omit the setting, Racket program, and query
answer; private files retain them. A future promotion must define a distinct
family/authority and rerun source-bound curriculum checks.

## D5 / P1 — use a parameter-independent teaching schedule

**Choice.** Every prototype episode uses profiles
`[canonical2, teaching, teaching, teaching]`: three demonstrations and one query.
The hidden setting is chosen once, independently of inputs.

**Rationale.** The first example proves canonical-default parity but is
invariant; the next two deliberately expose side-2 disjoint regions, and the
query also differs. This prevents input selection from leaking the setting while
making it inferable from demonstrations.

**Alternatives rejected.** All-`canonical2` demonstrations leave thresholds 2
and 3 observationally equivalent. Parameter-conditioned geometry would let a
model infer the setting from input distribution instead of transformation
behavior.

**Probe / limitation.** Demonstrations 1 and 2 refute the alternate threshold in
both retained episodes. This is finite direct-rival evidence only.

## D6 / V1 — use the portable selected-task stage as the authoritative test run

**Choice.** Report `arcpuzzles check ... --stage task_tests` as the selected-task
test result and retain raw repository pytest only as a diagnostic.

**Rationale.** The frozen inherited fixture imports the runtime alias
`puzzle_generators.per_puzzle.<task>`, which the portable stage intentionally
constructs. Editing that fixture is explicitly forbidden.

**Alternatives rejected.** Rewriting the frozen fixture or adding repository
alias shims would broaden the patch solely to satisfy the wrong launcher.

**Probe / failure mode.** Portable task tests pass 25/25. Direct repository
pytest fails at collection with the missing runtime alias; that failure is
retained in `checks/direct-pytest-diagnostic.log` and is not hidden.

## D7 — stop after the minimal source repair

**Choice.** Do not alter production distribution or rule after all remaining
baseline stages passed.

**Rationale.** The pinned source already had strong canonical support,
constructive semantic profiles, exact overrides, and declared rival coverage.
The 300-lesson census found no ambiguity under production order or rotations.

**Failure mode.** Finite rivals and finite seeds do not establish universal
induction. Future rule, axis, schedule, or helper changes require the same full
battery, task tests, and census.
