# Current notes: 083ba0fc4534

Version `4.0.0`; final reviewed generator SHA-256 `64834ff6d839ceebb41e6c873a35adb946535899e91be8cba80527be313be9d4`; canonical Racket rule hash `076637306d69`.

## Intended rule

Two full-height gray (`5`) columns divide the input into three equal aligned panels. For each panel-local cell, output a nonzero color exactly when that same color occurs in at least two panels; otherwise output `0`. The output has one panel’s height and width.

## Current production domain

- height: 4 or 5
- panel width: 4 or 5
- foreground palette: exactly 2 or 3 colors, excluding 0 and divider color 5
- active panel-local positions: 5–7
- required positive evidence: one `ab`, one `ax`, one `bx`, and one `abc` cell
- required negative evidence: 1–3 cells with two occupied panels holding different colors

All advertised exact overrides are validated and recoverable through `observe_overrides`. The full Cartesian product is supported; there are no declared incompatible combinations.

## Reversed decisions

Version 3.0.0 used broad 3–8 by 3–7 dimensions, dense per-cell filling, a mixed helpful/degenerate `texture` axis, permissive validation, and four requested demonstrations. It also omitted an explicit two-color disagreement. Those choices were replaced because they drifted from the sparse canonical profile and allowed a wrong occupancy shortcut to fit both canonical and generated examples.

The canonical Racket rule was not changed. `self_check` still accepts lawful canonical sparse inputs with zero conflicts, while production generation requires at least one conflict so new lessons teach the distinction.

## Semantic contract

Declared competitors are:

- `first_nonzero_if_two_occupied`
- `left_middle_only`
- `left_right_only`
- `middle_right_only`
- `unanimous_only`
- `copy_left`

Each has an executable witness. `first_nonzero_if_two_occupied` is additionally declared as a canonical-fitting shortcut and is refuted by the retained Racket-backed counterexample under `counterexamples/occupancy-shortcut/`.

`EXAMPLES_NEEDED=2`. Final evidence found 12/12 smoke lessons identifiable with 0/36 ambiguous query rotations, and 300/300 wider-census lessons with 0/900 ambiguous rotations against the declared competitors.

## Known limits

The production pattern always has four positive branch cells plus one to three conflicts. This regular count is a generator prior, although locations, shapes, palettes, colors, conflict pairs, orientation, and counts vary. The finite declared-rival suite and sampled census do not prove unique induction against every possible hypothesis.

The Python probe in `workspace/probe_consensus_contract.py` is a cheap regression diagnostic, not Racket authority. Acceptance evidence remains in the source-bound Racket battery, semantic report, counterexample, and lesson census.

Imported associated notes were empty. In-repository generators were used only as contract examples, not as evidence for this source.
## Current reviewer considerations

Source SHA-256: `64834ff6d839ceebb41e6c873a35adb946535899e91be8cba80527be313be9d4`.

# Decisions for 083ba0fc4534

Final generator: version `4.0.0`, SHA-256 `64834ff6d839ceebb41e6c873a35adb946535899e91be8cba80527be313be9d4`, canonical rule hash `076637306d69`.

## D1 — Preserve the canonical Racket rule

**Prior choice:** version 3.0.0 implemented a Python mirror of the existing three-panel consensus rule, but did not pin its rule hash.

**New choice:** leave the Racket authority unchanged and declare `RULE_HASH = "076637306d69"`.

**Reason:** the canonical labels and rule-smoke check were already correct. The observed defects were sampler, validation, and lesson-teaching defects, not authority defects. Changing the rule would create needless semantic risk.

**Evidence:** final `rule_smoke`, `racket_lint`, and `authority_sync` stages are green in `checks/after/checks/083ba0fc4534_after_battery_summary.json`.

## D2 — Replace dense broad sampling with a sparse canonical-scale domain

**Prior choice:** v3 advertised height 3–8, panel width 3–7, helpful and degenerate `texture` modes, and filled every local coordinate from a branch pool. In ordinary draws that produced dense boards with many colors and a strong distribution gap from the three sparse canonical examples.

