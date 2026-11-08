# Working notes: 3108da8bf9e8

## Frozen-baseline finding

The original generator correctly avoided tied sort keys, but hard-coded occupancies `0..8`. Canonical inputs select nine values from `0..9` and omit `[0,9,2,1]` across the four pairs. Baseline consequences:

- `self_check` rejected 3/4 canonical inputs.
- Generated data always omitted `9`.
- Nine advertised axes were mostly fixed, inert, aliases, or invalid degenerates.
- Override audit: 3,275 findings in 10,620 draws; unknown keys accepted.
- Semantic gate: `NO_CONTRACT`.
- Cached Racket authorities differed from canonical only in exact formatting; execution parity passed.

Evidence is retained under `checks/before/`.

## First-round repair

Version `3.0.0` replaced the misleading control surface with one lawful, exact axis: `omitted_count` in `0..9`. Every output has nine unique one-counts, exact override realization, and a recoverable observation. It added strict validation, a Python rule mirror, canonical parity checks, semantic rivals and witnesses, and task-local regression tests. The cached Racket `raw_code` and `target_code` were normalized byte-for-byte to the canonical program; no semantic Racket rule changed.

That pass fixed validity and support, but its hand-authored difficulty and texture families still contained unnecessary shortcuts.

## Second-round adversarial finding

The first-round generator passed all 12 repository stages, yet a position-map census found two simpler rules that solved whole bands:

- **Easy:** sorting only inside each existing macro-row matched 200/200 draws. Only six normalized input-position→output-position maps appeared.
- **Hard:** blindly reversing the three macro-rows matched 200/200 draws. One fixed position map appeared and survived all four examples in 96/96 sampled lessons.
- **Textures:** counts 1 and 8 exposed only 8/9 lawful masks, and most easy/hard interior counts exposed only eight masks, because the sampler permanently reserved a cell pattern to manufacture a repainting witness.

Reproduction: `checks/round2-shortcut-baseline-report.json` and `checks/round2-shortcut-baseline-console.log`. The subject hash in that report pins the first-round generator to `2d4ba9c…`.

## Second-round repair

Version `3.1.0` keeps the intended ranking curriculum while removing the fixed shortcuts:

- easy performs one cross-macro-row swap from the answer layout, so exactly two positions are displaced but row-local sorting cannot solve it;
- medium samples broad permutations with five to eight displaced positions;
- hard samples full derangements with all nine positions displaced;
- medium and hard reject solved order, top-left ascending order, row-local sorting, and fixed macro-row reversal;
- exact-count textures are sampled uniformly from all `C(9,k)` masks;
- only an all-prefix **joint** draw is repaired, preserving full marginal support while ensuring the repaint-by-count rival differs somewhere;
- the semantic contract now names five rivals and five witnesses, adding `sort_within_macro_rows` and `reverse_macro_rows`.

## Reusable shortcut census

`workspace/shortcut_census.py` measures:

- normalized rank-position maps and their reuse;
- rank displacement by difficulty;
- exact matches for all declared rivals;
- omitted-count support;
- exact texture-mask support by occupancy;
- whether one fixed position map fits all demonstrations or survives the query.

A 400-draw-per-band and 96-lesson-per-band run passed every threshold. Easy exposed all 27 legal cross-row swap maps. Medium and hard each exposed 400/400 unique maps. The two discovered shortcuts matched 0/1,200 draws. No fixed map survived all four examples in any of 288 lessons. Counts 1 and 8 covered all 9/9 masks in every band; counts 2 and 7 covered all 36/36. Evidence: `checks/round2-shortcut-census-report.json` and `checks/round2-shortcut-census-console.log`.

The census itself has a regression for error accounting: three valid draws that each trigger two rival exceptions must still report three valid draws, not `-3`. Red/green evidence: `checks/round2-valid-draws-red.log` and `checks/round2-valid-draws-green.log`. A second synthetic regression proves that one-mask-per-occupancy texture collapse fails the tool: `checks/round2-texture-threshold-red.log` and `checks/round2-texture-threshold-green.log`.

## Third-round adversarial finding

