# Layer Histogram Strip — current decisions (4.0.3)

## Intended rule and authority

The selected canonical Racket program is unchanged. It excludes 0 and 9 from
the shape mask, repeatedly removes cells that have a missing cardinal neighbor,
and outputs the number removed at each depth as one row, outside first.
These are exact shell populations, not cumulative remaining populations.
`RULE_HASH = "3e24db6285e1"`; the normalized program SHA-256 is
`3e24db6285e1c9e31be97d01f1dacfcb6985e88dc280c6fce4ecc72f5f4f7b45`.
Canonical outputs are `[[8,4,1]]` for a 13-cell diamond, `[[8,1]]` for a
solid 3x3 square, and `[[4,1]]` for a five-cell plus.

## Domain and distribution

Inputs have background 0 and one cardinal-connected, hole-free shape in one
foreground color 1..8. A shape has at least three cells and every nonempty
erosion shell has at most nine cells. The generator draws areas 3..14; the
validator accepts any shape satisfying the stated semantic conditions, rather
than artificially equating the generator's sampled maximum with rule validity.
Grids must be rectangular, nonempty integer grids. Booleans, floats, multiple
foreground colors, color 9, disconnected pieces, holes, and oversized shell
counts are rejected. Colors 9, multiple components, and holes are deliberate
distribution limits; no training coverage claim is made for them.

The prior total-area cap of nine excluded the canonical 13-cell diamond.
It is replaced by a per-shell digit bound. Small four-cell shapes remain lawful:
the unchanged Racket returns `[[4]]` for a solid 2x2 block and a four-cell line.
The stock minimal-impostor linter still questions those inputs. The optional
proposal under `workspace/lint_proposal/` adds a narrow evidence-bound shared
contract; it does not modify the stock linter or declare this generator approved.

Only four exact controls are advertised: `grid_h` and `grid_w` in 5..16,
`shape_size` in 3..14, and `color` in 1..8. Every joint combination fits in a
5x5 canvas. Unknown controls and silently coercible scalar values are rejected.
The former phantom texture/position/palette/shape-kind controls are removed.
Seed validation accepts any literal integer, including negative and wide values,
as the public GenCtx contract specifies. Version 4.0.3 removes an erroneous
reviewer-added unsigned-32-bit bound that caused the official 48-bit profile
and semantic seed streams to crash; the failures and exact-seed regression are retained.
Default canvases span 7..16 with extra weight at canonical dimensions 7 and 9;
5 and 6 remain exact override values. Colors and dihedral orientations vary.

Broad/core draws use bounded connected growth, hole and shell validation, and
an exact-size constructive fallback. Areas 13 and 14 are deliberately represented
to retain three-depth examples. This is not uniform sampling over polyominoes.
The difficulty labels change canvas-profile weights, not the mathematical rule.

## Teaching policy and rivals

Five demonstrations and one query form a six-pair lesson. The default input
sequence cycles through a nine-cell long plus, a nine-cell shape with both
row and column concavities, and a broader core draw. Every six consecutive
draws contain two examples of each role. The default roles have disjoint mask
support; successive copies use different placements when geometry and canvas
match, avoiding duplicate-removal skips within a lesson.

The four executable rivals are the actual declarations used by checks:
`axial_ray_depth`, `row_fill_then_peel`, `column_fill_then_peel`, and `area_lookup`.
All fit every labeled canonical pair. The long plus produces `[[8,1]]`, while
the straight-ray rival gives `[[8,0,1]]`. The concave nine-cell witness produces
`[[9]]`; both fill-first alternatives predict an illegal count above nine and
are represented as `[[0]]` by the rival-only scorer adapter. Retaining a copy of
each witness after any single holdout refutes all four rivals in every query position.
Both teaching shapes have area nine but outputs `[[8,1]]` and `[[9]]`. Their
presence in every five-demo holdout refutes every deterministic area-only rule.
The previous eight-cell concavity allowed an area lookup to survive 20/300
production lessons and 128/1,800 rotations despite the three-rival census pass.
Version 4.0.2 adds one cell to that witness, preserves both concavities, and
registers the new rival. The exact failed lesson is retained and tested in
`counterexamples/area_lookup_lesson_4_0_1.json`.
This six-pair policy applies to default sampling. An explicit area override
requests an exact-size input, not a certified lesson curriculum.

