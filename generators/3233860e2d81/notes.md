# Current notes: 3233860e2d81

## Intended rule

Count every nonzero color over the complete grid, sort by descending total count (numeric ascending only as a deterministic tie-break), and return the top three colors as a 3×1 column. Canonical rule hash: `3087638f0586`.

## Current generator decision

Version `4.0.2` supports 3–7 pairwise-distinct nonzero totals. Most lessons use 4–7 colors so top-three selection is nontrivial. A source-independent schedule (`sample_index % 13 in {0,8,12}` with no overrides) emits 12×12/three-color inputs to preserve the exact canonical profile.

The highest-total color is split into 2–3 components, and one randomly selected non-winner is split into two components. Accepted grids must refute both executable rivals:

- `largest_component` — rank by largest connected component;
- `fragment_count_then_size` — rank by number of components, then largest component.

This is a deliberate reversal of the first repair iteration, which split only the winner. That fixed the prior largest-component shortcut but made fragmentation a unique winner marker. Red/green evidence is retained under `checks/tdd-red-fragmentation/` and `checks/tdd-green-fragmentation/`; final authority witnesses are in `counterexamples/`.

## Input controls

Exact controls are `grid_h`, `grid_w`, `n_colors`, `min_count`, `min_count_gap`, and `count_distribution`. Types are strict (`bool` is rejected as an integer); explicit `None` means omitted. Full semantic tuples and dimension pairs are filtered jointly so standalone controls remain feasible in every band. Count profiles are deliberately distinct even at three colors.

## Parametric prototype

`workspace/parametric/` proposes episode-level `top_k ∈ {2,3,4}` with canonical/default `3`. It materializes and executes separate Racket for each setting and checks production and rotated queries. It is not part of the selected production rule or approval.

## Evidence and limits

Final focused tests: 49 pass. The one-seed override matrix covers 2,115 case/band combinations with no mismatches or undeclared rejections. Final battery and larger lesson-census evidence are under `checks/after-final-v2/` and `checks/lesson-census-final.json`.

The finite rival set does not prove universal identifiability. Tie totals are outside the generated manifold. The inherited frozen root fixture has a nonportable canonical path and blocks aggregate task-test collection; it was not edited, per packet instructions.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-900ed6c160ef9a05:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `8b41f359f950740d0f713b3a8f2c9abb0b425f481ec986aeb76dddb26f941147`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit resolution on accepted f4ef4d77aa7dd11df081d72b9c39442513dd98adacbb639feda4e979ff7fd1a9: generated scenes fragment winner and nonwinner, and both largest_component and fragment_count_then_size executable rivals are refuted. Final counterexamples retained in counterexamples/largest-component-repair.json and fragmentation-marker-repair.json. Reviewer reports12/12 battery,49 focused regressions,63450 override draws,600/600 witness triggers per rival,60 source-bound oracle disagreements per rival,300 lessons/1200 query rotations unambiguous. Old audited source 8b41f359f950740d0f713b3a8f2c9abb0b425f481ec986aeb76dddb26f941147. No owner task rerun; finite competitor scope and aggregate frozen-fixture failure remain explicit.

### Assessment or prior finding

## 3233860e2d81

**Possible shortcut reproduced: rank colors by largest connected-component size rather than total color count.** Ordinary `generate()` outputs 4–7 colors with exactly one connected component per color, so this rival is observationally identical to the intended total-count rule on every generated input. The generator therefore never teaches aggregation across separated fragments.

A validator-lawful canonical input provides an exact disagreement: total counts are color 3 = 8, color 2 = 7, color 8 = 4, so the Racket answer is `[[3],[2],[8]]`; largest component sizes are color 2 = 7, color 3 = 7+1 fragments (largest 7), color 8 = 3+1 (largest 3), with numeric tie-break giving `[[2],[3],[8]]`. The input and both outputs are in `checks/audit/3233860e2d81/counterexample.json`; `checks/audit/3233860e2d81/racket.json` is the supported authority receipt for generator SHA `8b41f359f950740d0f713b3a8f2c9abb0b425f481ec986aeb76dddb26f941147` and rule hash `3087638f0586`.

This is a curriculum/domain gap, not a bad label. The canonical demonstrations themselves include the counterexample, but ordinary generated lessons do not. I left the audit target unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-900ed6c160ef9a05-v0001/audit_assets.json), manifest SHA-256 `12a2bb0f3ab96a733a0655fd5f19002177343ff01a3ca456cbf7b4e8a2f6edaf`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `f4ef4d77aa7dd11df081d72b9c39442513dd98adacbb639feda4e979ff7fd1a9`.

# Decisions for 3233860e2d81

## D1 — Preserve the canonical rule

**Choice.** Keep rule hash `3087638f0586`: count every nonzero color over the whole grid, rank totals descending with numeric ascending as a deterministic tie-break, and return the top three as a 3×1 column.

**Why.** All eight canonical labels pass and the concrete defect was curriculum/domain coverage, not authority. Changing the Racket rule would hide the generator shortcut rather than repair it.

