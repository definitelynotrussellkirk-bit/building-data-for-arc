# Working notes: cb439f1b5f4a

## Review identity

Assignment: review-4ea175c0c4711abd, generator-shortcuts, October 7, 2026 UTC.
Original source SHA-256: 1faeecd8422b49b653d8e7d5dac34fc54a67f5f78d3ebf3da936917befc7eebf.
Repaired source SHA-256: 78801e7652917d18617a7fd84359b4bc25c6c94ce4e87ab6e2342714977799b6.
Pinned normalized Racket rule hash: 33d95b8e8c4d; authority and canonical data unchanged.
No selected-task prior return was present in the imported notes.

## Included fixes

- R1: Replace ignored or misleading controls with five exact, observable controls.
  Values outside the declared domain, unknown keys, and invalid integer types
  fail explicitly. All advertised joint settings are constructible.
- R2: Restore compact canonical-profile support while adding blue and multicolor
  bodies, taller crops, noncanonical marker spacing, and bottom padding.
- R3: Add seven canonical-fitting shortcuts, nine other distinct lesson rivals,
  named semantic witnesses, four required demonstrations, and an actual
  lesson-identifiability check. Labels continue to come from Racket.
- R4: Validate the whole connected union of nonzero body cells, preserving blue
  and multicolor bodies. Reject malformed grids and overflowing output widths;
  do not invent a minimum body size, blank row, or nonblue-only restriction.

## Measured evidence in the return packet

The focused regression suite progressed from 32 failures / 14 passes on the
original source to 49 passes. A later observer regression was first retained
as a real failing test, then repaired. The isolated portable task-test stage
also passed all 49 tests. The repository suite passed 417 tests with three
PyTorch-dependent tests skipped because torch was unavailable.

The final strict after battery has 11 green stages and one failed stage:
the shared minimal-impostor heuristic described below. Canonical validation
accepts all three labeled pairs. The profile floor has 24 matches in 60 draws
(easy 10/20, medium 5/20, hard 9/20), up from 0/60 before the repair.
The override gate has 512 cases, 30 seeds per case in each of three bands,
46,080 accepted draws, and no rejections, warnings, or findings.

The larger Racket-labeled census checks 100 lessons per band, starts 0..99,
four demonstrations and one query, period five. It materialized 300 lessons
and 1,500 labeled pair occurrences (1,499 distinct inputs). No production
ambiguity was found, and none was found in the 1,500 hold-one-out query rotations,
against 16 distinct declared rivals (24 namespaced registry entries). Exact
seeds, grids, labels, source hashes, and rival results are in checks/lesson-census.json
in the return packet. This finite census does not establish unique induction.

## Retained warning and diagnostic

The defect linter reports selfcheck-minimal-impostor: solid_2x2 accepted 6/6.
Its representative grid is [[1,1,0],[1,1,0],[0,0,0]]. The header has K=2;
the body crop is [[1,1]], so the unchanged Racket rule outputs [[1,1,0,1,1]].
The accepted shape is lawful under the intended semantics. Rejecting it merely
to satisfy this heuristic would introduce an unsupported restriction.

The shared linter is not changed or suppressed. Acceptance needs maintainer
attention to this concrete warning. The reusable workspace diagnostic retains
all exact mutant pixels and actual reference receipts, so future agents can
assess aggregate linter findings without guessing. In this review it retained
30 mutations, six accepted, and six matching valid Racket executions.

## Distribution self-review

The sampler does not cover every lawful prototype. Every non-solid generated
shape contains a complete outer row and adjacent outer column, plus optional
growth; a missing opposite corner guarantees internal background. Multicolor
and blue_motif samples have exactly two body colors and always begin with a
nonblue primary pixel. No all-blue bodies, three-or-more-color bodies, full
multicolor rectangles, or one-dimensional multicolor bodies are generated.
The validator accepts those lawful cases where the connectivity and size
conditions hold. No claim is made that untested shape or palette rivals are
eliminated by the finite declared set.

The default five-phase schedule is deliberate teaching context, not a universal
guarantee for independently sampled or forced-override lessons. Such lessons
must pass the hook on their actual demonstrations and queries before export.

Imported associated notes retain original evidence/timestamps in evidence/associated_notes.jsonl.
## Current reviewer considerations

Source SHA-256: `78801e7652917d18617a7fd84359b4bc25c6c94ce4e87ab6e2342714977799b6`.

# Decisions for cb439f1b5f4a

Final generator SHA-256: 78801e7652917d18617a7fd84359b4bc25c6c94ce4e87ab6e2342714977799b6.
Assignment: review-4ea175c0c4711abd. All final measurements below refer to these
generator bytes; original and intermediate results are labeled explicitly.

## D1 / R4: Preserve the authoritative operation and validate the complete body

The existing Racket rule counts blue only in the top row, finds the bounding
rectangle of every nonzero cell below that row, and repeats the whole crop with
one zero separator column. The canonical examples are narrower than that rule:
their bodies are monochrome and nonblue. Treating that accidental appearance as
a color restriction hides a real header-versus-body distinction.

