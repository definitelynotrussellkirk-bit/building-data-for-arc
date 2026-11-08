# Working notes: ba9d8eb0cd5a

## 2026-10-04 review repair

The 1.2.0 sampler's metadata had drifted far beyond its implementation. It
advertised nine axes but used only dimensions/row count; accepted unknown keys;
clipped documented values by difficulty; mixed negative textures into the valid
domain; had no `RULE_HASH`, observer, or semantic contract; rejected all five
canonical inputs; accepted an all-background grid; and produced zero exact
canonical-profile hits in the pinned profile census.

Version 2.0.0 deliberately replaces that surface with three exact controls that
can be reconstructed from pixels: height, width, and distinct nonzero-color
count. Every legal combination is constructive in every difficulty band. The
sampler uses full-domain choices with probability weighting, so difficulty and
the canonical-scale curriculum alter frequency without narrowing the override
contract.

Every ordinary sample includes:

1. a gappy row for which left compaction visibly changes the grid;
2. an active row already anchored at column zero, matching canonical examples;
3. a descending adjacent color pair in row-local order, which forces the true
   stable-compaction output to differ from a sort-then-pack rival; and
4. every selected palette color at least once.

`self_check` validates this semantic teaching manifold while accepting every
canonical input. The selected Racket authority and canonical data were not
changed. The declared `sort_then_pack` rival is executable and linked to the
`order_preservation` witness.

### Retained probes

- `tests/test_generator.py`: canonical acceptance, independent Python oracle,
  exact boundary overrides in all bands, invalid-key/type/range rejection,
  distribution support, validator negatives, and rival refutation.
- `workspace/coverage_probe.py`: deterministic per-band counts for unique
  inputs, shapes, colors, canonical profiles, witness firing, and rival
  disagreement. Run through the packet wrapper so runtime dependencies and
  canonical data are pinned.

### Known limits

The normal sampler intentionally excludes uninformative already-packed-only and
all-background lessons. The finite declared-rival checks do not prove universal
identifiability; in particular, they test stable order against sorting, not
every possible row-compaction heuristic. The generated palette count is exact,
but color identities are nuisance variation rather than an advertised control.
## Current reviewer considerations

Source SHA-256: `2e8eff2841fb77f8c50326cb0f5b871f5f4f93dc290cc961248adeac8ca7cf94`.

# Decisions for `ba9d8eb0cd5a`

## D1 — Keep the canonical Racket authority unchanged

**Input evidence.** The current canonical pairs all implement the stated row-wise stable left compaction, and the existing Racket rule passed rule smoke before the generator repair. Its hash is `8cd149b15ecf`.

**Original rationale.** The original author’s detailed rationale is unknown. The concise source summary and canonical outputs agree with the rule.

**Decision.** Do not modify `repo/shared/data/canonical/puzzles.jsonl` or the referenced Racket file. Pin `RULE_HASH = "8cd149b15ecf"` in the selected generator instead.

**Alternatives rejected.** Rewriting the authority to match the baseline’s false “all active rows start with a gap” invariant would narrow the task and contradict canonical examples. Adding generator-specific behavior to the rule would hide rather than repair the distribution defect.

**Probe.** Canonical pairs are checked by an independent Python row-compaction oracle in `tests/test_generator.py`; `rule_smoke`, `racket_lint`, and `authority_sync` all pass in `checks/after/`.

**Failure mode / limit.** Oracle and Racket agreement on finite canonical/generated samples does not prove semantic equivalence for all possible grids, but there was no observed authority defect requiring a rule change.

## D2 — Replace the nine-entry advertised axis surface with three honest exact axes

**Input evidence.** The baseline listed nine `AXES` entries but ordinary generation only used dimensions and row count; most metadata controls were dead or lossy, unknown keys were accepted, and difficulty silently clipped advertised values. The before override stage failed extensively.

