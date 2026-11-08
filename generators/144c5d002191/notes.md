# 144c5d002191 — current generator decisions

## Current native parametric build

`workspace/parametric/adapter.py` now promotes identity and the retained exact
horizontal-mirror program, and adds `visible_majority`. The new branch paints
canonical clipped/overlapping stamps first, then retains the largest visible
color population (numeric-smallest tie break). Raw marker frequency is an
explicit wrong-intermediate counterfactual, not an equivalent shortcut.
Production source and canonical bytes are unchanged. Inputs are setting-neutral;
2–6 demos and four prefix-stable queries extend through substantive 30x30 scenes.
The old separated-stamps prototype remains available but is not the new sampler.

Adversarial self-review found a column-major overlap shortcut under mirroring
and a maximum-visible-color shortcut under filtering. The two-demo curriculum
was repaired constructively: an empty-origin asymmetric template and a surviving
higher-color decoy. The Racket-backed before/after column-order regression is in
`checks/144c5d002191/audit-final/teaching-regression.json`; no demo-count increase.
Bounded audit: 32 seeds x three policies x five demo counts, 480 episodes,
3,840 pair observations, 320 distinct inputs, no declared-rival failures;
53 protected Racket executions. Final suite: 136 tests. The strict witness parser
also caught an extra trailing delimiter tolerated by the execution wrapper; a
complete-expression parser regression now protects every setting and ablation.
Initial qualification/audit evidence and pre-privacy-fix `*-current` receipts
are superseded by `audit-final/`, `qualification-final/` and `causal-final/`.
Final self-review also found and repaired a public-projection edge case: injected
private metadata in demonstration pairs is now stripped by field whitelisting.
A red/green regression is retained; both qualification and witness were rebuilt.
Focused counts/type/privacy tests and exact-source
native qualification are retained in this return. See the current prototype
README and source/evidence manifest for replay commands and limits.
Reviewer-ready is not owner acceptance or training admission. No independent
reviewer agent was available; the final review is an author self-review.


## Rule and authority

Selected generator version: **3.0.0**. Canonical Racket is unchanged:
`RULE_HASH = c3118b3e9e62`; raw `program_solution` SHA-256
`c3118b3e9e629ff93f91ec234da20861592d6cf52661280e9d134c61dd4f2316`.

Use monochromatic 4-connected components. The largest component with more than
one cell supplies a binary shape cropped to its bounding box. Each singleton
component anchors a recolored copy at that bounding box's top-left. Clip cells
individually; later row-major markers overwrite earlier painted cells. Empty
shape cells do not erase earlier paint. The input template disappears.
The general reference permits more cases than this training sampler.

## Current input contract

- Integer colors 0..9, zero background, rectangular list grids: height 7..16,
  width 9..18.
- Exactly one multi-cell monochromatic 4-component of size 4..7 and 2..5
  singleton 4-components. Marker colors may repeat; diagonal equal-color
  singleton contacts and orthogonal different-color contacts are lawful.
- Exact controls: `grid_h`, `grid_w`, `n`, `template_size`. All joint integer
  endpoints are supported; no incompatible combinations are declared.
- Reject unknown/retired controls and booleans, floats, or strings supplied as
  integer controls, seed, or sample index. Sample index must be nonnegative.
  An integer seed may be negative. An override value of `None` means default.
- `self_check` measures component semantics, not global color populations;
  `observe_overrides` measures the actual generated grid. Strict fraction is 1.

## Distribution and lesson policy

Even sample indices use support scenes: bounded frontier-grown polyominoes,
varied template positions, fully fitting marker anchors, distinct role colors,
and a nonminimum template color. Odd indices use a constructive witness with
an empty crop origin, repeated diagonal marker colors, boundary clipping and
overlapping stamps. Default witnesses have 4 or 5 markers, including an
overlapping high–low–high color row and a lower-left repeat.

The declared schedule period is 2. A lesson has **3 demonstrations plus 1
query**. Four consecutive accepted inputs contain two support and two witness
scenes; every single-query holdout retains both profiles. Support refutes the
minimum-color template rival; a default witness refutes all 19 canonical-fitting
shortcuts. The executable lesson contract contains 20 unique rivals, counted
once despite names being bound in several declaration dictionaries.

Canonical dimensions and total color counts receive a two-thirds weighted core
mixture; the remaining mixture retains the full declared dimension ranges.
Within the core, dimension anchor values receive 80 extra copies in their draw
lists. Marker count receives the corresponding color-profile anchor in both
mixtures. Template size favors 4/easy, 5/medium, 7/hard while supporting 4..7 in
every band. This is a deliberate distribution, not a uniform sampler.