The validator now checks a rectangular grid of integer colors 0..9, a nonempty
blue-only header on background 0, and one 4-connected union of nonzero body
cells. It rejects disconnected foreground, malformed rows/cells, empty headers
or bodies, and an output wider than 30. It accepts a singleton, a blue-only body,
K=1, multicolor connected bodies, internal zeros, and body cells on row 1.
It intentionally accepts lawful inputs outside the sampler's narrower controls.
The one-connected-union condition retains the task's single-exemplar grammar;
the repair does not generalize to disconnected exemplars merely because the
reference can mechanically crop them.

The canonical ledger and selected base authority are unchanged. Rule pin
33d95b8e8c4d was added to make the dependency explicit. The full canonical file
SHA-256 remains f5aa554e2aa0959cddca2a4a693e3524f8ad2836fbdff7f85a481058bcded6ee.
[Actual Racket edge-case receipts](checks/selected-witnesses/racket.json) cover
the tiny blue case, a K=1 singleton, and a mixed body. Python test oracles are
independently anchored to all three canonical labels; they are not replacement
label authorities.

## D2 / R1: Replace misleading controls with five exact, observable controls

| Control | Legal requested values | Observable meaning |
|---|---|---|
| grid_h | Integers 4..12 | Exact input row count |
| grid_w | Integers 6..15 | Exact input column count |
| K | Integers 1..4 | Number of blue cells in row 0 |
| prototype_color | Integers 2..9 | Row-major first nonblue body cell |
| texture | solid, notched, multicolor, blue_motif | Filled mono rectangle, sparse mono crop, two nonblue colors, or primary color plus body blue |

The original palette, density, and position controls could be accepted without
affecting their claimed property. They are removed from the advertised contract;
unknown keys now fail rather than being silently ignored. Invalid diagnostic
textures are not part of normal sampling. Boolean, floating, and string values
do not masquerade as integers. An explicit valid value is honored in every
difficulty band, even when it is outside that band's default range.

Construction is feasible for all joint settings. The prototype width is bounded
by floor((31-K)/K), so the final output fits without truncating the body, changing
K, or rejecting a legal override. The minimum grid size still accommodates the
two-dimensional sparse shape used by multicolor/blue_motif. No incompatibility
exceptions or retry/shrink fallback are required. The final gate observed
512 cases, seeds 0..29 each in three bands (sample_index = seed*17 + 3),
46,080 accepted draws and zero rejection,
warning, or finding. The suite also checks 240 forced lower-bound combinations
and width 6 versus 7 at K=4 on the validator's output-size boundary.

The primary-color convention is a recoverable control, but is also a sampling
restriction: generated mixed bodies start with a nonblue cell. The observer
returns null for a lawful all-blue body, rather than raising StopIteration.
That boundary was first retained as a failing regression and then repaired.

## D3 / R2: Restore compact support without canonical replay

Default phases 0 and 1 choose height 4, width 6 or 7, and solid/notched mono
prototypes. Those phases yield three grid colors and restore the compact profile
that the old defaults missed entirely. Prototypes and placement are generated;
there is no lookup or exact replay of canonical examples.

This is a structural two-of-five allocation for consecutive default samples.
The profile-floor checker uses a separate finite sample: 24/60 final matches,
with 10/20 easy, 5/20 medium, and 9/20 hard, compared with 0/60 originally.
The profile-floor seeds are the first 12 hexadecimal digits of
sha256(profile-floor:v1:TASK:BAND:INDEX), with index 0..19 per band and
sample_index = seed % 7919 + index. Those band rates should not be described
as 40% each. The remaining phases use
larger difficulty-dependent grids and supply the teaching counterexamples.

## D4 / R3: Use repeated witnesses and check the actual lesson

The intended default assembly takes four consecutive samples as demonstrations
and the next as a query. Five consecutive sample indices span every phase,
regardless of starting residue. Phases 2..4 have tall sparse prototypes and
bottom padding; phases 3 and 4 contain blue in the body. Broad phases use
adjacent header markers. K = 1 + (seed + phase) mod 4 varies counts independently of
a globally fixed profile-to-count mapping and includes all four counts in a cycle.

This makes the body-blue witness appear twice, while several marker, crop,
padding, and internal-background witnesses appear in three broad phases.
Holding out one pair therefore leaves evidence against each declared shortcut
whenever that shortcut would change the query. Simply adding one blue example
at the end would not suffice: rotation could make that sole witness the query.

Seven CANONICAL_SHORTCUTS fit all three usable canonical labels: header_runs,
header_spacing_is_output_gap, last_two_input_rows, two_row_crop, count_all_blue,
erase_blue_body, and first_nonblue_component. Nine other distinct lesson rivals
cover fixed K values 1..4, no/two-column separators, filled bounding boxes,
mirroring, and vertical repetition. SEMANTIC_RIVALS reuses eight of these;
the census therefore has 24 namespaced entries but 16 distinct rival rules.

