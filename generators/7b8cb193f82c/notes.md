# Working notes: 7b8cb193f82c

## Current rule and calibrated domain

The selected authority is unchanged. Each complete rectangular color-8 annulus
encloses a rectangular zero hole. Hole cells are colored by inward 4-neighbor
depth: depth 1 is 2, depth 2 is 3, then 2/3 alternate. Ordinary generation is
restricted to 1–3 disjoint rectangular annuli, common scene thickness 1 or 2,
canvas 9–24 by 10–24, and maximum depth 1–5. Irregular enclosures, open frames,
solid blocks, and unsupported palettes remain outside the calibrated teaching
grammar even though the Racket program may execute some of them.

Prior return `local-random-2868c1b5beed` was used as a lead for the existing
five-profile schedule, depth-five shortcut witness, rectangular-annulus scope,
and authority pin. Those claims were remeasured on the pinned source rather
than accepted as current evidence.

## R-7B8C-STRICT-SCALARS-1 — repaired public call contract

The before battery had 11/12 green stages. `defect_lint` alone failed because
`generate` accepted 33 invalid scalar calls across easy/default/hard: bool,
float, and string seeds; bool, float, and string sample indices; and negative
sample indices. `schedule_profile` had the same coercion behavior but was not
covered by the shared defect probe.

The repair adds one exact public-scalar validator used by both `generate` and
`schedule_profile`: `seed` and `sample_index` must have exact type `int`, bool is
rejected, and `sample_index` must be nonnegative. The internal `int(...)`
coercions were removed. Valid-call sampling, the five-profile schedule, Racket
text, `RULE_HASH`, and `VERSION` are unchanged. `VERSION` intentionally remains
`3.0.0` because this is an invalid-input contract repair; changing it would
needlessly perturb every valid deterministic draw.

Regression coverage is in `tests/test_strict_call_validation.py`; the compact
reproducer is `counterexamples/strict_public_scalars.json`. The focused tests
were observed red before the fix and the final portable task-test run is 39/39
green. The final battery is 12/12 green; generator SHA-256 is
`635443e704565b189ac31fb4688b3d07668591da4e44fc52d1d256b3831f7f5f`.

## Teaching evidence and ordering limit

The production schedule remains period five: a combined three-frame,
thickness-2, depth-1 control followed by depth 2, 3, 4, and 5 witnesses. Five
ordered demonstrations therefore refute identity, all-red, two-ring,
depth-four-cap, and largest-frame-only rivals. Final profile-floor support was
37/60 exact and 37/60 envelope, with at least one exact hit in each band.

The 100-lessons-per-band census materialized 300/300 production lessons (1,800
pairs; 554 unique inputs) with zero production ambiguity or hook warnings
against the declared rivals. Arbitrary query rotation is **not** supported:
476/1,800 rotated holdouts leave the depth-four-cap rival alive, and 1,200/1,800
rotations omit at least one scheduled depth. This is an ordered-curriculum
limitation, not hidden by the production pass. A downstream exporter must retain
the generated train/query order or run an explicit rotation gate and resample.
Finite declared-rival checks do not prove universal identifiability.

## Proposed parametric extension (not production)

`workspace/parametric/` contains an isolated `outer_color` prototype with allowed
values `{2, 3}` and canonical default 2. The setting is selected once per episode.
Value 2 returns the exact canonical Racket text; value 3 changes only the single
alternating-color expression to start at 3. Two retained Racket-executed episodes
(seeds 731 and 733) cover both settings. All three demonstrations in each episode
refute the other setting and the masked query differs. This prototype does not
change canonical generation, authority, approval, or `RULE_HASH`.

## Remaining limits

- Production teaching is ordered; arbitrary query holdout is unsupported as measured above.
- The semantic contract covers five named rivals, not every rule compatible with finite examples.
- The grammar intentionally excludes irregular color-8 arrangements.
- The proposed color-phase parameter is easy to identify from any nonempty demonstration and is evidence of interface correctness, not a difficult latent-rule benchmark.
## Current reviewer considerations

Source SHA-256: `635443e704565b189ac31fb4688b3d07668591da4e44fc52d1d256b3831f7f5f`.

# Decisions — 7b8cb193f82c

