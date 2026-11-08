# Current notes: `08f1d9bdd2ef`

## Intended rule and authority

Two complete cyan rows and two complete cyan columns partition a black input
into a 3×3 zone grid. Preserve the dividers and corners; fill top-middle red 2,
middle-left yellow 4, center magenta 6, middle-right green 3, and bottom-middle
blue 1. The selected Racket authority is unchanged at `RULE_HASH = 99b51630ed1d`.

Final generator SHA-256:
`59191c7937096e5736f246ec65d62df4fa5ac49ea01d938b79d161a20493e9d0`.
Baseline lead: the packet's pinned source and before battery at
`checks/before/`; no unintegrated prior return was treated as measurement.

## Current decisions

- `seed` and `sample_index` must be exact Python integers; booleans, floats, and
  strings are rejected. `sample_index` must be nonnegative; negative seeds remain
  legal.
- `schedule_profile` uses one `canonical_scale` coordinate per four and `broad`
  otherwise. Exact candidates preserve the lawful divider grammar and selected
  public/generalized family.
- `schedule_scene_family` has period 4 with one public and three generalized
  scenes, phase-shifted by seed. This guarantees generalized evidence in every
  three-demo holdout of a four-pair lesson while preserving the prior 25% public
  rate.
- Explicit `scene_family` overrides remain supported and are consumed through
  `gen_ctx`.
- The declared rival `public_style_only` applies the correct transformation only
  to public-style layouts. `generalized_style` is its witness, and
  `lesson_identifiable` requires demonstrations to refute it.

## Evidence

The final 12-stage battery is all green. Profile support is 12/60 exact and
19/60 envelope, with four exact hits in each band. The final source-bound census
materialized 300 three-demo-plus-one-query lessons and checked all 1,200 query
rotations with zero declared-rival ambiguity. The intermediate failure before
the family schedule (2/300 lessons and 9/1,200 rotations ambiguous) is retained.
See `REVIEW.md`, `DECISIONS.md`, `checks/lesson-census.summary.json`, and
`checks/LARGE-EVIDENCE-MANIFEST.json`.

Focused reviewer tests: 12 pass. The inherited root fixture is frozen and still
uses a nonportable fixed-depth canonical path; portable task-test preflight is
therefore an open maintainer-owned blocker, not a repaired-test failure.

## Parametric proposal

`workspace/parametric/` contains a separate, unapproved episode-level
`arm_rotation` prototype with settings 0–3 and canonical default 0. All four
instantiated Racket programs match the Python mirror; three demonstrations
refute every alternative setting. Its verifier reuses one Racket session for the
full program/episode matrix, with a regression test binding that bounded execution
path. It is not a production axis and does not change canonical authority.

## Known limits and open findings

- Finite declared-rival tests do not prove universal induction.
- The period-4 guarantee assumes the exported lesson uses four consecutive
  sample indices with three demonstrations and one query.
- The parametric verifier covers four cyclic color rotations only.
- Maintainer action remains required to migrate the frozen fixture to portable
  `reviewer_support` path helpers.
## Current reviewer considerations

Source SHA-256: `59191c7937096e5736f246ec65d62df4fa5ac49ea01d938b79d161a20493e9d0`.

# Decisions for `08f1d9bdd2ef`

## D1 — preserve the selected canonical rule

**Choice.** Keep the Racket authority and `RULE_HASH = 99b51630ed1d`
unchanged.

**Rationale.** The rule correctly identifies two full cyan rows and columns and
fills the five central-cross zones by position. Baseline failures were in input
validation, distribution support, and lesson teaching—not output semantics.

**Alternatives rejected.** Rewriting the Racket rule would add authority risk
without addressing a reproduced rule error. The parametric color rotation is
therefore separate and unapproved.

## D2 — require exact integer coordinates

**Choice.** Accept `seed` only when `type(seed) is int`; accept
`sample_index` only when `type(sample_index) is int` and it is nonnegative.

**Rationale.** The old `int(...)` coercions silently accepted booleans, floats,
and numeric strings, collapsing distinct caller mistakes onto valid coordinates.
The checker's 33 warnings reproduced this in easy/default/hard probes.

**Alternative rejected.** `isinstance(value, int)` would still accept booleans.
Coercion was rejected because the public generation contract should fail loudly.
Negative seeds remain legal; negative sample indices do not.

## D3 — add a production-shaped canonical-scale schedule

**Choice.** Select an exact canonical canvas scale at one quarter of deterministic
coordinates and the broad space at the other three quarters.

**Rationale.** This gives repeatable exact-profile support in every difficulty
band while retaining most broad-lawful draws. Candidate construction is derived
from the canonical dimensions and the same public/generalized style relation;
it is not a hard-coded checker seed list.

**Alternatives rejected.** Expanding every draw toward canonical dimensions
would narrow diversity. Adding a private test-only override would satisfy a gate
without repairing production support. Sampling exact scales randomly offered no
per-band floor guarantee.

**Limit.** The fixed one-quarter fraction is a curriculum choice, not an
empirically optimized probability.

## D4 — name the strongest plausible canonical shortcut

**Choice.** Declare `public_style_only`: transform public-style layouts correctly
and leave generalized layouts unchanged. Use a generalized-style witness and
require demonstrations to refute it.

