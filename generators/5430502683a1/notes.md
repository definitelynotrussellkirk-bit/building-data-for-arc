# Working notes: 5430502683a1

## Review revision 4.0.1

Assignment `review-21858deadc143484` repaired the selected v3.1.1 input
distribution. The associated imported-notes file was empty, and no previous
review return was used as evidence. The canonical rule was not changed.

### Rule and domain

Compare inclusive lattice-cell counts, `max(abs(dr), abs(dc)) + 1`, for
same-color exact endpoint pairs. Aligned H/V/45-degree endpoints keep the
whole line in bounds. Draw the unique winning span in 8 on background 0.
Palette values are identifiers, not ranks or color-coded operations. Input
color 8 remains eligible, despite also being the fixed output color.

The sampler emits two to four aligned pairs with a unique longest span.
The validator accepts this grammar over lawful ARC dimensions 1..30; it does
not require the sampler's particular schedule, dimensions or metric profile.
The wider Racket execution domain is not the training manifold. Blank and
solid-color texture overrides were observed to produce a lone output cell,
not a runtime crash. They and one-pair teaching degeneracies were removed
from the sampler, and their former control names now fail explicitly.

### Exact controls and variety

Only three exact axes remain: height 8..16, width 9..18, and pair count 2..4.
They work in every difficulty with public draw provenance and direct observers.
Known `None` means default; invalid types, ranges and unknown keys raise errors.
Sixty percent of default shape draws choose canonical 10×10 or 9×11; other
draws retain broader difficulty-dependent geometry. Count defaults are weighted
toward three. Palettes vary across seeds over 1..9, with count/palette stable
through a same-seed lesson. Endpoints are disjoint; implied spans may cross.

### Curriculum and rejected first repair

Three random demonstrations could leave Euclidean distance, Manhattan distance,
numeric color rank, scan order or preferred orientation consistent with every
demo but wrong on the query. An independent baseline probe retained 240 lessons
and 960 actual Racket labels; nine core rivals caused 102 ambiguous lessons.

The first revision used five demonstrations. Its 18-rival census passed, but
independent review found a new shortcut: every axis winner was exactly one cell
longer than a diagonal. A second counterexample, easy seed 25 at indices 0..5,
had only one winning color 8 example, so holding it out permitted ignoring 8.
The assignment return retains those exact intermediate inputs and labels.

The final eight-example cycle repeats four profiles twice: one-cell metric
gap, diagonal winner, larger metric gap, and free span. Both metric profiles
include a shorter diagonal that beats the true axis winner under Euclidean
and Manhattan distance. Every diagonal loser in the larger-gap profile stays
at least two cells shorter. Free profiles preserve long or ordinary geometry
that cannot provide a metric contrast. Tests must not require every free axis
winner to have a conflicting diagonal.

Every palette color and every scan rank wins at least twice per eight examples;
a color's repeated wins have different scan positions. Seven demonstrations
therefore retain witnesses after any one-pair holdout. This deliberate length
increase supports four-color scenes and query rotations. It is not a guarantee
for shorter, nonconsecutive, cross-seed or changing-control lessons. If a runner
skips a failed draw, assess the actual accepted lesson rather than assuming its
requested start implies coverage. Layout failures are explicit, with no biased
fallback; universal placement termination is not proved.

### Verification and reusable tools

Final generator SHA-256:
`bce41577f9df2fca1e65d5509eea59b24e332a353e0ab6c207ed6f8f1c8564d8`.
The review return retains 12/12 green battery stages with required rotations,
449 passing focused and isolated task tests, 15,480 exact override checks,
600/600 strict-domain hits, and exact canonical-profile support 6/20 per band.
The production census has 300 lessons, 2,400 unique Racket-labeled inputs and
2,400 rotations, with no ambiguity among 29 declared rivals. The independent
public-API window probe covers all 8 starts on seeds 0..2 in all bands:
72 overlapping windows, 576 rotations, 135 labeled inputs and 82 unique hashes.
These counts belong to this source and those finite populations.

`workspace/probe_lesson_windows.py` discovers actual competitor declarations,
checks canonical claims and labels inputs through public `Catalog.apply`.
It retains source hashes, exact labels, refuting-pair indices, query rotations
and errors. See its README for commands and scope. The two tests under `tests/`
use portable canonical-data helpers and independent observed geometry.

The full rationale, two findings-only audits, blind and exposed solve records,
failed iterations, exact command arrays and final patch replay are retained in
the response ZIP for this assignment. Passing these checks does not grant
training admission or demonstrate improved model accuracy.
## Current reviewer considerations

Source SHA-256: `bce41577f9df2fca1e65d5509eea59b24e332a353e0ab6c207ed6f8f1c8564d8`.

# Distribution decisions: 5430502683a1

