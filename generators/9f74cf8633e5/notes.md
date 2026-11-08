# 9f74cf8633e5 — current generator notes

## Intended transformation

Use color `0` as background. For each zero-valued cell, inspect the four diagonal neighbors at offsets `(-1,-1)`, `(-1,+1)`, `(+1,-1)`, and `(+1,+1)` in the original input. If all four are the same nonzero color, fill the center with that color. Preserve all other cells. The canonical Racket authority is unchanged and pinned as `RULE_HASH = "3de95ecac741"`.

## Current implementation

Version `3.0.0` replaces the former positive-only sampler. Each generated grid contains two or three disjoint true X motifs plus exactly one controlled negative motif:

- `mismatched_diagonals`: four nonzero diagonal cells use two colors, so equality matters;
- `partial_diagonals`: only three diagonal cells are present, so all four are required;
- `blocked_center`: the four diagonals match but the center is already nonzero, so existing content is preserved.

Positive motifs use either pairwise-distinct colors or one shared color. Some samples add orthogonal context in a different color. The controls `grid_h`, `grid_w`, `cross_count`, `color_mode`, and `texture` are strict, observable, and exhaustively checked over their advertised ranges.

## Teaching schedule

`EXAMPLES_NEEDED = 5`. Every three consecutive sample indices contain all three negative textures; one slot uses distinct positive colors and two use a shared positive color, with the distinct slot seed-dependent. Orthogonal context also appears exactly once per three-sample block. Thus any five demonstrations drawn from a consecutive six-pair block retain enough support after any one pair is held out as query to refute the declared canonical-fitting rivals.

The live registries cover: first-center only, one-center-per-color, exactly-four-occurrences, ignoring diagonal color equality, three-of-four diagonals, overwriting occupied centers, requiring blank orthogonals, and three texture-conditioned color-reuse rules. These are finite declared hypotheses, not a proof of unique induction against every possible program.

## Canonical support and assumptions

Canonical inputs remain accepted. The generator supports rectangular ARC grids from `7x7` through `17x17`, two or three true motifs, shared or distinct active colors, one controlled negative, and disjoint `3x3` motif footprints. A narrow inert two-cell pattern is accepted only to preserve the second canonical example; generated teaching inputs do not emit inert noise.

The rule itself is broader than the generated grammar: it can apply to any rectangular grid with any number of valid X centers, including overlapping motifs. The restricted teaching grammar is deliberate so negative types and exact controls remain recoverable from pixels.

## Retained evidence and limitations

- Strongest canonical-fitting shortcut witness: `counterexamples/ignore_color_equality.json`.
- Portable future-review probe: `workspace/reference_probe.py`; it reads the live rival registries and checks every query rotation of sampled six-pair blocks.
- Final source SHA-256 used for the battery, census, solve, and counterexample: `d50ff9c7b7256733a8126a3f541d0a0ae1543b42f9eb54a60c654381629b14b0`.
- The 300-lesson census and local cyclic probe found no ambiguity for the ten declared rivals. Undeclared rivals and the full infinite input domain remain unproven.

## Review history

The selected baseline (`2.0.1`) emitted only clean positive motifs, had dead or misleading controls, lacked a pinned rule hash, and supplied no executable rival contract. This review used the passing task-local structure in sibling generator `dee38d045bc9` as an implementation pattern, then independently bound all behavior and tests to `9f74cf8633e5`; no prior return was imported and no reference rule was changed.
## Current reviewer considerations

Source SHA-256: `d50ff9c7b7256733a8126a3f541d0a0ae1543b42f9eb54a60c654381629b14b0`.

# Decisions for 9f74cf8633e5

Final generator SHA-256: `d50ff9c7b7256733a8126a3f541d0a0ae1543b42f9eb54a60c654381629b14b0`
Canonical rule hash: `3de95ecac741`
Reference-rule change: **none**

## D1 — Preserve the canonical Racket authority

**Original state.** The baseline Python generator mirrored the intended local X rule, and the canonical outputs were correct, but the generator did not pin `RULE_HASH`.

