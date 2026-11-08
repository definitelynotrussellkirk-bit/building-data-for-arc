# Current notes: 33275a4aae3e

## Rule and source

Generator version **2.1.0** has SHA-256
`2b77752aa819ff3d2e1b5214f698055365f4ed747cd083baed087d97751fe67f`.
The canonical transformation fills enclosed four-connected zero components red
(2), fills edge-reachable zeros green (3), and preserves every foreground cell.
The single-color orthogonal network remains connected. The canonical Racket
program and rule hash `a7f4d11b444d` are unchanged. Synchronizing the two selected
`target_code` authority copies changed whitespace only; archival raw source and
transformation semantics remain intact.

## Distribution and lesson decisions

All eight original scene profiles remain available. Two additional left/right
stepped profiles supply a nonrectangular enclosure and a diagonally sealed
pocket. This closes a demonstrated shortcut gap: rectangle enumeration and
eight-neighbor exterior filling both fit all eight canonical pairs (four unique
inputs), but disagree with Racket on all six stepped profile/band draws in the
30-input final generated probe. One handmade witness also refutes both. See
`checks/shortcut-probe-final/report.json` and its retained cases and predictions.

Default generation alternates connectivity witnesses at even indices and legacy
networks at odd indices: period 2. Three demonstrations and one query drawn from
four consecutive default indices therefore contain two witnesses; every query
rotation leaves at least one witness among the demonstrations. The executable
lesson contract checks the declared five-rival family. This is a finite rival
argument, not universal identifiability or a guarantee after arbitrary filtering.

Explicit non-null `scene_profile` overrides take precedence and can deliberately
force legacy-only lessons; the default teaching argument does not apply to such
lessons. `scene_profile=None` is equivalent to omitting the override, including
the alternating pool. Strict integer guards reject Boolean/coercible seeds and
indices, negative indices, unsupported difficulty values, and Boolean grid
colors. Portable task tests use `reviewer_support` rather than fixed ancestors or
private generator loaders.

`strict_canonical_like` deliberately recognizes only the four public profile
signatures after ordinary validation. Other supported profiles are lawful
extrapolations, not newly claimed canonical support. Main focused verification:
**55 tests and 159 subtests passed**, retained in
`checks/green-final-contract.log`.

## Proposed parameter prototype

`workspace/parametric/` proposes `min_enclosed_area` in **{1, 32, 40}**, with
canonical/default 1. The inclusive threshold changes which enclosed zero
components become red; all remaining zeros become green. A seed-selected or
explicit parameter stays fixed across the complete episode. Inputs are identical
across explicit settings for the same seed, and reference labels and parameter
rivals execute the exact materialized Racket programs.

The four pairs alternate threshold/connectivity witnesses. Any one-query
holdout retains both kinds. Final evidence covers nine episodes, 36 labelled
pairs, and 12 unique inputs across seeds 17, 29, 41: all 18 parameter-rival checks
and all 36 query rotations (72 rotation-rival checks) found no ambiguity. All
30 profile/parameter controls and eight canonical controls passed. The separate
prototype suite passed **27 tests**. See
`checks/parametric/final-v2/private_evidence.json` and
`checks/parametric/tests-final-v2.log`.

Threshold-aware rectangle rivals are refuted in all nine episodes. At thresholds
32/40, sampled diagonal pockets are below the cutoff, so the eight-neighbor
rival survives all pairs in six episodes; it is refuted in the three canonical
episodes. This limitation is explicit, despite no measured query ambiguity.
Public challenges omit parameters, programs, and query answers. The prototype
narrows episode selection and remains proposed, without production integration,
approval changes, or training admission. These notes do not claim completed
fresh replay or a full final census; packaging/replay remains tracked separately
in `workspace/review-plan.md`.
## Current reviewer considerations

Source SHA-256: `2b77752aa819ff3d2e1b5214f698055365f4ed747cd083baed087d97751fe67f`.

# Decisions: 33275a4aae3e

## Repair the topology and retain the demonstrated family