**New choice:** public exact axes are:

- `grid_h ∈ {4,5}`
- `panel_w ∈ {4,5}`
- `palette_size ∈ {2,3}`
- `n_conflicts ∈ {1,2,3}`

Each generated input has exactly four required positive branch positions plus `n_conflicts`, hence 5–7 active local positions.

**Reason:** canonical inputs use 4–5 rows, 4–5 panel columns, sparse activity, and small foreground palettes. The narrower domain keeps generated examples visually and combinatorially close enough to teach the same decomposition while still covering eight shape/palette profiles and all public values in every difficulty band.

**Rejected alternatives:**

1. **Keep the dense filler but cap the palette.** Rejected because density—not just color count—was a major shortcut and profile drift.
2. **Keep the `texture` axis and sample degenerates rarely.** Rejected because `no_agreement` and `all_three_agree` hide most of the law and complicate honest exact-control claims; they are better diagnostic probes than ordinary training examples.
3. **Match only the three exact canonical shape/palette tuples.** Rejected as unnecessarily narrow. The lawful 5×14 profile shares the same panel decomposition and passed authority/semantic checks, while 4×14, 4×17, and 5×17 canonical profiles remain covered.

**Evidence:** final distribution and profile-floor gates are green. `checks/consensus-probe-final.json` records all eight shape/palette combinations and complete axis support per band.

## D3 — Put every positive branch and a disagreement counterexample in every generated input

**Prior choice:** v3 required `ab`, `ax`, and `bx` on `plain` boards, but `_fill_cell` chose an “other” value that could create branch examples while never creating two occupied panels with two different colors and no agreement. The canonical examples also lack that case.

**New choice:** place one `ab`, one `ax`, one `bx`, one `abc`, and one to three explicit two-color disagreement cells in every generated input.

**Reason:** the wrong `first_nonzero_if_two_occupied` rule fits all three canonical pairs. A disagreement cell is the smallest lawful input on which it differs from the selected rule. Requiring that witness in every production sample prevents an entire two-demo lesson from accidentally omitting it.

**Rejected alternatives:**

1. **Rely on probabilistic witness frequency.** Rejected because a good marginal frequency can still produce an ambiguous complete lesson.
2. **Add the conflict only in hard mode.** Rejected because the shortcut is not a difficulty concept; easy and medium training data also need the negative.
3. **Use lone occupied cells as the only negative.** Rejected because the occupancy rival already outputs zero for one occupied panel and therefore survives.

**Evidence:** Racket-backed minimal repro in `generators/083ba0fc4534/counterexamples/occupancy-shortcut/`; 600/600 semantic witness hits; 300/300 probe refutations in `checks/consensus-probe-final.json`.

## D4 — Separate validator support from production strictness

**Choice:** `self_check` accepts lawful sparse canonical inputs with zero conflicts, while the production sampler and public `n_conflicts` axis emit only 1–3 conflicts.

**Reason:** a validator should not reject the selected canonical examples merely because production data is strengthened against a shortcut. Conversely, accepting the canonical zero-conflict manifold does not require continuing to generate shortcut-ambiguous lessons.

**Failure mode considered:** making `self_check` require a conflict would have caused canonical support failure; making generation permit zero would have reintroduced R1.

**Evidence:** self-check and strict-profile stages pass, all three canonical inputs are accepted, and production probes have a minimum conflict count of one.

## D5 — Make every advertised override strict and observable

**Prior choice:** v3 read overrides opportunistically, allowed unknown keys to pass into context machinery, and exposed a `texture` axis whose behavior mixed ordinary and degenerate domains. It had no `observe_overrides` hook.

**New choice:** reject unknown, boolean, coerced, and out-of-domain values before sampling; use `ctx.draw_*` for all exact controls; recover all four axis values from returned pixels in `observe_overrides`; declare no incompatible combinations because the Cartesian product is fully legal.