**Decision.** Keep the Racket program unchanged, pin `RULE_HASH = "3de95ecac741"`, and expose an input-pure Python `rule_mirror` only for generator checks and rivals.

**Reason/evidence.** The rule-smoke and authority-sync stages are green; the exact mismatch counterexample was evaluated by the selected Racket authority at `checks/counterexamples/9f74cf8633e5/racket.json`.

**Rejected alternative.** Expanding or changing the Racket rule to match a narrow generator grammar would invert the dependency. The distribution should teach the selected authority, not redefine it.

## D2 — Replace the positive-only sampler, rather than adding random noise

**Original state.** Version 2.0.1 emitted clean true X motifs only. A learner could ignore diagonal equality, accept three-of-four patterns, overwrite occupied centers, stop after one center, or bind one output per color without encountering a counterexample.

**Decision.** Every generated input has two or three true motifs plus exactly one controlled negative motif. The negative is one of `mismatched_diagonals`, `partial_diagonals`, or `blocked_center`.

**Reason/evidence.** Each negative isolates one necessary condition of the intended predicate. The semantic gate and 300-lesson census found zero surviving declared rivals.

**Rejected alternative.** Unstructured clutter can increase pixel diversity without changing the hypothesis class; it also makes overrides hard to recover and can create accidental Xs. The repair uses constructive, classified negatives instead.

## D3 — Use two or three positive motifs

**Decision.** `cross_count` is an exact control in `{2,3}`; easy defaults to two, while medium/hard alternate two and three.

**Reason.** Multiple positives refute “first center only.” Three positives with a shared color refute “one center per color” and “fill colors that occur exactly four times.” Two is retained for smaller canonical-like scenes and easy grids.

**Failure mode/limit.** The generated grammar does not exercise four or more simultaneous positives or overlapping Xs, although the rule supports them. This is a deliberate finite curriculum bound, not a claim about the rule domain.

## D4 — Schedule shared and distinct positive colors

**Decision.** The `color_mode` control is exactly `distinct|shared`. In every three-sample block, one seed-dependent slot is distinct and two are shared.

**Reason.** Shared colors across multiple centers break occurrence-count and one-per-color shortcuts; distinct colors prevent a learner from treating all positives as a single repeated-color event. Making the distinct slot seed-dependent avoids a globally fixed sample-index semantic.

**Rejected alternative.** Always-distinct positives left color-reuse shortcuts alive. Always-shared positives made per-color behavior underdetermined.

## D5 — Add orthogonal context without making it a prerequisite

**Decision.** Exactly one sample in each three-sample block adds a pair of different-colored orthogonal neighbors around a true motif; other true motifs lack that context.

**Reason.** This refutes “fill only when orthogonals are blank” while retaining examples where blank orthogonals are present. The orthogonal context is placed inside the same disjoint `3x3` footprint, so it cannot create an accidental target elsewhere.

**Limit.** The context family is intentionally small. Arbitrary dense orthogonal clutter is not generated.

## D6 — Make every exact control observable from pixels

**Decision.** Keep only five controls: `grid_h`, `grid_w`, `cross_count`, `color_mode`, and `texture`. Use strict integer/choice draws, reject unknown keys, and expose `observe_overrides`.

**Reason/evidence.** The prior axis surface included controls that were absent or not observable. The final override battery executed **29,070 draws** over **323 cases**, with 29,070 accepted and zero findings.

**Rejected alternative.** Retaining decorative or latent axes merely to increase an axis count would recreate the baseline defect.

## D7 — Require five demonstrations and support every one-pair query holdout

**Decision.** Set `EXAMPLES_NEEDED = 5`. A production lesson is a consecutive six-pair block with one pair held out as query; every five-demo rotation must refute every declared competitor.

**Reason.** There are three negative types plus shared/distinct and orthogonal-context factors. Five demonstrations are sufficient under the three-period schedule even after any one of six pairs becomes the query.

**Evidence.** The focused tests enumerate 4 seeds × 6 starts × 3 bands × 6 rotations = 432 cyclic rotations. The reusable probe checked 2,592 rotations. The production census checked 1,800 rotations from 300 independently materialized lessons; all passed.

