# 2026-10-20 current review addendum

This addendum supersedes historical source IDs and measurements below; the older material is retained as provenance.

- Baseline generator SHA: `ea1d311193c9bfbce01c5466eea181ecfd49c35949b4c7917a175278a371a49f`; final generator SHA: `1607bce019f9e5bf2d9ca3465599e6067af6822ef1370a761957d5d2cea17d02`; version remains `4.0.0`.
- Canonical Racket `RULE_HASH=41d149922ac6` is unchanged. Rule smoke, Racket lint, and authority sync are green.
- Reproduced defect: invalid seed and difficulty scalars were accepted at the public boundary. Exact-type validation now rejects them before `gen_ctx`; valid generation was not changed.
- Before battery: 10 green, 1 advisory, 1 blocking defect-lint failure. Final battery: 12/12 green.
- Supported portable task tests: 51/51 passed. A direct repository-layout run passed 50 and hit one environment-only private-alias import failure; see `checks/task-tests-direct.log`.
- Final lesson census: 300/300 ordered six-demonstration lessons identifiable over 2,100 unique inputs. Hold-one-out rotation diagnostic: 1,848/2,100 identifiable, 252/2,100 ambiguous on `first_two_pairs_only`.
- Strongest shortcut remains `first_two_pairs_only`; the final-source seed-4242/sample-5 witness differs in 36 cells and is rebound to a live Racket receipt under `counterexamples/current-shortcut/`.
- Parametric priority delivered as a separate runnable `stamp_mask` prototype (`fill_cells` canonical/default; `template_holes` alternative): two settings, two complete 3-demo/1-query episodes, and 16 exact Racket outputs. It is not part of canonical generation or approval.
- Prior return used only as a lead: `review-1cc94d24b58aa938:v0001`; all current claims were remeasured on the pinned and final sources.
- Post-repair solve: 6/6 visible examples in revision 1; earlier exposure `yes`, reference consulted `no`. Blind task `9c5bdbcdcd50`: 3/3 visible examples by revision 2, exposure/reference both `no`.

# Archived prior notes

# Working notes: 0f5fbe0de38e

## Current source identity

- Version: `4.0.0`
- Final generator SHA-256: `ea1d311193c9bfbce01c5466eea181ecfd49c35949b4c7917a175278a371a49f`
- Canonical Racket rule hash: `41d149922ac6` (unchanged; authority sync and execution parity pass)
- Approval remains catalog-owned and unchanged.

## Intended rule and distribution

A 19–22 grid contains one sparse 3×3 three-color template. Its modal non-background color is the fill color; the two singleton colors occupy opposite-corner marker ports. Outside the template, one to three greedy-nearest cross-color pairs of equal solid squares occur at scale 1, 2, or 3. Each pair marks opposite corners of a scaled 3×3 footprint. The rule chooses the compatible D4 placement and paints only background cells corresponding to the template's fill positions, preserving marker blocks, template cells, and holes.

The production sampler keeps four literal template masks, six ordered lesson profiles (`unit_single`, `scaled2_single`, `scaled3_single`, `unit_double`, `mixed_1_2`, `mixed_1_2_3`), and same/opposite/mixed diagonal profiles. `EXAMPLES_NEEDED = 6`; a normal ordered six-demonstration window therefore contains unit, scale-2, scale-3, multi-pair, mixed-scale, both diagonal relations, and a three-pair case.

## Review decisions and repairs

