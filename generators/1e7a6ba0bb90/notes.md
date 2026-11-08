# Current generator decisions: 1e7a6ba0bb90

## Authority and intended rule

Version 2.0.0 retains the canonical Racket authority, rule hash `cb29ce937e33`.
Key 1 rotates clockwise; 2 reflects left/right; 3 reflects up/down. Keys 4, 5,
6 select union, intersection and XOR respectively. Extract the left object's
bounding-box mask, transform it, align both object-local origins, combine and
crop the nonzero support. Output is always color 8; empty output is `[[0]]`.
The former claim that output uses the operation-key color was incorrect.

## Domain and controls

The header contains exactly two keyed cells and the next row is blank. Body
motifs are monochrome and four-connected, use distinct colors 1..9, and have
horizontally disjoint bounding boxes separated by at least one blank column.
The validator supports motif boxes up to 4×4, including small lawful witnesses;
the sampler draws connected motifs of 3..8 cells. The easy and core pools use
3×3 bounds; medium/hard teaching pools allow 4×4. The geometry pools enumerate
connected masks and contain no copied canonical grids.

The six exact controls are `grid_h=8..14`, `grid_w=10..16`,
`transform_key=1..3`, `operation_key=4..6`,
`palette_kind=canonical|reversed|varied`, and
`relation=overlap|equal|disjoint`. Full valid control domains work in every band;
unknown axes and malformed values raise rather than being ignored. The observer
recovers every control from returned pixels. Scheduled singleton draws record
the actual default; explicit controls use the full documented choice domain.

Removed the old decorative palette-size, density, position and texture axes.
They neither changed the grid nor described real exact degrees of freedom.
Invalid `no_keys`/`no_motifs` fixtures are no longer offered as generation modes.
The old same-input-shape rejection was also removed: equality is meaningful
only after transformation and normalization, and empty Boolean endpoints are
lawful. They are retained in ordinary core profiles and exact relation controls.

## Teaching schedule and shortcut repairs

The nine `(transform, operation)` combinations occur once per seed-shifted
nine-index cycle. A different deterministic seed permutation distributes
source-color order, vertical source order and header order across the six
off-diagonal teaching slots; these cues are not all tied to the same parity.
The three diagonal core slots use the canonical 8×12 canvas and colors 2/3,
with overlap, equality and disjointness all available. Controls can replace
those defaults without being clipped.

Each teaching slot chooses masks whose final cropped answer differs from all
23 alternative D4-transform/Boolean combinations and from transforming the
second operand. A placement filter also requires the fully cropped relative-row
alignment rival to disagree; if no placement works, it advances one deterministic
motif RNG and tries another pair within an explicit bound. Union slots additionally require contributions from both
operands and a nonrectangular output. Thus every nine consecutive samples
contain two strong examples per transform and per operation. Default lessons
use `EXAMPLES_NEEDED=9` and one query; this is a sufficient contract, not a
claim of an information-theoretic minimum. Accepted-index receipts must still
be checked because materializer rejection can skip requested indices.

There are 35 declared lesson rivals, including eight that fit all four labeled
canonical pairs. Most notably, **key 1 = counterclockwise** fits the entire
canonical set: one union hides rotation direction, and the test source has
180-degree symmetry. `counterexamples/clockwise_vs_counterclockwise.json`
retains a Racket-verified 8×12 witness. The focused tests cover its literal
output and a separate coordinate-set oracle, canonical acceptance, controls,
malformed inputs, all cyclic starts, every held-out pair and rival purity.

## Evidence and current limitations

The selected generator SHA-256 for the repair checks is
`f2e3e653f292273c18c65d7b453f082cc1763786c23874de1e85fff1b22e3b5e`.
The after battery passed all 12 stages, with all 27,000 override draws accepted,
zero override findings/warnings, canonical profile hits 7/20 easy, 6/20 medium
and 7/20 hard, and a 12-lesson/120-rotation smoke test with no declared ambiguity.
The final census materialized 300/300 lessons (100 per band), 3,000 distinct
input grids and 3,000 held-out-query rotations, with no declared ambiguity,
materialization/scoring error, or hook warning. The 48-case focused regression
suite passed both directly and in the portable task-test stage. The return's
`REVIEW.md` and `RESULTS.json` retain exact commands, source-bound evidence,
reference-witness checks and the fresh-packet replay result.

All four canonical inputs pass the validator. Exact default core support is
retained for the three training key pairs. The ambiguous canonical query uses
an off-diagonal key pair and needs core-profile key overrides for exact support;
no claim is made that its exact grid is emitted by default.

