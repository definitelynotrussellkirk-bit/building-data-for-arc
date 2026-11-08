# Working notes: b5af3d6b3cd5

## 2026-10-06 repair (`4.0.0`)

The v3.1 source advertised nine controls, but only a subset were consumed and the difficulty branches made declared dimension extrema impossible. Its `self_check` also encoded non-rule constraints—three-cell room minima, unique colors per room, and no marker on a room bottom row—so it rejected all five canonical inputs. The sampler had weak canonical-profile support and no executable defense against the canonical-fitting shortcut “only colors 1–4 fall.”

The repaired source exposes only exact dimensions, pins the canonical rule hash, validates the authority-linked wall/room grammar, and restores canonical-scale anchors. Layout, palette, and density remain internal curriculum choices rather than dishonest caller controls. Every draw includes an extended color that changes position under gravity and an out-of-order stack that distinguishes stable compaction from numeric sorting.

The retained task-local regression suite covers canonical acceptance, exact override boundaries and rejections, deterministic replay, both semantic witnesses, all four query rotations, and 24 cyclic starts in every difficulty band. The large source-bound census remains finite evidence against declared rivals, not a proof of unique induction against every imaginable rule.
## Current reviewer considerations

Source SHA-256: `76cfb4e4ae8e52bbec79ad5e36f52146dc7130a626843f77061c89198eb35028`.

# Decisions for `b5af3d6b3cd5`

## D1 — Keep the canonical Racket authority unchanged

**Original rationale:** The imported v3.1 comments said the rule was verified as per-column gravity inside wall-separated rooms. No associated review note supplied a different rationale. **Probe:** the before rule smoke and authority-sync stages were already green, and all five canonical outputs matched the selected authority. **Choice:** retain the canonical rule and pin `RULE_HASH = "f37a4766f778"`; implement a Python mirror only for diagnostics and declared rivals. **Rejected alternative:** rewriting the Racket rule to match v3.1’s validator restrictions. That would have changed a working authority to preserve invented constraints. **Failure mode / limit:** the generator exercises rectangular divider rooms, not every connected-wall topology the authority may support.

## D2 — Expose only `grid_h` and `grid_w` as public exact controls

**Original rationale:** v3.1 advertised dimensions, divider counts, per-chamber marker count, palette kind, marker palette, position bias, and texture, apparently to claim combinatorial coverage. The source did not actually read several controls, and difficulty-specific `draw_int` bounds made declared dimension values invalid or mismatched. **Probe:** the before override audit recorded roughly 20,000 findings over 97,200 planned draws, including thousands of height/width mismatches, dead textures, missing provenance, and generation errors. **Choice:** publish only the two pixel-recoverable exact dimensions, with bounds 8–16 and 9–18. Reject unknown keys and non-exact values. **Rejected alternative:** add exact controls for every layout/palette/density concept. That would create a large compatibility matrix and expose implementation details that are not required by the task. **Final evidence:** 9,900/9,900 accepted matrix draws, zero findings/warnings, unknown key rejected.

## D3 — Use canonical anchors plus broad internal profiles

**Original rationale:** v3.1 tried to broaden dimensions and layouts after an earlier fixed 9×11 generator, but it drifted from canonical support. **Probe:** the before profile floor rejected all five canonical inputs and found zero exact support in medium and hard 20-draw samples. **Choice:** alternate `canonical_sparse`, `broad_sparse`, `canonical_dense`, and `broad_dense`; canonical profiles select among observed 8×9, 9×9, 9×10, 9×11, and 9×12 shapes. **Rejected alternatives:** all-canonical sampling would overfit shape; all-broad random sampling repeated the support failure. **Final evidence:** 37/60 exact profile hits, with 13/20 easy, 13/20 medium, and 11/20 hard.

## D4 — Use complete rectangular divider grids with 2–3 row/column segments

**Original rationale:** the canonical puzzles all use complete color-5 outer frames and divider lines. v3.1 imposed a three-cell minimum on every room, although canonical rooms can be two cells wide or tall. **Probe:** canonical `self_check` failures named short segments; the Racket rule passed those same examples. **Choice:** require every room dimension to be at least two cells and at least one room to be three cells tall so a moving two-marker witness can be placed. Layouts contain 4, 6, or—on broad large canvases—9 rooms. **Rejected alternatives:** keep the three-cell minimum (canonically false), allow a single chamber/no walls (weakens the observed task grammar), or generate arbitrary wall mazes (broader than demonstrated and harder to audit). **Failed iteration:** a 3-row split with all two-cell rooms made the witness impossible; the final vertical partition calculation reserves one extra room cell.

## D5 — Restore canonical marker counts while retaining broader density

**Original rationale:** v3.1 sampled 1–4 markers per chamber, producing totals and room-level constraints unrelated to the canonical distribution. **Probe:** strict/profile reports showed low canonical support; canonical examples contain 11–16 markers overall. **Choice:** canonical shapes draw 11–13 markers in sparse profiles and 14–16 in dense profiles; broad profiles use difficulty-aware wider ranges, clipped to lawful capacity. Every room retains at least one marker and one background cell. **Rejected alternative:** make marker count a caller axis. Exact total count is observable, but exposing it adds little teaching value and couples callers to room-capacity constraints. **Limit:** the chosen ranges are empirical support choices, not authority requirements.

