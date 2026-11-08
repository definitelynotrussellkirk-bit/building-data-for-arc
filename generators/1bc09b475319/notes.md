# Current generator notes: 1bc09b475319

## Current native extension — review-0ef1d91dd4d9916e

`workspace/parametric/` now supplies a self-contained native adapter and contract
with `cap_mode=caps|bridge_caps`. `caps` returns the exact selected canonical
program (SHA-256 `15debbc2b09d7b591e587879a201e865beeaa5153cac1d262ca493c6da156cfd`).
The production generator remains version 3.1.0, SHA-256
`aec1fee327a2ccf63f48630cf948a40133e3835ee38227307a35e4bf472d4362`, with its
existing rule pin and approval identity. Existing audit dispositions are not
changed by this separate extension.

The alternative first derives and paints new cap positions, then joins
consecutive new caps within each column only when the full intervening segment
of the frozen capped grid is zero. Existing cyan is neither a new anchor nor
transparent to a bridge; any nonzero interior cell blocks the whole gap.
The input-derived cap mask is the intermediate consumed by the bridge step.
Native protected construction/replay changes only `(anchors new-caps)` to
`(anchors old-cyan)`, preserving the capped grid, and demonstrates changed final
answers on both core examples. This is spatial composition, not iterative state.

The native grammar extends the separate rule family to 7–30 by 7–30 typed grids.
Constructive episodes support 2–6 demos and 1–4 queries, default to 3/4, construct
the full bank before slicing and use matched inputs across settings. Two core
demos distinguish horizontal thresholding, singletons, long/edge bars, occupied
cap targets, opposite-side alignments, consecutive versus extreme anchors,
blocked versus clear gaps and old-cyan decoys. Design review added a cyan-only
blocker to distinguish transparent-cyan traversal without adding a third demo.
Fields up to 30×30 contain over 200 input cells, many independently interacting
bars and cap columns, full-width edge bars, distractors and all-four-border contact.

Current evidence in `checks/1bc09b475319/`: **56 focused native/audit tests**;
**96/96** sampler/count/prefix requests across 16 seeds; **78 rival/episode
comparisons all demo-refuted** using 136 distinct protected-Racket evaluations;
and all 40 intended labels across both settings, seeds 0/17 and ten-position
banks. Native qualification executes 64 evaluations at six demos/four queries.
The causal witness has two replayed cases. Native export/verification produces
four private episodes and 16 one-query public files. The current inventory is
`workspace/parametric/evidence/manifest.json`; exact programs and execution
evidence are retained, not inferred from Python claims.

One intermediate native-test run had three failures because the test retained
a mutable comparison reference before deliberately altering an episode; fixing
that test isolation yielded the passing suite. The retained initial failing
commands are development evidence, not unresolved native defects. Production
batteries were not rerun. Variation remains a finite profile/shape bank, and
bounded rival success does not prove universal uniqueness. Next owner action is
exact-source native qualification and fresh acceptance of both assigned builds;
reviewer readiness grants no training admission or activation.

## Intended rule and authority

The selected canonical Racket authority is unchanged and pinned by `RULE_HASH = "187795461399"`. For every background cell, paint color 8 exactly when the two immediately adjacent horizontal cells on either the left or right are both color 6. Equivalently, each maximal horizontal run of at least two 6-cells receives an 8 at each in-bounds open end. Singleton 6-cells stay unchanged.

## Baseline defects used as repair leads

The selected baseline source SHA-256 was `3d9835756a2a0d9d692df242abd2cff7aa5928eacb08e008829faeb1c1ac2445`. Retained findings from `review-33f63450b2869f38-v0001` and `review-839c52ef87471169-v0001` were used as leads, then reproduced against the selected baseline. Ordinary generated lessons did not contain singleton 6-cells, so the simpler `adjacent_any_six` rule fit all three canonical demonstrations and generated lessons. The baseline also lacked a rule-hash pin, advertised dead/overlapping axes, accepted degenerate textures, and had a weak structural validator.

## Final sampling decisions (version 3.1.0)