An intermediate 300-lesson census exposed invalid rival predictions above 9.
Those alternatives are already inconsistent with this digit-valued domain.
The row/column rivals now return `[[0]]` for such an impossible prediction so
the grid scorer can record rejection instead of throwing an exception.
The true rule always returns positive shell counts; no canonical output is
clipped, reversed, recoded, or replaced by this sentinel. Exact retained cases
are in `counterexamples/rival_digit_domain.json` and covered by task tests.

Final source SHA-256:
`a60411538257c5711a7b3d672eae05dfb3c7e8c49d81ff75cd32414fcec140e9`.
The final production census materialized 300/300 lessons, 1,800 pairs,
1,670 unique inputs and 1,800 rotations, with no ambiguity or scoring errors.
The fixed-seed census covered all three start residues in all three bands:
9 lessons, 54 rotations, 18 unique inputs, with no ambiguity or scoring errors.
These finite checks cover declared rivals and tested assembly only; they do not
prove uniqueness against every conceivable rule or all seeds.

## Open findings and proposed extension

Output diversity is intrinsically constrained by small digit-valued count
strips and is further concentrated by two scheduled teaching roles. The stock
lint's observed low-diversity warning is retained. No unproved
`EXPECTED_OUTPUT_CODOMAIN` is inserted to bypass it. Review the final battery
in the return before treating the repair as accepted; this source does not
change training approval or canonical authority.

`workspace/parametric/prototype.py` is a separate runnable proposed extension.
It chooses `output_order` once per episode: canonical outside-first or proposed
inside-first. Both settings execute Racket, and two demonstrations distinguish
them before the query. It uses only three shape templates and is not a broad
training generator. Its default Racket bytes exactly match the selected rule.

Historical failures and exact commands are retained in the review's `checks/`
and `RESULTS.json`; this file records current choices rather than duplicating
full review logs. Imported associated notes retain their original timestamps
in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `a60411538257c5711a7b3d672eae05dfb3c7e8c49d81ff75cd32414fcec140e9`.

# Decisions — review-48f831f8020a3b47

## Scope and authority

The assignment remains repair `12ace26107fd`, blind solve `b47adc50b675`,
question `generator-shortcuts`, and audits `fa3550d200a0` / `204213f10aff`.
Only the repair task's generator, notes, tests, counterexamples and workspace
are part of the source delta. The shared linter proposal is transported as a
separate optional patch inside that workspace. Audit targets are findings-only.
No canonical Racket source, authority catalog, approval record, root frozen
fixture or assignment was changed.

The selected baseline is version 3.0.2, generator SHA-256
`825a4892e8a9d663536c3ec745e3f486aab761084b9fc6e14bde4bc4f66ee619`.
The final repair is version 4.0.3, generator SHA-256
`a60411538257c5711a7b3d672eae05dfb3c7e8c49d81ff75cd32414fcec140e9`.
`RULE_HASH = 3e24db6285e1` remains bound to normalized program SHA-256
`3e24db6285e1c9e31be97d01f1dacfcb6985e88dc280c6fce4ecc72f5f4f7b45`.
Apply's separate `rule_text_sha256` identifies the executed wrapped callable;
its `62885b...` value is not a contradictory raw-source hash.

I inspected the selected source, its placeholder notes, canonical pairs, and
current packet contracts. No predecessor return was used as measurement of
this source. The original rationale is unknown where no substantive notes
were supplied. Historical associated notes were not treated as current evidence.

## D1 — Use exact shell populations, not cumulative counts or total-area digits

The selected program counts the cells removed at each successive cardinal
peeling step. Its canonical 13-cell diamond produces `[[8,4,1]]`; a solid 3x3
square produces `[[8,1]]`; a five-cell plus produces `[[4,1]]`. The baseline
summary incorrectly described cumulative populations and its total-area cap
rejected the diamond. The before battery also recorded that rejection.

I retained the program and corrected the input domain and explanation. Every
nonempty shell count must lie in 1..9, but total area may exceed nine. The
sampler supports every exact area 3..14, including deeper 13/14-cell shapes.
The validator applies semantic shell constraints rather than pretending the
sampler's maximum is the full rule domain. Clipping counts, taking modulo ten,
recoloring digits, or changing the canonical rule would change the task and
were rejected.

Evidence: canonical acceptance tests, `checks/before/`, subsequent reference
batteries, and actual source-bound lesson censuses. The task test's independent
breadth-first distance calculation is diagnostic; Racket remains label authority.