## D6 — Include three canonical colors and one extended color per draw

**Original rationale:** v3.1 claimed the full non-{0,5} palette but gave no guarantee that an extended color was semantically relevant; the canonical rows use only 1–4. **Probe:** `canonical_colors_only` fits all five canonical pairs. **Choice:** each input uses three colors sampled from 1–4 plus one from 6–9, and at least one extended-color marker changes position. **Rejected alternatives:** canonical colors only leaves the strongest shortcut alive; uniformly random palettes can miss canonical-like support or fail to make the extended color move. **Failure mode / limit:** the forced four-marker palette is a distribution signature, documented in `REVIEW.md`.

## D7 — Force one stable-order stack counterexample

**Original rationale:** the task’s rule preserves top-to-bottom order, but many sparse columns contain at most one marker, so numeric sorting can accidentally agree. **Probe:** the declared `sort_each_stack_by_color` rival is refuted by only 3 of 5 canonical pairs, so relying on arbitrary examples would be fragile. **Choice:** place `[extended_color, lower canonical color, empty…]` in one tall room column; gravity moves the pair together and preserves that descending numeric order. **Rejected alternative:** hope random collisions create stacks. The witness rate would be low and complete lessons could miss it. **Final evidence:** the witness fired 600/600 semantic-gate draws and its Racket-checked rival claim held 60/60 times.

## D8 — Separate lawful-input validation from curriculum requirements

**Original rationale:** v3.1’s validator required unique colors per chamber, no bottom-row markers, and three-cell room dimensions. Those are sampler preferences, not the transformation’s grammar. **Probe:** all five canonical inputs failed it. **Choice:** `self_check` now verifies rectangular shape, ARC colors, solid frame/dividers, no stray wall fragments, nonempty/background-containing rooms, at least two marker colors, and at least one movable column. Witnesses and canonical-profile checks live in their own hooks. **Rejected alternative:** require the extended marker and special stack in `self_check`; that would again reject lawful canonical inputs. **Final evidence:** all canonical inputs accepted, 60/60 default draws clean, and 31/45 destructive mutations rejected.

## D9 — Use three demonstrations, one query, and test both production order and every query rotation

**Original rationale:** `EXAMPLES_NEEDED = 3` was inherited, but the old generator had no executable lesson contract. **Choice:** keep three demonstrations and one query. Production assembly preserves sampled order; diagnostics also hold out each of the four labelled pairs once. The schedule has four named profile types, and task-local tests traverse 24 consecutive starts in every band to cover all relevant cyclic interactions. **Rejected alternative:** only test individual witness frequency or two inference guesses; neither establishes that a complete lesson refutes a rival. **Final evidence:** 300/300 production lessons and 1,200/1,200 rotations are unambiguous against declared rivals; 1,200 unique inputs. **Limit:** this is finite rival evidence, not universal induction.

## D10 — Keep reusable probes task-local and portable

`tests/test_generator_contract.py` is the reusable regression tool. It locates the packet through `reviewer_support.find_root` and uses canonical helpers rather than fixed parent-depth guesses. It covers all canonical pairs, exact axis boundaries and rejection behavior, deterministic replay, both semantic witnesses, 24 cyclic starts × 3 bands, and all four query rotations. `workspace/README.md` records the source-bound commands. The general battery does not discover these tests automatically, so the explicit task-test command remains mandatory.

## D11 — Preserve failed and adversarial evidence without widening the patch

The initial red task suite was retained under `checks/task-tests-red/`; intermediate runs remain under `checks/task-tests-green-*`. The two assigned audits concern `db8923f18bcc` and `067f6e037e97`; their defects were reproduced and documented, but neither source was modified because the assignment permits changes only under the selected task. The audit evidence is not used to claim anything about the repaired generator.

## 2026-10-25 native parametric build (`bottom_color_relay`)

The production generator and canonical authority remain unchanged. The task-local native adapter keeps `mode=canonical` as an exact byte-for-byte canonical default and adds an opt-in matched-input `mode=bottom_color_relay`. Step A applies stable per-column gravity inside every wall-delimited room. The post-gravity controller bottom row then yields an intermediate count `k in {1,2,3}` of columns ending in color 9; Step B uses `k` as a one-based selector among three payload rooms and recolors only the selected room's settled markers to color 8. The protected counterfactual counts color-9 cells on the raw controller bottom row, so it selects a different payload.

The adapter supports 2–6 demonstrations and 1–4 prefix-stable queries, with a substantive 30x30 fourth query and identical inputs across modes. Final evidence: 53 focused tests passed; a 32-seed audit over demo counts 2/3/6 covered 192 episodes and 1,152 named-rival checks with no retained failures; native qualification passed four jobs (two modes x seeds 0/17), 32 protected-Racket evaluations, and four queries per job; 16 public one-query views passed exact identity/structure checks. The retained 30x30 witness has correct intermediate 2; the raw-bottom counterfactual changes eight output cells and replays as `reviewer_replayed`.

Limits: the rival audit is finite, the relay is an opt-in proposal rather than a production-rule change, and exact integrated-source owner acceptance plus any training admission remain pending.