1. **Retain the canonical grammar.** Associated note `GNOTE-001711` records that an older free-form distribution rejected the canonical inputs. The selected literal-template/square-pair grammar remains aligned with the task, so this review did not broaden it arbitrarily.
2. **Reverse permissive scalar acceptance.** The baseline accepted booleans, floats, strings, and negative `sample_index` values despite declaring exact scalar axes. `_validate_scalar_inputs` now requires exact declared types and a nonnegative integer sample index. Before evidence: 19 strict-scalar warnings; final defect lint is green.
3. **Reverse semantic round-tripping after construction.** `generate` now returns the scene it just built instead of reparsing it. Public observers share a one-entry content-keyed `_analyze` cache; equal content is parsed once and mutation invalidates the entry. This is bounded duplicate-call reuse, not an unbounded cache.
4. **Strengthen the teaching contract.** Seven witness predicates now name rivals they actually refute. `LESSON_COMPETITORS`/`SEMANTIC_RIVALS` contain ten executable rivals, including `first_two_pairs_only`; `lesson_identifiable` rejects lessons whose demonstrations leave a declared rival query-ambiguous.
5. **Leave Racket authority unchanged.** No transformation-law defect was reproduced. Python prediction remains an audit mirror; supported Racket execution supplies formal outputs.
6. **Do not edit the frozen inherited test.** Its fixed-depth canonical path blocks portable aggregate collection. New regressions use public `reviewer_support`; maintainer migration is required for the frozen fixture.

## Strongest retained shortcut

`first_two_pairs_only` applies the intended rule to only the first two greedy pairs. It fits all three canonical demonstrations (pair counts 1, 2, 2) and fails the three-pair canonical query. A final-source generated witness at seed 4242, sample index 5, hard difficulty differs in 36 cells and is bound to Racket output under `counterexamples/current-shortcut/`. `counterexamples/current-shortcut.json` is the compact manifest; `workspace/probe_shortcut.py` replays the search/check.

## Final measurements

- Full after battery: 12/12 green.
- Strict semantic profile: 600/600 generated draws and 4/4 canonical inputs accepted.
- Small lesson smoke: 12/12 ordered production lessons identifiable against declared rivals; diagnostic rotations 75/84 identifiable and 9/84 ambiguous.
- Large census: 300/300 ordered production lessons (six demonstrations, one trailing query) identifiable against ten declared rivals over 2,100 unique inputs; diagnostic rotations 1,848/2,100 identifiable and 252/2,100 ambiguous, all on `first_two_pairs_only`. Required-rotation policy exits 1; diagnostic policy exits 0. Advisory measured-label component filters were ambiguous on 13/300 production rows and 104/2,100 rotations.
- Override matrix: 151,020/151,020 draws; 145,170 accepted; 5,850 explicit incompatibility rejections; zero findings; 243.6 seconds.
- Focused portable regressions: 26/26 passed.
- Frozen aggregate task-test stage: preflight blocked before pytest; baseline fixture SHA remains `bfaf9b6c0dd1f4ce12b52116234d2a1be87c4e6917f3ebf169f23f62a64e2eba`.

## Known limits and open findings

- Production is intentionally ordered. Arbitrary hold-one-out query rotation is not guaranteed; the rotation ambiguity is retained, not hidden.
- The ten declared rivals are a useful finite hypothesis set, not a uniqueness proof over all programs.
- The advisory generic search mutates measured labels rather than executing independent rules; its 13/300 production ambiguities are retained for future task-specific rival design.
- No schedule period is declared, so the census does not exhaust every cyclic start residue or every seed.
- Four template masks and 19–22 grids are a bounded teaching domain, not every Racket-lawful scene.
- The override checker still warns that 5,580 multi-axis color-collision rejections use legacy unstructured incompatibility messages. No correctness finding remains.
- Catalog/training approval remains unchanged.

## Maintainer: inherited fixture portability

The reviewer correctly retained the original fixed-parent canonical-path blockage. The inherited fixture now uses public root/canonical/selected-generator helpers and explicit library/runtime data layouts. All original test functions and assertions are preserved; the public task-test stage executes 33 passing checks, including the reviewer regressions. This does not rewrite the original failed receipt or claim a new all-seed semantic review.
## Current reviewer considerations

Source SHA-256: `1607bce019f9e5bf2d9ca3465599e6067af6822ef1370a761957d5d2cea17d02`.

# Decisions — 0f5fbe0de38e

Final generator SHA-256: `1607bce019f9e5bf2d9ca3465599e6067af6822ef1370a761957d5d2cea17d02`. Canonical Racket hash: `41d149922ac6` (unchanged).