The defect was a teaching gap: intact rectangular ladders allowed two wrong
rules to reproduce every canonical answer. Color variation already existed
and cannot distinguish rectangle enumeration or four- versus eight-neighbor
reachability. The repair therefore adds two mirrored stepped profiles while
retaining the original eight profiles and the first four canonical profile
identities. Explicit crossing counts describe the new diagonal-seal topology.
The strict canonical-support hook accepts only the original four public-form
signatures; the new profiles are documented lawful extrapolations.
[Selected implementation](repo/generators/33275a4aae3e/generator.py).

The geometric envelope remains 21–24 rows, 21–25 columns, one connected
single-color network, two or three enclosed regions, an exterior, four or five
horizontal strokes, three to five vertical strokes, density 0.17–0.24, and
one or two boundary attachments. Network turns remain crossings or at most
one T-junction, with no elbow pixels. New profiles use tighter density and
area bounds. Construction has a **512-candidate deterministic rejection
limit** and raises on exhaustion; it does not silently return an invalid
fallback. Finite checks do not prove termination for every possible seed.
[Final probe](checks/shortcut-probe-final/report.json).

## Make lessons retain the necessary witness

Three demonstrations plus one query use a period-2 default schedule: even
indices choose a connectivity profile, odd indices choose a legacy profile.
Two witnesses in every contiguous four-pair window preserve one after any
single query holdout. A sole witness tied to one position would disappear
when that example becomes the query. The executable hook checks actual
labeled demonstrations against five rivals: rectangle filling, eight-neighbor
exterior, all-red background, all-green background, and identity.

The guarantee concerns this finite family and the stated schedule. Explicit
non-null profile overrides remain available and may remove it. An independently
reproduced `scene_profile=None` bypass was fixed: null is now omission-equivalent.
The completed seed-0 period census covers both residues in all three bands
(6 lessons/24 rotations); the larger final census covers 300 lessons/1,200
rotations without ambiguity or scoring errors.
[Period census](checks/schedule-census-final.summary.json);
[larger census](checks/lesson-census-final.summary.json).

## Preserve authority and make validation portable

The canonical program and transformation were unchanged. The selected
`racket_target.target_code` strings in the training and augmented authority
files were synchronized to canonical formatting through the inspected public
proposal. Only whitespace changed; archival `raw_code` remained untouched and
normalized rule hash `a7f4d11b444d` remained stable.
[Proposal](checks/authority-proposal.json);
[application receipt](checks/authority-apply.log).

Validation now rejects coercible or Boolean scalars where exact integers are
required, negative sample indices, unsupported difficulty values, unknown
overrides, and non-integer grid cells. Tests use portable `reviewer_support`
root, generator-loading, and canonical-pair helpers rather than fixed directory
depths or a first canonical row. Final focused checks report **55 passed plus
159 subtests**; the final after-repair battery reports **12/12 green stages**.
[Focused log](checks/green-final-contract.log);
[battery receipt](checks/after-final/result.json).

## Keep the parameterized extension proposed

The runnable prototype introduces `min_enclosed_area ∈ {1,32,40}`: an enclosed
four-connected zero component becomes red only when its area reaches the
threshold. Setting 1 preserves the canonical rule. The parameter changes the
executed transformation, while geometry sampling remains independent of its
value. Each episode balances **threshold, connectivity, threshold,
connectivity** roles, so every one-query holdout retains both kinds. Area-band
constraints distinguish the parameter settings; the connectivity scenes retain
rectangle-refuting red regions even at 40. Selection is bounded and explicitly
fails if its requirements cannot be met.
[Prototype design](repo/generators/33275a4aae3e/workspace/parametric/README.md).

Final-source evidence for seeds 17, 29, and 41 contains **9 episodes, 36 query
rotations, and 12 unique inputs**. Same-seed settings intentionally reuse
inputs. All declared parameter alternatives are distinguished; separate
controls cover all 10 scene profiles at all three settings. Labels and
parameter-rival predictions were Racket-executed, with Python agreement checks.
[Private evidence](checks/parametric/final-v2/private_evidence.json).

The eight-neighbor diagnostic rival **survives every pair at thresholds 32 and
40**, because the diagonal pockets are below those thresholds. Thus those
episodes do not establish four- versus eight-neighbor connectivity, even though
their parameter alternatives are distinguished. The prototype narrows input
selection, supports a restricted callable-program adapter, and supplies no
production parameter API or training admission. Only its `public/` challenge
files are model-visible; programs, parameters, query labels, and receipts stay
in authoring evidence.
