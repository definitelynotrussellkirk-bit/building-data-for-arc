## Native parametric promotion (review-adf929d968f3fb1a)

A new `workspace/parametric` promotion path preserves the exact canonical
cardinal-neighbour rule as `mode=canonical` and adds
`mode=interior_count_relay`.  The alternate runs the canonical transform,
counts produced colour-2 interior cells on the controller side, and uses that
1–3 intermediate to select one of three payloads.  A raw-component-count
counterfactual changes the retained 30×30 result.  The source-bound task suite,
bounded shortcut audit, native qualification, public projection, and causal
witness are recorded in the current assignment checks.  The older threshold
prototype is retained only as historical evidence.

# Working notes: 70205357c60a

## Current account

The intended rule is unchanged: on a `0` background, recolor a `5` to `2` iff
all four in-bounds cardinal neighbours are `5`; preserve every other cell.  The
canonical normalized rule hash remains `24d0faa4acb9`, and the final generator
SHA-256 is `aa275438df6776e6e49b8f58dde1600e8fa2974fdc3257ac859375145a422475`.

## Repaired public-call contract

**Prior choice:** integer axes were delegated to `gen_ctx.draw_int`, so Python's
`int(...)` coercion silently accepted values such as `grid_h=9.75` and
`n_components=4.75`.  Invalid difficulty values, non-literal seed/index scalars,
and negative sample indices were also accepted by the task boundary.

**Current choice:** `generate` rejects non-literal `seed` and `sample_index`,
negative `sample_index`, difficulty outside `{None, easy, medium, hard}`, unknown
overrides, and non-literal values for the integer axes `grid_h`, `grid_w`, and
`n_components` before constructing `gen_ctx`.  This changes only invalid-call
handling: generator `VERSION` stays `3.0.0` so lawful seeded examples and the
training distribution are not perturbed.  Minimal counterexamples are retained
in `counterexamples/strict_scalar_contract.json`; focused coverage is in
`tests/test_strict_overrides_regression.py`.

## Authority decision

The selected `racket_target.target_code` was semantically/normalization-equivalent
but not byte-identical to the canonical authority.  Only that JSON pointer was
replaced with the exact canonical program (SHA-256
`99525ad6325994c076ffdf4c9285fce9d99329884a7d4a9e248ec76fffe3eb76`).
Archival `racket_target.raw_code` was deliberately left unchanged.  This is an
authority synchronization, not a rule change; all three canonical pairs replay.

## Teaching schedule and limits

Production lessons use three ordered demonstrations and one query.  The profile
cycle deliberately gives the demonstrations solid rectangles, single notches,
and deep notches, which jointly refute `solid_rectangle_only` and
`bbox_interior_fill`.  A 300-lesson census (100 per band) materialized 1,200
pairs and 961 unique inputs with zero production ambiguity or hook/scoring
errors.  All 1,200 query rotations also refuted every declared and searched
rival, but 600 rotations omitted one scheduled profile and therefore triggered
the profile-coverage hook.  Arbitrary rotation support is not claimed; the
ordered curriculum is retained.

The task-local prototype in `workspace/parametric/` varies one episode-level
parameter, `min_cardinal_neighbors` in `{4, 3}`.  Threshold `4` is exact
canonical; threshold `3` is proposed only.  Two complete Racket-labelled
episodes show every demonstration and query distinguishes the opposite setting.
No production API or training-admission change is proposed.

## Open limitation

The immutable inherited `tests/test_generator_70205357c60a.py` uses a fixed
`Path(__file__).parents[...]` canonical-data lookup and fails portable task-test
preflight.  It was restored byte-for-byte and not patched.  The maintainer owns
that fixture migration; the separate new tests pass in the authoring runtime.
Finite rival checks do not prove universal identifiability, and masked reviewer
solve labels remain intentionally unscored.
## Current reviewer considerations

Source SHA-256: `aa275438df6776e6e49b8f58dde1600e8fa2974fdc3257ac859375145a422475`.

# Decisions — 70205357c60a

## D1 — Reject malformed scalars at the selected generator boundary

**Prior choice.** Let `gen_ctx` coerce integer overrides and allow the public
entry point to accept whatever seed, sample index, and difficulty values made it
through downstream code.

**New choice.** Require exact Python `int` values (not `bool`) for `seed`,
`sample_index`, `grid_h`, `grid_w`, and `n_components`; require a non-negative
sample index; require difficulty in `{None, "easy", "medium", "hard"}`; reject
unknown overrides before constructing `gen_ctx`.

