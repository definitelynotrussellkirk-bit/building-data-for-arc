# Working notes: b5df32f2dc17

## 2026-10-04 review-bc14f34072838c20

The selected 3.0.0 baseline passed the full 12-stage battery but its ordinary distribution was semantically homogeneous: a paired 600-draw census found every row in every scene had the same run count, needed reordering, and used ascending colors. The three canonical scenes instead contain already-sorted rows, blank rows, and a singleton test row.

Version 3.1.0 retains the canonical Racket authority and four exact axes while interpreting `n_runs` as the maximum per-row run count. Every ordinary scene contains a reorder witness, an offset already-sorted control, and an offset singleton control; blank controls are used when palette capacity permits. Two executable rivals were added: `multi_run_rows_only` and `leave_already_sorted_rows`.

The first large rotated census exposed a stale hook-only warning: rotations containing only three-run demos still refuted all six rivals, but `lesson_identifiable` separately required a two-run demo. A test-first repair removed that redundant profile condition; schedule-profile coverage remains independently checked. Final evidence is in `checks/after-final/`, `checks/lesson-census-final.json`, and `checks/row-role-census-after-final.json`.
## Current reviewer considerations

Source SHA-256: `618fff41de2f61b0f4e2764be354142f6eb9f51645713ecb1f6ce2a03ff19c93`.

# Decisions: b5df32f2dc17

## D1 — Treat retained prior notes as leads, not current proof

The retained `local-random-4373ff77cbf2` notes correctly identified the rule, exact override surface, and four previously modeled rivals. I used them as design context only. I reran the full baseline battery and generated a new paired census against the actual selected source; no prior result was treated as current evidence merely because it appeared in `associated_notes.jsonl`.

## D2 — Repair the curriculum rather than the authority

The selected Racket program, Python mirror, canonical examples, and generated outputs agreed. The defect was what the generator taught, not what the task meant. Therefore the patch leaves canonical/Racket source unchanged and changes the ordinary scene distribution in `generator.py`.

Rejected alternative: change the Racket rule or canonical row to accommodate the baseline distribution. That would alter correct semantics to fit weak examples and was unsupported by the parity evidence.

## D3 — Require mixed row roles inside every ordinary scene

Every normal scene now includes:

1. a multi-run row whose order must change;
2. an offset multi-run row already in descending-length order, which still must be left-repacked;
3. an offset singleton row, which also must be left-repacked; and
4. a blank row whenever height/palette capacity allows it.

This directly encodes the row-wise scope and mandatory repacking behavior visible across the canonical set. It avoids relying on chance frequencies that could leave complete lessons shortcut-compatible.

Rejected alternative: independently randomize row types. That improves aggregate diversity but does not guarantee any one scene or lesson contains the controls needed to reject a shortcut.

## D4 — Define `n_runs` as the maximum per-row run count

The baseline effectively made `n_runs` the run count of every row, which caused the homogeneous curriculum. Version 3.1.0 preserves exact observability by defining `n_runs` as the maximum positive run count in the returned grid. This permits singleton, blank, and multi-run rows together while allowing `observe_overrides()` to recover the requested value exactly.

Rejected alternative: keep all rows at `n_runs` and merely change their ordering. That would still omit row-wise controls and continue teaching “only multi-run rows matter.”

## D5 — Preserve the exact override corner without weakening axes

At `grid_h=3`, `grid_w=11`, `n_runs=2`, `palette_size=6`, all six palette colors must appear and three rows provide exactly six two-run slots. A singleton would make the palette request unobservable. That corner therefore uses one reorder row plus two already-sorted two-run controls; the ordinary default distribution still emits singleton controls in every sampled scene.

Rejected alternatives:

- weaken or remove `palette_size` exactness;
- silently use fewer than six colors;
- encode multiple colors in one run;
- introduce length-one runs solely to create extra slots.

Each would violate an existing exact axis or the declared clean teaching grammar.

## D6 — Model the two newly exposed shortcuts explicitly

I added `multi_run_rows_only` and `leave_already_sorted_rows` to executable lesson competitors/semantic rivals and added witnesses tied to the new controls. The existing four canonical shortcuts remain unchanged because the new rivals do not fit every canonical pair and therefore are lesson competitors rather than canonical-shortcut claims.

The focused tests were written red first (`checks/tdd-red-task-tests/`) and then passed after implementation (`checks/task-tests-final/`).

## D7 — Vary color order independently of length order

The baseline used ascending colors on every multi-run row, creating an unnecessary correlation between run position/color and the transformation. The repaired distribution emits both ascending and descending color orders while keeping colors distinct within a row. This makes color-sort rules less attractive without adding irrelevant texture.

Rejected alternative: arbitrary unrestricted color repetition. Same-colored separated runs can merge after repacking and complicate the intended run identity, so the generator retains distinct colors per multi-run row.

## D8 — Remove the stale hook condition, not lesson diversity

The first 300-lesson census had zero rival ambiguity but 198 hook warnings because `lesson_identifiable` separately demanded a two-run example in every rotated demo subset. Rotated all-three-run subsets still refuted all six declared rivals, and the deterministic schedule/profile tests separately verify two-/three-run coverage. I captured this exact warning as a failing regression (`checks/tdd-red-rotation-hook/`) and removed only the redundant profile check.

Rejected alternative: force each query rotation to retain a two-run demonstration. That couples identifiability to an incidental profile rather than actual rival survival and is impossible for some hold-out choices without duplicating examples.

## D9 — Keep a reusable task-local census tool

`workspace/row_role_census.py` compares canonical and generated support for row roles, run counts, length-order templates, and color-order patterns. It reads the generator’s actual declarations and reports source hashes/sampling formulas, so later edits can reproduce this review’s key measurement instead of depending on prose.

## Remaining limitations

- The exact height-3/six-color corner cannot include a singleton while keeping every axis exactly observable.
- Blank controls occur only when capacity permits: 413/600 in the final paired sample.
- Equal-length ties and length-one runs remain outside generated teaching grammar although the authority handles them.
- Named-rival and finite-census success is strong evidence, not a proof that no unknown shortcut exists.

## 2026-10-25 native parametric review `review-905638ee737372d6`

The production generator and canonical Racket authority remain unchanged at SHA-256 `618fff41de2f61b0f4e2764be354142f6eb9f51645713ecb1f6ce2a03ff19c93` and `5afe989c75c537b73cc0c2233c696d662dfd8762c3ff4599cd06e3ea27742339`.

A native episode-fixed family now exposes `length_order=descending` (the exact canonical default) and `length_order=ascending`. Both settings extract maximal nonzero runs independently per row, retain row/start/length/color records, sort by the selected length direction with original start as the tie-breaker, and then repack complete runs flush left with one zero separator.

Teaching scenes deliberately mix rows that need reordering, already-descending and already-ascending offset controls, singleton offsets, equal-length ties, and blanks. The two-demo constructor retries deterministically until the intended policy alone survives among retained keep-order, color-sort, position-preserving, multi-run-only, already-ordered, extreme-only, and wrong-tie candidates. The family supports independent 2–6 demonstration and 1–4 query counts, stable prefixes, matched inputs, four distinct private queries, and one-query public projection.

The 30×30 query contains 433 foreground cells, touches all boundaries, and differs by 353 cells across settings. Protected evidence: 16 staged tests; a 96-evaluation self-audit; 40 native qualification labels; and a source-bound causal replay where substituting canonical descending order for the qualified ascending intermediate changes 82 cells. Owner exact-source acceptance remains pending and `training_admitted` remains false. The finite rival set and seed sweep do not establish universal uniqueness.
