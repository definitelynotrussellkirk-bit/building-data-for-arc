# Working notes: b1972482cb43

## Native parametric family prepared in this review

`workspace/parametric/` adds `rule=point|visible_span_echo` without editing the
approved canonical generator or its reference authority. The default returns
that exact Racket text. The alternative computes the clipped first reflection,
measures its visible height/width, then echoes that clipped set across the
anchor row when height >= width or across its column otherwise. Equal spans
choose the row. Both the branch and the cells available to B depend on A.

Three constructive demonstrations teach a clipped plus, a complete equal-span
L and a clipped tall L. The third is necessary to reject bringing clipped-away
cells back into the grid; choosing the source aspect before clipping is a
separate rival. The sampler checks the actual three-demo lesson against 12 point
and 20 echo rivals for both settings, with settings-independent inputs and
bounded retries/fallback. The family supports 3–6 demonstrations, 1–4 independent
queries and a separate 2–240-cell connected-shape grammar up to 30×30. A query
stream preserves identical one-query and four-query first turns. Production's
old four-demo/one-query teaching contract below still describes only production.

`workspace/parametric/probe.py` replays labels and rivals through protected Racket
and checks public identifiers and reveal projections. See the task-local source
inventory, the native qualification/execution and causal replay in
`WORK/checks/b1972482cb43/`, and `WORK/RESULTS.json` for observed results. This is a
finite-rival claim and a reviewer-ready owner handoff, not acceptance or training
admission. The owner must qualify/accept exact integrated bytes.

## Current rule and authority

Version 2.0.0 preserves the input and reflects each shape cell through the unique
color-9 anchor: `(r,c) -> (2*ar-r, 2*ac-c)`. Reflection is a half turn, and clipping
is per cell. A partially off-grid reflection still contributes its visible cells.
Color 9 is a fixed symbol; colors 1–8 are interchangeable shape colors. Zero is
background. The canonical Racket authority is unchanged and pinned by
`RULE_HASH = "add600b28dfb"`. Python geometry supplies input-selection diagnostics
and rival predictions, never exported labels.

## Domain and controls

The validator requires nonempty rectangular Python lists, dimensions 1–30,
integer cells 0–9 excluding Booleans, exactly one 9, and a 4-connected,
monochromatic 2–5-cell shape. Original and reflected shapes must be disjoint,
and at least one reflected cell must be visible. The sampler uses the narrower
size domain of heights 4–12 and widths 5–14. Overlap, multiple shapes, multicolored
shapes, and entirely off-grid copies are outside ordinary generation. All three
canonical inputs pass this domain check.

All legal size overrides are exact in all bands. Unoverridden sizes mix a
canonical-size component with a band-biased component, retaining every advertised
size. `strict_canonical_like` checks domain, height 5, and width 7 or 8; it is a
size/color profile, not an exact-input or exact-shape recognizer. See the final
profile receipt for measured support rather than assuming a guaranteed fraction.

`palette_kind` and helpful `texture` values are aliases. Families are
`default` = 1–8, `warm` = 2/4/7, `cool` = 1/3/8, and `varied` = 5/6.
Disagreeing explicit aliases raise an error and are declared incompatible.
`palette_size=2` counts foreground colors; `n_distinct_colors=3` includes zero.
These are fixed diagnostic controls, as are `density=sparse` and the retained
legacy `position_bias=shape_then_anchor_offset` token. Unknown axes, incorrect
types, and unsupported values fail explicitly. The position token does not
promise a separate selectable spatial distribution.

Negative textures `no_anchor`, `no_shape`, and `reflection_oob` are intentional
diagnostic calls, excluded from ordinary helpful texture values. The last fixture
now really places every reflected cell outside the grid.

## Teaching schedule and its proof boundary

Four demonstrations and one query use five consecutive accepted draws with one
seed and constant valid overrides. The declared period is five:

| Index modulo 5 | Profile | Required evidence |
| --- | --- | --- |
| 0 | Interior | Plus with a visible reflected center |
| 1 | Clipped asymmetric | Partial copy refuting every non-outline rival |
| 2 | Interior | A second visible-interior witness |
| 3 | Clipped asymmetric | A second clipping/asymmetry witness |
| 4 | Broad | Symmetric small shape, or a complete asymmetric reflection |

