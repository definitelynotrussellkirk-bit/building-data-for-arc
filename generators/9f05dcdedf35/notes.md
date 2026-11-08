# Current decisions: 9f05dcdedf35 — v1.4.1

The canonical Racket rule remains unchanged (`85fa63b64c3c`): recolor leaf
components, defined by degree 1 in the canonical contact graph, to 8. Count
neighboring **objects**, not distinct neighboring colors. Prior audit material
was a lead; current-source reproduction and canonical pairs remain authoritative.

## Repair and reversal

The supported validator domain is an integer rectangle of size 1–30 with a
changing non-8 leaf, an interior component and an isolate. It accepts canonical
degree-4 examples, L-shaped objects and input 8. Generated support is narrower:
maximum degree 3 and main-object span at most 2 do not cover arbitrary large shapes.

The six active axes are height 8–14, width 8–16, palette size 5–6, orientation
(chain axis / branch stem), family (chain / branch), and main-object span 1–2.
Retired no-op axes and degenerate settings are rejected. Unrecognized difficulty
hints retain neutral handling for compatibility.

The period-4 schedule uses teaching branches at positions 0 and 1, followed by
ordinary positions 2 and 3. Positions 0 and 2 use canonical dimension/palette
triples; positions 1 and 3 use the broad size range. Teaching draws use full
2×2 branch layouts: 7 objects with palette 5, or 8 with palette 6.
They include a same-color leaf/isolate distinction and preserved input 8.
Ordinary scenes have 5–7 objects, including L shapes; 8 is optional in any role.

**Reversal:** the initial v1.4.0 family did not adequately teach `neighbor_colors`,
which counts distinct neighboring colors and nevertheless fits the canonical
pairs. It survived demonstrations but disagreed on 32/300 production queries and
138/1200 rotated queries. In v1.4.1 teaching branches, center and end colors are
forced equal while remaining separate objects: the stem touches two objects of
one color. This distinguishes object degree from distinct-color count.

Ten distinct rivals are retained under 22 namespaced declarations: 10 semantic,
10 lesson, and two canonical shortcuts (`nonmax_degree`, `neighbor_colors`).
Strict named-rival checks provide finite evidence, not universal induction.

## Evidence status

Initial before evidence recorded five failures. Earlier v1.4.0 receipts (source
prefix `80fe…`), including historically named `final` files, remain retained;
identify them by source hash rather than filename. Their palette-8 lint population
had 39 cases already containing 8 and 21 introducing it globally, while all 60
had visible 8 marking. The check confuses globally new color with painting a
component. These figures are historical and are not asserted for v1.4.1.

Final v1.4.1 source SHA-256 is
`32eae1598eb032fa4de9d4af7c65aa2113405e9c392b5a8398b2071d5a135ecc`.
The task-test stage passes 99 tests (64 semantic/fixture tests and 35 coverage-tool
tests). The joint probe checks 8,064 controlled draws plus 48 defaults, and its
51 actual Racket comparisons agree. The 300-lesson census has 1,200 unique inputs
and no ambiguity in production or 1,200 query rotations against ten rivals.
Fixed-seed enumeration covers all four starts per band: 12 lessons, 48 rotations,
11 distinct inputs, with no measured ambiguity. These results are in
`checks/main-probe/*-v141.json`, `checks/lesson-census-repaired.json`,
`checks/schedule-census-repaired.json` and `checks/task-tests-final/result.json`.

The unmodified battery remains 11/12 green: defect lint flags 15/60 globally new
8 palettes even though all 60 actual Racket outputs visibly recolor leaves; 45
inputs already contain 8. The separate optional paint-color patch has 15 passing
tests and removes this finding on those same saved outputs. It is **not active**
in the main delta; acceptance needs a detector correction or an explicit waiver.
The offline coverage checker also passes on the final census, reports refuting
candidate sets honestly, and does not invent exact witness counts. Neither tool
changes the authority or establishes universal proof or training approval.
## Current reviewer considerations

Source SHA-256: `32eae1598eb032fa4de9d4af7c65aa2113405e9c392b5a8398b2071d5a135ecc`.

# Decisions — review-7e879c7a94298103

## Authority and scope

The selected rule remains `85fa63b64c3c`; no Racket, canonical ledger, shared implementation or audit-target source is changed. Original generator v1.3.0 SHA `949d042cb869e5a6cff8bc84d327ffcaab65235ab4a01564469d3791436ce0eb` becomes v1.4.1 SHA `32eae1598eb032fa4de9d4af7c65aa2113405e9c392b5a8398b2071d5a135ecc`. The final version includes an independently discovered correction to the intermediate v1.4.0 design.