**Rationale.** All canonical demonstrations have public-style divider-band
ordering, so this rival fits them exactly while disagreeing on lawful generalized
inputs already advertised by the generator. It is executable, source-bound, and
cheap to test.

**Alternatives rejected.** A prose-only shortcut cannot be checked by the
semantic battery. A weaker identity rival is trivially refuted by every labeled
pair and does not probe whether generalized scenes are actually taught.

**Limit.** Passing this rival does not rule out undeclared shortcuts.

## D5 — make scene-family selection a four-step lesson schedule

**Choice.** Use a seed-phased period-4 schedule
`public, generalized, generalized, generalized`, while preserving explicit
`scene_family` overrides through `gen_ctx`.

**Rationale.** The intermediate 300-lesson census found 2/300 ordered lessons
and 9/1,200 query rotations where independent family draws left
`public_style_only` alive. A four-pair lesson contains one public and three
generalized examples, so every three-demo holdout contains generalized evidence.
The long-run public rate remains 25%, matching the prior weighted choice.

**Alternatives rejected.** Removing the rival would hide the defect. Resampling
only failed lessons would make acceptance history-dependent and harder to replay.
Forcing all scenes generalized would erase the public anchor. A longer schedule
adds complexity without improving the four-pair teaching guarantee.

**Limit.** The proof covers the declared four-pair assembly; other assemblers
must inspect their own windows.

## D6 — keep the canonical-scale and family schedules independent

**Choice.** Derive both from validated seed/sample coordinates but use separate
selection logic; family guarantees teaching composition, profile guarantees
shape support.

**Rationale.** Combining them into one lookup table would couple two independent
curriculum goals and make overrides harder to reason about. Final semantic
sampling observed both profile classes (`canonical_scale` 139/600, `broad`
461/600) and the generalized witness fired 464/600 times.

## D7 — prototype `arm_rotation`, not a production axis

**Choice.** Build a task-local episode-level parameter with four clockwise
rotations and canonical default 0 under `workspace/parametric/`.

**Rationale.** It preserves the original object roles and cross-zone reasoning,
changes only the inferred arm-color assignment, and is distinguishable from any
single labeled demonstration because all four arm zones are nonempty and use
distinct colors.

**Alternatives rejected.** Varying divider count or center/corner behavior would
change the core rule. Per-example parameter selection would make demonstrations
incoherent. An arbitrary permutation space was unnecessary for this first
prototype.

**Implementation note.** The first verifier executed each program/episode pair
through a separate Racket process. A fresh rerun showed that startup pattern could
outlive the review wrapper despite correct completed evidence. A failing regression
test was added first, then the verifier was changed to reuse one offline Racket
session for the full matrix. The optimized rerun completed with identical exact
comparisons.

**Limit.** The verifier establishes four finite settings only; no variant or
training approval is implied.

## D8 — do not patch the inherited frozen fixture

**Choice.** Preserve `tests/test_generator_08f1d9bdd2ef.py` byte-for-byte and
report the portable preflight blocker.

**Rationale.** The assignment names the baseline root fixture as frozen and says
maintainers own migration when its portable preflight fails. Its fixed
`__file__.parents[...]` path is unrelated to the repaired production behavior.

**Alternative rejected.** Editing or deleting the fixture to obtain a green
portable stage would violate the assignment and conceal an infrastructure
migration requirement. Reviewer-owned tests instead use portable support
helpers and pass directly.

## 2026-10-25 native parametric promotion: arm-area ranking

This review retained the earlier unapproved `arm_rotation` prototype as
historical authoring work but promoted a different native two-setting family.
`arm_assignment=compass` is byte-for-byte the selected canonical Racket
program. `arm_assignment=area_ranked` detects the divider geometry, computes
the four arm areas, ranks the directions by descending area, and then consumes
that input-derived ranking to assign colors 2, 3, 1, and 4. Authored scenes have
four distinct areas and never use canonical compass order, so the dependency is
non-collapsing. The adapter supports 2–6 demonstrations, exactly four distinct
private queries, matched inputs across settings, and a substantive 30×30 query.

The bounded self-review used fixed compass assignment as the cheap bypass. It
is refuted by every area-ranked demonstration and query, while area rankings
vary across ordinary generated scenes. Native qualification covered both
settings at seeds 0 and 17 with three demonstrations and four queries (40
protected-Racket evaluations). A four-case protected wrong-intermediate replay,
including the 30×30 query, changed the final labels exactly as expected.
Single-query projection and first-turn private-field invariance also passed.

The current packet's portable-test contract supersedes the prior D8 decision to
leave fixed-depth fixtures untouched. Tests now use `reviewer_support` to bind
the selected generator and the copied task home explicitly. Two stale
pre-schedule distribution assertions were replaced by checks of the documented
period-4 curriculum and the declared generalized candidate space. The copied
task runtime passes 65 tests; one repository-wide divergence-ledger check is
explicitly skipped because those global inventories are not included in the
isolated task bundle.

Evidence is under `checks/08f1d9bdd2ef/qualification-v1/`,
`checks/08f1d9bdd2ef/causal-v1/`, and
`checks/08f1d9bdd2ef/first-turn-v1.json`. This is reviewer-ready source, not
owner acceptance or training admission; finite rival checks do not prove unique
induction.