Version `3.1.0` still made the easy band locally identifiable without the intended nine-block comparison. Sorting only inside each macro-column solved 135/400 deterministic easy draws. More generally, there are 280 unlabeled ways to partition the nine macro-positions into three triples and sort only within each triple. Every easy draw was solved by exactly 70 of those local decompositions. Across 256 four-example lessons, at least one fixed three-triple decomposition fit all three demonstrations in 201 lessons; the query refuted at least one survivor in 178. Medium also admitted such a decomposition on 37/400 individual draws and hard on 5/400, even though none survived three demonstrations in that sample.

Reproduction: `checks/round3-local-partition-baseline-report.json`. The earlier 53-test suite remained green, demonstrating that named rivals and exact-map diversity did not cover this hypothesis class.

## Third-round repair

Version `3.2.0` replaces easy transpositions with one four-cycle whose moved positions span every macro-row and macro-column. Only four blocks move, retaining a distinct easy band, but a four-cycle cannot be contained in any three-cell local group. Medium and hard now also reject candidate permutations whose cycle decomposition can be packed into three invariant triples. The semantic contract adds `sort_within_macro_columns` and a matching witness.

`workspace/shortcut_census.py` is upgraded to schema v2. It enumerates all 280 three-triple partitions, counts how many solve each draw, intersects their survivor sets across demonstrations, records row/column movement support, and fails if any draw or lesson admits the local hypothesis class. `workspace/verify_cycle_partition_equivalence.py` independently checks the production cycle-packing predicate against brute-force bin assignment for all 30 integer partitions of nine.

The final 400-draw-per-band census reports 213/399/400 distinct maps for easy/medium/hard, zero column-local matches, zero three-triple local solvers in all 1,200 draws, and zero local or fixed-map survivors in 288 lessons. Every easy draw moves four positions and touches all three rows and columns. Evidence: `checks/round3-shortcut-census-report.json`, `checks/round3-local-partition-final-report.json`, and `checks/round3-cycle-partition-equivalence.log`.

## Test-first evidence

- Frozen baseline: 46 failures and 1 pass before the first repair; then 47/47 passed.
- Second-round shortcut tests: 3 failures with 47 existing passes; then 50/50 passed.
- Missing census tool: 1 failure with 50 existing passes; then 51/51 passed.
- Census accounting regression: 1 targeted failure, then pass.
- Collapsed-texture threshold regression: 1 targeted failure, then pass.
- Second-round final focused suite: 53/53 passed.
- Third-round locality tests: 6 failures with 51 existing passes, then 57/57 passed.

Retained logs are under `checks/test-*.log`, `checks/round2-*.log`, and `checks/round3-*.log`; final commands are recorded in `RESULTS.json`.

## Final repository evidence

The third-round required battery is green on all 12 stages. The semantic gate reports 600/600 strict-lawful draws, six strong witnesses firing on 600/600 draws, all six rival claims holding on every checked case, no surviving named competitors, no weak witnesses, 12/12 identifiable lessons, and no warnings or errors. Override, profile-floor, lint, grammar, Racket, and authority-sync stages are also green. See `checks/round3_final/` and `checks/round3-final-battery-console.log`.

## Reviewer solve

The final fresh solve used only `solve/challenge.json`, reviewer-authored Python, and visible check feedback during the episode. A challenge-only tile-count probe identified the global whole-block sort; revision 1 matched all three visible examples. Earlier rule exposure is honestly recorded `yes`, reference consultation during solve is `no`, and masked-query correctness remains withheld. See `solve/SOLVE_NOTES.md` and `solve/summary.json`.

## Remaining questions

- Difficulty labels encode structural displacement, not model-calibrated Qwen accuracy.
- Uniform omission and texture sampling are breadth policies, not inferred natural frequencies.
- Easy is a four-block correction curriculum with 270 legal cycle maps; it is still structurally easier than unconstrained global permutations.
- The three-triple locality class is exhausted, but larger arbitrary decompositions (for example an eight-position group plus one fixed position) are reported only as a residual analysis question, not claimed impossible.
- Named-rival and low-complexity-map audits cannot prove that every possible shortcut has been eliminated.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `4c5d75752ec9c0899595a62b17076b1ed5e5240b3069e2d55b413477469730d3`.

# Decisions for generator 3108da8bf9e8

## D1 — Represent the lawful occupancy family with `omitted_count`

