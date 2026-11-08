# Shared tooling feedback

## F1: **Top shared change — mine canonical-fitting structural shortcuts automatically**

**Symptom.** The selected, previously approved v4.0.0 generator declared no
canonical shortcut, yet “choose the smallest qualifying mover” matches all 8
canonical labels. The ambiguity was found only by manually enumerating candidate
selection heuristics.

**Evidence.** `checks/shortcut/smallest-mover-evidence.json` records 8/8 canonical
fit and an exact Racket-checked disagreement; the repaired semantic gate later
fires the witness 317/600 times.

**Suggested change.** Extend `scripts/generator_semantic_gate.py` (or add a helper
used by the `generator-shortcuts` question) to search common object/candidate
ranking features—size, area, color, reading order, wall size, nearest/farthest—and
report any rival that fits every canonical pair but differs on validator-accepted
or generated inputs. Emit a small source-bound counterexample template rather
than requiring each reviewer to rebuild the search.

## F2: Provide a portable supported API for deriving bounded Racket rule variants

**Symptom.** The shared high-level `puzzle_generators.rule_wrap.wrap_rule`
calls `convert_for_shorthand`, which imports parser classes from
`scripts.comment_solutions`. That repository-only module is absent from the
portable task-test runtime. The prototype therefore had to bypass `wrap_rule`,
call only the closed `strip_line_comments`/`strip_rule_wrapper` helpers, and
reconstruct the small `h`/`w` lambda preamble itself.

**Evidence.** `generators/537b409b6744/workspace/parametric/prototype.py` function
`_racket_callable` records the workaround; the portable task-test receipt in
`checks/task-tests/result.json` and the fresh replay receipt both execute the
prototype successfully without importing `scripts.*`.

**Suggested change.** Remove the `scripts.*` dependency from the runtime
normalization path, or expose a small closed API for wrapping already-standard
lambda rules without invoking the repository parser. A separate helper could
then transform a selected rule and materialize Racket-labeled episode evidence,
while keeping variant approval distinct from canonical authority.

## F3: Centralize strict generator call validation

**Symptom.** One missing guard produced 48 repeated defect-lint warnings across
bands for invalid `seed`, `sample_index`, and `difficulty` values.

**Evidence.** `checks/before/checks/537b409b6744_before_defect_lint.log`.

**Suggested change.** Add a shared `validate_generate_call(seed, sample_index,
difficulty)` helper or a validated base wrapper used by per-puzzle generators.
It should reject booleans as integers, negative indices, nonintegral scalars, and
unknown difficulty strings before RNG construction.