## Decisions reversed during this review

1. Replaced v2.0.1's global color-count validator, weak scalar handling and
   advertised but ineffective axes with the observable contract above. Retired
   `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`,
   `density`, and `texture`; degenerate no-template/all-one-color modes are
   outside the repaired domain. Original author rationale was not recorded.
2. An initial three-marker witness refuted 16 declared rivals but left a real
   color-tie-order teaching defect: seed 0, medium, start 23 supplied three
   matching demonstrations and a differing query. The independent rival sorts
   markers by (row, descending color, column). Replaced the default witness with
   the four-marker high–low–high construction and declared both within-row color
   orders plus global descending order. Explicit `n=2/3` remains supported, but
   opts out of the complete default lesson guarantee.
3. The first complete after battery then caught 24 invalid seed/index scalar
   acceptances. Added explicit call-argument validation, preserving valid
   generation. Retained that failed battery and the 24-failure red regression.

## Evidence and reusable tools

Final source and command receipts are indexed in `WORK/RESULTS.json` and
`WORK/REVIEW.md`. Source-bound minimal evidence is in
`counterexamples/row-color-order.json` and
`counterexamples/review-p1-lesson.json`; the latter deliberately preserves the
superseded input source identity and its genuine failed lesson.

From the outer extraction directory, with the packet's Python 3.12+ dependencies:

```bash
python3 review.py run python3 generators/144c5d002191/workspace/check_contract.py --seed 0 --out ../checks/replay-controls
python3 review.py run python3 generators/144c5d002191/workspace/check_witness.py --out ../checks/replay-witness
```

The first tool exhausts all 9,600 joint control/band/residue combinations at one
seed and measures construction only. The second materializes a generated
witness, obtains its actual public Racket label, and checks the generator's
actual canonical-shortcut declarations against all four canonical labels and
the witness. It does not substitute Python predictions for reference labels.

## Known limits and review scope

Exactly one multi-cell template is generated, so “largest” versus “first
multi-cell” remains answer-equivalent inside this sampler. The validator accepts
disconnected template-color singleton markers, but generation does not produce
them. Witness shape/location/color ranks correlate with profile; support uses
distinct role colors and full-fit stamps. These restrictions limit transfer to
the broader reference domain. No universal identifiability or all-seed claim is
made; the finite inventory can miss another plausible rule.

The supplied selected task had no existing review index or substantive notes.
No unrelated audit is closed by this repair. The two drawn peer audits remain
findings-only in `WORK/AUDIT.md`.

`workspace/parametric/stamp_orientation.py` is a **proposed prototype** with
identity and horizontal-mirror rule settings. It chooses a setting once per
episode and executes matching Racket. Its narrower sampler, separate evidence,
and 25 tests are described in its README. Acceptance of this canonical repair
does not select or approve the variant.
## Current reviewer considerations

Source SHA-256: `616644a1bffebb2adc85789f699373fa3be15ca499b99137fc2547f41f17b631`.

# Decisions for review-1f4b2a09912ae523

Main task: `144c5d002191`, “Recolor-stamp the template at each marker.”
Final generator version 3.0.0, SHA-256
`616644a1bffebb2adc85789f699373fa3be15ca499b99137fc2547f41f17b631`.
The original selected v2.0.1 source was
`0684a5ef0dc8162778284f0926a33e95876ced119b23f7a956827e102f034ffc`.
The assignment and both audit draws were kept unchanged.

## What the rule actually requires

The selected Racket rule groups monochromatic four-neighbor components,
chooses the largest non-singleton as the template, crops its binary occupied
shape, and pastes one recolored copy for each singleton marker. The marker is
the crop origin even if that corner is empty. Clipping is per occupied cell,
not per whole stamp. Marker discovery is row-major and later paint wins;
unoccupied template cells do not erase earlier paint. Template input cells do
not survive automatically.

The selected execution authority and all four canonical input/output pairs are
unchanged. The raw canonical program hash is
`c3118b3e9e629ff93f91ec234da20861592d6cf52661280e9d134c61dd4f2316`.
The public Catalog's executed wrapper has a different text hash,
`97956adc1e0ffa6b5119dd32ae21c67264b86a3119f2cbdc179e98c6ed31f232`;
that distinction is preserved in receipts. No catalog, shared runtime,
reference ledger, baseline fixture, approval record or audit target was edited.

## Input choices and alternatives

