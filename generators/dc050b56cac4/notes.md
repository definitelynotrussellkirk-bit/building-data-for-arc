# Working notes: dc050b56cac4

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `5c2069293d9871570c6d9210941c26a1e3e3cfd4865ddf04b326cc9d1524a157`.

# Decisions for `dc050b56cac4`

## D1 / R1 — preserve the rule and repair only the public boundary

The reproduced defect is input-contract handling, not puzzle semantics. The baseline accepted Python scalar aliases and negative sample indices; valid literal nonnegative integer calls already produced lawful, well-supported lessons. I therefore added one validator at the earliest shared boundary and did not change generation geometry, schedule selection, random recipes, axis domains, or Racket authority.

This is preferable to coercing values with `int(...)`: coercion would silently merge strings, floats, and Booleans into ordinary seeds or indices and would preserve the defect. It is also preferable to validating only in `generate`, because `schedule_profile` is itself public/reusable and would otherwise retain inconsistent behavior.

No generator version marker was changed because every previously valid public call is behaviorally identical; the source hash changes, but the selected semantic version/rule identity does not. The final rule hash remains `4fe6d23687d0`.

## D2 — keep the existing lesson distribution

The pre-existing three-profile schedule already addressed the canonical shortcut family:

1. `canonical_stack` preserves canonical-looking examples;
2. `same_row_witness` separates total gray-cell count from gray-bearing rows and vertical span;
3. `scattered_witness` separates count from both span and top-right-stack length.

Changing this schedule while repairing scalar validation would bundle unrelated behavior and risk invalidating prior semantic evidence. Final measurements support retaining it: the profile floor is 15/60 exact hits, the override matrix is clean over 63,810 draws, and the 300-lesson census is clean under every single-pair query holdout.

Rejected alternative: randomize all gray placements. That might widen geometry but would no longer guarantee that every three-demonstration bundle contains the intended counterexamples. A future widening should preserve an explicit witness quota rather than replace the deterministic teaching cycle with unconstrained sampling.

## D3 / P1 — choose one direction parameter, once per episode

For the original-family parametric priority, the smallest useful parameter is the diagonal direction in which the colored cross moves. It preserves all object roles and the core inference chain: find the unique cross, count gray markers, erase them, and translate the cross by that count. Only the signs of the row/column displacement change.

The allowed settings are `down_left`, `down_right`, `up_left`, and `up_right`, with canonical `down_left` as the default. A setting is drawn once per episode, never independently per pair. Controlled fixtures leave enough margin for all four settings, so every rival can be executed on the same inputs. Three demonstrations are retained because one is already sufficient to identify the sign pair on these fixtures, while three matches the production lesson size and supplies repeated evidence before the query.

Rejected alternatives:

- Vary marker-count arithmetic, such as `N+1` or row-count instead of cell-count. Those choices alter the family’s central quantitative relation and overlap known canonical shortcuts rather than giving a clean original-family extension.
- Vary cross thickness or replace the cross object. That changes object grammar and introduces a second design problem.
- Draw direction per pair. That would create inconsistent episodes and teach no single rule.

The proposal remains outside production. Its four instantiated programs, labels, rivals, and public/private episode artifacts are source-hash-bound under `checks/parametric/direction-prototype/`.

## D4 / T1 — load the staged source without re-importing the staged dependency tree

Portable task tests run the frozen fixture and new tests in one Python process. The frozen fixture imports this task first; a later call to the selected-generator helper sees cached modules from the first staged path and correctly treats them as cross-tree contamination. A temporary path-manipulation attempt did not solve the root cause and was removed; both failed receipts remain available.

The final tests resolve the exact controller-selected file through `GENERATOR_UNDER_TEST`, read and hash its bytes, and compile only that source under a unique module name. Direct repository tests fall back to `reviewer_support.find_root`. This keeps the test bound to the intended generator without disturbing cached runtime dependencies. The final portable snapshot passes 85/85.

## D5 — audit findings remain audit-only

No source under `89704f9047c0` or `2cefa1581476` was changed. For `89704f9047c0`, the actionable repair is to orthogonalize palette-rank permutation from scene profile and add the retained profile-plus-palette rival to the semantic contract. For `2cefa1581476`, the minimum repair is to correct the public summary to match the authority’s secondary tie-breaks and add an executable witness/test. Those changes belong to their own assigned reviews.

## D6 — evidence and stopping rule

I stopped generator work after the exact final source passed the 12-stage battery, 85 portable tests, the required query-rotation gate, and the 300-lesson census; the proposed direction family also passed all task-local tests and materialized source-bound Racket evidence. No blocker remains. The remaining limitations are epistemic rather than failing gates: finite rivals do not prove unique induction, and no Qwen3.5-9B training experiment was run.