Independent review found a genuine intermediate placement weakness at seed 92,
index 2, hard: displaced operands gave the same cropped output `[[8], [8]]`
under both alignments. `counterexamples/vertical_offset_neutral.json` preserves
that source-bound case. The final filter turns this replay into intended
`[[8], [8]]` versus rival `[[8]]`; the regression is retained. This was a missed
teaching witness, not a demonstrated complete-lesson ambiguity.

The selected rule also defines tied-left and vertically stacked source order;
the current training domain excludes these layouts. This is intentional:
canonical examples do not teach tie handling, and overlapping boxes can make
Racket's extracted subgrids include another object's pixels. The restriction
avoids asserting unsupported ordering semantics in generated lessons. It does
not claim those reference-defined grids are universally invalid. Same-color
operands and boxes larger than 4×4 are also outside the declared sampler.
Finite rival checks do not establish uniqueness against all possible rules.
Explicit overrides can remove teaching diversity; the default schedule claim
does not certify arbitrarily overridden lessons or unrestricted resampling.

No inherited `evidence/review_index.json` was present in this pinned task.
No prior return was used as a repair claim, and no unrelated audit is marked
resolved by this change. The packet's independent audits are findings-only.
## Current reviewer considerations

Source SHA-256: `f2e3e653f292273c18c65d7b453f082cc1763786c23874de1e85fff1b22e3b5e`.

# Decisions for review-265ea8b9cf8072a8

## Authority and scope

The selected repair is task `1e7a6ba0bb90`. Its canonical Racket authority remains `cb29ce937e33`. I changed only the permitted Python generator, task notes/summary, and new task-local tests, counterexamples and workspace probes. The two drawn audit tasks are findings-only. The default reference and approval state were not changed.

The canonical semantics are transform the first object by key 1/2/3 (clockwise rotation, left/right reflection, up/down reflection), align the two local bounding-box origins, then apply key 4/5/6 (union, intersection, XOR), paint surviving cells 8, and crop. An empty result is `[[0]]`. Header codes are meaningful only in row 0; a body pixel can lawfully have the same color. The old description that the operation-key color is the output color was wrong.

## R2: repair canonical support and accepted input domain

The original validator excluded body colors 1–6, rejecting all four canonical inputs. It also treated equal motifs as intrinsically invalid, conflating pre-transform equality with post-transform Boolean behavior. I permit distinct body colors 1–9 and retain equal and disjoint cases. An XOR cancellation or empty intersection is valid data, even though it often carries less teaching information.

The generator still produces a structured subset of the reference domain: one header row, a blank separator row, exactly two monochrome connected body objects, horizontally separated bounding boxes and a blank inter-object column. Both boxes fit within 4×4. This prevents a bounding-box subgrid from accidentally including pixels from the other object and gives the leftmost rule an observable role. Tied-left, vertically stacked, overlapping-box, same-color and larger-object inputs are explicitly outside this generated domain. Canonical examples do not establish the tie-break semantics, so enlarging the domain without teaching those distinctions would have created a new ambiguity.

All four canonical inputs are validator-valid. The three training key pairs have exact default core-profile support, not merely a matching size/palette envelope. The ambiguous canonical query has an off-diagonal key pair; exact support for that particular grid requires core-profile key overrides. I do not claim its exact shape is emitted by default or that the generator is a uniform sampler over the full reference-defined domain.

## R3: make controls real

The six controls are grid height 8–14, grid width 10–16, transformation key 1–3, operation key 4–6, palette kind canonical/reversed/varied, and transformed-operand relation overlap/equal/disjoint. A pixel observer recovers these settings from each returned grid. Unknown axes, booleans masquerading as integers, coerced strings/floats and invalid choices raise clearly. Full valid dimension bounds work in every difficulty band.

The old palette-size, density, position and texture declarations were decorative. I removed them rather than inventing a grid effect after the fact. The scheduled defaults are recorded as the actual singleton choice; explicit overrides draw from the full declared domain. This preserves faithful generation receipts while allowing an ordered curriculum. Existing reviewed code uses the same supported choice mechanism.

## R1: teach the composition instead of relying on canonical coincidences

A strong plausible rival replaces only key 1's clockwise turn with a counterclockwise turn. It fits all three canonical demonstrations and the labeled canonical test: the demonstrated union hides the direction difference, while the test's first shape has half-turn symmetry. More random examples of equally uninformative shapes would not resolve this.