| Choice | Previous behavior or rationale | Decision and reason | Evidence / remaining restriction |
|---|---|---|---|
| Object semantics | The prior validator inferred roles from total color populations; no author rationale was recorded. | Validate actual monochromatic 4-components. Separate markers may share a color or touch diagonally. Reject invalid grids before component traversal. | Canonical inputs remain accepted; repeated-color regression and invalid-grid tests. One non-singleton template remains the sampled domain. |
| Palette | Prior normal palette omitted color 1; canonical templates are maximum color. | Sample nonzero colors 1..9 with seeded role assignment. Support selects a nonminimum template rank; witnesses use the minimum rank. | The maximum-color and new minimum-color hypotheses are refuted across both lesson profiles. Profile membership still correlates with template color rank. |
| Shape and placement | Ordinary polyomino support did not deliberately teach crop-origin anchoring, clipping or ordering. | Keep bounded random polyomino support and add a constructive S-shaped witness with an empty crop origin and boundary overlaps. | All template sizes 4..7 are supported; the witness uses a small family of extensions and a fixed relative placement. |
| Dimensions and color profiles | Before: 2/60 exact canonical-profile hits and 10/60 envelope hits; easy and hard each had zero exact hits. | Use a two-thirds canonical-profile core with full-range draws retained, rather than excluding canonical geometry at easier/harder bands. | Final profile-floor receipt gives exact counts; profile matching is measured jointly by height, width and distinct-color count. |
| Exact controls | Several declared axes were ignored; combined degenerate overrides also overrode dimensions. | Expose only height, width, marker count and template size. Measure all four directly; reject unknown and retired axes. | `workspace/check_contract.py` exercises 9,600 joint cases at seed 0: all dimensions, sizes, counts, three bands and two residues. Old callers using retired axes must update. |
| Degenerate textures | No-template/all-one-color modes could violate the intended task or accepted domain. | Remove these modes from the advertised interface instead of inventing labels or loosening validation. | Raw before failures are retained. Blank/no-template scenes do not teach recolor-stamping. |
| Scalar arguments | Shared context accepted some bool/float/string seeds, booleans and negative indices. | Require literal integer seed/index, nonnegative index, literal integer overrides. Preserve `None` as default and all valid draws. | First after battery: 24 scalar warnings. Red regression: 24 failures/9 passes; final portable suite includes all 33 cases. |
| Lesson length | No executable baseline lesson contract; larger random batches would only improve chance of seeing a witness. | Three demonstrations plus one query, period-two support/witness schedule. Every four consecutive indices contain two of each profile. | Any single-query rotation retains both profiles. `n=2/3` explicit overrides are lawful inputs but outside this default guarantee. |
| Rival inventory | Canonical examples hide template-rank, connectivity, crop, overlap and marker-order alternatives. | Declare 19 canonical-fitting shortcuts and a twentieth minimum-color lesson rival; compare all actual declarations in reusable probes. | Inventory is finite, not a proof against arbitrary rules. Namespace aliases are counted once. |

The exact four canonical (height, width, total-color-count) profiles are
(10,12,4), (9,13,5), (11,14,4), and (10,14,5). A core draw weights its selected
height and width anchor with 80 extra copies; a broad draw uses the full integer
dimension lists without that anchor weight. Marker count is profile-anchored
even on broad draws. All four size options remain possible in each difficulty
band, with three extra copies of the favored size. These weights are recorded
as implementation choices, not estimated from a population distribution.

## The important failed intermediate and its repair

Intermediate source
`a3e21d4ea25700280832635bb9af391686399b3b7926cc8944f16d7ee6ae4d14`
used three default witness markers. Its then-declared 16 canonical shortcuts
passed a fixed-seed schedule check and its task tests passed. Independent review
found a stronger, unlisted rival: sort marker ties within each row by descending
color. It fit all four canonical labels and all three demonstrations of a real
default lesson, yet changed the query at (3,4) from 5 to 3.

That lesson is seed 0, medium, samples 23/24/25 as demonstrations and 26 as query.
`checks/review-p1/prior_generator.py` retains the exact generator bytes;
`reproduce.py` verifies captured input hashes and obtains fresh labels through
public Catalog application. Its exit 1 intentionally means the historical
teaching defect was reproduced. The old hook returned an empty reason list,
showing why a finite declared-rival pass was insufficient.

The revised default witness has an overlapping high–low–high row and a
lower-left repeated high-color marker. One such input exposes both within-row
ascending and descending color order. It also retains the earlier connectivity,
clipping, column-order and deduplication distinctions. Added all three missing
color-order rivals, including global descending color. The new four-marker
fixture is exactly generated by seed 138, index 1, medium, height 7, width 9,
n=4, template_size=4. Public Racket labeling and every declared canonical rival
are retained in `checks/witness-release/`.