## D1 — Preserve the canonical transformation and valid sampling stream

The before battery already passed rule smoke, grammar, Racket lint, and authority synchronization. The reproduced failure was at the Python call boundary, not in the transformation law. I therefore left the canonical Racket program, rule hash, generator version, masks, pairing logic, and valid keyed draws unchanged. Rewriting the authority or incrementing the RNG version would have created unnecessary parity risk.

## D2 — Reject invalid public scalars before `gen_ctx`

The baseline accepted non-integer seeds and unsupported difficulty values because Python booleans and numbers flowed into the generic sampling context. I added exact-type checks in `_validate_scalar_inputs` and call it at the start of `generate`. The function also preserves the existing nonnegative integer sample-index and declared override checks. Coercion with `int(...)` was rejected because it silently aliases distinct caller inputs; downstream failure was rejected because it produced inconsistent behavior.

## D3 — Keep the parametric extension isolated from the selected canonical path

The bounded parameter is `stamp_mask` with values `fill_cells` and `template_holes`. Both settings retain the same template discovery, greedy cross-color pairing, scale inference, D4 placement, anchors, and object roles; only the set of template-background cells painted at each footprint changes. `fill_cells` is byte-identical to the canonical program. The extension remains under `workspace/parametric/` with its own Racket sources, episode builder, public/private projections, and tests. It is labeled `prototype`, not merged into `generate` or the canonical authority.

## D4 — Retain the ordered six-demonstration curriculum and report rotations separately

Production uses six demonstrations followed by one query. The final census found 300/300 production lessons identifiable against all declared rivals. Arbitrary hold-one-out rotation is not part of that assembly contract and fails in 252/2,100 rotations, all through `first_two_pairs_only`. I retained those failures and state the production/rotation verdicts separately instead of weakening the rival or claiming rotation support.

## D5 — Keep `first_two_pairs_only` as the primary shortcut witness

This is the strongest simple canonical-fitting rival found: the canonical demonstrations contain at most two pairs. The generated three-pair witness at seed 4242/sample 5 differs in 36 cells and is checked against the live Racket authority. The generator emits such cases every six-step schedule. Ten declared rivals are still a bounded search, not a uniqueness proof.

## D6 — Treat the supported portable task-test stage as authoritative

The supported isolated stage passed 51/51 and records copied source hashes. A direct repository-layout invocation passed 50 tests but could not import the task through the staged `puzzle_generators.per_puzzle` alias for one oracle test. I did not alter the test to hide this environmental distinction; it is shared-tool feedback rather than a selected-task blocker.

## D7 — Report, but do not repair, peer audit targets

Per the assignment, `30d3af94d21e` and `13507b4f7614` were inspected without source edits. Both accept invalid scalar arguments under standalone defect lint. The first also has a portable canonical-path failure and a weak strict semantic contract; the second passes the combined audit yet fails standalone defect lint, exposing an audit-preset coverage gap.

## D8 — Stop after source-bound verification and documented limits

The strict after battery is 12/12 green, portable tests are 51/51, the parametric prototype passes all focused tests, the final solve is frozen, both audits are complete, and no selected-task blocker remains. Further canonical changes would add risk without addressing a reproduced defect.

## Native stamp-mask completion (current review)
Reuse the exact retained fill_cells/template_holes programs and the reviewed template, greedy-pair, scale and D4 analysis. The native input bank has six independent demos and four privately shuffled queries; the first two demos include three pairs, all scales, both diagonal relations, and distinct masks. A 30x30 three-pair scene occupies all boundaries and quadrants. A is greedy pairing plus placement inference; the intermediate is each pair's scale/anchor/D4 transform; B paints the selected transformed mask. A no-rotation counterfactual tests that dependency. Production and the legacy prototype remain unchanged. Implementation sequence: native count/masking/geometry regressions, executed-rule/rival audit, bounded seed sweep, source manifest, qualification and causal replay. These are reviewer evidence, not owner acceptance or training admission.