**Rejected alternative.** Three demonstrations can cover the three negative types in ordered production, but a held-out query can remove the only witness for a rival. The larger lesson makes query position robust.

## D8 — Preserve canonical profiles without leaking them into ordinary generation

**Decision.** Default shapes rehearse `(7,7)`, `(8,8)`, `(9,9)`, and `(7,8)` on four of every five sample indices, with broader band-specific sizes on the fifth. `self_check` accepts the canonical second example's isolated same-color two-cell pattern, but `_generated_errors` forbids inert noise in generated teaching inputs.

**Reason.** This passes the profile floor and keeps direct canonical support while separating canonical compatibility from the stricter teaching grammar.

**Limit.** The special inert pair is a compatibility exception, not an advertised generated texture.

## D9 — Retain executable rivals and witnesses in source

**Decision.** Define ten `SEMANTIC_RIVALS`, use the same live functions for `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, and bind named witnesses through `SEMANTIC_WITNESSES` / `WITNESS_RIVALS`.

**Reason.** String descriptions can drift. Executable hypotheses let the semantic gate, census, tests, and future probe measure the same contracts.

**Limit.** Passing a finite registry does not establish unique induction. The reports explicitly leave undeclared rivals unknown.

## D10 — Build a source-local future-agent probe

**Decision.** Add `workspace/reference_probe.py` and test it from an unrelated working directory.

**Purpose.** It locates the repository dynamically, imports the adjacent generator, checks canonical support, verifies that every declared canonical shortcut truly fits the canonical training pairs, checks default scheduling/controls, and rotates every sampled six-pair block against the live `LESSON_COMPETITORS` registry.

**Evidence.** `checks/reference-probe-final.json` reports 3/3 canonical pairs, 10/10 canonical shortcuts, 612/612 generated samples, and 2,592/2,592 query rotations passing.

## Failed and corrected iterations

1. **Baseline battery:** lint and defect lint failed because the rule hash was not pinned and advertised controls/coverage were defective; the run was retained under `checks/before/`.
2. **First TDD run:** the new tests produced 163 failures and 5 passes, establishing that the baseline did not satisfy the planned authority, override, semantic, and lesson contracts (`checks/task-tests-red2/`).
3. **First implementation test:** 165/168 passed. The three failures came from the test requiring `ValueError` for type-invalid strict integer controls, while the shared strict helper correctly raises `TypeError`. The production code was unchanged; the test was corrected to accept the contract's `TypeError`/`ValueError` distinction (`checks/task-tests-green1/`).
4. **Final tests:** after adding the portable probe test, 169/169 pass (`checks/task-tests-final2/`).

## Lead consulted

No prior return was imported. I read sibling generator `dee38d045bc9` as a passing structural pattern for source-bound authority, constructive negatives, executable rivals, and a portable probe. All task semantics, examples, hashes, schedules, and tests were independently adapted and verified for `9f74cf8633e5`.

## 2026-10-25 parametric family

- Preserved the exact canonical default as `neighbor_mode=diagonal`; its program SHA-256 remains `3de95ecac741e5f478b577404e5124b950342e23768a85b8926595d5e4dd9e7c`.
- Added the nearby `neighbor_mode=orthogonal` rule on matched inputs. Every scene contains valid motifs for both relations plus partial or color-mismatched near-misses, so two demonstrations identify the finite setting without relying on a fixed color, count, or location.
- The required A→intermediate→B dependency is: detect relation-specific `(row, column, color)` assignments, then paint exactly those derived centers. The protected wrong-intermediate witness substitutes diagonal assignments into an orthogonal episode and changes the final output.
- A 32-seed audit checked 320 generated pairs, all 2–6 demo and 1–4 query prefixes, declared rivals, and one substantive 30×30 query per four-query bank. Target tests pass 187/187.
- The shared built-base preflight currently mishandles a legacy canonical `test` stored as one pair object. `workspace/parametric/preflight_compat.py` only normalizes that in-memory shape and delegates source binding, hashes, protected execution, and receipts to the shared implementation.
- Reviewer work is ready; exact-source owner integration, fresh native qualification, acceptance, and any training admission remain separate and pending.