**Original rationale.** The baseline avoided tied sort keys by forcing unique counts `0..8`, but that fixed the omitted count at `9` and contradicted three canonical inputs.

**Decision.** Use nine distinct values from `0..9`, expose the missing value as the sole exact axis `omitted_count: int 0..9`, and recover it from every grid through `observe_overrides`.

**Alternatives rejected.** Keeping `0..8` collapses a canonical-varying statistic. Sampling with replacement creates ambiguous ties. Hiding omission as uncontrolled randomness weakens curriculum construction and override verification.

**Probe.** `workspace/semantic_support_probe.py` measured canonical omissions `[0,9,2,1]`, frozen-baseline support `{9}`, and repaired support for all ten values.

**Limit.** Uniform keyed coverage is a breadth policy, not an inferred natural frequency.

## D2 — Remove inert and invalid axes

**Original rationale.** The baseline advertised fixed geometry/palette controls, generic boilerplate axes, a density label that did not change the exact occupancy multiset, and invalid “degenerate” textures.

**Decision.** Delete every non-observable or unlawful axis and reject unknown overrides. Keep fixed geometry, palette, separators, and block count because those are canonical invariants.

**Alternatives rejected.** Fixed-value axes create false controls; invalid degenerates violate preconditions; arbitrary geometry would require a different rule family without canonical evidence.

**Probe.** Final override diagnostics report zero findings or warnings and reject unknown keys.

**Limit.** Consumers of bogus legacy keys now fail loudly and must migrate.

## D3 — Define difficulty by displacement while preventing small local decompositions

**Earlier mistakes.** The first easy design used within-row swaps, so row-local sorting solved every draw. The second used one transposition, which removed that named rival but left every easy draw solvable by 70 different partitions into three independently sorted triples. The first hard design used one fixed map, making macro-row reversal sufficient.

**Decision.** Easy applies one four-cycle whose positions span all three macro-rows and columns, moving exactly four blocks. Medium samples permutations with five to eight displaced positions. Hard samples full derangements. Every band rejects solved order, top-left ascending order, row-local sorting, column-local sorting, macro-row reversal, and any position permutation whose cycles can be packed into three invariant triples.

**Alternatives rejected.** Identity-like examples are too weak. Transpositions always fit inside a three-cell local group. A fixed hard permutation teaches a positional transform. Making easy a full derangement would erase the structural curriculum distinction. Correlating cycle choices across lesson indices would couple generation to one materializer schedule and risk a new periodic shortcut.

**Probe.** The final census shows displacement `{4}` / `{5,6,7,8}` / `{9}`, 213/399/400 unique maps, zero named-rival matches, and zero three-triple solvers in 1,200 draws.

**Limit.** Structural labels are not model-calibrated, and easy intentionally remains a four-block correction task.

## D4 — Preserve full marginal texture support while guaranteeing a lesson witness

**First-round mistake.** Hand-authored texture templates permanently excluded one location at occupancies 1 and 8 to guarantee a repainting counterexample.

**Decision.** Sample each exact-count texture uniformly from all `C(9,k)` masks. Permit individual row-major-prefix blocks. Only when every block in the grid is the named rival's prefix texture, repair one mixed block without changing its count.

**Alternatives rejected.** Permanently banning one mask distorts every draw. Canonicalizing all blocks teaches count-and-redraw. Relying on unconditioned chance permits a rare lesson where repainting is indistinguishable.

**Probe.** In 400 draws per band, occupancies 1 and 8 cover 9/9 masks and occupancies 2 and 7 cover 36/36; the repainting rival matches zero draws.

**Limit.** Uniform mask sampling is a chosen prior and does not reproduce unknown source frequencies.

## D5 — Expand the executable semantic contract around observed failures

**Original rationale.** The baseline had no executable semantic contract. A green gate checks only rivals the author has declared.

**Decision.** Declare six rivals—identity, ascending from top-left, repaint-by-count, row-local sort, column-local sort, and fixed macro-row reversal—with one matching witness each. Keep `rule_mirror`, strict canonical validation, and `lesson_identifiable` independent of Racket execution.

**Alternatives rejected.** Comments are not executable evidence. Calling Racket for every unit assertion reduces independence. Treating a finite rival list as exhaustive would overstate the result.

