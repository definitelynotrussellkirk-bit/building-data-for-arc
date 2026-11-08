# Working notes: 9ff30d18e156

## Review review-0c3255d49c88983e

Version 2.0.0 keeps Racket hash `efbc8aee85e7` unchanged. Four actual axes replace
placebo metadata. Default profiles cover clean endpoints, >=3 same-color hits,
two disjoint same-row color spans, and their combination. All colors 1..9,
short gaps, borders, and singleton distractors are supported. n_pairs means
exact productive rows; it is not total colors or endpoint count. Obsolete keys
and malformed overrides now raise ValueError.

Defaults anchor canonical geometry; explicit h=3..10/w=8..14 remain valid in all
bands. Overlapping repeated-color spans remain excluded: the demonstrations do
not teach collision order. Self-check is a broader-domain validator, not exact
sampler membership. Identity/invalid fixtures are separate from generation.

Evidence in the returned checks/probe-final summary measures 480 draws per
source: 240/240 overlapping three-demo windows refute both named rivals after
repair versus 0/240 before. This is finite-rival evidence, not a universal
identifiability or trained-model-performance claim. Final battery is 12/12
passing, and 34 focused tests pass. The full repository suite has 169 passes
and one startup-sensitive timeout failure, diagnosed but not patched.

Read workspace/HANDOFF.md before extending this review. Keep canonical labels
and the Racket authority separate from any fresh Python solve episode.
## Current reviewer considerations

Source SHA-256: `b1f2c9d0e06f5aa88208443adc11b990d27d9ea2c4b8b9ae86f15b957ec5a323`.

# Decisions and rejected alternatives

## Scope / authority

The immutable assignment is `review-0c3255d49c88983e`, selected task
`9ff30d18e156`. No reroll, shared-code edit, canonical-row edit, archival rule
edit, audit-target edit, or approval change was made. Original design rationale
beyond the source docstrings is unknown; associated notes were empty. The
packet is an extracted snapshot, not a Git checkout (`git status` reported
"not a git repository"). Frozen baseline hashes and packet manifests are used
for comparison instead.

## G1: Geometry and canonical anchors

Original defaults were h=4..6, w=10..12; documented h=3..10 and w=8..14 were
not actually honored. Canonical heights are 7..9 and widths 10..13, with an
actual one-cell gap. The revised public bounds remain h=3..10 and w=8..14,
while default dimensions are easy 7..8 by 10..11, medium/unspecified 7..9 by
10..13, and hard 8..9 by 12..13. All legal explicit dimensions work in every
band. Larger hard defaults are a geometric convenience, **not** evidence of
psychometric difficulty.

The first revision drew all sizes uniformly and treated difficulty as inert.
It passed 32 local tests but failed dead-band and per-band canonical-profile
checks. Those failures are preserved in `checks/after/`. Restricting all
public bounds to canonical sizes would sacrifice useful small/boundary
experiments. Instead, only defaults are anchored; explicit bounds stay broad.
Clean endpoint rows are separated by a blank row when dimensions permit,
constructed without retries. Small explicit heights deliberately permit
adjacent rows, which remain lawful under the row-local rule.

## G2: Honest controls and constructive placement

`n_pairs` is retained as a legacy name for **productive rows**, exact in 1..5,
with default 3. Values exceeding explicit `grid_h` raise a structured
`IncompatibleOverrides` carrying both axis names. The old capped retry loop
could silently miss requested structure; sampling rows directly removes that
failure mode. The old count override was ignored entirely.

The declared axes are now `grid_h`, `grid_w`, `n_pairs`, and `texture`.
`observe_overrides` recovers all four from the realized grid. Old placebo knobs
(`palette_kind`, `palette_size`, `n_distinct_colors`, `position_bias`, `density`)
and old palette-alias texture names now raise a clear error instead of
pretending to work. This is an intentional API compatibility break, documented
by version 2.0.0. Retaining no-op aliases would perpetuate false provenance;
implementing five overlapping knobs would expand complexity without adding
independent information. Non-integer dimensions, booleans, out-of-range
values, unknown keys, and unknown textures are rejected explicitly.

## G3: Distinguishing the intended row/color operation

The four default profiles cycle by `sample_index`:

- `endpoints`: one clean two-hit color per productive row; canonical anchor.
- `mixed`: two disjoint color spans, at least three hits of one color.
- `multihit`: one color with at least three hits and a guaranteed hole.
- `multicolor`: two disjoint two-hit color spans.

The cycle is fixed and documented, not chosen using held-out answers. Every
three consecutive default examples include evidence against both declared
rivals, regardless of start offset. Explicit single-profile overrides make
no such lesson guarantee. Curriculum coverage does not imply universal
identifiability, and a consumer shuffling individual examples loses the
consecutive-window guarantee. Every four start offsets were tested.

Color choice covers 1..9 rather than excluding 1. Primary colors are distinct
across active rows; secondary colors can repeat. Random horizontal reflection,
variable span lengths, variable padding, interior hits, and border-touching
placements remove unnecessary absolute-position dependencies. Non-endpoint
profiles may contain singleton colors outside intervals and in otherwise
inactive rows. These must survive without inducing a new fill. Endpoint
profiles stay free of distractors for canonical support.

Repeated colors have disjoint intervals. The Racket authority has an order
for overlapping-color writes, but the demonstrations do not teach that order.
Adding crossing/nested spans would conflate row completion with an extra
collision-priority task. Such inputs are deliberately excluded and rejected
by this generator's validator. The authority itself was not changed.

## Validator / diagnostic choices

Validation accepts the broader lawful domain, including small hand-built
witnesses and singleton distractors; it is not an exact sampler-membership
oracle. It checks rectangularity, integer/color bounds, interval conflicts,
and at least one productive span. It safely rejects malformed grids instead
of raising an indexing exception. One active row and one-cell gaps are valid;
an arbitrary two-active-row minimum is not part of the reference operation.

Identity scenes (`no_pairs`, mismatched endpoints, filled spans) are retained
as `mutation_fixtures()`, not public texture modes. This preserves negative
test material without silently producing rejected training samples. No rule
mirror supplies production labels. Diagnostic rivals live in the generator
for the existing semantic gate; an independent comparator exists only in the
probe and was compared against real Racket outputs.

## Evidence interpretation / stopping point

The 480-draw final census has 439 unique inputs; the baseline has 411. The
240 lesson windows per version overlap, and each conclusion is restricted
to the two named rivals. Canonical parity is 5/5; no model was trained.
The final generator battery and task-local tests pass. An unrelated repository
streaming test remains red because child startup exceeds its deadline here;
shared files were not changed to clear that test. Its exact reproducible
startup probe is included. Audits are findings only and are not folded into
the assigned generator's patch.

The fresh solve is a separate, exposure-declared exercise. Preparation/check
are allowed to use private authority internally; the reviewer reads only the
visible challenge and own Python code once that phase begins. Query correctness
is withheld, not claimed. See `solve/SOLVE_NOTES.md` for the actual solve log.