The hook compares each rival to actual demonstration labels and reports it if
it also disagrees with the query label. It does not return a blanket pass.
Witness declarations are mapped to the actual shortcut names, including the
two mappings that were missing in the first repaired battery. Those failures
are retained, and the final required-rotation semantic gate is green. Its strict
census uses the same profile-floor seed recipe for indices 0..199 in each band
and sample_index = seed % 7919 + index, yielding 600 draws. The 12-lesson smoke
sample uses four lessons per band, local indices 0..3, seeds from the same
profile-floor helper with band key lesson:BAND, and starts 0, 11, 22, and 33.

The larger supported census materialized 100 lessons per band, starts 0..99,
with deterministic sha256-derived seeds. It retained 1,500 labeled occurrences,
1,499 unique inputs, and all five rotations of each lesson. Production: zero
ambiguities in 300 lessons. Rotations: zero ambiguities in 1,500 trials. The
focused regression separately checks all five cyclic starts across seeds 0..7
and three bands using its Python oracle; it is not the source of Racket labels.

These guarantees are scoped to default consecutive assembly. Forced dimensions,
textures, or arbitrary mixtures may remove required witnesses. The actual
lesson hook must assess those assemblies before export; the default census
does not authorize them automatically. No finite rival set proves uniqueness.

## D5 / F1: Retain the shared-linter warning with exact semantic evidence

The final strict battery remains failed because the minimal-impostor heuristic
flags solid_2x2 acceptance on six of six probes. The exact flagged grid
[[1,1,0],[1,1,0],[0,0,0]] has a two-marker header and a two-cell connected blue
body, and the unchanged Racket output is [[1,1,0,1,1]]. A minimum body size,
mandatory blank row, or nonblue-only body rule would reject lawful inputs solely
to satisfy a generic shape heuristic. Those alternatives are rejected.

Shared source is outside the authorized task delta. More importantly, a
reference returning a valid grid is insufficient on its own to waive a domain
finding. The review instead retains the strict failure, explains the exact
semantics, and requests maintainer disposition. Acceptance is needs attention.

The included generic workspace tool reproduces the five named mutations,
retains the pixels and validator decisions, and obtains actual references using
public Catalog.apply. Its seed-0, indices-0..5 population cycles difficulty
bands and is explicitly not claimed to be the linter's identical baseline
population. All 30 mutants are retained; six accepted solid-2x2 cases all receive
the same valid reference result. It is a diagnostic, not a waiver or label path.

## D6: Bound the diversity claims and expose new restrictions

Constructive sparse shapes start with a complete boundary row and adjacent
column, grow through connected neighbors, and leave the opposite corner empty;
random row/column flips change orientation. This provides guaranteed connectivity,
full crop extent, and internal background without repair-by-repainting.
It does not sample all connected shapes: many T shapes and other non-spine
shapes remain absent. The defect is not hidden by the diversity totals.

Mixed prototypes have exactly two body colors; all-blue bodies, three-or-more
body colors, full multicolor rectangles, and one-dimensional mixed bodies are
not generated. The validator still accepts lawful versions. Broad default
prototypes have at least three rows and bottom padding, making spatial cue
correlations deliberate teaching choices. The source needs further independent
rivals before any stronger generalization claim is justified.

## D7: Preserve failed iterations and solve exposure honestly

The original focused suite had 32 failures and 14 passes. The first repair had
46 passes; later review added meaningful edge cases and captured the real
all-blue observer failure before fixing it. Final direct and portable task
runs each pass 49 tests. The repository-wide run separately passes 417 with
three torch-dependent skips. Missing isolated pytest was resolved in a local
environment with pytest 9.1.1, preserving both dependency-missing attempts and
the successful receipt. No shared worker isolation was weakened.

The blind solve preceded generator/rule inspection and matched five visible
examples in its first submitted revision. The final-source solve followed the
repair, disclosed earlier exposure, used only visible examples during solving,
and matched four examples in its first submitted revision. Both finished two
query executions without correctness feedback; their labels remain unknown.
No artificial failed solve was invented. Notes are agent work logs and program
revision records, not captured token-level conversations or log probabilities.

## D8: Keep audits findings-only and distinguish old leads

The immutable audit draw selected ba32e05911b0 and 99601629ab88. The former
reproduces an existing same-source review lead: seed 10, medium, three clear-climb
demonstrations permit a no-roll rival, while the fourth long-roll query differs
in 35 cells. Actual Racket executions and accepted-domain evidence are retained;
this is a generated teaching ambiguity, not a rival that fits every canonical
rolling example. No audit-target code was edited.

The latter audit found no issue in 31 actual reference probes spanning four
public profiles and nine general profiles across three bands, plus inspection
of seven canonical training pairs. Its modal-divider rival fits the seven
canonical pairs but is refuted on 22/31 sampled inputs. Public replay profiles
remain an explicit domain limitation. This bounded audit does not claim a
lesson census or general safety approval.