**Rationale.** `grid_h=9.75` and `n_components=4.75` were silently truncated,
so a malformed recipe could be recorded as one control while materializing
another.  Subsequent strict probes also found invalid difficulty and negative
sample-index acceptance.  Rejecting at the task boundary gives deterministic,
source-local failure messages and prevents mislabeled control metadata.

**Alternatives rejected.** Changing shared `gen_ctx.draw_int` would affect many
unassigned generators and could break callers that intentionally use its legacy
coercion.  Merely checking ranges after coercion would preserve the defect.
Normalizing bad values and recording the normalized metadata would still allow
invalid recipes into training.

**Probe/evidence.** `counterexamples/strict_scalar_contract.json`,
`tests/test_strict_overrides_regression.py`, baseline/intermediate
`defect_lint` logs, and `checks/focused-tests-final.xml`.

**Known edge.** Exact `type(x) is int` intentionally rejects NumPy integer
scalars and custom integer-like classes.  That is appropriate for the declared
JSON/public recipe contract, but a future API that explicitly promises such
objects should normalize them in one documented shared layer rather than
silently per generator.

## D2 — Keep generator `VERSION = "3.0.0"`

The change affects only invalid-call handling.  `VERSION` participates in
seeded generation, so incrementing it would unnecessarily perturb lawful
examples and the established distribution.  The final source hash records the
repair while lawful generation remains on the existing versioned stream.

## D3 — Synchronize only the selected executable authority pointer

**Choice.** Replace `/racket_target/target_code` with the exact canonical Racket
program and leave `raw_code` untouched.

**Rationale.** The selected code was semantically and normalization-equivalent
but failed byte-exact authority synchronization.  The canonical target is the
execution authority; `raw_code` is archival provenance.  Rewriting both would
erase useful history without changing behavior.

**Rejected alternative.** Treat normalization equivalence as sufficient.  That
would leave source hashes and replay receipts split across two textual programs
and keep the explicit authority gate red.

**Evidence.** `checks/authority-sync-proposal.json`, final authority stage in
`checks/after-final/`, canonical exact SHA `99525ad…fe3eb76`.

## D4 — Preserve the three-profile ordered production schedule

The current three demonstrations deliberately cover solid, single-notch, and
deep-notch scenes before the query.  Production census evidence is clean, and
both declared shortcuts are refuted in every measured lesson.  I rejected
random profile selection because it could omit a decisive notch witness, and I
rejected relaxing `lesson_identifiable` because that would hide a real teaching
coverage requirement.

## D5 — Treat rotation profile warnings as a documented limitation

Every one of 1,200 held-out rotations still refuted every declared and searched
rival, with zero ambiguity or scoring errors.  Two rotations per lesson omit one
of the scheduled profiles and therefore produce 600 hook warnings.  The
downstream production assembly is ordered, so I kept the production contract
and report arbitrary rotation support as unsupported rather than manufacturing
a pass.  A rescore requested with `--rotation-policy diagnostic` retained the
original `require` policy; that shared-tool issue is recorded as F3.

## D6 — Prototype one semantic parameter, separate from production

**Parameter.** `min_cardinal_neighbors ∈ {4, 3}`, chosen once from the episode
seed and held fixed over three demonstrations plus one query.

**Why this parameter.** It preserves the task's local cardinal-neighborhood
reasoning, palette, preservation branch, and per-cell structure while changing
observable boundary behavior.  Threshold 4 is exact canonical; threshold 3
adds non-corner boundary positives.

**Rejected alternatives.** Varying colors is mostly superficial and risks
teaching palette lookup rather than the rule.  Varying neighborhood topology
(e.g. diagonal or 8-neighbor) changes the reasoning family more sharply.
Per-example threshold changes would make the episode internally inconsistent.

**Evidence/limits.** `workspace/parametric/README.md`, `prototype.py`, focused
prototype tests, and `checks/parametric/neighbor-threshold-gallery-final/`.
This remains a proposed finite prototype, not a production or approval change.

## D7 — Do not patch the frozen inherited fixture

The packet explicitly marks `test_generator_70205357c60a.py` immutable.  An
early exploratory edit was discarded, and the file was restored to baseline
SHA `8ea4a348d5232d14b8141dd4beceb462aba2467af7d2642b5c1c530dacb891d1`.
New tests live in separate files.  Because the frozen test's fixed-depth path
fails portable preflight, completion is reported `blocked` rather than falsely
claiming an aggregate task-test pass.

## D8 — Keep audits read-only and source-bound

The two randomly assigned audit targets were not modified.  I ran their task
tests, used the public defect lint where practical, and built
`checks/audit/strict_scalar_probe.py` to record exact accepted/rejected calls,
self-check results, grid hashes, and selected source hashes.  Audit findings are
reported as findings only, not approvals or repairs.