Source
`50210d202b830b2e8726ed0f28ab905d0a465512b9297fccf16bef55b116ffa2`
resolved the teaching defect and passed a 300-lesson/1,200-rotation census but
failed the full after battery solely on scalar arguments. The final
`616644a1...` source adds entry validation. Valid generation is unchanged;
required final-source checks were run again rather than relabeling the older
receipts. All failed evidence is retained.

## Lesson assembly and limits

The intended default assembly is three ordered demonstrations and a fourth
query, with arbitrary single-query rotations explicitly checked. Requested
sample indices determine the period-two profile; every generated input is
expected to be accepted under the declared strict domain. Four consecutive
indices give two support and two witnesses. Holding out any one leaves at least
one of each. The support example exposes the minimum-color template rival; the
witness exposes the 19 canonical-fitting alternatives.

The final random census uses 100 production lessons per band and their four
query rotations. The separate schedule census enumerates both declared starts
at fixed seed 0 in each band. These are different denominators: six overlapping
schedule windows are not 24 unique inputs. The precise unique-input and failure
counts appear in the source-bound summaries and REVIEW.md.

Remaining restrictions are explicit. Exactly one multi-cell component means
“largest” and “first multi-cell” are indistinguishable within sampled inputs.
Template-color singleton markers are accepted when disconnected but are not
generated. Witness geometry, shape family and template-rank correlate with
profile; support markers use distinct colors and full-fit anchors. Conditional
rules can exploit these correlations. The review establishes finite declared
rival support, not general human-like induction, model mastery, or training
admission. Introducing distractor templates or unrestricted palettes would
need a separately tested extension of the distribution and teaching policy.

## Proposed parametric extension

Implemented `workspace/parametric/stamp_orientation.py` and 25 separate tests.
`stamp_orientation` has exactly two settings: original/default `identity`
and `horizontal_mirror`. Mirroring changes cropped-template columns before
the same recolor/stamp operation. The default returns the canonical program
string byte-for-byte. The alternative program SHA-256 is
`ccddc90a7416ad7b7e8b8f4354fdef13a788e4a9babaa5ee956dce32f6e6664b`.

A seeded selector chooses one setting once per episode, then all demonstrations
and queries execute that exact Racket program. The input sampler never receives
the hidden setting. Public exports contain only train inputs/outputs and test
inputs; settings, seeds, programs and query answers remain in private authoring
evidence.

The bounded evidence includes all 4 canonical pairs, identity episode seed 34,
mirror episode seed 31, two demonstrations/one query each, and all three
rotations per episode. Both episodes and all six rotations distinguish the two
settings. A lawful 6×7 witness gives different outputs at (3,4) and (3,5). A
deliberately symmetric two-demo teaching negative remains ambiguous and is
labeled intentional. See `checks/parametric/evidence-31/report.json` and
`checks/parametric/HANDOFF.json`.

The sampler uses four asymmetric masks, separated full-fit boxes and reserved
central row/column space. It omits clipping, overlap, distractors and larger
templates; two-setting identifiability says nothing about all other shortcuts.
This is a **proposed prototype**, separate from the production canonical sampler.
The first macro wrapper triggered a protected filesystem denial; an ordinary
lexical identity procedure now executes the exact program without changing the
runtime policy. The failed source, logs, wrapper diagnostic and final evidence
are retained. No production parametric API was added.

## Audits, solves, and acceptance boundaries

The two drawn audit sources were inspected independently and left unchanged.
`AUDIT.md` retains the ordering limitation for `28b87bd4c441` and the
portability/semantic-contract failures plus numeric-color lesson counterexample
for `f112ec4615da`. Those findings require action in their own task homes and
are not closed by this repair.

The blind solve and later exposed solve use separate directories and preserve
every genuine checked revision plus frozen finish notes. Initial broad README
reconnaissance makes the blind record's earlier exposure conservatively
`unknown`; reference consultation during the solve is `no`. The post-repair
record is explicitly exposed (`yes` earlier exposure, `no` reference
consultation during solving). Query correctness is withheld and remains unknown.

The handoff includes exact commands, working directories, source hashes and
evidence paths. The final patch is replayed into an independently extracted
original packet with Git rooted at that fresh WORK directory; byte comparison
of every changed path and fresh portable tests establish that the transported
patch applies. Reported checks are reviewer evidence, not an approval or
training-admission action.