**Original rationale.** Unknown. The metadata appears to have been inherited from a more general generator template rather than derived from observable pixels.

**Decision.** Expose only `grid_h`, `grid_w`, and exact distinct nonzero `n_colors`. Add strict key/type/range validation and `observe_overrides()`.

**Alternatives rejected.** Implementing all nine legacy entries would preserve a large, coupled API with ambiguous observability (`palette_kind`/`texture`, `palette_size`/`n_distinct_colors`, fixed `density`, fixed `position_bias`). Keeping them as advisory controls would continue to imply exact support that the override gate cannot verify.

**Probe.** The focused suite tests both boundaries in all four difficulty settings, invalid values and types, deterministic replay, and observer equality. The full override stage passes (`checks/after/checks/ba9d8eb0cd5a_after_override_results.json`).

**Failure mode / limit.** This is an intentional compatibility break for callers relying on undocumented or nonfunctional legacy keys. That is preferable to silent acceptance; such callers now get an explicit error.

## D3 — Use full-domain sampling with probability weights, never difficulty clipping

**Input evidence.** Difficulty-specific ranges caused legal advertised overrides to fail or be replaced. At the same time, unweighted broad sampling gave insufficient canonical-profile support.

**Original rationale.** The baseline likely intended easy/medium/hard to control size and active-row count, but implemented it by changing support rather than frequency.

**Decision.** Put every legal value in each draw’s options in every band. Add repeated anchor values to change frequency. A `canonical_profile` draw chooses one of the authoritative shapes `(4,9)`, `(5,8)`, `(6,7)` as a dimension anchor and favors nine nonzero colors; a broad component uses band-specific anchors.

**Alternatives rejected.** Hard-coding canonical grids would leak/replay examples and collapse diversity. Restricting each band to disjoint ranges would again make the exact override contract false. Pure uniform sampling failed the profile-floor objective.

**Probe.** Profile floor: exact hits `12/20`, `12/20`, `10/20` across easy/medium/hard. Independent 100-draw probe: `39/100`, `29/100`, `43/100`, with 300/300 unique grids and broad shapes/color counts (`checks/coverage-probe.json`).

**Failure mode / limit.** Weighted duplicate options couple exact probabilities to `gen_ctx.draw_choice` behavior. The test contract checks support and observed coverage, not a fixed probability distribution.

## D4 — Choose bounds that include canonical scale and remain constructible

**Input evidence.** Canonical shapes span heights `4..6`, widths `7..9`, and use all ten ARC values (background plus nine foreground colors). The generator also needs enough columns to place a leading gap and enough cells to realize every selected color.

**Original rationale.** The baseline ranges (`grid_h 2..18`, `grid_w 3..24`, color-related controls `1..9`) were not honored by its own ordinary sampler and included combinations that were poor or awkward for the claimed teaching manifold.

**Decision.** Use height `4..12`, width `7..16`, and nonzero color count `2..9`.

**Alternatives rejected.** Retaining the full legacy size range would make tiny grids hard to reconcile with two active rows, visible motion, order evidence, and exact palette realization; very large grids would add sparse nuisance area without a demonstrated teaching benefit. Allowing one foreground color cannot directly establish color-order preservation.

**Probe.** Tests construct both joint extremes `(4,7,9)` and `(12,16,2)` in every band over eight seeds each. The full override matrix and 100-draw probe pass.

**Failure mode / limit.** The ranges define a useful training manifold, not all grids on which the rule is mathematically valid.

## D5 — Guarantee three complementary teaching facts in ordinary samples

**Input evidence.** A valid transformation example can still be uninformative: all-background and already-packed grids have identity outputs; single-cell rows teach only translation; monotone color sequences cannot distinguish stable order from sorting.

**Original rationale.** The baseline tried to avoid weak rows, but encoded the wrong requirement that every active row must have a leading gap and separately exposed degenerate textures.