- Grid defaults are canonical-scale squares: 7×7 easy, 8×8 medium, and 9×9 hard. Exact `grid_h=7..18` and `grid_w=7..20` overrides remain constructive.
- Each input has three or four bars in distinct rows and exactly two interior singleton distractors. `singleton_layout` is exactly observable as `separate` or vertically adjacent.
- `bar_length` is the exact length of the topmost bar. Other bars deliberately provide a complementary short/long contrast, so every generated input contains at least one length 2/3 bar and one length 4/5 bar.
- Ordinary samples always include one edge-touching bar, while `edge_bar=false` is an exact supported override that makes every bar interior. At least one other bar remains interior in either case.
- `self_check` accepts the canonical zero-singleton manifold and the generated two-singleton extension, but rejects malformed colors, shapes, run counts, illegal lengths, missing short/long support, edge singletons, and profiles with no interior bar.
- `observe_overrides` reports every advertised exact control. Unknown, mistyped, wrong-typed, and out-of-range controls fail loudly.

## Teaching contract

Two canonical-fitting shortcuts are declared: `adjacent_any_six` and `canonical_lengths_only`. A third lesson rival, `interior_bars_only`, captures missing edge-clipping evidence. Their witnesses are respectively singleton exclusion, a length-4/5 bar, and an edge-touching bar. Every ordinary generated input contains all three witnesses, and `lesson_identifiable` requires demonstrations to refute each declared lesson competitor.

The production lesson policy is three demonstrations plus one query. Final source SHA-256 `aec1fee327a2ccf63f48630cf948a40133e3835ee38227307a35e4bf472d4362` passed a 300-lesson census (100 per band): 300/300 materialized, 0 production ambiguities, and 0 ambiguities across 1,200 hold-one-pair-out query rotations. This is finite evidence against the declared rivals, not a proof against every possible hypothesis.

## Retained counterexample and tests

`counterexamples/adjacent-singleton-v0001/` contains a source- and rule-bound Racket counterexample. The adjacent-any-6 rival changes four cells next to two singleton 6s while the authority leaves them black. `tests/test_generator.py` covers canonical ownership, all boundary override combinations, invalid controls, default teaching support, every query rotation over sampled lessons, validator impostors, deterministic purity, profile support, and the retained fixture.

## Reversed intermediate decision

An intermediate repair made every bar in one input the same length and randomized ordinary edge exposure. Self-review found that this introduced `canonical_lengths_only` and `interior_bars_only` shortcuts. Version 3.1.0 replaced that choice with mandatory mixed short/long bars and ordinary edge exposure while preserving exact overrides.

## Known limits

The rule remains a single local operation with fixed colors 6 and 8. The generator intentionally does not add unrelated composition. The declared-rival census does not enumerate arbitrary undeclared programs or every possible cyclic schedule start. Catalog approval and training admission remain unchanged.
## Current reviewer considerations

Source SHA-256: `aec1fee327a2ccf63f48630cf948a40133e3835ee38227307a35e4bf472d4362`.

# Decisions for 1bc09b475319

## D1 — Keep the canonical authority unchanged

**Choice.** Pin `RULE_HASH = "187795461399"` and repair only the sampler, validator, semantic contract, tests, and retained evidence.

**Rationale and probe.** The independent Python transcription matched all three canonical pairs, and the public Racket smoke/authority-sync stages passed. The defect was under-teaching and false generator contracts, not an incorrect reference transformation.

**Rejected alternative.** Expanding or rewriting the Racket rule to legitimize singleton capping would change the task rather than repair the generator.

**Failure mode / limit.** This preserves a simple single-operation task; no claim of new compositional reasoning is made.

## D2 — Teach singleton exclusion in every generated input

**Choice.** Add exactly two interior singleton color-6 cells to every generated grid, with an exact `singleton_layout` control (`separate` or vertically adjacent).

**Rationale and probe.** The canonical-fitting `adjacent_any_six` shortcut agreed with every canonical pair but disagrees beside singleton 6s. The retained Racket counterexample changes four cells, and the final tests require the shortcut to be refuted on every generated example.

**Rejected alternatives.** Optional or rare singleton textures were rejected because a three-example lesson could omit them. Treating length-one runs as ordinary bars was rejected because it obscures the intended threshold rather than teaching it.

**Failure mode / limit.** The generator teaches horizontal singleton exclusion; it does not attempt arbitrary object shapes or colors.

## D3 — Make `bar_length` exact without making all bars identical

**Choice.** `bar_length` is the topmost bar's exact length. Remaining bars add a complementary length, so each input contains a short bar (2/3) and a long bar (4/5).

**Rationale and probe.** This keeps the override observable while refuting `canonical_lengths_only`, which caps only lengths 2 and 3 and fits all canonical demonstrations.

**Rejected alternative.** The intermediate version used one common length for every bar. Self-review found that it introduced a length-specific shortcut and erased within-example evidence of generality, so it was replaced before final verification.

