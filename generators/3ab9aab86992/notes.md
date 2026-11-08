# Reviewed distribution: 3ab9aab86992

Current review assignment: `review-c43dee774bf3dba1`; selected generator
version `2.2.0`. The canonical Racket rule and normalized `RULE_HASH`
`bbdf13ba2dfd` are unchanged. This review does not alter approval or training
status.

## Intended rule and domain

The input is an odd square of side 5–15 with a nonzero strict-majority
background and one to four monochrome 4-connected L triominoes. Each L occupies
three cells of a 2×2 bounding box. Orientations are unique; colors may repeat
only across disconnected components. The occupied vertex of each small L—not
its position or color—selects the corresponding output corner. The output draws
a same-color enlarged border L at every selected corner and leaves unselected
corners as background.

Zero remains a valid foreground color but not a background under the selected
Racket mode. Different colors may touch or interlock. Same-color components may
not touch orthogonally because they would merge. Explicit `no_corners` and
`full_grid` textures remain rejected diagnostics, not ordinary training draws.

## Repaired lesson contract

Prior version `2.1.0` sampled each pair independently. A retained audit from
`review-38c015cb27208030:v0001` found two lessons in which the only incomplete
orientation set became the query. The other three examples all contained four
orientations, so the canonical-fitting `complete_all_corners` rival survived
all demonstrations and changed the query. The exact source-bound replays are
retained in `counterexamples/review-c43dee774bf3dba1/rotation-schedule.json`.

The new default schedule has period two and alternates `partial` / `complete`
profiles for every fixed seed. With three demonstrations plus one query, every
cyclic query rotation therefore retains at least one incomplete demonstration.
The seed phase is grouped in period-sized blocks so fixed sample positions and
the common `generate(seed, seed)` census both exercise both profiles. Explicit
`n_corners`, `palette_size`, or `texture` overrides remain exact diagnostics and
bypass this teaching schedule.

`EXAMPLES_NEEDED = 3`, `LESSON_SCHEDULE_PERIOD = 2`, and
`SCHEDULE_PROFILES = ("partial", "complete")` make the assembly policy
machine-readable. `lesson_identifiable(demos, query)` validates labels and
rejects a lesson when any declared `LESSON_COMPETITORS` rival fits every
training pair but changes the query. The currently declared finite rival set is
only `complete_all_corners`; passing it is not a proof of unique induction
against arbitrary programs.

## Distribution and API decisions

Complete ordinary-default samples contain all four orientations and four
distinct foreground colors. This preserves the canonical five-color profile
(background plus four foreground colors) in every difficulty band. Partial
samples retain palette-size variation and repeated-color support. Difficulty
still controls size and partial-cardinality support; it is not claimed to be a
calibrated reasoning-difficulty scale.

`seed` must be a non-boolean integer. `sample_index` must be a non-boolean,
nonnegative integer. This rejects lossy or surprising scalar values before the
shared generation context can coerce them. Existing exact override validation,
packing, nonidentity sampling, and canonical rule authority remain unchanged.

## Parametric prototype

`workspace/parametric/` contains a separate proposed `corner_basis` prototype:

- `occupied` is the byte-exact canonical/default Racket program.
- `missing` uses the absent cell of each L's 2×2 box, selecting the diagonally
  opposite output corner.

The parameter is selected once per episode and held fixed across three
demonstrations and one query. Prototype labels are executed by Racket. Its
bounded evidence sampler requests exactly one L per pair so the two declared
settings disagree on every retained input and every query rotation remains
identifiable. This one-object restriction is prototype evidence scope, not a
production distribution change. Multi-object symmetries can make the two
settings coincide and would require episode-level distinction checks or
resampling before promotion. The prototype does not modify the selected rule,
`RULE_HASH`, or approval.

## Assumptions, limits, and open findings

- The output meaning of conflicting duplicate orientations is intentionally
  outside this generator family.
- The period-two guarantee covers four-pair lessons assembled from consecutive
  default sample indices. A different assembler must honor or recheck the
  declared schedule.
- Exact overrides may deliberately construct ambiguous lessons; they are not
  promised the default teaching guarantee.
- The executable finite-rival checks establish evidence only for named rivals
  and sampled inputs, not universal identifiability.
- The parametric `missing` rule is a proposal with bounded evidence, not an
  approved variant.