The user authorized the same complete random-review procedure. Routine, reversible implementation choices were resolved within that scope; no extra approval step or assignment reroll was introduced. Code, tests and utilities were built, not merely proposed. Optional shared-tool adoption is kept as a concrete separate patch because the task delta permits selected-task edits only.

## Input choices and alternatives

| Choice | Prior rationale / behavior | Current decision and reason | Probe / limit |
|---|---|---|---|
| Object definition | Existing helper used monochrome four-connectivity; generation reduced each object to one pixel | Preserve the authoritative definition; count distinct neighboring component IDs | Canonical pairs, independent graph oracle and actual Racket labels agree |
| Multi-cell support | Source comment emphasizes singleton chains for diversity; broader shape restriction rationale unknown | Main tiles span 1 or 2; ordinary 2×2 tiles can become connected L shapes without changing their graph | Multi-cell leaves refute pixel degree; wide contacts refute contact-edge count. Arbitrary larger components remain unsampled |
| Graph families | Straight chains of 3–4 singletons | Four-node chain, or five-node branch with degree 3 and a degree-2 stem; isolates supply degree-zero contrast | The nonmaximum-degree rival fits canonical stars/chains but fails the branch stem. Generated maximum degree remains 3 |
| Input 8 | Explicitly excluded to avoid hiding the operation and presumed confusing preservation | Permit 8 everywhere in semantic validation. Default teachers include a preserved isolated 8; ordinary draws may omit 8 or use it in any role | Original canonical test rejection reproduced. A non-8 changing leaf is always required |
| Repeated colors | Main and distractor colors drawn distinctly | Repeat colors across disconnected objects. Teachers have a leaf sharing color with an isolate and center sharing color with a nonadjacent end | Distinguishes global color repainting and, after revision, neighboring colors from neighboring components |
| Teaching object count | Initial repair fixed seven | Palette-5 teachers have 7; palette-6 teachers have 8 to satisfy both repeated-color contrasts plus exact palette size | Third isolate fits the 8×8 boundary. Ordinary count varies 5–7 to retain smaller morphology |
| Dimensions | Defaults 8–11 by 10–13; advertised range partly inconsistent with orientation placement | Exact height 8–14 and width 8–16; allow boundary placement. Core slots use (9,11,5), (8,12,5), (10,12,6), with the last value counting foreground colors | Native profile floor counts background too: 6/7 total colors. Final support is 10/20, 10/20, 9/20 per band |
| Palette | Advertised size 3–4 ignored; eight non-8 color identities sampled | Exact 5–6 distinct foreground colors; all selected colors realized; touching objects always differ in color | Exhaustive joint controls; adjacent equal colors would merge components and are forbidden constructively |
| Orientation | Working horizontal/vertical behavior had an unprobeable `choice` declaration | Retain behavior, declare a string enum. For chains it is the chain axis; for branches the center-to-stem axis | Independent pixel-derived observer tests both orientations, including minimum dimensions |
| Other controls | `palette_kind`, `position_bias`, `n_distinct_colors`, `density` were ineffective; texture degenerates bypassed normal generation | Retire them and reject unknown/invalid controls; None means default, booleans/floats/text do not coerce into integer axes | All malformed/retired-axis regressions and unknown-key native probe pass |
| Difficulty | Existing API accepted arbitrary hints | Easy/hard weight smaller/larger broad sizes; the whole advertised range remains legal in every band. None/unrecognized hints keep neutral weighting | No new incompatibility for legacy numeric/unrecognized hints; only the three named bands have reported census guarantees |
| Validator | Required two leaves plus isolate, rejected any 8; malformed rows could raise | Rectangular integer 0–9 grids, 1–30 dimensions, a changing leaf, an interior component, an isolate; ignores metadata as an exemption | Accepts all canonical inputs, degree-four graphs, L shapes and repeated colors. No claim that all executable Racket grids belong to this teaching subset |

## Lesson assembly and the failed intermediate design

`LESSON_SCHEDULE_PERIOD=4`, `EXAMPLES_NEEDED=3`. Residues 0 and 1 are full-square teachers; residues 2 and 3 are ordinary draws. Residues 0 and 2 use a canonical size/palette profile; residues 1 and 3 use broad dimensions. Explicit exact controls override these defaults and can intentionally remove teaching witnesses. The complete default-lesson guarantee does not apply to arbitrary user-forced lesson axes.