**Probe.** The final semantic gate gives all six witnesses 600/600 hits, validates every rival claim checked, and finds 12/12 materialized lessons identifiable.

**Limit.** New hypothesis classes still require discovery or generic structural gates.

## D6 — Build a task-local shortcut census that works at draw and lesson level

**Rationale.** Repository diversity and semantic gates were green while normalized object movement had collapsed. Exact-map diversity then became green while a broad local-sort class still survived.

**Decision.** `workspace/shortcut_census.py` measures rank-position maps, displacement, map reuse, moved row/column support, declared rivals, omissions, exact texture masks, fixed-map survival, and all 280 partitions of nine positions into three triples. It intersects local-sort survivors across three demonstrations and a query. It fails on analysis errors, weak support, unexpected displacement, any named shortcut match, any per-draw three-triple solver, or any local solver surviving all demonstrations.

**Alternatives rejected.** Pixel hashes do not expose semantic collapse. A finite list of hand-named rivals missed the third-round class. A one-off notebook would not help future reviewers. Requiring every lesson to have four distinct maps is neither necessary nor sufficient.

**Probe.** Version `3.1.0` had 400/400 easy draws and 201/256 easy demonstration sets admitting the class; version `3.2.0` has zero in all 1,200 sampled draws and all 288 sampled lessons.

**Limit.** The extractor is task-specific; repository-wide adoption needs an object/rank correspondence hook.

## D7 — Use cycle structure as the production rejection test

**Rationale.** Enumerating all 280 partitions for every candidate is acceptable in an audit but wasteful in the generator. A local three-triple sorter exists exactly when the permutation's invariant cycles can be packed into three bins of capacity three.

**Decision.** Reject candidates using cycle lengths and a small exact bin-packing search. Retain exhaustive partition enumeration in the independent census rather than sharing the production implementation.

**Alternatives rejected.** Reusing one implementation in both generator and verifier risks correlated bugs. Checking only row and column partitions covers two of 280 cases. Heuristic connectivity checks would not prove class exclusion.

**Probe.** `workspace/verify_cycle_partition_equivalence.py` compares the fast predicate with independent brute-force assignment for all 30 integer partitions of nine and reports zero mismatches.

**Limit.** This equivalence applies to the bounded three-triple hypothesis class, not arbitrary program synthesis.

## D8 — Normalize cached Racket authorities without changing semantics

**Rationale.** Cached `raw_code` and `target_code` were whitespace-equivalent to canonical and execution parity passed, but exact text divergence caused authority-sync failure.

**Decision.** In round one, copy canonical `program_solution` text exactly into both cached fields. Make no Racket authority change in rounds two or three.

**Alternatives rejected.** The canonical rule already solves all pairs. Weakening authority-sync would preserve avoidable drift.

**Probe.** Exact source groups went from two to one; rule hash remains `05977542b8d5`; final execution parity is `PASS`.

**Limit.** This is source synchronization, not an algorithmic change.

## D9 — Keep every repair test-first and retain failed attempts

**Decision.** Add focused tests before each implementation increment: frozen-law coverage, positional rivals and map diversity, complete texture support, census output/error accounting, column-local leakage, four-cycle coverage, and the full three-triple hypothesis class.

**Probe.** The cumulative progression includes 46 failures/1 pass → 47 pass; 3 failures/47 pass → 50 pass; missing-tool failure → 51 pass; targeted accounting and texture failures → pass; round-two final 53/53; and third-round 6 failures/51 existing passes → 57/57. All logs are retained.

**Limit.** Task-local tests complement but do not replace the full repository battery, independent code review, or model evaluation.

## D10 — Add a separate topology-ranking family with an exact canonical default

**Decision.** `workspace/parametric/` exposes the episode-fixed setting
`rank_basis=cells|components_then_cells`. The default returns the selected
canonical Racket program byte for byte and keeps its 11×11 grammar. The alternate
sorts by the lexicographic pair (four-connected color-1 component count, color-1
cell count), then moves the original whole blocks to the same bottom-first
target order. Distinct cell counts make the tie-break unique. The production
generator, canonical reference and approval identity are unchanged.

