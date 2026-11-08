# Task-local review tools

The selected implementation is `../generator.py`. These scripts stage clean
copied execution trees and do not change shared tools or audited generators.
They require the repository's declared Python dependencies and a working Racket.

## Tests and semantic census

From an extracted packet root:

```bash
python3 run_with_racket.py python3 generators/54a83e6bbc20/workspace/run_review.py \
  --action tests --phase replay --out ../checks/replay-tests \
  --runtime /tmp/arcpuzzles-54a83-replay-tests

python3 run_with_racket.py python3 generators/54a83e6bbc20/workspace/run_review.py \
  --action census --phase replay --out ../checks/replay-census \
  --runtime /tmp/arcpuzzles-54a83-replay-census \
  --per-band 200 --oracle-samples 40 --width-sweep
```

Use new empty runtime directories on each invocation. Without `--runtime`, a
fresh temporary directory is allocated. Outputs include source hashes, actual
runtime paths, commands, exit status, logs and exact JSON witnesses. Test mode
explicitly stages all task-local tests; the static runtime manifest alone does
not discover newly added test files. The census exits nonzero for validation,
mirror, determinism or selected-oracle failures. The finite width sweep deliberately
records out-of-distribution authority counterexamples separately from failures.

The census decoder is specific to this task's three-row complement grammar.
Do not apply it to an unrelated task without replacing its interpretation and
independent model. Counts are draw instances unless expressly marked unique.

## Two findings-only packet audits

```bash
python3 run_with_racket.py python3 generators/54a83e6bbc20/workspace/audit_assigned.py \
  --out ../checks/replay-audits --runtime /tmp/arcpuzzles-6910-replay-audits
```

This is a reproducible experiment for immutable targets `3fcea70c3acf` and
`67e9e17efb62`, not a universal quality gate. It retains requested/observed override
values, input grids, real Racket outputs, candidate rivals when applicable, and
all target hashes. A zero process exit means the checked independent predictions
matched Racket; it does not mean no override-contract defects were found. Read
the per-target JSON summaries and audit report.