This document records task-local choices for v4.0.1, generator SHA-256
`bce41577f9df2fca1e65d5509eea59b24e332a353e0ab6c207ed6f8f1c8564d8`.
R1–R4 correspond to the findings in `REVIEW.md`. Original intent is described
only where the supplied source or summary supports it; no earlier review
return was consulted, and associated imported notes were empty.

## Semantic boundary and authority

**Keep the canonical Racket program unchanged.** The three canonical labeled
pairs and actual generated labels support comparing inclusive aligned span
length, then drawing the winning span in 8. The training defect was inadequate
contrast and dishonest sampling controls, not an established authority error.
Changing the rule to Euclidean distance would make familiar visual intuition
easier but contradict the selected rule's line-cell semantics. The rule hash
remains `182c38f86c20`; canonical file SHA-256 remains
`f5aa554e2aa0959cddca2a4a693e3524f8ad2836fbdff7f85a481058bcded6ee`.

**Define the sampler's intended input domain explicitly.** Inputs have black
background, two to four colors appearing exactly twice, H/V/45-degree endpoint
alignment, and a unique longest pair. Losing spans may tie with each other.
The baseline summary already described two to four endpoint pairs; it did not
justify training on arbitrary Racket execution behavior. Blank and solid-color
grids in the baseline actually produced a lone output-8 cell at `(0,0)` in this
runtime, rather than crashing. A one-pair grid may execute lawfully, but teaches
no pair comparison. We exclude all three special textures from this curriculum
and reject their removed control names. This restriction is a pedagogical
choice, not a claim that Racket is undefined outside the sampler domain.

**Use a broader validator than the sampled dimensions.** The validator accepts
ARC dimensions 1..30 when the endpoint grammar is satisfied, including lawful
long or nonsquare examples. It does not demand a metric-contrast profile,
scheduled winner rank, sampled minimum height, or canonical dimensions. This
avoids using distribution support as the definition of semantic legality.
Rectangularity, integer colors, endpoint counts, alignment and unique maximum
are independently checked. Color permutations may preserve valid geometry;
they should not be rejected merely because a generic mutation labels them
destructive. The final mutation check rejected 48/63 tested mutations versus
0/65 before; valid color swaps and some removals from a four-pair grid explain
why rejecting every mutation is neither intended nor required. [R2 evidence:
final self-check](checks/after-v401/checks/5430502683a1_after_selfcheck.log).

## Dimensions, count, colors and controls

| Choice | Original rationale / defect | Final choice and reason | Alternative and limitation |
|---|---|---|---|
| Canvas size | Difficulty-dependent size variety; advertised global ranges narrowed by band, canonical profile floor missed | Exact height 8..16 and width 9..18 in every band; 60% probability selects canonical 10×10 or 9×11, otherwise use a broader band-dependent range | Fixing every canvas to canonical dimensions would improve matching while unnecessarily removing size variation |
| Pair count | Baseline documented 2..4 pairs but ignored the exact override and coupled defaults strongly to difficulty | Exact count 2..4, seed-stable defaults weighted `(2,3,3,3,4)` | Three-only would closely match canonical palettes but remove distractor-count transfer; varying count within a lesson would undermine simple role-eligibility guarantees |
| Input palette | Original palette variety was desirable; several palette controls were ineffective | Sample four distinct colors from 1..9 per seed, use the chosen count, and keep that palette stable across a lesson | Per-example fresh colors leave an unseen color eligible only on the query; a universally fixed palette would overfit numeric identities |
| Output / background | Defined semantic constants | Background 0; all winning output cells 8, even when an input pair already uses 8 | Global color permutation would change the task unless fixed-role colors and output transformation were handled explicitly |
| Advertised controls | Pair count, texture, palette and layout controls could be silently ignored; unknown keys accepted | Advertise only `grid_h`, `grid_w`, `pair_count`; expose direct observers and public draw provenance | Pretending to support removed controls would keep an attractive API but preserve R1; undeclared names now raise an actionable error |
| Types and bounds | Python coercions or band narrowing obscure exactness | Reject bool, float, string and container values; known `None` means no override; full declared integer domains apply in every band | Coercing `True` to 1 or clipping an out-of-range request would violate exact control semantics |

The sample dimensions deliberately have enough room for a meaningful metric
contrast with multiple pairs. At the minimum 8×9 canvas, an eight-cell axis and
six-cell diagonal already give a gap of two while the diagonal has greater
Euclidean distance. The final public override matrix accepted all 15,480
requests, and focused tests exercise every declared single-axis value and
complete cycles at joint extremes. These finite checks do not establish that
every imaginable seed or unsupported shape will generate successfully.

## Geometry and layout

