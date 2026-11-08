# Working notes: 5ee8de1860a7

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.

## 2026-10-21 review: strict call contract and proposed border thickness

### Current intended rule and authority

A lawful input is a rectangular 3..15 grid with background 0 and exactly one
nonzero marker strictly inside the border. The canonical Racket rule reads the
marker color, paints the complete one-cell outer border that color, preserves
the input dimensions, and leaves every interior output cell zero. Version
`3.1.0` and rule hash `474fc5439247` remain authoritative; no Racket row,
canonical label, valid draw, schedule, or override behavior changed in this
review.

### Repair

The before battery was green in 11 stages and failed only strict scalar
validation: boolean seeds, boolean sample indices, and negative sample indices
were accepted. `_validate_call` now requires literal Python integers for `seed`
and `sample_index` and requires `sample_index >= 0` before `gen_ctx` is built.
Coercion and clamping were rejected because they would alias invalid requests to
valid deterministic keys. The inherited task-test fixture remains unchanged;
new regressions are isolated in `tests/test_strict_scalar_contract.py`.

Final generator SHA-256:
`e873b03d9c41089e03092de4ad9b4f9fc3eb1ed1e611578faf74ceeee972784c`.
The final resumed battery is 12/12 green in
`checks/after-final/checks/5ee8de1860a7_after_battery_summary.json`, and the
portable task suite passes 24/24. The final source-bound curriculum
census materialized 300 three-demonstration/one-query lessons (1,200 pairs, 697
unique inputs) and all 1,200 query rotations with zero reported ambiguity, hook,
materialization, or scoring findings against the declared rivals. Those are
finite checks, not universal identifiability.

### Proposed parametric extension

`workspace/parametric/` contains an unapproved task-local prototype with one
hidden episode parameter: `border_thickness` is 1 or 2. Thickness 1 instantiates
the canonical Racket source byte-for-byte; thickness 2 changes only the border
predicate. The input grammar, marker-color extraction, output dimensions, and
zero interior outside the selected border are preserved. Two four-pair episodes,
all eight leave-one-out query roles, and a separating witness were executed in
the protected Racket runtime; public challenges hide the parameter, source, and
query labels. Evidence is in
`checks/parametric/border-thickness-v1/report.json`.

This remains `status: prototype`, `approved: false`: it is not part of
`generate(...)`, does not change canonical authority, covers only the finite
setting set `{1,2}`, and currently allows a thickness-2 border to cover an entire
small output when the literal predicate implies that result.

### Open limits and decisions

The strongest declared shortcut is `canonical_profile_only`: it fits all five
canonical pairs and returns zero off the exact centered canonical profiles. A
default emitted witness at seed 17/sample index 1 is Racket-checked in
`checks/question/`; the existing schedule and the final census refute that rival
in every sampled lesson and query rotation. Undeclared rivals, untested seeds,
and semantic equivalence beyond exact grid hashes remain unknown. No training
approval is created by this review or by the prototype.

## 2026-10-05 review: arbitrary query rotations

### Baseline and lead

The retained July note `GNOTE-001382` was used only as a lead: it claimed that
the 3-in-10 canonical schedule and the other draws taught the intended rule in
ordinary ordered lessons. The pinned selected source was measured again rather
than trusting that prior claim. Its full before battery completed with 11 green
stages and one override advisory. A separate 100-lessons-per-band production
census with every query rotation found three teaching defects among 1,200
rotations:

1. one easy lesson left three centered demonstrations when the off-center pair
   was held out;
2. one easy lesson left three `(5, 7)` demonstrations when the `(7, 7)` pair was
   held out;
3. one medium lesson left three color-2 demonstrations when the color-3 pair
   was held out.

The old schedule varied each marginal in aggregate, but keyed random draws could
still collide three times inside one four-pair window. The override checker also
reported 14,040 intentional multi-axis rejections under legacy warning policy
because the incompatibility set was not declared structurally.

### Selected repair

Version 3.1.0 preserves the exact canonical rule and 30% anchor residues
`{0, 4, 8} mod 10`. Default non-anchor draws now use:

- a band-specific dimension cycle excluding all canonical dimension pairs;
- a four-color cycle `(4, 5, 7, 9)`, disjoint from canonical colors;
- an interior position cycle that excludes the geometric center.

Within four adjacent sample indices, general dimensions and colors are unique,
and at most two samples can be canonical anchors. Therefore no three-demo
rotation can support a different fixed-size, fixed-color, or center-only answer.
Exact overrides deliberately leave this schedule and retain the prior per-axis
behavior.

The module now publishes all 156 impossible linked pairs (`grid_h` with
`marker_row`, and `grid_w` with `marker_col`) in
`INCOMPATIBLE_OVERRIDE_COMBINATIONS`. This converts intended refusals from an
undeclared warning into strict machine-checkable override evidence.

### Regression evidence and limits

