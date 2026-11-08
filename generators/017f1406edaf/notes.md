# Working notes: 017f1406edaf

## 2026-10-07 repair

Baseline version `3.0.0` had no pinned `RULE_HASH`, overlapping/dead `texture` declarations, difficulty-dependent override rejection, accepted unknown overrides, no executable semantic contract, and decoys that were attempted rather than guaranteed. A 2,000-seed probe found requested decoys missing in 18 blue-only draws, 426 row-0-only draws, and 566 `both` draws. The before battery failed lint, defect lint, and override, with profile and semantic stages advisory.

Version `4.0.0` preserves the Racket authority and replaces the sampler contract:

- exact axes are `grid_h`, `grid_w`, `K`, `n_blobs`, and `decoy`;
- difficulty reweights defaults but never narrows legal override values;
- canonical profiles reproduce the canonical size/palette statistics;
- counterexample profiles guarantee both exclusion decoys by default and make the target nonmedian;
- `self_check` and `observe_overrides` independently recover the advertised semantics;
- declared rivals cover counting all blue cells, admitting row-0 objects, and choosing the median-sized candidate;
- four-demo lessons alternate canonical/counterexample profiles and remain identifiable when any of the five materialized pairs is used as query.

An intermediate semantic-gate run exposed a lower-median edge case for two candidates. A new regression first reproduced it; `_counterexample_sizes` now forces the distractor below `K` when `n_blobs == 2`. The final task suite has 55 tests, the 12-stage after battery is all green, and the 300-lesson/1,500-rotation census found no ambiguity against the declared rivals.

Limits remain deliberate: examples have 2–4 isolated eligible blobs with distinct colors and distinct areas in 1–8, exactly one eligible match, fixed semantic colors `1` and `8`, and no no-match or multiple-eligible-match cases. The finite rival set does not prove unique induction against every possible hypothesis.

## Native parametric family

`workspace/parametric/` now implements `count_scope = row0 | all_blue`. `row0` is the exact canonical/default source; `all_blue` changes only the blue-count scope. Every matched input contains distinct eligible objects for both derived areas, lower blue cells, an excluded row-0 object, and distractors; target order swaps across examples. The adapter supports 2–6 demos and exactly four private queries, ending with a substantive 30×30 case. A protected-Racket self-audit covers both settings, seeds 0/17, demo boundaries 2/6, six plausible bypasses, stable prefixes, and 64 additional seeds. Native qualification and owner acceptance remain separate gates.

The sequential dependency is count scope -> input-derived target area -> eligible object selection/painting. A wrong-count witness must select a different object and output, not merely alter metadata. Finite seeds/rivals do not establish universal learnability or training value.
## Current reviewer considerations

Source SHA-256: `e80637ec485a311e67a526463fdf36166f860c7e21cb7885643ba710708edadd`.

# Decisions: 017f1406edaf

## D1 — Preserve the canonical Racket authority

**Choice.** Leave the Racket rule unchanged and pin `RULE_HASH = "e05af36c455d"`.

**Rationale.** Canonical pairs and the baseline rule smoke agreed. The observed defects were in input generation, override semantics, and teaching support, not label production.

**Alternatives rejected.** Rewriting the rule to force uniqueness or alter object order would have changed canonical semantics without evidence. A Python-produced output was also rejected; outputs remain owned by Racket.

**Probe and failure mode.** Final rule smoke and authority sync pass; the authority-set SHA-256 is identical before and after. Remaining risk is only untested behavior outside the generator's documented domain.

## D2 — Replace the axis contract instead of preserving misleading aliases

**Choice.** Advertise only five exact, observable controls: `grid_h`, `grid_w`, `K`, `n_blobs`, and `decoy`.

**Rationale.** Baseline `texture` overlapped semantic behavior and contained a no-op value. Several controls were declared broad but rejected by difficulty-specific draw bounds. A small contract that can be recovered from pixels is more useful than a large nominal one.

**Alternatives rejected.** Keeping `texture` as a palette alias would remain semantically dead because the task's colors have fixed roles. Declaring dozens of structured incompatibilities would preserve accidental complexity rather than fix it.

**Probe and failure mode.** `observe_overrides` recovers all five controls. The compact checker accepted 7,050/7,050 draws with zero findings; the full override stage also passes. Unknown axes and invalid values now raise. The contract does not expose exact candidate areas/colors individually.

## D3 — Difficulty reweights defaults but never changes legal override domains

**Choice.** Use common legal bounds in every band and add repeated favored values only to default sampling.

**Rationale.** An exact override should mean the same thing regardless of difficulty. Baseline easy-band calls rejected values that AXES declared legal.