I enumerated connected normalized masks of 3–8 cells. Core/easy masks use 3×3 bounds; medium/hard teaching masks use 4×4. These pools are geometric constructions, with no canonical grid lookup or memorized output. Teaching pairs must produce a final cropped answer different from all 23 alternative D4/Boolean combinations and from transforming the second operand. Union teaching cases must contain a contribution from each operand and leave a nonrectangular output. Ordinary core and exact relation controls still cover lawful equality, disjointness and empty outputs.

The nine key pairs occur once per seed-shifted nine-index cycle. Three diagonal slots retain the canonical 8×12 and colors 2/3 defaults. Six off-diagonal slots teach the distinctions. A separate seed permutation balances numeric color order, vertical source order and header position, so the same parity bit does not encode all semantic choices. Six off-diagonal profiles supply two strong witnesses for each transformation and operation; nuisance rivals receive repeated witnesses as detailed in `checks/code-review.md`.

Default lessons use nine demonstrations and one query. This is a sufficient declared curriculum, not a claim that nine is the mathematical minimum. Over any ten consecutive samples, withholding any one pair retains a relevant refutation of every declared rival that changes the held-out answer. The focused test evaluates the equivalent leave-one-out criterion for all nine cyclic starts, seeds 0 and 17 and all three bands. Materialized lessons must still be checked because rejection sampling could skip schedule positions.

The final census used 100 hash-derived seeds and starts 0–99 in each band: 300 materialized lessons, 3,000 distinct grids, 3,000 held-out-query rotations, no materialization errors, rejections, ambiguity, scoring errors or hook warnings. All accepted indices were consecutive. The report's default period-6 bookkeeping is not used to claim period-9 coverage; `checks/final-metrics.json` derives actual modulo-9 starts, and the independent focused tests explicitly enumerate them.

## R4: reject the insufficient vertical-placement argument

Independent code review found that different input rows alone do not establish different outputs after Boolean combination and crop. On intermediate SHA `15e5f1b620e062df3809fddec4358197a80fd49ff1cf373d564cf3e8f932e943`, seed 92, index 2, hard produced intended and relative-offset answers both `[[8], [8]]`. Racket verified that input's intended answer. This was a missing teaching witness, not an observed whole-lesson ambiguity; the passing initial battery/census are preserved with that qualification.

I first added an actual failing regression, then changed teaching placement selection to compare the fully cropped relative-offset rival output directly. If no informative placement exists, a bounded outer loop advances the same motif RNG and tries a new pair. It does not reset the RNG or silently weaken the pair requirements. The final seed-92 case yields intended `[[8], [8]]` and rival `[[8]]`. Cached values remain immutable. The final source passed the 48-case suite and an independent review of both offset signs and minimum-size placements.

## Alternatives rejected and limits retained

Using only palette changes would not expose wrong transformations or Boolean operations. Requiring every sample to be a strong witness would erase legitimate equality/disjointness endpoints and canonical anchor support. Unconstrained random scenes would require a rejection rate and distribution analysis without guaranteeing complete lessons. Copying canonical grids would improve superficial profile counts but not teach the missing semantics. The selected constructive schedule balances these concerns within an explicit small domain.

The 35 rival functions and eight canonical shortcuts are test hypotheses, not training-label authorities. The Python authoring predictor supports probes; public selected Racket execution labels authoritative examples. Finite tests do not prove uniqueness against undeclared hypotheses. Explicit controls may deliberately remove teaching diversity; the default lesson guarantee does not certify arbitrary overridden curricula, unrestricted shuffling or arbitrary resampling. Medium and hard currently share the same 4×4 shape-pool bound; that is a documented difficulty limitation, not a correctness claim.

## Independent audits, tooling and failed evidence

AUD-E58-01 identifies an accepted-domain teaching gap in `e58953aee67a`: singleton, width-one and height-one red selectors agree throughout its constructed 1×1/2×2 support, yet differ on validator-valid domino queries. AUD-E26-01 reproduces the existing `e26f5e11d316` wall-color/authority mismatch on a small authored witness and a real generated sample. Neither task was edited or marked fixed.

The replay utility under `checks/tooling/` is a passive shared-tool proposal. It chooses the source patch's actual root, initializes an isolated Git repository, checks that root, applies exactly the supplied patch and verifies the generator hash. It executes no packet code automatically. Its own regression failures and subsequent passing tests are retained. Original archive size/format was inspected so its bounded extraction limits cover this real packet.

Original failing checks, the genuine intermediate vertical regression, the optional repository-suite failures and every actual solve revision remain retained. Full intermediate/final census reports are losslessly gzipped with original path/size/SHA and restoration commands. Earlier all-green reports are labeled intermediate rather than relabeled as final. Final handoff tests, commands and runtime directories are in `RESULTS.json`.
