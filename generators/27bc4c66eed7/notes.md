# Working notes: 27bc4c66eed7

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b6dee800cf7404169e351298da0408f08477071d2d18aa8210e0da67575a9d78`.

# Decisions for `27bc4c66eed7`

## D1 — Treat the canonical Racket rule as correct and repair only the generator

**Original rationale:** unknown. The selected baseline’s prose described middle-cell extraction, and its Racket rule already implemented the canonical row-wise transformation.

**Evidence:** the baseline `rule_smoke` passed before repair; the canonical rule hash is `a6711bc4802c`; the final rule smoke and authority-sync stages pass. The mismatch was in the generator and validator, not the authority.

**Alternatives rejected:** changing the rule to odd-only or one-run-per-color behavior would fit the baseline generator but contradict canonical examples. No Racket source was changed.

**Failure mode / limitation:** the Python mirror is secondary evidence only. Official Racket application, rule smoke, and authority synchronization remain the authority checks.

## D2 — Replace the baseline grammar with 2–5 independent horizontal runs

**Choice:** allow 2–5 maximal runs, including multiple separated runs on one row.

**Why:** canonical inputs contain 2, 3, and 4 runs and include shared rows. Five runs provide a small extrapolative branch without creating dense or hard-to-separate scenes.

**Alternatives rejected:** retaining 2–3 runs failed canonical ownership; allowing arbitrary dense rows would make constructive non-overlap and visual parsing less reliable.

**Probe:** task-local boundary tests and the official self-check/profile stages. Final evidence: `checks/final-task-tests.log` and `checks/after/checks/27bc4c66eed7_after_profile_floor.log`.

**Limitation:** the generator does not attempt every possible number of runs the total rule could process; it defines a finite 2–5-run teaching domain.

## D3 — Cover lengths 1–5, with right-middle semantics for even runs

**Choice:** public exact `run_length` accepts `0..5`; `0` means a mixed scene, while `1..5` fixes all runs. Ordinary defaults cycle through mixed, 2, 3, 4, and 5; fixed 1 is explicit-only.

**Why:** the authority handles singleton, even, and odd runs. Canonical data already includes length 2, so an odd-only grammar was wrong. The exact midpoint is `start + length // 2`, giving the right-middle cell for even runs.

**Alternatives rejected:** left-middle for even runs contradicts the canonical rule; making all-singleton lessons ordinary produced identity-only scenes and triggered the strict defect gate.

**Probe:** `test_self_check_accepts_lawful_edge_cases_authority_handles`, the exact override matrix, and the retained intermediate failure in `checks/after-defect_lint-v2.log`.

**Limitation:** identity-only all-singleton scenes are not sampled by default, but `run_length=1` remains supported and tested.

## D4 — Guarantee a repeated-color counterexample every five samples

**Choice:** four canonical-scale anchor profiles plus one `adversarial_repeated_color` profile in a five-sample cycle.

**Why:** the strongest plausible canonical-fitting rival emits only the first midpoint of each color. Pure random color reuse could leave complete lessons without a refutation; a finite schedule guarantees one witness in every five consecutive demonstrations.

**Alternatives rejected:** always-distinct colors preserve the shortcut; probabilistic repeats provide no per-lesson guarantee; repeating colors in every example would overfit the teaching distribution to the adversary.

**Probe:** `workspace/lesson_probe.py` imports the exact source, iterates actual `CANONICAL_SHORTCUTS`/`LESSON_COMPETITORS`, checks the rival against every canonical pair, and tests all cyclic starts for 100 lessons per band. Results: 600 unique inputs per band and 0 surviving lessons for the rival.

**Limitation:** the modulo-five profile is position-correlated. The correlation is documented rather than hidden, and each lesson spans all residues.

## D5 — Keep canonical-scale shapes prominent

**Choice:** use exact 5×7, 5×9, 6×8 profile anchors and one broad adversarial branch; allow 5–7 rows and 7–10 columns.

**Why:** strict profile support should be visible in every band, not left to chance. The canonical profiles also preserve observed palette sizes and run-count scales.

**Alternatives rejected:** a fully broad uniform sampler had lower guaranteed canonical support; copying the canonical grids verbatim would sacrifice diversity.

**Probe:** official profile floor reports exact-profile 49/60 and envelope 53/60; the diversity stage reports 100% unique inputs and outputs over 300 pairs.

**Limitation:** the profile cycle favors canonical-scale dimensions rather than uniform coverage of the full declared rectangle range.

## D6 — Use colors 1–9 and expose only live controls

**Choice:** foreground colors draw from all 1–9 values. Public axes are only `grid_h`, `grid_w`, `n_runs`, `color_mode`, and `run_length`; every one is exact, observable, and tested.

**Why:** the baseline advertised several generic palette/texture controls that did not express meaningful task variation. A smaller truthful interface is easier to verify and less likely to create silent override failures.

**Alternatives rejected:** retaining dead compatibility axes would keep lint and override defects. Palette-size is a consequence of run/color mode, not an independent exact control in this constructive design.

**Probe:** 162 official override cases × three bands × seeds produced 14,580 accepted draws with no findings. Boundary combinations are also covered by 48 parametrized task-local cases.

**Limitation:** callers using undocumented baseline axes now receive an explicit unknown-axis error instead of silent acceptance.

## D7 — Exclude one visually ambiguous teaching case, not a rule case

**Choice:** `self_check` rejects a lone monochrome solid 2×2 while the rule mirror and Racket authority remain total over it.

**Why:** the strict defect probe correctly noted that this can be read as one 2D square rather than two independent horizontal runs. It is not needed to teach the intended row-run abstraction.

**Alternatives rejected:** claiming the shape is impossible would be false; changing the authority would be unjustified; silently accepting it left an ambiguity warning.

**Probe:** `test_ambiguous_monochrome_solid_2x2_is_outside_teaching_grammar` and `checks/after-defect_lint-v3.log`.

**Limitation:** this is a teaching-domain restriction. It is explicitly documented in `SUMMARY.md` and not presented as an authority restriction.

## D8 — Make the semantic contract executable

**Choice:** declare `repeated_color_runs`, `one_midpoint_per_color`, witness-to-rival mapping, canonical shortcuts, lesson competitors, and `lesson_identifiable`.

**Why:** prose alone cannot prove that the generator emits a disambiguating lesson. The official semantic gate and task-local probe can execute these declarations.

**Alternatives rejected:** hard-coding rival names only in a test would let source declarations drift; relying on a small battery lesson sample would undermeasure cyclic schedules.

**Probe:** semantic gate strict 600/600, 1/1 witness firing, 1/1 rival verified, 12/12 lessons identifiable; deep probe 100/100 lessons per band refute the rival.

## D9 — Use TDD and retain failed iterations

**Choice:** add tests before implementation and keep the RED/GREEN logs.

**Evidence:** initial RED was 54 failures / 1 pass; later RED cycles exposed the ambiguous 2×2 and identity-default regressions; final is 58/58 passing. Logs are under `repo/generators/27bc4c66eed7/workspace/`.

**Failure modes caught:** missing authority pin and semantic declarations, canonical rejection, override incompatibilities, dead rival coverage, 2×2 ambiguity, incomplete run-length span, and identity-only defaults.

## D10 — Prior evidence was a lead, never a substitute for measurement

The row in `repo/shared/data/derived/kimi_generator_assignment.jsonl` named only the missing rule hash and expected hash. I used that to prioritize inspection, then independently measured canonical rejection, dead axes, and the shortcut gap in this packet. No prior return was treated as proof that the selected baseline passed or failed a current check.