Task-local tests retain the three exact production-census reproducers and the
full finite override declaration. `workspace/check_rotation_windows.py` is a
reusable independent probe for all four query rotations. Its 64-seed,
201-window-per-seed-and-band run covered 38,592 overlapping windows, 154,368
rotations, and 5,973 unique inputs with zero findings.

That finite census establishes the documented schedule behavior over its tested
ranges, not universal ARC identifiability. It checks only the three named
competitors; undeclared hypotheses remain outside its claim. The reference
Racket rule was not changed.

### Strict semantic-contract follow-up

The first after battery retained all behavioral stages as green but rejected the
semantic stage because five predicates were unclassified weak witnesses. The
repair does not manufacture rival claims: `canonical_centered_profile` and
`marker_on_interior_ring` are now honest `BRANCH_WITNESSES`. The three
off-manifold predicates point to one executable `canonical_profile_only` rival,
which matches all five canonical labels and returns an incorrect zero output for
any lawful off-manifold input. It is exposed consistently through
`SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; the lesson
hook also reports it when diverse canonical demonstrations fail to teach a
noncanonical query.
## Current reviewer considerations

Source SHA-256: `e873b03d9c41089e03092de4ad9b4f9fc3eb1ed1e611578faf74ceeee972784c`.

# Review decisions for 5ee8de1860a7

## D1 — Preserve the canonical rule, version, and valid draw stream

**Choice.** Keep generator version `3.1.0`, canonical rule hash
`474fc5439247`, all valid default/override behavior, and the existing teaching
schedule. Change only validation of invalid `seed` and `sample_index` calls.

**Rationale.** The before battery showed 11 green stages; the sole failure was
strict scalar validation. Distribution, authority, semantic teaching, and
canonical support were already healthy. A version bump or schedule rewrite
would create needless replay churn for behavior that did not need repair.

**Alternatives rejected.** Coercing booleans/floats to integers, clamping a
negative sample index, or changing the generation schedule. Coercion hides caller
errors; clamping aliases distinct invalid requests; schedule changes would not
address the observed defect.

**Probe and limit.** The final generator SHA-256 is
`e873b03d9c41089e03092de4ad9b4f9fc3eb1ed1e611578faf74ceeee972784c`.
The final battery and source-bound solve confirm the same canonical authority.
This decision does not claim compatibility for invalid calls that were never a
supported API.

## D2 — Enforce literal integer call scalars at the public boundary

**Choice.** Reject `seed` unless `type(seed) is int`; reject `sample_index`
unless `type(sample_index) is int`; reject negative sample indices. Validation
runs before constructing `gen_ctx`.

**Rationale.** Python booleans are subclasses of `int`, so an `isinstance`
check would retain the bug. A nonnegative literal index is the contract used by
sampling, replay, and schedule reasoning.

**Evidence.** The red regression accepted `True`/`False` seeds and
`True`/`False`/`-1` indices (`checks/tdd-red-scalar/progress.log`). The focused
regressions now live in the new portable file
`repo/generators/5ee8de1860a7/tests/test_strict_scalar_contract.py`; the inherited
`test_generator_5ee8de1860a7.py` fixture was restored byte-for-byte. The final
portable task-test stage executes 24 tests.

**Failure mode.** This is intentionally stricter than permissive Python APIs;
callers passing NumPy integer scalars must convert them explicitly. That is
preferable to silently changing deterministic keys.

## D3 — Keep the parametric extension task-local and unapproved

**Choice.** Build a separate prototype with one episode-level parameter,
`border_thickness ∈ {1, 2}`. Thickness 1 is the exact canonical Racket program;
thickness 2 changes only the border predicate. Marker extraction, output color,
output dimensions, and the one-interior-marker input grammar stay unchanged.

**Rationale.** Border thickness changes the executed spatial transformation
while preserving the family's core reasoning. It is small enough for complete
finite rival checks. Parameterizing color would be mostly a reskin because the
input marker already supplies color; varying only size, position, or sampling
would not change the rule; arbitrary thickness would add unnecessary edge cases.

**Evidence.** `workspace/parametric/prototype.py` materializes both exact Racket
programs. `checks/parametric/border-thickness-v1/report.json` records canonical
program SHA-256
`0c7da94ef6eeddc6eb84caea41529a0e05df9a51633fea076201a8769d89deea`
and alternative SHA-256
`ce72fa9a6037ba97c24e2e2a6253bfe031d92c7689b4b48cbfaf766421e75e64`.
It retains two four-pair episodes, eight leave-one-out role rotations, and a
Racket-labeled separating witness. The public challenge copies omit hidden
parameters, Racket text, and query answers.

**Limit.** This is `status: prototype`, `approved: false`. Evidence covers one
medium episode per setting and the exact finite domain `{1,2}`; it is not a
production parametric API or a claim about arbitrary thickness. Small grids may
be completely covered by a thickness-2 border under the literal predicate.

## D4 — Require every query role to identify the episode parameter

**Choice.** Each prototype episode contains four pairs. For every one of the four
possible query positions, the remaining three demonstrations must leave exactly
the chosen thickness consistent and the two settings must disagree on the query.

**Rationale.** Selecting a hidden rule once per episode is meaningful only if the
demonstrations identify it before the query. Testing one fixed query slot would
allow accidental ordering dependence.

**Evidence and limit.** All eight rotations across the two retained episodes
pass in `checks/parametric/border-thickness-v1/report.json`. This is complete for
those two episodes, not a census over all seeds.

## D5 — Retain the existing three-demonstration/one-query curriculum policy

**Choice.** Preserve the production sampler and support holding out any of the
four materialized pairs as the query.

**Rationale.** The repair does not touch generated grids, so the earlier
rotation-safe teaching design should remain exact. Re-measure rather than infer
that from source similarity.

**Evidence.** The final census sampled 100 lessons per band: 300 lessons, 1,200
pairs, 697 exact unique inputs, and 1,200 query rotations. There were zero
materialization errors, ambiguities, hook warnings, or scoring errors in both
production and rotation views (`checks/lesson-census.summary.json`). The declared
`canonical_profile_only` rival fits all five canonical pairs and was refuted in
every sampled lesson.

**Limit.** This is a finite declared-rival census. Rotations reuse each sampled
four-pair bundle and do not enumerate every seed or every possible program.

## D6 — Use an emitted off-manifold case as the shortcut witness

**Choice.** Answer the assignment question with the executable
`canonical_profile_only` rival and a default, no-override witness generated by
`seed=17`, `sample_index=1`, `difficulty="easy"`.

**Rationale.** A generated witness is stronger than an artificial override: it
shows the curriculum actually contains cases that distinguish the shortcut.
The witness changes dimensions, color, and marker position relative to the
canonical profiles, while remaining accepted by `self_check`.

**Evidence.** `checks/question/shortcut-witness.json` contains the exact input,
rival output, predicates, and generator hash. `checks/question/racket.json`
contains the protected-Racket border output and matching rule hash.

## D7 — Preserve honest solve provenance

**Choice.** Keep the pre-repair blind solve separate from the exposed final
solve. The final solve declares earlier rule exposure `yes` and reference
consultation during solving `no`.

**Rationale.** The final generator work necessarily exposed the rule, so calling
the later solve blind would be false. Both solve records remain useful when bound
to their exact generator hashes.

**Evidence and limit.** The blind solve finished after two visible-only attempts;
the final solve finished after one and is bound to generator hash
`e873b03d9c41089e03092de4ad9b4f9fc3eb1ed1e611578faf74ceeee972784c`.
Neither receives masked-query correctness feedback in this packet.

## D8 — Leave audit targets unchanged and separate from repair acceptance

**Choice.** Record one clean finite audit for `af373b71d67d` and one reproduced
validator defect for `1282792eaad1`; do not patch either target.

**Rationale.** The assignment asks for adversarial evidence, not cross-task
repairs. Mixing audit changes into the selected-task delta would violate scope
and make source binding ambiguous.

**Evidence.** See `AUDIT.md` and `checks/audit/`. The clean finding is explicitly
finite; the defect finding states that its counterexample is outside the
documented lawful domain but incorrectly accepted by `self_check`.

## 2026-10-25 — native border-to-clockwise-corner family

The ordinary generator and canonical authority were rechecked and left unchanged.
The earlier task-local `border_thickness` experiment was replaced by the native
sequential family `finish_rule=border_only|clockwise_segment`; `border_only` is
the exact selected canonical Racket source. In `clockwise_segment`, stage A
replaces the marker with its colored outer border, the input-dependent
intermediate is the first newly created border cell hit by a marker-color-keyed
cardinal ray, and stage B traverses clockwise from that hit through the next
corner and recolors the segment color 8.

The sampler supplies matched inputs across settings, independent prefix-stable
2–6 demonstration and 1–4 query streams, all four hit sides, and a 30×30 fourth
query whose segment spans 29 cells in the retained witness. Two demonstrations
distinguish both settings and reject fixed-direction, counterclockwise,
whole-side, thick-border, and border-only shortcuts. The retained bounded audit
covers seeds 0 and 17, 12 count/setting episodes, 40 protected Racket labels,
and two skip-A counterfactuals. The packet-native authoring preflight passed four
jobs and 32 protected-Racket evaluations; the replayable witness proves that
omitting the created border removes the endpoint consumed by stage B. Public
projection produced 16 one-query views and passed 24 private-field invariance
checks plus four positive controls. Final adversarial review also reproduced and
fixed a totality defect: the alternate Racket rule previously used a zero-length
ray for the base task's legitimate color-8 marker and could loop forever. Color 8
now follows the left-ray branch in both Python and Racket, while generated scenes
still exclude it so the two settings remain distinguishable.

Status is reviewer-ready only. Exact-source owner review, native qualification,
acceptance, and any training admission remain separate downstream gates.
