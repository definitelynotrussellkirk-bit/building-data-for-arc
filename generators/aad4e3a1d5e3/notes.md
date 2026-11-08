# Working notes: aad4e3a1d5e3

## 2026-10-11 review repair

Baseline generator SHA-256: `ce1fafae099a4d4967326cb0099866276368f880a3af18e88f1094e56e64a790`.
Final generator SHA-256: `7be953b0ea06e73bf51c94e89de387fd9f7ee9c2a90ee3bf650a8dd4ae5e863a`.
Selected rule hash: `3fcc1761aea7`; the Racket authority was not changed.

The baseline had no rule pin, dead/unobservable axes, a one-color narrow distribution, no executable semantic rival, and a `self_check` that rejected none of 45 destructive mutations. The first repaired version passed 11/12 battery stages but kept identical easy/medium/hard defaults; defect lint correctly caught that restriction. Version 2.0.1 adds an observable motif-size curriculum and passes all final gates.

The final distribution stays near canonical dimensions while varying all four source quadrants, connected/split motifs, centered/off-center axes, 6..9 motif cells, two motif colors, and which guide owns the crossing. Horizontal-owned crossings refute the canonical-fitting “require an unbroken vertical 5-guide” shortcut. Every five-sample lesson has at least two such witnesses, so arbitrary one-pair query holdout leaves a witness.

Evidence:

- `checks/before/`: baseline battery, 5 green / 2 advisory / 5 failed.
- `checks/after-v1/`: intermediate battery, 11 green / 1 failed (dead difficulty bands).
- `checks/after-v2/`: final battery, 12/12 green.
- `checks/task-tests-final/`: 28 focused tests pass.
- `checks/required-rotations/`: required query-rotation semantic gate passes.
- `checks/lesson-census-final.json`: 300 lessons / 1,500 rotations, no ambiguity.
- `checks/schedule-census-final.json`: all 8 declared starts across 3 bands at seed 0, 120 rotations, no ambiguity.
- `counterexamples/require_unbroken_vertical_guide.json`: exact shortcut witness.
- `workspace/probe_shortcut.py`: reusable witness/canonical-fit probe.

