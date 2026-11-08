# Workspace

The selected implementation is `../generator.py`. Files here are diagnostics and review aids, never alternate selected generators.

## Analyze retained rival coverage

`audit_rival_coverage.py` reads a complete source-bound shared lesson-census JSON receipt, or its gzip-compressed equivalent. It does not generate grids, execute rival code, or obtain reference labels. It detects a specific gap that a query-ambiguity test can miss: a rival fails canonical examples yet survives every generated label in the measured distribution.

From the repository root, after restoring the corresponding return's `checks/` evidence:

```bash
python generators/747486860e56/workspace/audit_rival_coverage.py ../checks/lesson-census-final.json.gz --out ../checks/tooling/replayed-final-coverage.json
python generators/747486860e56/workspace/audit_rival_coverage.py ../checks/lesson-rescore-v1.json.gz --canonical-census ../checks/lesson-census-final.json.gz --out ../checks/tooling/replayed-old-gap.json
```

The first command should exit 0 (`no_finite_coverage_gap_found`) on this return's final receipt. The second should exit 1 (`finite_coverage_gap`): the old distribution's conditional rival survives all 300 lessons and 2,100 holdouts despite failing eight of ten canonical pair occurrences. Exit 2 denotes incomplete, malformed, inconsistent, or errored evidence. This expected exit 1 is successful detection, not a failed tool execution.

Rescore receipts lack canonical-fit measurements. `--canonical-census` supplies them only after exact task, current rival-generator, rule-source, rule-callable, and declaration-name joins. Namespace-qualified rows stay separate: sixteen rows in this return do not mean sixteen independent hypotheses. Refuted lesson/holdout counts mean that a demonstration refuted the rival; they are not counts of incorrect query predictions. Repeated canonical occurrences and overlapping holdouts are not independent examples.

Tests live in `../tests/test_rival_coverage.py`. The actual original receipt test skips when review evidence is absent; structural, malformed-input, strict-join, gzip, and exit-status tests remain source-local. The tool does not discover undeclared rivals or certify universal identifiability.

## Reproductions

`../counterexamples/main_identity_regressions.json` stores the four original component-identity/count-drift cases. `../tests/test_triangle_contract.py` contains an independent connectivity oracle and their regressions. The return's `checks/` holds the authoritative Racket receipts, original failures, larger censuses, source bindings, and command records. Consult the return's compression manifest before following an original uncompressed evidence path.
