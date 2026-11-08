# Working notes: 71b44cea4ed1

## Current contract

The input is a rectangular 7–16 grid on background 0.  A rule application is an
equal, nonzero endpoint pair at displacement `(2, 2)` or `(2, -2)` whose
midpoint is zero.  The canonical output copies the endpoint color into every
such blank midpoint.  The selected Racket authority was not changed; the Python
generator is pinned to `RULE_HASH = "814976eb9ffc"`.

Version 3.0.0 exposes only three exact, recoverable axes: `grid_h` (7..16),
`grid_w` (7..16), and `pair_count` (2..3).  Calls require literal integer seeds,
nonnegative literal integer sample indices, one of the four supported difficulty
values, known override names, and literal integer override values.

## Distribution and lesson design

Every generated input has two or three active pairs in distinct colors and
contains both diagonal orientations.  The four-slot schedule is:

1. exact canonical profile, with three pairs and no decoys;
2. axis-aligned plus wrong-distance and different-color near misses;
3. wrong-distance and different-color plus blocked-midpoint near misses;
4. blocked-midpoint plus axis-aligned near misses.

Three demonstrations are required.  Any three of four consecutive slots retain
all four near-miss families, while every individual scene refutes the identity
and one-orientation-only rules.  Canonical anchors cycle deterministically
through `(7,7,4)`, `(8,8,4)`, and `(9,9,4)` height/width/palette profiles.  An
explicit axis override disables the canonical anchor but remains exact and fully
constructive.

`self_check` accepts this task-local grammar rather than any grid on which the
rule happens to fire.  It rejects blank or one-pair scenes, missing orientation
coverage, repeated active colors, ambiguous midpoint ownership, arbitrary
singletons, arbitrary repeated colors, invalid colors, and unsupported local
roles.  `strict_canonical_like` narrows this to the three exact canonical
profiles with exactly six active endpoints and no decoys.

## Semantic evidence

The declared witnesses cover both diagonal orientations and four near misses:
axis-aligned, wrong-distance, different-color, and occupied midpoint.  Declared
rivals cover copying unchanged, either one-orientation rule, axis-aligned fills,
longer diagonal spans, color-blind fills, and overwriting blocked midpoints.
`lesson_identifiable` checks the actual demonstrations against those rivals.

Final generator SHA-256:
`0d4d4600d98170c18b3e0c86be72c239ee4f406a657f4befa036fb990f6900fb`.
The strict after battery passed all 12 stages.  It measured exact/envelope
canonical-profile support at 15/60, strict support at 151/600, all 6/6 witnesses
firing, all 6/6 rival claims verified, 12/12 smoke lessons identifiable, and
0/48 ambiguous smoke rotations.  A larger source-bound census materialized 300
lessons (100 per band), 1,200 unique inputs/query rotations, and found zero
ambiguities or scoring/materialization errors against the declared rivals.

## Regression fixtures

- `counterexamples/ambiguous_midpoint.json` gives two colors ownership of the
  same blank midpoint and must be rejected.
- `counterexamples/unrecognized_repeated_color.json` adds an unsupported
  repeated color to an otherwise lawful two-pair scene and must be rejected.
- `tests/test_generator.py` also binds all canonical pairs, exact override
  boundaries, scalar validation, schedule rotations, deterministic replay,
  global-RNG purity, canonical-anchor profiles, and executable semantic hooks.

## Reversed baseline decisions

The imported 2.0.1 generator advertised nine axes, including inert aliases and
negative textures, accepted unknown/ill-typed controls, used difficulty-specific
bounds that contradicted its public ranges, and validated only a minimum nonzero
count.  Those choices were replaced rather than preserved because the before
battery showed a missing rule pin, 140 defect warnings plus a blocking texture
issue, thousands of override-contract findings, no semantic contract, zero easy
exact-profile support, and only 10% pooled envelope support.

No prior return was used as authoritative evidence.  The repair used the current
selected baseline, assignment metadata, the canonical examples, and the retained
`56169a1e5c1d` diagonal-midpoint generator only as an architectural lead; all
claims above were remeasured on this task's final bytes.

## Limits and open findings

The semantic result is finite and relative to the declared rival family; it is
not a proof against every imaginable induction rule or every seed.  Exhaustive
schedule enumeration covers all four start residues at fixed seed 0 in all
bands, while the 300-lesson census samples the production sampler more broadly.
The grammar intentionally excludes one-pair and one-orientation inputs even
though the Racket rule can process them; this is a teaching-domain choice, not a
claim about the rule's maximal mathematical domain.  Training approval remains
a maintainer/catalog decision despite the green review evidence.
## Current reviewer considerations