**Reason:** an exact-control API is useful only when every declared value is both generatable and verifiable. A small fully supported product is preferable to a broad domain with silent coercion or undeclared pairwise failures.

**Evidence:** override stage green; task-local tests cover every axis value in all bands, unknown/retired keys, booleans, strings, out-of-range values, and observational round trips.

## D6 — Use two ordered demonstrations, while requiring query-rotation robustness

**Choice:** set `EXAMPLES_NEEDED = 2`; production lessons use two ordered demonstrations and one query. Retain a `lesson_identifiable` hook against all declared competitors and test every held-out pair as query in the census.

**Reason:** every generated input independently contains all required branch and shortcut witnesses, so two demonstrations are sufficient for the declared competitor set. The second demonstration adds diversity rather than patching missing branch evidence.

**Rejected alternative:** retain v3’s four-demo default. Rejected because it adds tokens without increasing declared-rival separation on the final sampler.

**Evidence:** semantic smoke: 12/12 lessons identifiable, 0/36 ambiguous rotations. Wide census: 300/300 materialized, 0/300 production ambiguities, 0/900 ambiguous rotations. See `checks/after/checks/083ba0fc4534_after_semantic_gate.json` and `checks/lesson-census-final.json`.

**Limit:** these are finite declared-rival checks. They do not prove uniqueness against every possible hypothesis.

## D7 — Retain a cheap future-agent probe, but keep Racket as authority

**Choice:** add `workspace/probe_consensus_contract.py` and a focused test for it.

**Reason:** future reviewers can cheaply detect regressions in branch presence, axis support, canonical-shortcut fit, mirror behavior, and declared rival separation before running the expensive Racket battery. The tool discovers competitors from generator declarations instead of duplicating names.

**Boundary:** its independent Python mirror is diagnostic only. Acceptance remains source-bound to the Racket rule smoke, semantic gate, and lesson census.

## D8 — Evidence and prior-review use

`evidence/associated_notes.jsonl` was empty, so no prior return supplied current-source measurements. I used `generators/b90d4c3d5553/` and `generators/8f10b83435aa/` only as in-repository contract/authoring patterns; their task-specific distributions and claims were not copied as evidence for this task. All counts in this return are from the assigned baseline or final source and are bound to the hashes named above.

## 2026-10-24 native parametric admission handoff

Built a native episode adapter under `workspace/parametric/` with one episode-fixed parameter, `agreement ∈ {majority, unanimous}`. `majority` preserves the exact canonical program; `unanimous` is a lawful alternate rule over the same generated inputs. The adapter supports 2–6 demonstrations and exactly four distinct queries, including a substantive 30×29 case (30×30 is incompatible with three equal panels plus two divider columns because width must equal `3p+2`).

The bounded protected-Racket teaching audit used seeds 5 and 23 at both 2- and 6-demo limits. Across eight jobs and 226 Racket evaluations, only the selected setting survived the demonstrations; tested rivals were the other setting, exactly-two agreement, color-blind occupancy, and fixed-divider lookup. Public projection hides settings, programs, answers, future queries, and total query count.

Sequential dependency: A discovers the two full-height gray divider columns; its input-dependent intermediate is the divider pair/panel width; B uses those offsets to compare aligned cells and apply the selected agreement predicate. The retained 30×29 witness shows fixed dividers `[4,9]` instead of discovered `[9,19]` change both output width and content.

Native qualification is `qualified` for both settings at seeds 0 and 17 with three demonstrations and four queries. This is reviewer-ready only: exact-source owner integration, fresh qualification, and owner acceptance remain pending; no training data was admitted.

Packaging preflight caught that the first retained causal witness used a task-local schema rather than the owner replay schema. The probe now requires a qualified native receipt, copies its exact `source_binding`, emits `arcpuzzles-sequential-dependency-witness-v1` with the minimal protected-Racket identity, and is pinned by a regression test. The final report and witness were regenerated against the final qualification and were byte-identical to the provisional source-bound run.