## D2 — A clear solid-shape manifold with explicit limits

One foreground color in 1..8, zero background, cardinal connectivity, no enclosed
background hole, at least three cells, rectangular literal-integer grids and
per-shell digit validity define the sampled manifold. These conditions reject
empty shapes, multiple components/colors and illegal cells that the baseline
checker admitted, and enforce the correct per-shell digit bound. The three-cell minimum preserves
small useful shapes without single-pixel examples.

The selected rule has additional behavior for color 9 and more general masks.
The chosen sampler does not teach ignored-9 semantics, multiple components or
holes. Broadening all of those dimensions at once would require additional
teaching witnesses and a separate domain assessment; no such coverage is claimed.
Difficulties vary canonical canvas-profile weights rather than changing the rule.

Four-cell lines and 2x2 blocks remain lawful. They produce `[[4]]` under actual
Racket execution, and the current semantic constraints accept them. Rejecting
only those named shapes to silence the stock minimal-impostor probe would be an
arbitrary domain restriction. The optional linter proposal instead requires an
explicit, reviewed, rule-bound declaration and matching live reference labels.
That proposal is not applied to the authoritative shared tool.

## D3 — Honest exact controls and bounded construction

The old source advertised inactive palette, position, texture and shape-kind
controls. Its dimensions were advertised as 5..16 but narrowed by difficulty,
so nominally legal overrides were rejected or ignored. These phantom controls
are removed. The four remaining controls are fully observable: height/width
5..16, shape area 3..14, foreground color 1..8. All joint combinations fit a
5x5 canvas; no incompatibility exemption is required.

Ordinary canvases use 7..16 with additional weight at canonical dimensions 7
and 9. Exact overrides still support 5 and 6. Bounded connected growth produces
varied masks; hole/shell checks reject unsuitable proposals internally, and a
constructive exact-size fallback guarantees completion. Thirteen- and fourteen-
cell shapes receive explicit support for depth-three cases. This is not uniform
polyomino sampling. A fixed shape dictionary alone was rejected because it would
make shape classification too easy and underrepresent variation within an area.

Exact overrides request individual inputs, not a promised lesson curriculum.
An explicit area override may remove a scheduled witness; the default lesson
claims are deliberately scoped to empty overrides.

## D4 — Five demonstrations with teaching evidence in every query rotation

Canonical examples do not distinguish exact erosion depth from a shortest
straight-ray shortcut, row-fill-before-peeling, column-fill-before-peeling, or
an area-only lookup. The first repaired schedule cycled through a long plus,
an eight-cell dual-concavity witness and broad/core draws. It passed the three
then-declared rivals, but independent rescoring found an area lookup surviving
20/300 production lessons and 128/1,800 rotations. That failed source and exact
lesson are retained, rather than being relabeled as a pass.

The final schedule uses **two area-nine teaching masks**: the long plus has
output `[[8,1]]`, and the dual-concavity mask has output `[[9]]`. The third role
is a broader core draw. A six-pair window contains two of each role. Holding
out any one pair leaves both area-nine outputs among its five demonstrations,
which contradicts every deterministic area-only function. The concavity also
refutes both fill-first rivals, and the long plus refutes straight rays.

Every role is transformed, colored and translated. Core support excludes the
two fixed witness families. Default canvases and cyclic placement make repeated
matching geometry distinct within a window. This matters because the production
sampler removes duplicate grids; checking raw indices alone would not establish
what an exported lesson actually contains.

The four actual rival declarations are shared by canonical-shortcut, semantic
and lesson checks. The final census and fixed-seed residue enumeration execute
actual production assembly with required query rotations. Their exact final
counts and hashes are in `REVIEW.md` and `RESULTS.json`. A finite rival census
is not universal identifiability; an area-only impossibility argument does not
rule out every hypothesis using additional shape features.

## D5 — Rival-domain errors are explicit rejection, never transformed labels

An intermediate census generated all 300 lessons correctly but encountered one
production scoring error and six rotation scoring errors when fill-first rivals
predicted counts above nine. Such a rival prediction is already impossible on
the output domain. It now becomes `[[0]]`, a valid grid that cannot equal a
positive shell histogram. Only hypothetical rival outputs use this sentinel.
The selected canonical Racket output is neither modified nor replaced.