Every five consecutive positions contain two witnesses of each required kind.
Each repeated profile receives consecutive shape colors within a palette of at
least two colors. Different profile classes cannot share an input: only the
interior class has a plus interior; clipped asymmetric shapes are asymmetric and
partially clipped; broad asymmetric copies are complete, while broad symmetric
shapes have different geometry. All five inputs are therefore distinct, including
across the period boundary, so duplicate rejection cannot remove a witness.
Holding out any one pair leaves a refuting demonstration for every declared rival.

The canonical shortcuts are fixed anchor `(2,3)`, grid center
`(h//2,(w-1)//2)`, all-or-nothing clipping, outline-only copying, and copying only
the source half-plane at or left of the anchor column. Each fits all three stored
canonical labels. Six further rivals cover identity, horizontal/vertical
reflection, reflection without retaining the original, anchor-colored copies,
and translation without rotation. Namespaced aliases are not independent rivals.

Random placement is bounded to 256 attempts. Constructive fallbacks satisfy the
same profile predicate at every advertised size, including 4×5. A fallback never
silently returns an invalid negative example.

## Decisions reversed during this review

The imported 1.2.1 source had no explanatory design notes, so the reasons for its
size defaults, ignored controls, and limited templates are unknown. Its ten shape
motifs remain reachable. The five-cell plus was added to distinguish outline
copying on this small connected-shape domain.

An initial two-profile repair overconcentrated lessons on plus and clipped
asymmetric witnesses. Self-review restored dominoes, lines, squares, and other
symmetric shapes through a fifth broad slot. A second correction restored
complete asymmetric copies; otherwise fully visible canonical motifs would have
been excluded. `test_lesson_support.py` preserves both genuine failing iterations.
The final contract covers a period-5 schedule, not the superseded period-2 draft.

The first after battery was advisory because the short schedule had not been
explicitly enumerated. Subsequent full batteries consume a complete source-bound
fixed-seed receipt and require query-rotation identifiability. Earlier failing and
advisory evidence remains in this review return.

A supplemental rival search found that the ten-rival draft still allowed a
canonical-fitting left-half-plane rule to survive 7/300 production lessons and
53/1,500 query rotations. The new rival includes the anchor column, as required
by a canonical source cell on that column. It is now an executable declaration,
so each clipped witness must refute it as well. The right-of-anchor fallback is
already a counterexample. The exact old lesson, failing regression, and new-source
verification are retained rather than treating the earlier finite-rival pass as
universal evidence.

## Reproducers, checks, and limits

`counterexamples/reflection_witnesses.json` contains three small inputs with fresh
canonical Racket outputs. The 4×5 clipped plus refutes the original four canonical
shortcuts together. The 4×5 corner L also refutes left-half-plane copying.
`workspace/probe_reflection_lessons.py` dynamically reads the live declarations,
checks canonical fits, all cyclic starts, distinct witness inputs, and every
single-query holdout. It rejects missing, empty, and malformed contracts.

The return for review `review-94649ff728f83147` contains source-bound full before
and after batteries, portable task tests, a 100-lessons-per-band production census,
query rotations, fixed-seed schedule enumeration, independent source review,
fresh-copy patch replay, and separate blind/post-repair solve records. Final
counts and exact command evidence are in `REVIEW.md` and `RESULTS.json` in that
return. A passing check does not change training approval.

The contract does not cover fewer than four demonstrations, more than one
held-out query, changing overrides inside a lesson, or every undeclared rule.
Generic label-mutation diagnostics are reported separately with exact recipes;
they are not automatically independent executable solvers. Their remaining scope
is discussed in `checks/lesson-design/searched-rival-findings.md` in the return.

Imported associated notes retain their original evidence and timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `5de19b883ae5a9875abc09824ca005cdae155d345506898b60b2f0df382bf76d`.

# Decisions and evidence

## Scope and baseline

The immutable draw selected repair `b1972482cb43`, blind solve `a3086dea6cff`,
question `generator-shortcuts`, and audits `7e7614405852` and `e1d032e35937`.
The input ZIP was verified before the draw. The blind solve finished before the
repair source or rules were opened. Audit selections were drawn once after initial
repair work. No assignment or authority was changed.