**Decision.** Construct every sample with (1) a row that visibly moves, (2) an active row anchored at column zero, (3) a non-monotone row-local sequence, and (4) every selected palette color present.

**Alternatives rejected.** Randomly generating and rejecting until these facts appear makes support/probability opaque and can fail at boundaries. Allowing degenerates as ordinary textures would dilute instruction and complicate validator semantics.

**Probe.** `self_check` is called on every generated sample. Focused tests and `workspace/coverage_probe.py` independently verify visible motion, anchoring, order witness, and exact color count.

**Failure mode / limit.** These facts create recognizable curriculum regularities. Active row positions, palette, row count, and gap layouts are randomized, but the guaranteed witness structure is still a distribution signature.

## D6 — Make `self_check` describe a useful semantic manifold, not one layout

**Input evidence.** Baseline validation rejected all five canonical inputs because some active rows begin at column zero; it accepted all-background through an early return.

**Original rationale.** The comment suggests an attempt to ensure “normal rows really need left-packing,” but it generalized the sampler’s preferred leading gap into a false task invariant.

**Decision.** Validate rectangular ARC colors, selected bounds, at least two active rows, exact allowable color-count range, visible effect, one anchored row, and a non-monotone order witness. `strict_canonical_like` delegates to the same contract.

**Alternatives rejected.** A permissive structural validator would admit weak lessons. Requiring every active row to move or every row to contain multiple colors would reject legitimate canonical support and overfit presentation details.

**Probe.** All canonical inputs pass. Explicit negative fixtures cover all-background, already-packed-only, no order witness, booleans, ragged rows, and insufficient activity. Battery self-check/profile stages pass.

**Failure mode / limit.** Some lawful but weak inputs are intentionally rejected. The validator is a training-data quality filter, not a complete decision procedure for the mathematical rule domain.

## D7 — Declare `sort_then_pack` as the primary executable rival

**Input evidence.** Sorting before left packing is locally plausible, cheap, and exactly matches examples whose row-local colors happen to be monotone. Stable order is the defining distinction in the task title and canonical outputs.

**Original rationale.** No baseline semantic rival declaration existed.

**Decision.** Add `order_preservation` as a semantic witness and an ascending `sort_then_pack` competitor linked through `WITNESS_RIVALS` and `LESSON_COMPETITORS`.

**Alternatives rejected.** A large rival catalog inside production source would create maintenance overhead and encourage task-specific overfitting. The primary rival should target the defining ambiguity; additional hypotheses belong in reusable probes unless they become required contracts.

**Probe.** The final semantic gate passes. The 300-lesson census refutes the declared rival in every lesson and finds no declared ambiguity.

**Failure mode / limit.** A single declared rival is not exhaustive. `checks/self-review-rivals.py` therefore post-processes the same 300 lessons against four additional plausible rivals; all are refuted at lesson level, but individual pairs sometimes fit them.

## D8 — Add source-bound tests and a deterministic coverage probe

**Input evidence.** The selected task had no task-local regression suite and no compact way to measure joint support, canonical-scale frequency, uniqueness, observer agreement, or rival disagreement from final source bytes.

**Original rationale.** Unknown.

**Decision.** Add `tests/test_generator.py` and `workspace/coverage_probe.py`. The probe records exact replay coordinates for failures and aggregates 100 deterministic draws per band.

**Alternatives rejected.** Relying only on the shared battery would miss task-specific construction details and undeclared rival analysis. Saving raw grids for every routine probe would unnecessarily enlarge returns; deterministic seed/sample coordinates are sufficient for replay.

**Probe.** TDD red evidence is retained at `checks/task-tests-red/`; final task tests are 24/24. The coverage report passes with no failures at `checks/coverage-probe.json`.

**Failure mode / limit.** The probe tests a finite deterministic slice. It is designed to catch regressions and contract drift, not certify the full pseudorandom state space.

## D9 — Treat complete lessons, not every individual grid, as the identifiability unit