**Failure mode / limit.** The length support is 2..5 only, matching the intended generator domain; longer runs are outside this sampler's contract.

## D4 — Put edge clipping in ordinary lessons

**Choice.** Ordinary samples always contain exactly one edge-touching bar and at least one interior bar. `edge_bar=false` remains a constructive exact override for all-interior bars.

**Rationale and probe.** This refutes the plausible `interior_bars_only` rival in every ordinary demonstration and shows that an edge bar receives its one available cap.

**Rejected alternative.** Random ordinary edge exposure was rejected after self-review because an entire three-demo lesson or a query rotation could omit the boundary case.

**Failure mode / limit.** The false override intentionally removes this witness for control testing; production defaults do not.

## D5 — Use a small truthful axis contract

**Choice.** Advertise only `grid_h`, `grid_w`, `n_bars`, `bar_length`, `edge_bar`, and `singleton_layout`. Validate unknown keys, types, and ranges before generation; provide `observe_overrides` for every axis.

**Rationale and probe.** The baseline advertised dead singleton-domain axes and negative textures as ordinary values. All Cartesian boundary combinations of the replacement contract are constructive and covered by parametrized tests and the exhaustive override gate.

**Rejected alternatives.** Cosmetic palette/density/position labels with no observable effect and malformed negative textures were removed rather than marked as useful variation.

**Failure mode / limit.** The palette is intentionally fixed to background 0 and object 6 because the authority produces fixed output color 8.

## D6 — Preserve canonical support while strengthening generated validation

**Choice.** `self_check` accepts either zero singletons (canonical pairs) or exactly two (generated extension). Generated cases additionally require both short and long bars; all cases require 3/4 legal bars, rectangular 0/6 grids, one run per active row, interior singletons, and an interior bar.

**Rationale and probe.** Canonical ownership remains green while structure-destroying impostors are rejected. The baseline validator had accepted all-background, full-one-color, short-line, and solid-2×2 impostors.

**Rejected alternative.** A generated-only validator that rejected canonical examples would make canonical support unverifiable and break portable tests.

## D7 — Declare executable rivals and witnesses

**Choice.** Declare `adjacent_any_six`, `canonical_lengths_only`, and `interior_bars_only` as semantic rivals; the first two are also canonical shortcuts. Declare singleton, long-bar, and edge witnesses and make `lesson_identifiable` score the actual rival outputs against demonstrations.

**Rationale and probe.** Named executable hypotheses make the teaching claims falsifiable and reusable by the shared semantic gate/census instead of relying on prose.

**Rejected alternative.** A hook that merely counted object types without comparing predictions was rejected as weaker evidence.

**Failure mode / limit.** Declared rivals are finite; an undeclared program may still fit the lessons.

## D8 — Lesson policy and query ordering

**Choice.** Keep `EXAMPLES_NEEDED = 3` and production bundles of three demonstrations plus one query. Support arbitrary hold-one-pair-out query rotations for the materialized four-pair bundle.

**Rationale and probe.** Every ordinary pair independently contains all three boundary witnesses, so each three-demo subset refutes all declared lesson competitors. The required-rotation semantic gate passed, and the final census tested 300 lessons (100 per difficulty band) and all 1,200 query rotations with zero declared-rival ambiguities.

**Rejected alternative.** Depending on one privileged demonstration position was rejected; it would be fragile to downstream reordering.

**Failure mode / limit.** The census uses 300 deterministic production starts, not every possible seed or cyclic schedule start.

## D9 — Keep canonical-scale defaults

**Choice.** Default to 7×7, 8×8, and 9×9 for easy, medium, and hard, while honoring the full declared height/width domains.

**Rationale and probe.** These profiles hit canonical size/palette support in all 20 profile-floor draws per band and keep lessons compact. The dimensions still vary exactly when explicitly overridden.

**Rejected alternative.** The baseline's larger default range was not needed to teach the local rule and diluted direct comparability with canonical examples.

## D10 — Retain exact counterexample and explicit regression suite

**Choice.** Save the Racket output, rival output, source/rule hashes, reproduction command, and cell-level differences in `counterexamples/adjacent-singleton-v0001/`; add 283 portable task-test cases.

**Rationale and probe.** This turns the motivating shortcut into a durable regression rather than a one-off explanation. The test stage runs independently of the 12-stage battery.

**Rejected alternative.** Relying only on a successful battery was rejected because the battery cannot discover every undeclared rival automatically.
