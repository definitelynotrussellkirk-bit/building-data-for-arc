# Current account: 2d59c1b766d5

## Intended rule

The input contains two exact rectangular color-8 frames. Each frame encloses color-5 walls, exactly one colored gate, and zero-valued floor cells. For each frame independently, copy the gate color into only those zero cells reachable from the gate by **four-neighbor** motion inside the frame. The frame and gray walls are barriers. The selected canonical Racket authority was not changed; its declared hash is `61c97755a0ea`.

## Reversed decision

**Prior choice (2.0.1):** generate four fixed 5×6 hollow frames containing unrelated random motifs. This did not model the selected gate/wall/reachability rule and omitted `RULE_HASH`.

**New choice (3.0.0):** generate two canonical-scale framed chambers with gates, walls, and an executable four-neighbor flood oracle. The repair was driven by all five canonical pairs and by two shortcuts that fit every canonical pair: (1) fill every non-wall interior cell and (2) use eight-neighbor flood fill. Exact selected-Racket counterexamples are retained in `counterexamples/sealed_fill_all.json` and `counterexamples/diagonal_joint_witness.json`.

## Curriculum and assumptions

A lesson has five demonstrations and one query. Sample positions follow a period-three `open → sealed → diagonal` topology schedule; six consecutive pairs therefore contain each topology twice, and every single query holdout leaves at least one of each. `open` is a canonical-like connected control, `sealed` creates a truly unreachable chamber, and `diagonal` separates four-neighbor from eight-neighbor reachability.

The supported input family deliberately stays near canonical scale: canvas 15–17×20–22, two horizontal non-overlapping frames sized 7–8×7–9, one gate per frame, gate colors from `{2,3,4,6,7,9}`, and 5–7 gray wall cells per frame. Advertised exact controls are only `grid_h`, `grid_w`, and `profile`; all are independently observable. Every default draw is intended to satisfy the strict profile (`MIN_STRICT_FRAC = 1.0`). Difficulty changes dimension weighting, not the semantic rule.

## Evidence and tools

`workspace/probe_curriculum.py` independently checks canonical parity, every declared schedule start and query rotation, both retained witnesses, and optionally the selected Racket rule. The 300-lesson production census materialized 1,800 pairs and 1,800 query rotations with zero declared-rival ambiguity or errors (`checks/lesson-census.summary.json`). Focused tests cover canonical pairs, controls, schedule rotations, malformed calls, determinism, selected-Racket parity, retained counterexamples, and the probe.

No prior return was used as factual evidence. The packet’s passing `b90d4c3d5553` task was used only as a structural example for authority pins, observable controls, semantic rivals, and retained probes.

## Known limits and open findings

The wall grammar is intentionally three structured topology families, not an unrestricted chamber generator. Both frames share one topology and are laid out horizontally; mixed profiles, vertical pair layouts, more than two frames, and arbitrary wall mazes are unsupported. The finite rival suite and census establish separation only from the named shortcuts and generic searched rivals, not universal identifiability. The deterministic period is an authoring schedule rather than a claim that every independently sampled subset is sufficient.
## Current reviewer considerations

Source SHA-256: `33afef8aad91520ecf7854b65e1520c64ccaab421f7330c359717b2a6c55bfab`.

# Decisions for 2d59c1b766d5

## 1. Authority and repair boundary

**Input choice:** preserve the selected canonical Racket rule and rebuild only the assigned generator, focused tests, notes, counterexamples, and task-local workspace tool.

**Original rationale:** unknown. The imported 2.0.1 generator described four hollow 5×6 frames with small motifs, while the selected authority describes gate-seeded chamber flood fill. No retained evidence justified the mismatch.

**Alternatives considered:** change the Racket rule to match the motif generator; minimally add `RULE_HASH` while retaining the old distribution; or reconstruct a generator from the canonical task. The first would replace the actual task, and the second would make lint green without teaching the rule. I chose the third.

**Probe/evidence:** all five canonical pairs were parsed before implementation. The independent Python mirror now matches all five labels and selected-Racket outputs. `checks/authority-sync/result.json`, `checks/racket-lint/result.json`, and `checks/semantic-gate-schedule/result.json` bind the final source to the unchanged authority hash `61c97755a0ea`.

**Failure modes/limits:** Python `rule_output` is a test oracle, not authority. Selected-Racket checks remain required. No canonical row or rule source was edited.

## 2. Canonical-scale scene grammar

**Input choice:** generate a 15–17×20–22 zero background with exactly two disjoint horizontal color-8 rectangular frames. Each frame is 7–8 high and 7–9 wide, contains 5–7 color-5 wall cells, one non-reserved colored gate, and at least one reachable zero.