## D1 / R-7B8C-STRICT-SCALARS-1 — reject coercible public scalars

**Choice.** Require exact Python `int` values for `seed` and `sample_index`, reject
`bool`, reject float/string coercions, and reject negative sample indices. Apply
the same contract to `generate` and `schedule_profile`.

**Original rationale.** Unknown. The pinned source converted `sample_index` with
`int(...)` and passed seeds through to `gen_ctx`; this made convenient coercion
possible but erased distinctions between invalid API calls. The before defect
lint reproduced 33 accepted-invalid-scalar warnings across three difficulties.

**Alternatives considered.** Keep permissive coercion; validate only `generate`;
normalize all values in `gen_ctx`; accept negative indices as cyclic schedule
positions.

**Probe and evidence.** `tests/test_strict_call_validation.py` was run before the
repair and failed on every newly asserted rejection, then passed afterward.
`checks/before/checks/7b8cb193f82c_before_defect_lint.log` records the shared
probe; `counterexamples/strict_public_scalars.json` is the compact reproducer;
`checks/final-task-tests/checks/task_tests.xml` is the final portable run.

**Why selected.** Exact types make deterministic identities unambiguous and match
the strict public-call contract already enforced by the review battery. Applying
the helper to both entry points prevents the schedule API from silently diverging
from generation.

**Failure modes / limits.** This rejects integer-like NumPy scalars and custom
`__int__` objects. That is intentional at this public boundary; callers must
convert explicitly. Extremely large nonnegative integers remain legal and are
not range-limited by this repair.

## D2 — preserve valid generation bytes, schedule semantics, and authority

**Choice.** Do not alter the five-profile input distribution, Racket program,
`RULE_HASH`, or `VERSION`. Remove only invalid-input coercion.

**Original rationale.** Prior return `local-random-2868c1b5beed` established a
five-example curriculum with a depth-five witness and exact authority pin. The
current before battery independently showed all non-defect-lint stages green,
including profile floor, semantic gate, overrides, rule smoke, and authority
sync.

**Alternatives considered.** Bump `VERSION`; redesign the schedule; modify the
Racket rule; broaden to irregular enclosures; add a schedule-period declaration.

**Probe and evidence.** Before and after aggregate reports are
`checks/before/checks/7b8cb193f82c_before_battery_summary.json` and
`checks/after/checks/7b8cb193f82c_after_battery_summary.json`. Final authority
source SHA-256 remains
`1e2425379d5d08e4b3b618bb1d98883c8c582cacec276711cccf829c2a256767`.

**Why selected.** The failure was solely at the invalid-call boundary. A version
bump would change every valid deterministic draw without improving training
content, and a rule edit would add unnecessary authority risk.

**Failure modes / limits.** The five-profile curriculum remains intentionally
ordered and does not support arbitrary query rotation. No new schedule-period
metadata was added after the post-repair solve because any generator-byte change
would invalidate that solve record.

## D3 — add task-local regression tests rather than edit the frozen fixture

**Choice.** Add `tests/test_strict_call_validation.py` and
`tests/test_parametric_outer_color_prototype.py`; leave the baseline
`test_generator_7b8cb193f82c.py` untouched.

**Original rationale.** Packet policy marks the baseline fixture frozen. The
shared defect linter covered `generate` but not `schedule_profile`, and no test
covered an isolated parametric extension.

**Alternatives considered.** Patch the frozen test; rely only on defect lint;
place checks in a workspace script without portable task-test discovery.

**Probe and evidence.** The strict test had 27 expected failures after adding the
full entry-point coverage and before implementation. The prototype test had six
expected setup errors before its source existed. Final portable task tests are
39/39 green in `checks/final-task-tests/`.

**Why selected.** New tests travel with the task patch, replay in the staged
runtime, and make the omitted schedule contract explicit without weakening
inherited checks.

**Failure modes / limits.** Task tests are a focused suite, not a substitute for
the full battery. The inherited fixture emits a legacy-runtime-namespace warning
but passes and was not rewritten.

## D4 — keep the rectangular-annulus grammar

**Choice.** Retain the existing axes and input manifold: 1–3 disjoint complete
rectangular color-8 annuli, common thickness 1 or 2, and demonstrated depth 1–5.