The imported generator was version 1.2.1, SHA-256
`78578d4744d8b087982109ad829d4abd88c5b00c545155f80d88074e2da666fa`.
Its placeholder notes contained no design rationale. Reasons for its earlier
sampling restrictions are therefore unknown, not inferred as intentional policy.
There was no selected task root regression fixture to migrate. The selected
source and its notes/tests/workspace/counterexamples are the only code delta.
Both audit sources remain unchanged.

## Distribution decisions

| Area | Evidence/problem | Decision and alternative considered |
| --- | --- | --- |
| Grid validation | Ragged/scalar/non-integer grids crash or pass; shape and reflection assumptions are missing. The initial 67-case regression run had 44 failures and 23 passes. | Validate representation, colors, unique anchor, cardinality, connectivity, monochromatic shape, disjointness and visible copy. Return diagnostic strings instead of guessing through malformed data. |
| Dimensions | Advertised dimensions are rejected by band-specific defaults; canonical exact support is 5/60, confined to easy. | Honor 4–12 by 5–14 exactly in every band. Mix canonical-size and band-biased draws. Every advertised size retains support, avoiding a repair limited to copied canonical layouts. |
| Colors | Palette/texture controls were ignored; diagnostic counts were misleading. | Keep 9 fixed, cycle colors within explicit families, reject conflicting aliases, distinguish two foreground colors from three total colors. A multicolored source would change the intended object domain and was rejected. |
| Shape geometry | All original motifs have no four-neighbor interior, permitting outline-only copying. | Add a five-cell plus with a visible copied center. Retain original small motifs; do not make every input a plus. |
| Clipping | Canonical pairs do not distinguish individual-cell clipping from dropping a whole off-grid copy. | Require two partially clipped asymmetric witnesses in each five-pair lesson. Preserve complete copies in the broad slot. |
| Anchor placement | Fixed-anchor and grid-center rules fit all canonical pairs. | Make clipped witnesses actually disagree with both rivals, rather than merely checking that anchor coordinates moved. |
| Source side | A supplemental independent rule using only cells with `c <= anchor_c` fits all canonical labels and survives some ten-rival lessons. | Add that exact rival and require visible right-source evidence. Including the anchor column is essential to the canonical-fit claim. |
| Fallbacks | An invalid or generic fallback could break both domain and lesson guarantees. | Bound random placement to 256 attempts and use a lawful constructive fallback for each profile. Each works at the minimum 4×5 and larger advertised sizes. |
| Negative fixtures | `reflection_oob` was not actually entirely off-grid; negatives appeared in ordinary axis support. | Make names truthful, honor requested sizes, and reserve explicit negative textures for diagnostics. |

The scale branch gives equal weight to canonical-biased and broad-biased
components; it does not promise half of individual outputs have canonical sizes.
Dimension weights still include the full legal range. Final profile evidence is
31/60 exact and envelope hits: 9 easy, 11 medium, 11 hard, with no crashes or
warnings. This exceeds both the pooled floor and the per-band requirement.

## Lesson assembly and duplicate rejection

The exported contract uses **four demonstrations and one query** from five
consecutive accepted draws, with a fixed seed and constant valid overrides. The
schedule is interior, clipped asymmetric, interior, clipped asymmetric, broad.
It is valid for every cyclic starting offset and every single-pair query position
against its eleven declared alternatives.

A visible-interior plus necessarily refutes outline-only copying because its
reflected center remains in bounds and cannot overlap the original. A clipped
asymmetric witness is accepted only if each of the other ten rivals disagrees
with the intended point reflection. Two witnesses of each type leave at least
one refuting demonstration after any one pair is withheld.

The production worker filters duplicate inputs, so profile frequency alone was
not enough. For each seed, the palette family is stable; the two occurrences of
each witness profile receive consecutive colors, including across a period wrap.
Every family has at least two colors. The three classes have disjoint geometry:
only the plus has an interior; the clipped asymmetric class is partially clipped;
broad asymmetric copies are complete, and broad symmetric shapes are symmetric.
Thus all five inputs differ and neither witness is silently filtered out.

This is a bounded teaching construction. It does not certify lessons with fewer
demonstrations, more held-out queries, mid-lesson changes of overrides, or every
possible hypothesis. The official post-repair solve presents two masked queries;
that exposure record is distinct from the one-query identifiability contract.