**Original rationale:** the canonical inputs consistently use two framed local chambers at these approximate scales. The prior four-frame 2×2 motif layout was unrelated to the selected rule.

**Alternatives considered:** arbitrary numbers of frames; unrestricted canvas sizes; tiny synthetic chambers; vertical or mixed frame arrangements; or exact replay of canonical layouts. Arbitrary grammars enlarge the task beyond the selected family, while fixed replay provides weak diversity. The chosen range preserves the observed family while varying dimensions, placements, frame sizes, gate colors, wall transforms, and gate positions.

**Probe/evidence:** `strict_canonical_like` accepts every canonical input and every default draw. The profile-floor check passes in every difficulty band (`checks/profile-floor/result.json`), and the diversity check passes (`checks/diversity/result.json`). The 300-lesson census reports 1,800 unique inputs from 1,800 generated pairs.

**Failure modes/limits:** both frames are horizontal and share one profile. Mixed per-frame topologies, vertical frame pairs, more than two frames, clipped frames, and arbitrary wall mazes are out of scope. This is a bounded curriculum, not the full space of all reference-lawful inputs.

## 3. Three semantic topology profiles

**Input choice:** define three observable profiles from free-cell connectivity:

- `open`: one four-neighbor component; a five-cell L wall varies appearance without altering reachability.
- `sealed`: a full-span straight wall produces multiple four- and eight-neighbor components.
- `diagonal`: a one-cell-shifted spanning wall produces multiple four-neighbor components but one eight-neighbor component.

Each frame’s gate is sampled from a component with at least one zero cell.

**Original rationale:** all canonical chambers are connected after removing walls, so two plausible rivals fit every canonical pair: fill every non-wall interior zero, and use eight-neighbor reachability. Random walls do not guarantee either disagreement.

**Alternatives considered:** random sparse walls, random connected polyominoes, a single sealed profile, or a profile inferred after unconstrained generation. Random sampling can silently miss the distinctions; sealed alone does not prove the four-neighbor convention; post-hoc filtering complicates exact controls and can bias the support. Constructive profile families make the semantic property recoverable and testable.

**Probe/evidence:** `counterexamples/sealed_fill_all.json` differs from fill-all in 28 cells. `counterexamples/diagonal_joint_witness.json` differs from both named rivals in 19 cells. Both outputs were obtained from the selected Racket rule and are regenerated in focused tests. `workspace/probe_curriculum.py --racket` checks five canonical pairs plus both witnesses.

**Failure modes/limits:** profile membership is defined by connectivity counts, not by every possible visual topology. A future wall-family change must re-run both the independent observer and selected-Racket witness checks.

## 4. Five demonstrations, one query, period-three schedule

**Input choice:** set `EXAMPLES_NEEDED = 5` and schedule `open → sealed → diagonal` by `sample_index mod 3`. A six-pair lesson therefore contains each profile twice.

**Original rationale:** unknown. The prior generator had no semantic schedule. The repair target requires a training lesson to distinguish plausible rivals, including when any one labeled pair is held out as the query.

**Alternatives considered:** three demonstrations plus one query; four demonstrations plus one query; independent random profiles; or resampling until a lesson happened to cover witnesses. With fewer than six total pairs, a period-three profile can occur only once and be removed by a query rotation. Independent randomness has a nonzero omission probability. Resampling obscures the actual sampler and complicates replay. Six consecutive positions provide a simple deterministic guarantee.

**Probe/evidence:** focused tests enumerate six start offsets and every query position. `workspace/probe_curriculum.py` enumerates all three distinct schedule starts and all 18 start/holdout combinations. The production census materialized 100 lessons in each band: 300 lessons, 1,800 pairs, 1,800 rotations, zero declared-rival ambiguity, zero materialization/scoring errors, and 1,800 unique inputs (`checks/lesson-census.summary.json`). The source-bound schedule semantic gate passes (`checks/semantic-gate-schedule/result.json`).

**Failure modes/limits:** the schedule proves support for the declared rivals under the production consecutive-window assembly and single-query rotations. It does not prove uniqueness against arbitrary rules or under a different sampler that selects nonconsecutive positions.

## 5. Dimensions, placement, colors, and difficulty

**Input choice:** expose only exact `grid_h`, `grid_w`, and `profile` axes. Use canvas domains 15–17 and 20–22 in all bands, with easy weighted toward smaller values and hard toward larger values. Frame dimensions, legal placements, wall variant, gate color, and gate position remain deterministic keyed random details rather than public overrides. Gate colors are sampled without replacement from `{2,3,4,6,7,9}`.