Pairs occupy two distinct endpoints. Endpoints of different pairs are disjoint;
their implied line interiors may cross another line or endpoint. The reference
groups the original input cells by color, so banning all such crossings would
add an unnecessary distribution restriction. The winner is placed first, then
each shorter pair is placed on the required side of its first row-major point
to vary the winner's observed scan rank. No post-placement shortening silently
changes the intended metric or exact pair count.

The layout attempts up to 256 geometric proposals and raises an explicit error
if none fits. A deterministic emergency grid or short-span fallback was rejected:
it could reintroduce the very support bias being tested. Only immutable endpoint
placement lists are cached. Every final tested draw succeeded, but finite tests
cannot prove rejection-free generation over all seeds. Production code should
retain accepted sample indices and validate actual assembled lessons if it skips
draws; the shared census does this.

## Lesson length, sequence and query policy

R3 required examples that contradict Euclidean/Manhattan distance, diagonal
preference, numeric rank and scan position. Three randomly sampled demos did
not reliably provide them: the baseline independent Racket probe found
102/240 core-rival ambiguous lessons, including 36/240 from the three
canonical-compatible geometric rivals. Exact definitions and all inputs are in
`checks/baseline-probe/README.md` and its lossless full report.

The first repair used six examples, five demos plus a query, with metric and
diagonal contrasts and varied colors. It passed its finite 18-rival checks.
R4 then exposed two defects in that construction: all axis winners had a gap
of exactly one to a diagonal, and a four-color palette could have a color that
won only on the held-out query. Both failures are retained with actual Racket
labels in `checks/intermediate-v400-probe/`.

The final contract is **seven demonstrations plus one query, assembled from
eight consecutive examples of the same seed with unchanged controls**. Its
profiles are `gap_one`, `diagonal`, `gap_many`, and `free`, each repeated twice.
The two metric profiles force a shorter diagonal that would beat the true axis
winner under both incorrect distance metrics. For `gap_many`, every diagonal
loser is at least two cells shorter; this prevents a second distractor from
undoing the profile. The two free slots permit any direction and all feasible
winner lengths, including axis cases where Euclidean distance agrees with the
correct rule. Requiring a metric conflict in every axis case was rejected as an
unnecessary geometric restriction; the initial tests with that old expectation
are retained and explicitly marked superseded.

For four colors, each color wins twice per cycle. This is the minimum eight-pair
population that makes a positive win for every color survive any one-pair
holdout by frequency alone. For two or three colors, ranks repeat more often.
The winner's numeric rank and its first-appearance scan rank follow separate
schedules; repeated wins of the same color occur at different scan positions.
This distinguishes fixed-color preference, ignored-color eligibility, minimum,
maximum, interior rank, and first/last scan alternatives without changing the
color vocabulary in the middle of a lesson.

The added four demonstrations over the original default increase token and
label cost. We accept that cost to preserve four-pair scenes and arbitrary
single-query rotations. Alternatives were shorter ordered lessons, at most
three colors, or adaptive per-query resampling. Each could be defensible for a
different downstream contract, but none meets the retained four-color/any-holdout
contract as directly. No claim is made that seven demos are necessary for every
possible teaching construction or every model; it is a sufficient tested design
for these rivals under this schedule.

The production census checks starts 0..99 with independently derived seeds,
100 lessons per band. The task-local probe enumerates all eight cyclic starts
for seeds 0..2 and all bands, reusing actual Racket labels for all rotations.
The census is production-shaped; the probe is direct consecutive sampling.
Both report unique input counts separately from overlapping windows. Declared
rivals may survive every pair when they coincide with the intended answer,
such as ignoring a color absent from the entire palette; that is not an
ambiguous query. These are finite tests of 29 specific alternatives, not proof
against all possible hypotheses.

## Tests, tools and scope

Two portable task-local test files contribute 449 cases using
`reviewer_support.find_root`, `canonical_path`, and `canonical_pairs` rather
than repository-depth guesses. They derive geometry from emitted grids,
exercise exact and invalid controls, validate broad lawful inputs, retain all
canonical labels, and test complete lesson windows and holdouts. Python
geometric oracles are useful unit-test checks; actual label authority comes
separately from Racket in the battery, census and reusable probe.

`workspace/probe_lesson_windows.py` is included for future agents. It imports
the selected module, discovers its actual competitor and canonical-shortcut
declarations, verifies canonical claims, calls public `Catalog.apply` in
bounded batches, retains exact inputs/labels/receipts and checkpoints, and
tests every requested start and holdout. It fails explicitly on invalid input,
missing rivals, materialization errors or ambiguous lessons. It is an analysis
tool that sees answers and must not be used during a visible-only solve.

Only the selected task's generator, notes, summary, tests and workspace are
changed. Audits remain findings-only; generic improvements are proposed in
F1–F3 rather than applied to shared sources. Neither correct individual labels,
passing rival checks nor an exposed Python solve constitutes a model training
experiment or changes training approval.