Limits: the finite rival census does not prove unique induction against every possible rule. One of 1,500 pair slots duplicated another input (1,499 unique), reported without suppression.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl` with their original provenance.
## Current reviewer considerations

Source SHA-256: `7be953b0ea06e73bf51c94e89de387fd9f7ee9c2a90ee3bf650a8dd4ae5e863a`.

# Decisions for aad4e3a1d5e3

## D1 — Preserve the selected rule and repair only the lesson generator

The canonical rule is stable and the Racket authority already produces the expected canonical outputs: preserve the input and reflect every non-background, non-guide motif cell across the vertical color-5 guide and horizontal color-6 guide. I therefore left the authority unchanged and pinned its normalized hash as `RULE_HASH = "3fcc1761aea7"`. The final authority-sync and rule-smoke stages are green in `checks/after-v2/`.

Rejected alternative: changing the rule to require a perfectly continuous color-5 guide. That behavior fits the canonical demonstrations only because their guide intersections are all color 5; it is a shortcut, not the selected semantics.

## D2 — Replace decorative metadata with observable controls

The previous generator advertised many controls that did not affect the returned grid. The replacement exposes only exact, recoverable axes:

- dimensions: `grid_h` 10..12 and `grid_w` 11..14;
- motif size: `n_cells` 6..9;
- source quadrant: all four quadrants;
- motif topology: `connected` or `split`;
- horizontal and vertical guide placement: `center` or `off_center`;
- intersection owner: `vertical` (cell 5) or `horizontal` (cell 6).

`observe_overrides` recovers every axis from the grid, unknown keys fail loudly, and focused tests round-trip exact joint overrides in all difficulty bands. I rejected aliases such as generic “density,” “texture,” or “palette kind” because they were not needed to express the task and would have been hard to observe exactly.

## D3 — Stay near the canonical visual manifold while widening semantics

Five canonical-sized dimension profiles are scheduled: 11x13, 10x12, 12x14, 11x11, and 12x12. Every ordinary scene contains one near-full vertical 5-guide, one near-full horizontal 6-guide, and a two-color motif of 6..9 cells wholly within one quadrant. Reflections are guaranteed in bounds and initially empty. This keeps the generated task recognizable while varying guide placement, source quadrant, motif topology, colors, and motif size.

Rejected alternative: broad random dimensions and arbitrary sparse motifs. That would increase superficial diversity but weaken canonical-profile coverage and make malformed/clipped reflections more likely. Rejected alternative: single-color motifs. Two colors make preservation of per-cell identity visible and rule out a weaker “copy a monochrome silhouette” interpretation.

## D4 — Make difficulty observable without changing the rule

The first scheduled sample defaults to 6 motif cells in easy, 7 in medium, and 8 in hard; subsequent schedule positions span the rest of the 6..9 domain. This was added after the first repaired battery showed the three bands were byte-identical and defect lint correctly flagged dead difficulty. The final focused test records `[6, 7, 8]` for the same seed/sample across easy/medium/hard while all grammar and semantic checks remain unchanged.

Rejected alternative: making hard examples use a different rule or extra guide. Difficulty should alter search/visual load, not semantics.

## D5 — Teach against the strongest canonical-fitting shortcut

The strongest retained rival is:

> Reflect the motif only when the vertical color-5 guide is completely unbroken; otherwise return the input unchanged.

It fits every usable canonical pair because every canonical guide intersection is 5. The repaired generator alternates the intersection owner so horizontal-owned scenes contain a full row of 6 and a one-cell gap in the vertical 5-guide. Those scenes remain lawful under the selected rule and directly refute the rival.

The eight-position schedule has a horizontal-owned witness at every odd position. Any five consecutive materialized pairs therefore contain at least two such witnesses; holding out any one pair still leaves at least one witness among the four demonstrations. `workspace/probe_shortcut.py` materializes an exact case and `counterexamples/require_unbroken_vertical_guide.json` stores it. The selected Racket receipt is `checks/shortcut-witness-racket.json`.

Rejected alternative: add only one counterexample per five-pair lesson. That would make the lesson identifiable in its fixed ordering but ambiguous whenever that one witness became the query.

## D6 — Enforce a strict teaching grammar

`self_check` now rejects empty/ragged grids, invalid colors, wrong dimensions, missing/duplicated guides, stray guide colors, illegal intersections, motifs on an axis, mixed quadrants, clipped/occupied reflections, wrong motif size or color count, and motif unions outside the one-or-two-component contract. Degenerate fixtures cover these failure modes, and standard destructive mutations are tested. Generation calls `self_check` before returning.

Rejected alternative: use `self_check` only as a loose rule-lawfulness check. The old recognizer accepted every one of 45 destructive mutations, so it could not protect the intended lesson distribution.

## D7 — Evidence and limits

Final generator SHA-256: `7be953b0ea06e73bf51c94e89de387fd9f7ee9c2a90ee3bf650a8dd4ae5e863a`.

Measured final evidence:

- 12/12 after-battery stages green (`checks/after-v2/`).
- 28/28 focused task tests pass (`checks/task-tests-final/`).
- Required-rotation semantic gate passes (`checks/required-rotations/`).
- 300 production lessons, 1,500 pairs, and all 1,500 query rotations: zero ambiguity, hook warnings, materialization errors, or scoring errors (`checks/lesson-census-final.json`).
- Every declared schedule start at fixed seed 0 across three bands: 24 lessons and 120 rotations, all clear (`checks/schedule-census-final.json`).

These are finite checks against the declared rivals, not a proof of unique induction against every possible hypothesis. The large census contained 1,499 unique inputs across 1,500 pair slots; one duplicate does not affect labels or rival results but is reported rather than hidden.

## 2026-10-23 `None` override sentinel repair

Baseline generator SHA-256: `7be953b0ea06e73bf51c94e89de387fd9f7ee9c2a90ee3bf650a8dd4ae5e863a`.
Final generator SHA-256: `9644b3b42ef6fa3ab533b8cd8568523154f4996efff01354836fdeb6a6634752`.
Final focused-test SHA-256: `a4230f3c453ec78f5d792c851fd9fd5df5ddd26fdb8e6452ab9466ae2fa82fb1`.
The selected Racket rule/hash `3fcc1761aea7` was not changed.

The generator's scheduled-axis helper treated the mere presence of an override key as a concrete override. That contradicted the shared `GenCtx` contract, where `None` means “no override”: `axis=None` widened a scheduled singleton to the full random domain. A second key-presence check made `n_cells=None` bypass difficulty-band defaults. The repair changes both conditions to treat `None` as omission; concrete overrides keep their existing validation and pinning behavior.

`VERSION` remains `2.0.1` because ordinary/default generation is byte-preserved. The retained adversarial comparison found 0 mismatches across 256 baseline/current default calls (four seeds × four bands × sixteen samples), 0 mismatches across 576 omitted/`None` calls (four bands × nine override configurations × sixteen samples), and 0 failures across eight concrete override round-trips: `checks/none-override-adversarial.json`. The staged focused suite passes 29/29, including the new all-axis regression: `checks/task-tests-final-20261023/`. A representative hard-band `n_cells=None` grid matched the unchanged Python mirror and canonical Racket execution with rule hash `3fcc1761aea7`: `checks/none-override-racket-parity.json` and `checks/none-override-racket.json`.

Limit: the broad override-stage matrix was interrupted after 6,000 of 22,860 accepted draws with zero findings and is **not** counted as a pass (`checks/override-after/`). The bounded source-specific tests above cover the repaired sentinel contract, but they do not replace a future complete matrix run if maintainers require it.

## 2026-10-24 native parametric review `review-8b9ef40bf656e4bb`

The canonical production generator and selected rule hash `3fcc1761aea7` are unchanged. The new task-local native adapter preserves the exact canonical `complete_orbit` program byte-for-byte and adds one nearby episode-fixed `chain_only` setting. Both settings first reflect the source motif across the vertical guide. The canonical setting then reflects the complete intermediate across the horizontal guide; `chain_only` instead reflects only cells created by the vertical pass, producing source, vertical, and diagonal copies but no direct horizontal copy.

The adapter supports 2–6 demonstrations and independently 1–4 queries. Inputs are setting-neutral and count-independent, four queries are distinct, a one-query request exposes exactly the same first query as a four-query request, and the fourth query is a substantive 30×30 scene with 18 source-motif cells. Public exports reveal one query at a time and hash only visible bytes; settings, programs, answers, and future queries stay private. The authoring audit built four episodes and 16 one-query public views, then replayed 32 labels through protected Racket.

The finite teaching check tests both settings against `vertical_only`, `horizontal_only`, `diagonal_only`, `identity`, `horizontal_chain_only`, and the retained `require_unbroken_vertical_guide` shortcut. Two demonstrations leave only the selected setting among these declared rivals; six demonstrations do the same. This is bounded evidence, not universal uniqueness.

Sequential dependency: A reflects every non-guide motif cell across the vertical guide. Its input-dependent intermediate is the vertical-pass grid plus the exact colored cells present after A but absent from the original input. B reflects only those A-created cells across the horizontal guide. The protected witness replaces that worklist with the original motif: final output changes by 18 cells on a 13×15 query and 36 cells on the 30×30 query. Native qualification passed four jobs across both settings and seeds 0/17. Reviewer readiness does not grant owner acceptance or training admission.

Evidence:

- `checks/aad4e3a1d5e3/qualification/qualification.json` and sibling `execution.json` — native qualification, four jobs, protected Racket.
- `checks/aad4e3a1d5e3/causal/witness.json` and `replay.json` — two protected-Racket wrong-intermediate cases.
- `workspace/parametric/evidence/current/authoring-audit-manifest.json` — four episodes, 16 sequential public views, 32 Racket evaluations.
- `workspace/parametric/evidence/current/boundary-teaching.json` — 2/6-demo, 1/4-query, first-turn, finite-rival, and 30×30 checks.
- `checks/aad4e3a1d5e3-task-tests-after2/result.json` — 51 staged task tests pass.

Owner next action: integrate these exact bytes, rerun native qualification on the live source, replay the causal witness, and explicitly accept or reject the family. No training activation is claimed by this return.