- Catalog/training approval remains external to this review.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-38c015cb27208030:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `195f414894a16f9ee8986b7053c5757746bdee66eb89e5f781145e9d5e762d73`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve prior query-rotation finding on277f63c0a443811356a15528b6f80b5e30c1025b4cb95237bece99f125403e3f. Default period-two partial/complete schedule places two incomplete witnesses in each four-pair window,so every query holdout retains a refutation of complete_all_corners. Seed phase avoids seed=index cancellation;explicit override diagnostics bypass schedule honestly. Reviewer reports12/12 battery,115 local/fresh tests,12 lessons/48 required rotations,all6 period-residue lessons/24 rotations and300 lessons/1200 larger rotations clean. Canonical Racket unchanged. Prior minimal source-bound counterexample retained;finite declared-rival evidence only,no universal identification or owner battery rerun.

### Assessment or prior finding

## 3ab9aab86992

**Reproduced issue: lesson assembly is not safe under all query rotations.**

Assigned generator SHA-256:
`195f414894a16f9ee8986b7053c5757746bdee66eb89e5f781145e9d5e762d73`;
rule pin `bbdf13ba2dfd`. The generator correctly declares the canonical-fitting
`complete_all_corners` rival and emits ordinary one-corner witnesses that refute it.
The exact request
`generate(0, 0, canvas_size=7, bg_color=8, n_corners=1, palette_size=1)` passes
`self_check`, triggers `incomplete_corner_set`, and makes the rival disagree with the
canonical Racket output. The Python mirror and Racket output match. Evidence:
`checks/audit/3ab9aab86992/counterexample.json`.

However, the required-rotation semantic gate failed: the normal production order was
identifiable for 12/12 materialized lessons, but 2 of 48 query rotations remained
ambiguous against `complete_all_corners`. The generator has no `lesson_identifiable`
hook, so assessment falls back to declared-rival scoring only. Exact ambiguous replays:

- medium: seed `261084514713971`, sample index `22`, query index `0`, training indices
  `[1,2,3]`, instance hash
  `fa1e2613d72db2b10a590272a37186b5cd7e66521c734b4018460fbcd02fbe73`;
- hard: seed `30084842535242`, sample index `11`, query index `2`, training indices
  `[0,1,3]`, instance hash
  `95a7a1661b798cb240683ea997f43f786525bf88fa648361fd95067158d75fdc`.

Compact evidence is `checks/audit/3ab9aab86992/rotation-finding.json`; the complete
source-bound report and exact grids are in
`checks/audit/3ab9aab86992/semantic-gate/checks/3ab9aab86992_after_semantic_gate.json`.
This is an audit finding only. No source under `generators/3ab9aab86992/` was modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-38c015cb27208030-v0001/audit_assets.json), manifest SHA-256 `de81dc79ddebdfa2d54b0662660f0197487eece78360467c881d7fa4aa31bfee`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `277f63c0a443811356a15528b6f80b5e30c1025b4cb95237bece99f125403e3f`.

# Decisions — `3ab9aab86992`

Final generator SHA-256: `277f63c0a443811356a15528b6f80b5e30c1025b4cb95237bece99f125403e3f`. Canonical `RULE_HASH`: `bbdf13ba2dfd` (unchanged).

## D1 — guarantee a partial witness by schedule, not probability

**Prior choice.** Version `2.1.0` sampled cardinality independently. A partial example was common but not guaranteed to remain among three demonstrations under arbitrary query rotation.

**New choice.** Ordinary defaults alternate `partial` and `complete` with declared period 2. The phase is `(seed // 2 + sample_index) % 2`.

**Reason.** A four-pair episode then has two partial and two complete pairs. Holding out any query leaves at least one partial demonstration, which necessarily refutes `complete_all_corners`.

**Rejected alternatives.** A higher random probability of partial samples still gives no lesson guarantee. Making every sample partial would remove canonical all-four support. The simpler `(seed + sample_index) % 2` phase collapses to one profile in a common `generate(seed, seed)` census. A phase based only on sample index preserves lessons but makes a fixed sample position population-homogeneous.

**Evidence.** `counterexamples/review-c43dee774bf3dba1/rotation-schedule.json`, `tests/test_rotation_schedule.py`, and the fixed-seed schedule receipt under `checks/after-final/`.

## D2 — keep exact overrides outside the teaching schedule

**Choice.** Explicit `n_corners`, `palette_size`, or `texture` requests bypass the ordinary partial/complete lesson schedule.

