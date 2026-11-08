# Generator notes: 9e47b59d6afc

## Intended rule

The input contains one connected red(2) shape and one connected green(3) shape on background 0. Normalize each shape independently to its own bounding-box origin, overlay the normalized cell sets, and emit shared cells as 8, red-only cells as 2, and green-only cells as 3. The canonical Racket authority is unchanged and pinned by `RULE_HASH = "cc8053a66713"`.

## Current sampler (v3.3.0)

Generation is constructive. It deterministically enumerates normalized connected shapes in a 3×3 box and retains 144 ordered pairs with distinct authoritative outputs, nonempty overlap, exclusive cells for both shapes, and disagreement with a filled-bounding-box shortcut. Seed/sample index select a profile; red and green are placed in opposite corners on an eight-profile canvas schedule containing all canonical sizes plus broader canvases.

Exact public overrides are `grid_h` (9..13), `grid_w` (11..15), and `placement` (`red_nw|red_ne|red_sw|red_se`). They round-trip through `observe_overrides`. Unknown, retired, malformed, or out-of-range controls raise; shape profile is internal sampled state exposed by `observe_profile` for diagnostics.

## Semantic contract

`expected_output` is the Python oracle. Witnesses test independent normalization, overlap color 8, and cell-shape rather than bounding-box reasoning. Declared rivals are `keep_input_spacing`, `red_wins_overlap`, `green_wins_overlap`, and `overlay_filled_bboxes`; `lesson_identifiable` requires the demonstrations to refute them for the query.

## Reversed choices and evidence

The prior generator used capped random placement and returned the current grid after failure; a forced-exhaustion probe returned a blank 13×13 grid. It also advertised controls that were dead or metadata-only and lacked a semantic lesson contract. The current constructive sampler removes the fallback path, retires those controls, pins the rule, and adds strict validation plus executable rivals. Reproducer: `counterexamples/baseline_forced_exhaustion_blank.json`; full receipt: `checks/baseline-source/fallback_repro.json` in the review workspace.

## Verification and limits

Final generator SHA-256: `e350f01e1fbe0c029450c31a655409b0a995642a4812faa5a3c48eea8afcf07e`. The final battery has 12/12 green stages; task-local tests have 44/44 passing cases; 12/12 three-demo lessons and all 48 diagnostic query rotations were identifiable against tested rivals. Known limits: fixed role colors, opposite-corner presentation, a finite 3×3 shape bank, no declared schedule period, and no claim of universal identifiability against undeclared rivals.
## Current reviewer considerations

Source SHA-256: `e350f01e1fbe0c029450c31a655409b0a995642a4812faa5a3c48eea8afcf07e`.

# Decisions — 9e47b59d6afc

## D1 — Replace rejection sampling, not merely increase attempts

**Prior choice:** the baseline randomly placed shapes inside a capped loop and returned the current grid after exhaustion. **New choice:** construct both shapes directly in opposite corners and never expose a partial fallback. Increasing the attempt cap would only reduce, not remove, R1; the forced `_free=False` reproducer proves the old control flow could emit an invalid blank grid. Evidence: `checks/baseline-source/fallback_repro.json` and task-local counterexample `generators/9e47b59d6afc/counterexamples/baseline_forced_exhaustion_blank.json`.

## D2 — Use a deterministic bank of 144 strong shape pairs

I enumerated normalized 4-connected shapes inside a 3×3 box, then retained the first ordered pair for each distinct authoritative output that has shared cells, exclusive cells on both sides, and disagrees with the filled-bounding-box rival. This gives 144 distinct semantic outputs without generation-time rejection. A small hand-written bank was rejected after lint correctly showed insufficient output diversity; retaining all connected pairs without semantic filters was rejected because it would reintroduce weak/ambiguous lessons.

## D3 — Keep only observable exact controls public

`grid_h`, `grid_w`, and `placement` remain advertised because each is exact and round-trips through `observe_overrides`. The baseline's palette/texture-style controls and singleton/meta controls were retired because they were either fixed by the rule, dead, or not observable. A public 144-value `shape_pair` enum was briefly considered, but defect lint would have to enumerate a large control domain and the axis is not needed by downstream callers; shape profile therefore remains deterministic sampled state exposed only through `observe_profile` for diagnostics.

## D4 — Anchor canonical support while broadening canvas size

The eight-entry dimension schedule includes all three canonical input sizes `(9,11)`, `(10,12)`, `(11,13)` and five broader canvases through 13×15. Difficulty shifts the schedule rather than restricting grammar. This reversed the baseline hard-band zero-support finding while avoiding a canonical-only distribution. Final profile-floor evidence: 21 exact hits and 25 envelope hits across 60 draws, with exact support in every band.

## D5 — Make grammar and validation strict

The sampler accepts only integral nonnegative seed/sample index, the known difficulty bands, and declared overrides with strict types/ranges. `self_check` validates rectangularity, legal colors, exactly one connected object per role, spatial separation, normalized overlap, and exclusive cells for both shapes. `strict_canonical_like` adds the canonical-size/palette profile, while `expected_output` is a standalone Python oracle used only for authoring checks.

## D6 — Encode the teaching contract as executable rivals

Three witness classes cover independent normalization, cyan overlap coding, and cell-shape rather than filled-bounding-box reasoning. Four named rivals implement the natural shortcuts: preserve input spacing, let red win overlap, let green win overlap, and overlay filled bounding boxes. `lesson_identifiable` requires every three-demonstration window to refute all declared rivals for the labeled query. The final semantic smoke measured 12/12 ordered lessons identifiable and 0/48 ambiguous diagnostic rotations.

## D7 — Leave the Racket authority unchanged

All four canonical pairs matched the independent Python oracle and the pinned rule hash `cc8053a66713`. Rule smoke, Racket lint, authority synchronization, and execution parity passed, so changing the reference rule would add risk without correcting a rule defect.

## D8 — Do not overclaim a large lesson census

The actual declared rivals each matched 0/4 canonical pairs (`checks/canonical-rivals.json`). DUTIES requires at least 100 lessons per band when plausible rivals fit canonical pairs; that condition was false, so I did not run the larger census merely to manufacture a stronger-looking claim. The retained 12-lesson/48-rotation smoke is finite evidence only; undeclared hypotheses and all possible schedule starts remain outside the claim.

## D9 — Preserve interrupted and failed evidence

The aggregate battery exceeded the outer command timeout more than once while its short child stages continued to checkpoint; I used the supported `--resume` path with unchanged source/settings until all 12 stages were green. Earlier final-source interruptions remain under `checks/after/` journals and `checks/after-v1-interrupted/`. The new counterexample characterization first failed because it compared historical baseline wording to the repaired validator's wording (`checks/task-tests-final2/`); the record now separates historical and current messages, and `checks/task-tests-final3/` is green.

## Distribution limitations accepted

The rule itself allows more than the current fixed colors, opposite-corner presentation, and 3×3 normalized shape universe might suggest. I accepted that bounded domain because it is constructive, diverse enough for the repository gates, canonical-compatible, and semantically strong; I did not claim it covers the full lawful input space. A future expansion should vary legal spatial relations and larger normalized shapes while retaining explicit witnesses and avoiding search/fallback control flow.
