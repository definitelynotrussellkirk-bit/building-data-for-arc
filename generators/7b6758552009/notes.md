# Review handoff — 2026-09-28

Assignment `review-e0d62364b09f1ce0`; selected task `7b6758552009`.
No canonical rule, base authority, shared helper or other generator was changed.
The associated-notes ledger was empty; it was not overwritten.

## Established findings

Version 2.1.1's normal sampler always used distinct colors and planted singleton
anchors at `(1,0)` and `(height-2,0)`. Its comments explain the latter as an attempt
to teach the secondary sort key. That intervention removed repeated-color
examples and made the lesson depend on fixed positions. The distinct-color
shortcut fits all four training demonstrations and the one canonical test,
and all 600 baseline draws in the retained census.

The old self-check counted nonzero pixels rather than components, so a single
solid blob and invalid palettes passed. Several declared axes were ignored,
others had bounds inconsistent with difficulty, and the “components_touching”
mutation actually contained separated components.

## Selected implementation

Version 3.0.0 keeps the canonical component rule and uses four interleaved input
profiles. Repeated colors teach multiplicity, randomized ties teach the minimum
row key, and crossing spans distinguish left-edge from right-edge ordering.
The canonical profile samples observed size/count triples but never loads or
copies canonical grids, coordinates or answers. All oriented connected shapes
of sizes one through five are available, with size selected before shape.

Only five real override axes remain. Validation checks integer palette, grid
shape, component count/size and inter-component background separation. The
validator deliberately accepts some small lawful witnesses outside sampler
size/count bounds; it is not an exact description of every input Racket can
execute. Invalid fixtures stay outside normal training draws.

## Tested and rejected iterations

Initial feature tests failed against 2.1.1 (30 failures, 12 passes). A lexical
linter warning on a local variable named `objects` was removed by renaming that
variable, not by weakening checks. Broad independent dimension sampling then
underrepresented canonical profiles (2 exact hits / 60); the canonical-scale
quarter fixed this. A transient missing parenthesis is retained in development
evidence. A naive schedule aliased when seed equaled index; a Gray-code seed
offset fixed it. Finally identical canonical-scale scenes across difficulty
bands were separated by a difficulty-specific geometry RNG stream.

Final evidence: 12/12 battery stages green; 48 task tests and 132 repository
tests passed; all 6,048 advertised override tuples across four difficulty
settings passed independent Python checks. The source-bound probe made 1,484
actual Racket evaluations with no mismatches, including 600 revised draws.
Those 600 contained 150 repeated-color cases, 150 ties and 600 distinct inputs.
These are finite samples, not a theorem over all seeds or competing programs.

## Next agent

Apply the source patch to the same packet revision; do not redraw this task.
Read root `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md` and `AUDIT.md` from
the return. Run task tests, then the probe in a new output directory. Preserve
source hashes and the input-only/private-answer split. Use four consecutive
demonstrations without semantic overrides for the reviewed curriculum.

Do not broaden to all 30x30 grids, diagonal-touching components or arbitrary
large blobs without a separate input-grammar decision. Do not promote the
catalog approval bit from these checks alone. The two findings-only audits
remain unfixed and need separately scoped owner work.
## Current reviewer considerations

Source SHA-256: `e2fef372f755f08b6a27f5c522c616207cf376c0a4b534902de612fdeb51e8c1`.

# Input distribution and implementation decisions

Assignment `review-e0d62364b09f1ce0`; task `7b6758552009`.
References below are paths in the original packet or this return. Original
motivations are only attributed when the source comments state them; otherwise
they are unknown. Review diagnostics are not a new rule authority.

## D1. Preserve the selected Racket rule