**Alternatives rejected.** Band-specific valid ranges were rejected because the public contract did not express them and the override checker correctly treats controls as exact.

**Probe and failure mode.** Tests exercise a joint extreme override in all four band settings, plus every individual override domain through the framework checker. Extreme geometry still uses bounded construction retries and raises loudly instead of silently degrading.

## D4 — Alternate canonical and combined-counterexample profiles

**Choice.** Even sample indices use one of three canonical statistical profiles; odd indices use a combined counterexample. `EXAMPLES_NEEDED=4` makes an ordinary four-demo lesson contain two of each.

**Rationale.** Purely broad random sampling missed canonical dimensions/palettes, while purely canonical sampling preserved strong shortcuts. Alternation guarantees both fidelity and disambiguation without resampling labels.

**Alternatives rejected.** Independent random witness probabilities were rejected because a complete lesson could omit the needed distinction. A longer period was unnecessary and harder to prove rotation-safe.

**Probe and failure mode.** The profile floor is 28/60 exact and 28/60 envelope hits. Task tests cover eight consecutive starts and each of five query positions; the 300-lesson rotation census found 0/1,500 ambiguous rotations. This only covers three declared rivals.

## D5 — Use one grid to refute three canonical-compatible rivals

**Choice.** Counterexamples contain (a) a lower blue size-`K` decoy, (b) a nonblue size-`K` object touching row 0, and (c) an eligible target that is not the lower median by candidate area.

**Rationale.** The canonical demonstrations do not distinguish counting all blue cells, allowing row-0 candidates, or selecting the median-area candidate. Combining witnesses is token-efficient and makes every counterexample useful.

**Alternatives rejected.** Separate one-rival profiles would require a longer schedule and make query rotations fragile. Random decoy inclusion had already failed.

**Probe and failure mode.** `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS` are executable. The semantic gate verified all claims. Fixed colors are necessary semantics here; palette permutation was not used.

## D6 — Guarantee excluded decoys geometrically

**Choice.** Build a row-0-touching vertical nonblue size-`K` component first, choose markers away from it, reserve rows 0 and 1, then grow isolated lower blobs (including an optional blue size-`K` decoy). Return only after semantic observation matches the request.

**Rationale.** Baseline decoys could merge, be truncated, or fail to materialize. In 2,000 draws, requested blue/row0/both decoys were absent 18/426/566 times.

**Alternatives rejected.** Post-hoc relabeling was rejected because it can alter connectivity and candidate counts. Merely increasing placement attempts would not prove the requested feature exists.

**Probe and failure mode.** Known failing seeds are retained in tests; exact `decoy` observations pass across bands. The construction intentionally leaves a blank separator row and therefore does not cover touching lower objects.

## D7 — Keep candidate sizes distinct and exactly one eligible match

**Choice.** Generate 2–4 eligible blobs with distinct colors and pairwise-distinct areas, exactly one of area `K`.

**Rationale.** This gives a single teachable answer and makes object-area comparison visible. It also keeps the task aligned with all canonical pairs.

**Alternatives rejected.** Same-size multiple matches and no-match boards were rejected for this repair because the rule's row-major/blank behavior would introduce additional concepts not taught canonically.

**Probe and failure mode.** `self_check` enforces uniqueness and rejects mutations. Domain limitation: the sampler does not teach row-major tie resolution, no-match behavior, merged objects, or areas above eight.

## D8 — Correct the lower-median edge test-first

**Choice.** For two candidates, force the distractor below `K`; for three or four candidates, place all distractors on either side of `K` so the target is extremal.

**Rationale.** The retained median rival selects the lower median. With two candidates and an above-`K` distractor, the target was itself the lower median, so some counterexamples did not refute the rival.

**Alternatives rejected.** Removing the rival or weakening `lesson_identifiable` would conceal a real teaching defect. Increasing demo count was unnecessary.

**Probe and failure mode.** `checks/red-two-candidate-median.log` records 20 failing parameterized cases before the fix; the same cases pass afterward and the final semantic gate is green.

## D9 — Add an independent reusable oracle and portable tests

**Choice.** Put `reference_probe.py` under task workspace and tests under the selected task's `tests/` directory. The probe independently implements components, observations, intended behavior, and rivals.

**Rationale.** Reusing production helpers in tests would let one bug validate itself. Future agents need a small way to inspect distributions and semantic disagreements.

**Alternatives rejected.** Private `scripts` imports and fixed `parents[...]` paths were rejected because task tests must survive portable runtime snapshots.

**Probe and failure mode.** The explicit `task_tests` stage passed 55/55 in its isolated runtime. The probe is still a Python mirror; decisive output checks use `arcpuzzles apply` and Racket evidence.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/017f1406edaf/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