**Original rationale.** The canonical rule can execute broader shapes, but the
examples support a rectangular enclosure interpretation. The prior note
`GNOTE-003763` explicitly treats irregular arrangements as unsupported negative
recombinations.

**Alternatives considered.** Emit arbitrary closed color-8 components; add open
frames; mix frame thicknesses in one scene; use nonzero backgrounds or alternate
frame colors.

**Probe and evidence.** Final self-check, strict profile, override, grammar,
semantic, and rule-smoke stages are green in `checks/after/`. Profile floor is
37/60 exact and 37/60 envelope.

**Why selected.** No measured defect implicated the data distribution. Broadening
would introduce new object-discovery hypotheses without canonical-backed rivals
or mutation tests.

**Failure modes / limits.** Model competence on this generator does not imply
competence on irregular enclosures or mixed-thickness scenes. The domain is a
calibrated teaching family, not the full executable Racket language.

## D5 — report ordered-production success separately from rotation failure

**Choice.** Keep the production schedule because 300/300 ordered lessons are
unambiguous against declared rivals, but explicitly mark arbitrary query
rotation unsupported: 476/1,800 ambiguous rotated holdouts and 1,200/1,800
rotation hook warnings.

**Original rationale.** The period-five schedule guarantees that each five
consecutive demonstrations contains depths 1–5. A sixth pair repeats the first
residue; holding out an arbitrary member can remove the only depth-five witness
or another required depth.

**Alternatives considered.** Claim the production pass as universal; weaken the
depth-four-cap rival; add deeper content to every profile; redesign lesson
assembly around more demonstrations; suppress rotation diagnostics.

**Probe and evidence.** `checks/lesson-census.summary.json` is the 100-per-band,
query-rotation census. Its production verdict is `no_ambiguity_found`; its
rotation verdict is `ambiguous`.

**Why selected.** The generated exporter uses an ordered five-demo plus one-query
policy, so production data is teachable as emitted. The rotation result remains
important for any downstream shuffle or alternate holdout policy and must not be
collapsed into the production verdict.

**Failure modes / limits.** The random census does not exhaust every seed or every
possible rule. The generator also lacks a declared `LESSON_SCHEDULE_PERIOD`, so
this return did not run the tool's period-enumeration mode. Existing task tests
cover cyclic five-example starts at the generator level.

## D6 — propose `outer_color` as an isolated rule parameter

**Choice.** Build a task-local prototype with `outer_color ∈ {2,3}`. Canonical
default 2 produces depth colors `2,3,2,3,…`; alternative 3 produces
`3,2,3,2,…`. Select once per episode and use the same exact Racket program for
all demonstrations and the query.

**Original rationale.** The starting color is a small bounded semantic parameter
that changes the transformation while preserving the core inward-layer reasoning.
It has one unambiguous edit point in the canonical Racket source.

**Alternatives considered.** Parameterize frame color; parameterize thickness or
max depth (input distribution only, not rule semantics); add a third output
color; reverse depth direction; vary colors independently per frame.

**Probe and evidence.** Source and README are under
`generators/7b8cb193f82c/workspace/parametric/`. Racket-executed evidence is in
`checks/parametric/outer-color-v1/`: seed 731 selects 2, seed 733 selects 3,
every one of three demonstrations refutes the rival, and each query differs.
Focused prototype tests are part of the final 39/39 task-test pass.

**Why selected.** It is minimal, exact, easy to audit, and preserves the original
setting byte-for-byte. It demonstrates the requested episode-level parameter
interface without touching production authority.

**Failure modes / limits.** Any nonempty labeled demonstration directly reveals
the setting, so this is not a hard latent-rule task. Evidence covers two seeds and
one declared parameter rival. The extension is **proposed prototype** only and is
not approved production behavior.

## D7 — optional ARC composition annotation left conservative

**Choice.** Do not claim broad multi-rule or sequential composition coverage.
The frame cue plausibly constitutes contextual gating, but this return leaves
machine curriculum axes unreported rather than manufacturing a new certified
witness after the repair.

**Alternatives considered.** Mark `contextual_gating=present` from prose alone;
mark all other axes not applicable; invent a composed rule variant.

**Why selected.** The task is a single gated fill operation. Optional annotations
should be source-bound to a retained witness and rival, and they are not needed
to complete the repair.