**Rejected alternatives.** Ranking by largest component, first scan occurrence, bounding-box size, numeric color, or fragmentation count. Final-source counterexamples under `counterexamples/` distinguish the two strongest topology rivals.

## D2 — Prototype `top_k`, but keep it outside production

**Choice.** Build a task-local proposed parameter `top_k ∈ {2,3,4}` with default `3`, chosen once per episode.

**Why.** It changes the executed transformation while preserving the family's exact reasoning: global counts → ranking → prefix selection. Five distinct-count input colors make all settings observable. Seeds 0–2 cover all values; all Racket labels and rotations are retained in `checks/parametric/top-k-s0/`.

**Rejected alternatives.** Canvas size, palette, and count-gap controls are sampler parameters, not rule parameters. A changing output color would be cosmetic and unrelated to the original abstraction.

**Limit.** The packet has no production parametric-rule API. The prototype is proposed only.

## D3 — Restore exact canonical-profile support with a fixed schedule

**Choice.** With no overrides, sample indices whose residue modulo 13 is `{0,8,12}` use 12×12 grids with three nonzero colors. Other draws keep the broad 4–7-color selection curriculum.

**Why.** Baseline ordinary sampling had 0/60 exact-profile hits. The final schedule measured 17/60 pooled hits and support in all bands (6/6/5), while most lessons still require selecting three from a larger palette.

**Rejected alternatives.** Always using three colors collapses “top three” into “return every color.” Always using 4–7 colors fails the required canonical profile floor. A random probability would make support less replayable than a source-independent residue schedule.

## D4 — Use distinct, observable count-gap profiles

**Choice.** Keep `ascending` gaps `[g,g,…]`, `tight_spread` gaps `[g,g+1,g,…]`, and `wide_spread` gaps `[g,g+2,g+4,…]`.

**Why.** The prior `wide_spread` formula was identical to `tight_spread` when only three colors were requested. The revised formulas remain distinguishable at the smallest legal palette.

**Probe.** `test_three_color_distribution_override_is_observable`; red/green evidence in `checks/tdd-red-override/` and `checks/tdd-green-override/`.

## D5 — Select dimensions and semantic controls jointly

**Choice.** Enumerate complete feasible semantic tuples, compute their minimum area, then draw only dimension pairs that admit at least one tuple. After dimensions are fixed, draw semantic values from the surviving tuples.

**Why.** Drawing defaults too early made standalone overrides such as `grid_w=5, n_colors=7` spuriously impossible. Joint filtering honors every advertised exact control and reserves incompatibility errors for genuinely impossible combinations.

**Probe.** The exhaustive one-seed matrix checked 705 cases in each band: 2,115 accepted, zero mismatches/rejections (`checks/override-preflight-final-v2.json`).

## D6 — Fragment a winner and a non-winning decoy

**Prior choice.** The first repair split only the highest-count color into 2–3 pieces, making its largest piece smaller than the runner-up total. That correctly refuted largest-component ranking.

**Reversal.** Split one randomly chosen non-winner into two pieces as well. Require every accepted grid to disagree with both `largest_component` and `fragment_count_then_size`.

**Why.** Winner-only fragmentation introduced a new shortcut: component count identified the winner, then component size ranked the rest. The failing regression is retained in `checks/tdd-red-fragmentation/pytest.log`; final witnesses are source-bound in `checks/counterexamples/final/racket.json`.

**Rejected alternatives.** Fragmenting every color needlessly increases object count and geometry failures. Fragmenting a fixed rank such as the smallest color leaks another stable rank marker. Choosing a random non-winner and filtering explicit rivals is both simpler and less correlated.

**Limit.** Other undeclared topology heuristics may exist; the finite rival set is not a universal proof.

## D7 — Strict public API types and `None` omission

**Choice.** Require exact `int`/`str` types, reject booleans, reject negative sample indices and unknown difficulties/axes, and treat an explicit `None` override as omitted.

**Why.** Python's `bool` is an `int` subclass; the baseline accepted values such as `min_count_gap=True`, producing misleading override coverage. `None` omission supports stable caller option dictionaries without changing generation.

## D8 — Synchronize selected authority representations only

**Choice.** Apply the tool-generated authority-sync proposal only to the selected `racket_target.target_code` fields in the two baseline solution JSON files.

**Why.** Execution parity already passed; divergence was formatting only. The canonical ledger, rule text, callable hash, and rule hash remain unchanged. Archival raw code was left untouched.

## D9 — Do not modify the inherited frozen fixture

**Choice.** Report aggregate task tests as blocked.

**Why.** The fixture hard-codes source-tree depth and fails portable preflight before pytest collection. `DUTIES.md` explicitly says it is frozen and maintainer-owned. New tests are in the permitted task-local test file and pass independently.

## Evidence and stopping condition

Final acceptance is conditional only on the shared fixture migration. The task-local stopping condition is: final-source battery complete, larger declared-rival lesson census complete, 49 focused tests green, final solve bound to the same source, audit sections written, and fresh patch replay verified. Measured limitations are reported rather than converted into approval claims.