The canonical comparator uses each component's bounding-box `(min_column,
min_row)`, then emits its color. The input description explicitly permits
repeated colors across components. All five canonical input/output pairs match
this rule. No label bug was found. Changing Racket to deduplicate colors or
restrict ties would accommodate the sampler's defect rather than fix it.

Decision: keep the rule, base authority and shared runtime byte-for-byte.
The authority-sync stage reports selected sources synchronized with archival
raw-code divergence; that pre-existing archival difference was not repaired or
mistaken for a selected-authority failure. Racket remains the production label
source; the Python mirror only powers local checks and declared rival hooks.

## D2. Replace unique-color sampling with a real multiplicity lesson

Original: `rng.sample(..., target)` makes every component a different color.
No associated notes justify this restriction. An earlier-version comment says
repeated colors formerly occurred, then a tie-focused edit replaced the sampler.
The resulting unique-color shortcut agrees with all five canonical pairs and
all 600 baseline draws.

Decision: one of four ordinary profiles uses 1 through N−1 colors for N blobs,
ensuring repeated colors without requiring all blobs to share a color. Other
profiles retain distinct colors so their ordering changes are visibly testable.
A repetition-only sampler was rejected: it would remove useful canonical cases
and hide ordering mistakes when all relevant colors coincide. In the final
census, repeated-color examples are 150/600, exactly 50/200 in each band.

## D3. Preserve ties but randomize their position and shape

Original comments explicitly say the two singleton anchors teach the documented
tiebreaker. They are always at column zero, rows one and height minus two.
This is a real intervention, but it teaches an unnecessary coordinate template.

Decision: one profile places two blobs with the same minimum column in separated
vertical regions, with random column, vertical locations and one-to-five-cell
shapes. Extra components have distinct left columns so the designated tie stays
interpretable. No mandatory top/bottom-border or singleton anchors remain.
The old coordinates happen to be occupied in 12/600 final draws versus 600/600
baseline; zero accidental occurrences is not required. Four-example lessons
still include a visible tie. Forcing ties in every draw was rejected because it
crowded out canonical untied scenes and repeated-color examples.

## D4. Distinguish minimum column from other component summaries

Canonical examples also fit sorting by the right edge. Spaced narrow objects
rarely distinguish these policies; only 16/600 baseline draws did so.

Decision: one profile uses a four- or five-cell horizontal bar and a separate
small blob strictly inside its horizontal projection. Their min-column order
and right-edge order differ; distinct colors make that observable. Row bands
are randomly swapped and the whole construction is translated. Additional
objects are randomly placed. In the final census the rival fails on 208/600
inputs, including incidental failures outside the designated crossing profile.
Residual limitation: the long-bar construction is itself a recognizable
subfamily. Arbitrary crossing polyomino pairs could broaden this later, but
were not needed to establish this specific counterexample contract.

## D5. Bound real controls instead of advertising dead axes

Original metadata advertised height 4–16, width 6–24, component/color counts
1–9, palette kinds, position bias, density and texture. Several were ignored;
others contradicted difficulty-specific bounds. A request for one component
also conflicted with the forced two-anchor placement. Original rationale for
the metadata mismatch is unknown. The “components_touching” fixture contained
two separated blobs and did not implement its name.

Decision: version 3.0.0 advertises only height 6–12, width 10–18, components 2–5,
`color_policy={distinct,repeated}`, and `layout={separated,tied,crossing}`.
All explicit supported values override difficulty defaults. `None` is omitted;
unknown names, retired axes and non-integer numeric controls fail loudly.
Validation observes the requested controls from the actual grid, not echoed
metadata. The finite full product has 6,048 cases over four difficulty settings;
all passed a source-bound independent-Python sweep at one seed/index per tuple.
The battery additionally ran its own override probes. This is deliberately a
breaking compatibility change, hence the major version bump; callers using
old ignored keys must update rather than silently believe those keys work.

## D6. Preserve canonical scale without copying demonstrations

Independent broad dimensions initially produced only 2 exact profile hits in
60 battery draws, below the configured floor. That failed iteration remains in
`checks/after-attempt2/`. Simply disabling the floor or narrowing every profile
would hide the problem or lose useful support.

Decision: the canonical quarter draws `(height,width,components)` from the four
observed training scale triples `(6,11,2)`, `(7,10,3)`, `(8,12,3)`, `(9,13,4)`.
It uses distinct colors and separated horizontal spans, then independently
samples all shapes, colors and coordinates. The generator does not read a
canonical file or embed any canonical grid/answer. The other three profiles
retain wider dimensions and counts. Final profile-floor evidence has 22 exact
profile hits out of 60; its profile metric counts palette colors including
background, rather than directly counting components. Easy/medium/hard are
sampling preferences, not disjoint validity sets; the canonical quarter can
therefore have a two-component scene in the hard band.

## D7. Use small connected shapes and an explicit background gap

Original shape library had five fixed templates, while a canonical blob has
five cells despite the old summary claiming at most four. Decision: generate
all oriented connected shapes of sizes one through five once, then choose a
feasible size uniformly before choosing a shape. This avoids overweighting
five-cell shapes merely because there are more combinatorial possibilities.
Shapes remain monochromatic. Distinct components have Chebyshev distance greater
than one between their cells, preserving a background gap on all sides.

Tied/crossing scenes use bounded retries; failed free placement can choose a
legal singleton without changing the requested count/layout/color policy.
Exhaustion raises an error rather than returning a short batch or silently
switching to another profile. All advertised dimension/count combinations were
observed to succeed in the Cartesian sweep; this is not an all-seed proof.
No claim is made to sample all larger ARC shapes, diagonal-touching components
or every input on which the canonical Racket program returns a value.

## D8. Schedule four demonstrations without RNG aliasing

A naive sum of seed and index modulo four aliased under common `seed=index`
smoke sampling. A regression test exposed missing profiles. Decision: use
`((seed ^ (seed >> 1)) + sample_index) % 4`. At a fixed seed every four consecutive
indices visit all profiles; the common diagonal probe no longer loses half the
profiles. Every normal four-example lesson refutes the four named rivals in
tested seeds/bands. This is a relative finite competitor claim, not a proof that
no other program fits the demonstrations. Explicit semantic overrides and
fewer than four examples do not inherit it.

An initial successful battery/census still had identical canonical-profile
scenes for the same seed/index across difficulty bands: 496 distinct inputs in
600 draws. A separate regression failed at 79 distinct scenes out of 96 band
comparisons. Adding the band to the geometry RNG stream fixed this without
changing the rule; final census uniqueness is 600/600. All random choices use
local versioned generator streams; global random state and fresh returned-grid
identity are tested. Exact replay is tied to generator version/source hash.

## D9. Validate the scene, not the desired answer

Original `self_check` only counted nonzero pixels. Decision: reject empty/ragged
grids, booleans/non-integers/out-of-range colors, insufficient components,
oversize blobs and contacts between components. It deliberately accepts lawful
small counterexamples outside normal sampler dimension/count bounds. The
output width remains bounded by the ARC limit of 30. Invalid mutations are
checker tests, never disguised as normal training examples. Canonical inputs,
repeated-color scenes and all generated census examples remain accepted.

## D10. Retain independent evidence and honest provenance

Tests use a separate flood-fill implementation. The probe relocates the
selected sources and uses the existing protected Racket bridge/rule wrapper,
recording source and runtime identities. Its baseline comparison is a finite
distribution comparison, not a performance benchmark. Translation and bijective
color renaming are metamorphic checks; unrestricted rotation/reflection would
change the column-sort rule and was not asserted to be invariant.

All red runs, the transient parenthesis error, earlier green runs and final
source-bound results remain in `checks/`. No shared linter was patched or
approval bit set. A lexical warning on a harmless local name was handled by
renaming that local variable and recorded in F1. The complete library pytest
command was run as well as task tests, with 132 and 48 passes respectively.
Review was performed locally, not by an independent external reviewer.

## D11. Separate solver inputs from private diagnostic answers

Racket witnesses retain exact inputs, labels and rival answers in a private
file. The diagnostic input-only challenge export still has semantic rival IDs
and may repeat a grid across rival cases, so it is explicitly not a blinded
benchmark. Neutral-ID public integration episodes remove all query outputs,
program strings and provenance that might disclose the rule. Private receipts
stay separate. The return builder binds artifacts to this immutable assignment;
no unrelated repository edits or audit-target fixes are included.