Each default teacher independently refutes all ten declared competitors. Any raw four-consecutive-sample window therefore has two refuting teachers, leaving at least one when any single pair is held out. This argument is about the schedule, not a proof of production materialization: duplicate/invalid inputs can advance indices. The actual public materializer was checked with 300 lessons / 1,200 rotations and fixed-seed enumeration of all four starts in all three bands.

In v1.4.0, only palette 5 repeated the center and end colors. Palette 6 used all distinct main colors to realize its palette with seven objects. Independent review showed the resulting neighboring-color rival fits all three canonical pairs yet causes 32/300 ambiguous production lessons and 138/1,200 ambiguous rotations. Retaining only the original nine rivals would have hidden this. `checks/final-review/neighbor-colors-v140/` preserves the exact lessons and independent rescore.

The rejected alternative was to restrict teachers to palette 5, which would weaken the exact control and profile support. Instead, v1.4.1 repeats center/end in both palettes and puts palette 6's extra color on an additional isolate. The repaired independent rescore has zero ambiguities in both populations, with two refuting examples in each materialized lesson. Actual before/after same-argument Racket cases are retained in `neighbor_colors_teaching.json`.

## Rival scope

The ten hypotheses cover pixel degree, contact-edge count, nonmaximum degree, degree at most one, all touching objects, global repainting of leaf colors, distinct neighboring colors, deletion of input 8, identity, and diagonal contact. They are deliberate wrong competitors, never label authority. Ten semantic and ten lesson declarations plus two canonical-shortcut declarations produce 22 namespaced records; namespace duplication does not multiply the number of hypotheses.

Seven distinct rivals are refuted by canonical labels. Global repainting of leaf colors, nonmaximum degree and neighboring-color count fit the canonical set but are refuted by generated teachers. The new offline gate handles the first category's missing support; the existing lesson scorer handles a surviving rival that disagrees on a query. Neither mechanism discovers every possible rival or proves universal identification.

## Remaining detector warning

The final strict battery is honestly failed at one stage: 11/12 are green. `transformation_drift` requires palette novelty, while preserved input 8 is an intended distinction. On the exact final 60-draw population, all 60 outputs visibly paint leaf cells to 8, but only 15 introduce 8 globally because 45 inputs already contain it.

Removing the preserved-8 teachers to appease that heuristic was rejected: it would recreate the canonical support defect and weaken rotation-safe teaching of preservation. The separate patch instead records newly painted colors for same-size grids, keeping untouched-color and identity negatives and the old thresholds. It leaves resized-grid correspondence conservative. Fifteen tests and the exact retained Racket population support that correction. Main shared source stays unchanged; adoption or waiver is the explicit remaining maintainer decision.

## Evidence, resources and reproducibility

Test-first failures remain: 33/54 against v1.3.0; 9/63 when the new rival was added against v1.4.0; coverage-tool missing-module and malformed-record failures; optional detector patch's 9/15 red cases. These are genuine development failures, not invented solve attempts. The audit helper's mistaken initial radius assumption is also preserved.

The original packet and pinned source were verified before drawing. A previous round's completed replay tree was reset to the original manifest to avoid another full copy on the full disk. The once-drawn contract was checkpointed. The final patch replay passed on a freshly extracted original baseline with its own Git root: native verification covered 59,760 WORK files, exact patch check/application succeeded, and the 99 focused tests passed with no failures, errors or skips. All 12 patched source hashes and 59,747 unchanged original repository files matched. Its exact commands, runtime paths and source checks are retained in `checks/fresh-replay/` and RESULTS. The existing Python venv and Racket binary were reused; source imports came exclusively from the fresh repository while the old source repository was absent. This verifies independent source replay, not an independent dependency installation.

The full deliverable is the native small delta ZIP. Large check evidence is packaged with the native evidence-bundle mechanism, retaining original paths and hashes. No environment, full repository tree or unrelated prior return is included.

## Compressed evidence

Three large reports retain their original logical paths in this document: `checks/coverage-tool/actual-final.json`, `checks/coverage-tool/actual-repaired.json`, and the historical `checks/lesson-census-final.json`. Their exact bytes are returned as `.json.gz` files. After extracting the native evidence bundle, run `python3 checks/restore_evidence.py` from WORK to restore them without overwriting differing files. `checks/COMPRESSION-MANIFEST.json` records original/compressed paths, sizes and SHA-256 hashes. The round-trip verification passed for all three. The final `checks/lesson-census-repaired.json` remains directly readable.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/9f05dcdedf35/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