**Reason.** Overrides are an exact authoring and diagnostic API. Silently changing an explicit cardinality to satisfy a lesson policy would make provenance false and break product tests. Lesson assembly must request ordinary defaults when it wants the guarantee.

**Known limit.** A caller can deliberately assemble an ambiguous lesson from exact overrides. `lesson_identifiable` exists so the lesson builder can reject that episode rather than corrupting the override.

## D3 — restore canonical five-color support only on complete defaults

**Prior issue.** The initial repair made the schedule rotation-safe but the actual default palette path did not guarantee the canonical background-plus-four-foreground profile was reachable.

**Choice.** Complete ordinary defaults use four distinct foreground colors. Partial defaults continue to sample smaller palettes and repeated colors.

**Reason.** This preserves canonical support without introducing a universal one-color-per-object shortcut. It also keeps the partial lessons that refute the cardinality rival.

**Rejected alternative.** Making every sample all-distinct would simplify coverage but erase useful repeated-color/disconnected-component evidence.

## D4 — reject invalid call scalars before generation context use

**Choice.** `seed` must be a non-boolean `Integral`; `sample_index` must be a non-boolean, nonnegative `Integral`; difficulty must be `None`, `easy`, `medium`, or `hard`.

**Reason.** Booleans are integers in Python, negative indices affect modular schedules, and unsupported difficulty values previously fell through to a default band. Allowing them creates valid-looking grids with invalid provenance. Validation is at the public generator boundary, not buried in downstream sampling.

**Compatibility note.** This intentionally tightens out-of-contract behavior; no documented valid call changes.

## D5 — make the finite lesson contract executable

**Choice.** Declare `EXAMPLES_NEEDED`, `LESSON_SCHEDULE_PERIOD`, `SCHEDULE_PROFILES`, and `LESSON_COMPETITORS`; add `lesson_identifiable(demos, query)`.

**Reason.** Grid validity, correct Racket labels, and lesson identifiability are different properties. The hook checks all labeled pairs and reports a concrete survivor when a declared wrong rule fits demonstrations but changes the query.

**Limit.** The hook tests declared deterministic rivals, not every possible algorithm. Generic measured-label mutations are useful leads but are not independent unseen-input predictors.

## D6 — preserve canonical Racket authority

**Choice.** Do not edit the selected Racket program or normalized rule hash.

**Reason.** The root cause was lesson sampling and API validation, not the transformation law. Changing authority would expand the review scope and invalidate existing canonical evidence without solving the scheduling defect.

## D7 — isolate the parametric extension

**Choice.** Prototype one episode-level parameter, `corner_basis`, in `workspace/parametric/` rather than adding it to canonical `generate`.

- `occupied` is the byte-identical canonical setting.
- `missing` uses the absent cell of the 2×2 L box.

**Reason.** The two settings preserve the original orientation/corner reasoning family, are easy to explain, and are distinguishable on every retained one-L prototype input. One setting is fixed per episode so the demonstrations teach a stable rule.

**Rejected alternatives.** Color-conditioned corner remapping changes the semantic family and risks a color shortcut. Per-example parameter changes make the lesson inconsistent. Multi-L prototype inputs can allow settings to agree after corner unions, so the evidence sampler restricts itself to exactly one L.

**Status and limit.** Proposed prototype only. Passing 16 episodes and 64 rotations does not approve the new Racket program, broaden canonical authority, or establish adequacy on the full multi-object domain.

## D8 — acceptance interpretation

The final evidence supports routine acceptance of the task-local repair. It does not change catalog approval or training admission. The strongest remaining uncertainty is undeclared-rule identifiability, which is bounded but not eliminated by the retained census and generic-rival diagnostics.

## Current overlapping proposal

Unselected older-baseline alternative:current accepted277f63c0 already fixes query rotations with a period2 partial/complete schedule,strict integer guards,four distinct colors on complete default scenes,and an occupied/missing prototype. Proposed14f3c3a8 starts from195f4148 andcollides on generator,notes,tests,shortcut andprototype;it uses a different period4 cardinality schedule andelbow/missing prototype. Its118reported tests,12/12battery and300lessons/1200rotations qualify only the proposed bytes. Preserve exact source,evidence and partial367-file runtime-closure replay;the interrupted full replay is not a full pass. Rebase useful scalar/incompatibility changes without losing current profile/palette behavior before promotion. No current generator,prototype,authority orapproval modification. Retained at `workspace/proposals/review-d4bc3df4ac3b5abb/manifest.json`.