The original census and four distinct invalid-rival inputs are retained.
Focused tests cover every retained case. This resolves scorer exceptions while
preserving the exact logical rejection, rather than constraining lawful input
support around a diagnostic's formatting bug.

## D6 — Correct the public seed contract, including our own failed assumption

I initially tightened call arguments with an unjustified unsigned-32-bit seed
bound and wrote tests reflecting that mistaken bound. The full stock battery
uses 48-bit seed hashes: it rejected all 60 profile draws and 600 semantic draws
on version 4.0.2. Those failures remain in `checks/after-v4-0-2/`.

The public `GenCtx` contract accepts an integer seed and hashes its textual
representation; it imposes no word size. Version 4.0.3 checks `type(seed) is int`
without a sign or width bound. Booleans/floats/strings remain invalid. Sample
indices remain nonnegative literal integers, and difficulty is None or one of
the three documented strings. New tests cover negative, 32-bit-boundary, actual
48-bit gate and 128-bit seeds. The exact failing seed is reproduced before the
fix in `checks/integer-seed-red/`; the corrected regression run is retained.

## D7 — Output concentration is a visible tradeoff, not a fabricated codomain

Two thirds of default draws intentionally carry fixed teaching outcomes, while
core draws vary area, geometry and shell structure. This makes individual
lessons discriminative but concentrates the output distribution. The stock
lint's low-unique-output warning is retained. I did not set an arbitrary
`EXPECTED_OUTPUT_CODOMAIN` equal to a measured sample count: that would confuse
observed support with the mathematically justified full alphabet.

A stock transformation-drift warning also appeared on version 4.0.2 because
its outputs introduced canonical digits 1/8 on only 30/60 pairs. Those values
are counts, not fixed output color roles. The nine-cell counterexample must
legitimately output 9. Requiring every teaching example to introduce 1 or 8
would conceal the very same-area distinction the repair is intended to teach.
The final battery's actual warnings govern the handoff; no warning is silently
waived and no training admission is claimed.

## D8 — A bounded, separately proposed rule parameter

`workspace/parametric/prototype.py` chooses one `output_order` per episode:
canonical `outer_to_inner` or proposed `inner_to_outer`. The default program
bytes are unchanged; the alternative reverses only the final strip expression.
The diamond's actual executed outputs are `[[8,4,1]]` and `[[1,4,8]]`.

Seeds 1 and 0 materialize the two different settings. Each episode has two
non-palindromic demonstrations and one query; both demonstrations independently
reject the other declared setting. Both programs and every label/rival are
executed through Racket. Public files contain only demonstrations and query
inputs; parameters, rules and query answers are separate evaluator files.
The prototype uses only three templates and two settings, and remains a
proposed experiment, not a production training generator.

Portable public helpers and runtime-manifest mappings replace fixed parent-depth
paths. An actual isolated test run is required because a repository-only pass
would not exercise the execution layout. Historical startup/path-authoring
failures and the eventual portable passes remain in the evidence.

## D9 — Reusable tooling and lossless evidence

The optional minimal-probe patch has focused red/green tests and actual copied-
runtime linter integration. It remains an independent maintainer decision.
The area-lookup rescorer works from retained Racket labels and saves exact
ambiguous lessons without executing private runner functions. The evidence
archive CLI uses explicit roots, deterministic gzip, path/size/SHA mappings,
verified round trips and conflict refusal. Its task-local tests cover corruption,
traversal, symlinks and restoration. No full runtime or virtual environment is
transported in the small return.

Large reports may be compressed only after their consumers have finished.
`checks/ARCHIVE-MANIFEST.json` and the tool README describe restoration. Every
failure keeps a lossless retained copy. The official packet builder creates the
source patch, intake metadata and final ZIP; a hand-authored return is not used.

## Handoff limits

The final stock battery, isolated task tests, exposed solve and independent
fresh-extraction replay are separate pieces of evidence, with exact commands
and statuses in `RESULTS.json`. A passing regression or census does not turn a
warning-blocked aggregate into a pass. Acceptance remains a maintainer decision;
canonical authority and training approval are unchanged.

## D10 — correct the imported task summary before replay

The imported SUMMARY.md still described cumulative remaining counts. Its allowed task-local documentation was corrected to exact removed-cell counts, the reviewed version, witness policy, and the two remaining stock warnings before constructing the replayed patch. This documentation-only change does not change generator bytes, the final solve binding, or the canonical authority. The final patch replay verifies SUMMARY.md along with every other changed path.