## Rejected and superseded designs

The first repair used only alternating interior and clipped asymmetric profiles.
It repaired the named geometric shortcuts but lost easy symmetric-shape support.
A genuine red test motivated adding the broad fifth slot. Initially making that
slot symmetric-only still excluded complete asymmetric motifs, including canonical
shape families; another red test motivated allowing complete asymmetric copies.
The final broad branch preserves all ten predecessor motifs.

The d43 revision passed the original ten-rival census, all required gates and
69 focused tests. A further search then found the left-half-plane rival. Its
saved-label scores were 7/300 ambiguous production lessons and 53/1,500 ambiguous
rotations. We retained those exact failures and added an independent regression
before changing the generator. The failing five-pair recipe had agreements
TTTTF; the repair produces TTFTF. The final declaration has 11 distinct rivals,
21 public namespace bindings, and 16 bindings in the local probe's two namespaces.
These counts are not interchangeable.

The old ten-rival probe, source review, public solve episode, and full census
remain explicitly labeled as prior evidence. They are not rebranded as verification
of the final generator. The initial after battery's missing schedule-enumeration
advisory also remains retained. The release battery consumes the exact full
schedule receipt rather than a compact summary.

## Label authority and independent evidence

The canonical rule `add600b28dfb` is unchanged. Its stored program SHA-256 is
`add600b28dfbb75042e9e8a10b68d027ca52ea1fe78d57ad42b0b3bac74344d6`.
The executed wrapper text has a different, separately reported hash; these are
not interchangeable source identities. The before/after authority audit reports
selected authority synchronization and execution parity. It also notes an
existing archival raw-code textual divergence, which was not rewritten.

The local probe uses an independent Python reflection model for generated draws,
calibrated against all three stored canonical labels and three freshly executed
Racket fixture labels. The 300-lesson public census supplies authoritative
Racket-generated labels for the larger population. Every exact command and its
source/runtime binding are retained. Python diagnostic predictions are labeled
as such and do not become training labels.

Final production and rotation counts are 300/300 and 1,500/1,500, with no declared-
rival ambiguity, hook warnings, materialization errors or scoring errors; there
are 1,469 globally unique input grids. Fixed-seed enumeration separately covers
15 lessons and 75 rotations: all five starts at seed 0 in three bands. Its 13
unique inputs reflect intentionally overlapping windows and repeated band support,
not within-window duplicates. The reporting modulus of a random census is not
the generator's declared schedule period.

## Self-review and residual findings

The repair intentionally correlates witness classes, clipping, colors, and
schedule positions. Restoring the broad slot avoids unnecessarily removing
symmetric and complete asymmetric inputs, while the distinct-input proof prevents
that restoration from weakening the stated holdout guarantee.

Generic spatial label mutations remain advisory leads in the final census.
Their input-only realizations and exact production/rotation counts are explained
in `checks/lesson-design/searched-rival-findings.md`. They fit zero of the three
canonical labels and are outside the declared-rival guarantee. The report retains
those finite ambiguities; it does not conclude that every lesson uniquely teaches
every conceivable rule. Training approval remains unchanged.

The broader repository run, performed on the d43 revision, had 970 passes,
16 failures and 3 missing-Torch skips. All 16 failures reproduced against the
untouched input ZIP using an independent environment; 25 relevant source files
were byte-identical across upload, pristine extraction, and repaired workspace.
The process-namespace capability failures, two archival expectation mismatches,
and two fixed-message/argv expectations are reported in
`checks/repository-suite-review/report.md`. No shared code or frozen test was
changed to force a repository-wide pass.

## Handoff and reproduction

The return builder creates the exact source patch and hash-bound intake. That
patch is checked and applied from the Git root of a fresh original `WORK/`.
Every changed path, including new tests and tools, is compared byte for byte.
Focused tests and a public Racket probe are rerun in that relocated copy with its
own environment. Final receipts are under `checks/patch-replay/` and `RESULTS.json`.

Large exact evidence is retained as deterministic gzip plus native size/hash
manifests. The original bytes remain verifiable and restorable. Only the compact
builder-produced delta ZIP is returned. The blind solve, prior post-repair solve,
final post-repair solve, and genuine setup failures retain their own provenance;
masked-query correctness is always unknown to this reviewer.