**Input evidence.** The production lesson assembly uses three demonstrations and one query pair. Some individual generated grids happen to fit undeclared shortcuts even though other pairs in the same lesson refute them.

**Original rationale.** The shared census already evaluates declared competitors at lesson level.

**Decision.** Report both pair-level and lesson-level counts. Require the declared rival to disagree on every generated grid, while evaluating extra rivals over the complete four-pair lesson.

**Alternatives rejected.** Forcing every imaginable rival to fail on every single grid would over-constrain the sampler and reduce natural variation. Reporting only aggregate pair disagreement could hide complete lessons that remain ambiguous.

**Probe.** `checks/self-review-rivals.json` shows all four extra rivals refuted in all 100 lessons per band, while pair refutation rates vary (for example, `pack_only_rows_with_leading_gap` is refuted on 334/400 easy pairs but 100/100 easy lessons).

**Failure mode / limit.** The census does not rotate each materialized pair into the masked query position. The pointwise rivals tested here are position-independent, but query-position effects for learned systems remain unmeasured.

## D10 — Preserve the interrupted run and add an exact clean-replay record

**Input evidence.** An after battery invocation was externally interrupted after four completed stages. Its partial aggregate is not a pass and the framework does not automatically resume.

**Original rationale.** The packet explicitly requires retaining interrupted evidence separately.

**Decision.** Keep it under `checks/after-interrupted-20261004T024820Z/`, then run a complete new battery. Build and run `checks/fresh-replay/replay_handoff.py` to extract the original upload, apply the exact retained patch, compare source hashes, prepare Racket, rerun focused tests, and confirm solve/source identity.

**Alternatives rejected.** Deleting the partial run would erase useful failure/process evidence. Treating checkpointed stages as a completed pass would be incorrect. Manually claiming patch identity without a fresh extraction would weaken intake confidence.

**Probe.** `checks/fresh-replay/handoff.json` reports both git-apply exits zero, all six source files matching, focused tests exit zero, and solve hash equal to final generator hash.

**Failure mode / limit.** The replay utility records absolute paths for this reviewer environment. Its operations and hashes are portable, but callers must provide their own original packet ZIP and fresh destination.

## D11 — Add a native two-stage packing family without changing production

**Decision.** Add `workspace/parametric/` with exact canonical default `finish_rule=pack_only` and an alternate `mark_vertical_contacts` rule. The second setting stable-packs every row, then recolors packed cells that acquire a vertical packed neighbor. Both settings share identical generated inputs; episodes support 2–6 demonstrations and four distinct queries, including a dense 30x30 stress query.

**Rationale.** The alternate branch makes stage order observable. Active adjacent rows use disjoint columns before packing, so pre-pack marking produces no contacts while post-pack marking does. Non-monotone row sequences independently refute sorting before packing.

**Evidence.** `checks/ba9d8eb0cd5a/qualification/qualification.json`, `checks/ba9d8eb0cd5a/causal/witness.json`, and `workspace/parametric/evidence/manifest.json`. The bounded protected-Racket audit executes six named rivals and retains zero demonstration-fitting/query-changing survivors for the sampled episodes.

**Limit.** This is reviewer-ready prototype source only. Owner exact-source qualification, acceptance, and any training admission remain separate.

## D12 — Make the inherited tests portable and verify sequential presentation

**Decision.** Replace the legacy installed-package/script assumptions in the task test with `reviewer_support.find_root`, direct module loading, and public canonical helpers. Export each four-query episode as four sequential single-query views and test hidden-field invariance plus visible-change controls.

**Evidence.** `checks/ba9d8eb0cd5a-tests-final/result.json` records 52/52 tests passing. `checks/ba9d8eb0cd5a/first-turn.json` covers 16 public views, four first turns, 24 private-field mutations, and four positive controls.

**Limit.** The portability repair is task-test scaffolding; it does not alter the approved production generator.