Source SHA-256: `0d4d4600d98170c18b3e0c86be72c239ee4f406a657f4befa036fb990f6900fb`.

# Decisions — 71b44cea4ed1

## D1 — Preserve the canonical authority

**Prior choice:** the baseline omitted a rule hash.  **New choice:** keep the
existing canonical Racket rule unchanged and pin `RULE_HASH = "814976eb9ffc"`.
All three canonical pairs agree with the Python mirror, and the final rule-smoke,
Racket-lint, and authority-sync stages pass.  Changing the rule would have added
risk without addressing the actual sampler defects.

## D2 — Replace broad nominal controls with three honest axes

The former `palette_kind`, `texture`, `palette_size`, `n_distinct_colors`,
`position_bias`, `diag_dir`, and `n_pairs` interface contained aliases, inert
singletons, negative fixtures, or values not consumed by generation.  The new
interface exposes only `grid_h`, `grid_w`, and `pair_count`, because those values
are exact, independently constructible, and recoverable from an output grid.
Alternative: keep aliases for compatibility.  Rejected because an accepted typo
or dead control is worse than a deliberate API break in this review setting.

## D3 — Use strict call and override semantics

Literal integers are required for seed, sample index, and integer overrides;
negative sample indices, unknown difficulty values, and unknown override keys
fail closed.  Public override ranges stay 7..16 and 2..3 in every band, while
defaults may be difficulty-skewed.  This separates a caller's exact request from
the sampler's default distribution and eliminates the baseline's per-band range
contradictions.

## D4 — Rehearse exact morphology one slot in four

Canonical anchors cycle 7x7, 8x8, and 9x9, always with three distinct active
colors plus background and no decoys.  This produces the actual canonical
profiles rather than merely staying near their dimensions.  A 25% anchor rate
was selected because the required strict floor is 25% and because it leaves 75%
of samples for broader counterexample lessons.  A one-in-three plan was
considered, but it would spend more capacity on morphology than required and
complicate the three-of-four lesson schedule.

## D5 — Make every three-of-four window teach all predicates

The four slots are canonical, axis+wrong-distance+different-color,
wrong-distance+different-color+blocked, and blocked+axis.  With three
demonstrations, removing any query slot still leaves all four near-miss families
represented.  Every scene independently includes both active orientations and
at least two distinct fill colors, which also refutes identity,
one-orientation-only, and fixed-color rules.  This supports arbitrary query
rotation rather than relying on a privileged final query position.

## D6 — Validate a teaching grammar, not mere rule applicability

`self_check` requires two or three active pairs, both orientations, distinct
active colors, unambiguous midpoint ownership, and only recognized local decoy
roles.  Blank grids, one-pair grids, arbitrary singleton/repeated-color noise,
and invalid colors fail.  The alternative permissive validator would accept
labels that are technically computable but pedagogically empty or outside the
sampler's documented domain.

`strict_canonical_like` is narrower still: one of the three exact
height/width/palette profiles, exactly three pairs, six endpoints, and no decoys.
This distinction prevents broad lawful lessons from being misreported as
canonical support.

## D7 — Construct decoys without changing the active rule applications

Active pairs are placed first, and each decoy is accepted only if rescanning the
trial grid yields exactly the original active-pair signature.  Crowded layouts
are retried with a local keyed RNG.  Color 9 is reserved from ordinary sampling
so the unsupported-repeat regression fixture remains unambiguous.  Global RNG
state is never read or changed.

## D8 — Declare executable semantics

Six witnesses and seven competitors are functions, not prose.  The lesson hook
checks labels and asks whether any competitor that matches every demonstration
would answer the query differently.  The final battery exhausts the declared
four-slot period at seed 0 in all bands, and the larger census samples 100
lessons per band with every materialized pair held out once.

## D9 — Keep counterexamples and tests portable

Two minimal invalid grids live under `counterexamples/`; tests locate them
relative to the selected task and use `reviewer_support` for canonical data and
module loading.  The seven tests cover canonical parity, exact boundary
controls, bad scalar calls, schedule rotations, profile anchors, validator
counterexamples, deterministic freshness/global-RNG purity, and semantic-hook
purity.

## D10 — Scope and limitations

The selected task alone was edited.  No audit target was patched.  Semantic
coverage is bounded by declared rivals and finite sampling; exhaustive period
coverage is fixed-seed coverage, not an all-seed proof.  The intended export
contract is exactly three demonstrations; a downstream change to that count or
to ordering/query policy requires a new census.
