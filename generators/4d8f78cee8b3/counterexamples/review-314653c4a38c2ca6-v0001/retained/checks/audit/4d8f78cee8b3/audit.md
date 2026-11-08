## 4d8f78cee8b3

**Findings-only audit. Target source and assignments unchanged.** Audited generator SHA-256: `b4effd60c55c9e79aeb4f3726da33265c13d6eead9efb4b252a13f9dea9ceb95`. Executed canonical Racket rule hash: `533915230c7f`; rule-text SHA-256: `6f762982c8a6ac3f1b435c8b930cfdc090ee2634bcfa144e5fb68e9fae8bbcd8`.

### A1 — Reproduced spatial shortcut: inspect only colors at the nonzero row edges

The rival removes a color only when it both repeats within a row and appears at that row's first or last nonzero position; it leaves all other cells unchanged. It agrees with all **4/4 labeled canonical pairs** and **27/27 generated inputs** covering every declared grid-profile × palette-kind × scene-profile combination. The bounded generated probe uses seed **23**, sample indices **0–26**, and cycles difficulty easy/medium/hard; exact calls are in `checks/audit/4d8f78cee8b3/preparation.json`. All 31 labels were independently checked through the public Racket apply command.

The source explains why this is a support-wide shortcut, beyond the finite probe: `_profile_rows` places every repeated color at a nonzero edge, and `_place_row` only reverses the token list before placing it in sorted columns. Neither reversal nor inserting zero gaps can move a repeated color entirely inside the row. Thus the current token grammar cannot produce a refutation of this rival. This is a confirmed distribution shortcut, not a reproduced incorrect Racket label or an all-seed empirical claim.

The primary counterexample starts from this exact generated call:

```python
generate(seed=23, sample_index=11, difficulty="hard",
         grid_profile="canonical_5x10", palette_kind="low", scene_profile="dense")
```

In zero-based row **2**, occupied columns **[1, 2, 3, 6]** originally contain **[6, 1, 2, 6]**. Reorder only those values to **[1, 6, 6, 2]**. Racket erases the two interior 6s at **(2, 2)** and **(2, 3)**; the rival preserves them. Both `self_check` and `strict_canonical_like` return `[]`. `observe_overrides` remains exactly `canonical_5x10` / `low` / `dense`. The mutation preserves every documented dimension, color, active-row, row-multiplicity and sparsity constraint. It belongs to the documented structural domain and the same observable profile; the current generation code cannot emit this token ordering.

Retained evidence: `checks/audit/4d8f78cee8b3/witness.json` contains the original generated input, exact call and mutation, accepted counterexample input, actual Racket output, rival output, mismatching coordinates, and source/rule hashes. `permutation-racket.json` is the public apply receipt. A second, simpler accepted interior-pair witness remains in `preparation.json` batch index 31 and `racket.json`; it is a hand-built structural-domain input, not a generated draw.

Suggested task-local repair: vary nonzero token order beyond reversal, deliberately include repeated colors between singleton colors at both nonzero edges, add this rival to the lesson competitor inventory, and ensure intended demonstration windows refute it. No repair is included for this audit-only target.

### A2 — Reproduced canonical-shortcut declaration mismatch

The actual `CANONICAL_SHORTCUTS` declaration aliases all five `SEMANTIC_RIVALS`, although four do not fit all usable canonical pairs. The audit iterates the live declarations, not a copied list. Fresh Racket labels match all four retained canonical outputs.

| Actual declaration | Agreement with canonical pairs | Counterexample identity |
| --- | ---: | --- |
| keep globally unique colors | 4/4 | none |
| keep only one singleton per row | 3/4 | variant 0, train pair 1 |
| keep the rightmost nonzero cell per row | 0/4 | all four pairs |
| erase repeated pairs but retain triples | 3/4 | variant 0, train pair 1 |
| keep only the lowest singleton color per row | 3/4 | variant 0, train pair 1 |

These remain useful `LESSON_COMPETITORS`, but the canonical-shortcut claim is incorrect for four entries. Restrict `CANONICAL_SHORTCUTS` to rivals that fit every canonical pair, while retaining other semantic rivals under their existing competitor roles. Evidence: `summary.json` and `preparation.json` under `checks/audit/4d8f78cee8b3/`, including exact pair identities and counts.

### Verification scope and limits

Five successful commands are retained in `checks/audit/4d8f78cee8b3/commands.json`, with exact argument arrays, wrapper cwd `.` (WORK), effective payload cwd `repo`, exit statuses, and evidence paths. Public Racket apply processed **33/33 valid outputs on 33 distinct inputs**: four canonical pairs, 27 generated axis combinations, and two lawful counterfactuals. The independent row-singleton mirror agreed with Racket on all 33. Both counterfactuals separate the edge-based rival, and both validators accept them. This audit did not run a full battery, test arbitrary query rotations, or claim empirical coverage of all seeds. Source inspection supplies the stated token-order argument. No private runner imports or solve-private reads were used.