**Teaching and scope.** Both settings use identical 11×11 demonstration inputs
for a given seed. Six-demo/four-query banks are built before request slicing, so
2–6 demonstrations and 1–4 queries have stable prefixes and novel inputs. The
first two demonstrations distinguish cell counting, connectivity and tie-break
choices. Alternate queries use 14×14, 20×20, 26×26 and 30×30 grids. The last has
nine 9×9 blocks with zero separator widths one and two: 729 occupied cells.
Larger geometry belongs only to the alternate grammar. At least one movement
cycle has length four or more under each setting, excluding independent-three-
triple sorting without claiming to exclude every larger decomposition.

**Evidence.** The three added test modules pass 82 focused tests. The current
six-episode audit executes 326 protected Racket evaluations and independently
checks 46 reference labels. Sixteen additional plausible rivals produce no
query disagreement after surviving all demonstrations or the first-two-demo
prefix. The equivalent cell-count rival remains allowed for the canonical
setting. A bounded Python-only probe passes 144 requests over seeds 0–23,
both settings and 2/3/6 demonstrations; the maximum pair cost is six draws
against a cap of 4,096. There are 480 full-bank pair records and 336 distinct
input grids because demonstrations are shared across settings. See
`workspace/parametric/evidence/current/` for the source-bound audit, corrected
sampler report, tests and export checks.

**Limit.** Finite native qualification passed on seeds 0 and 17 with three
demonstrations and four queries per setting. The owner must qualify and accept
the exact integrated source before accepted parametric use. There is no training
admission or measured Qwen learning claim.

## D11 — Make the rank intermediate observable and isolate each query turn

**Dependency.** Step A extracts the blocks and computes their component/count
keys and source-index rank permutation. Step B needs that permutation to select
the source block for each target slot. Protected witnesses replace the
intermediate with area-only statistics on an 11×11 demonstration and
eight-neighbor connectivity on a 30×30 query, leaving block copying and target
geometry fixed. Outputs change by 24 and 244 cells respectively; the native
helper independently replays both. This is a derived-statistic dependency,
not iterative grid-state simulation. The source-bound records are
`checks/3108da8bf9e8/causal/witness.json` and
`checks/3108da8bf9e8/causal/replay.json` in the return.

**Export.** The reusable writer and example builder publish exact visible-byte
hashes, private answer/program/settings records, and one-query actor payloads.
Two complete episodes contain eight actor turns and pass the saved-public
checker. Only a single `turns/<id>.json` is learner-visible; four-query controller
files, metadata and future turns stay private. Regressions check that private
data and unseen queries cannot alter the first turn, and reject malformed grids,
duplicate inputs and duplicate payloads before publishing a destination. The
native worker executes labels; the transport writer alone makes no semantic
verification claim.

## D12 — Proposed Qwen3.5-9B gate: expand demonstration-only semantic rivals

**Additional gate.** Extend the existing declared-setting check with a small
task-specific set of executable semantic mutations. Fit each candidate to
visible demonstrations first; reject a clean supervised episode only when a
survivor disagrees on a novel query. Cache exact (program, input) evaluations,
check each rival's mathematical meaning independently, and fail closed on errors.
The implemented `audit_native.py` supplies sixteen rivals, including connectivity,
tie-breaking, local sorting, repainting and a position map learned from demo one.

**Reproducible incremental failure.** In
`workspace/parametric/evidence/current/semantic-mutant-before.json`, raw sampler
seed 438271 selects draws 3 and 9. The two demonstrations distinguish the
declared component rule from cell counting, yet the undeclared eight-neighbor
rule fits both and differs on the original query in 16 cells. Replacing one weak
demonstration with a distinct teaching example removes that rival while keeping
two demonstrations and the original query novel. Twelve protected Racket
evaluations reproduce and check this case; the probe and command are retained.
This deliberately weak lesson is excluded from the clean generated core.

**False positive and cheapest check.** Merely surviving is insufficient: an
equivalent rule, such as the canonical cell-count rival, must stay allowed when
it agrees on every query. Intentionally ambiguous research lessons need an
explicit separate route. Start with the retained twelve-evaluation reproducer,
then run the existing six-episode audit on source changes. No model-training run
is needed to establish this teaching defect; any claim of improved Qwen accuracy
needs a separate matched-budget training comparison, which was not performed.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/3108da8bf9e8/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