**Original rationale:** canonical inputs use local rectangular frames, gray walls, frame color 8, and distinct non-reserved gate colors. There was no evidence that every internal placement choice needed to be a public contract.

**Alternatives considered:** expose every count and position; let difficulty change semantic profile; allow colors 0, 5, or 8 as gates; or retain a fixed canvas. Overexposing internal geometry makes compatibility promises difficult to honor; semantic difficulty weighting could break lesson coverage; reserved colors are ambiguous; fixed shape preserves positional shortcuts. The three public axes are directly observable and sufficient for boundary and witness probes.

**Probe/evidence:** the override gate passes across all axes and bands (`checks/override/result.json`). Focused tests independently observe every min/mid/max tuple in all four difficulty settings. Unknown, boolean, noninteger, out-of-range, and invalid-profile controls are rejected.

**Failure modes/limits:** difficulty is a dimension distribution label, not a monotone measure of reasoning difficulty. Exact frame/gate placements are not stable public axes.

## 6. Strict call validation and deterministic generation

**Input choice:** require plain integer `seed` and nonnegative plain integer `sample_index`; reject booleans, floats, and strings. Reject unknown overrides and invalid difficulty values. Use keyed `GenCtx` draws for all random choices and return fresh grids.

**Original rationale:** the first repaired draft delegated scalar coercion to the base context. Strict defect lint showed that booleans, floats, strings, and negative sample indices were accepted, making the public contract wider and less reproducible than intended.

**Alternatives considered:** coerce scalar-like values or leave validation implicit. Coercion aliases distinct calls and hides caller mistakes. Explicit validation is simpler and is covered by regression tests.

**Probe/evidence:** the defect-lint failure is retained at `checks/defect-lint/result.json`; the exact regression first failed in `checks/task-tests-strict-red/` and passes after the single fix in `checks/task-tests-strict-green/`. Final defect lint passes at `checks/defect-lint-green/result.json`.

**Failure modes/limits:** this is intentionally stricter than Python’s broad integer compatibility. `None` for advertised overrides retains the established “use the default draw” meaning.

## 7. Validation, oracle separation, and semantic contracts

**Input choice:** independently parse exact color-8 frames; reject non-ARC values, nonzero exterior cells, malformed frames, invalid interior colors, wrong gate/wall counts, empty traversable regions, or mixed profiles. Expose `observe_overrides`, a pure Python four-neighbor mirror, two named rivals, two named witnesses, and bindings for lesson and canonical-shortcut checks.

**Original rationale:** the old generator had no relevant validator or semantic contract. A distribution claim that cannot be recovered from pixels is not a reliable exact axis.

**Alternatives considered:** trust constructive generation without validation; use generator-private metadata as the observer; or declare natural-language rivals only. These cannot catch malformed mutations, silent axis drift, or teaching ambiguity. Pixel-level observation plus executable rivals lets shared tools test the actual instances.

**Probe/evidence:** destructive mutation and malformed-input tests pass. Lint, self-check, distribution, profile floor, semantic, diversity, override, grammar, Racket lint, and authority stages pass individually. Focused tests include real selected-Racket parity. The future-agent tool in `workspace/probe_curriculum.py` is source-bound and tested.

**Failure modes/limits:** the mirror shares some conceptual structure with generation, so selected-Racket parity remains the authority check. Declared rivals are finite.

## 8. Retained evidence and future-agent tool

**Input choice:** retain minimal JSON counterexamples and add `workspace/probe_curriculum.py` rather than only a prose report.

**Original rationale:** future reviewers need to replay the exact strongest shortcuts quickly, with source hashes and optional authority execution.

**Alternatives considered:** retain screenshots, full battery logs only, or a one-off notebook. JSON fixtures are diffable and tested; the command-line probe runs in both repository and staged layouts.

**Probe/evidence:** focused tests verify both fixtures regenerate byte-for-byte and that the probe reports the current generator hash, canonical shortcut fit, schedule rotation completeness, and witness distinctions. With `--racket`, it validates seven selected-rule cases.

**Failure modes/limits:** the probe intentionally checks the declared finite contract. It does not search arbitrary hypotheses or replace the production census.

## 9. Reference use and solve records

The blind task `d2708f8b731b` was solved before opening the assigned generator; the failed initial template attempt and successful second implementation are retained under `solve-blind/`. After repair, the exposed solve for `2d59c1b766d5` passed all five visible examples on its first revision; earlier rule exposure is declared `yes`, and no reference was consulted during that solve. These are process records, not generator qualification gates.

No prior return was used as factual evidence. The included passing `b90d4c3d5553` directory was consulted only for the shape of a good task-local contract and handoff.
