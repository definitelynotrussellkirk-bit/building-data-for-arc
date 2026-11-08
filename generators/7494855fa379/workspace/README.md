# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Predicate witness probe (authoring only)

`probe_predicate_witnesses.py` audits production support for four simple ring
predicate rivals and any named `LESSON_COMPETITORS`, `SEMANTIC_RIVALS`, and
`CANONICAL_SHORTCUTS`. It reads labeled canonical authoring data through
`reviewer_support`; do not use it during a blind solve. From the library root:

```bash
python3 generators/7494855fa379/workspace/probe_predicate_witnesses.py \
  --seeds 0 17 --sample-start 0 --sample-stop 12 \
  --verify-racket --racket-timeout 120 --require-observed \
  --out var/predicate-witnesses.json
```

Outputs must be new. Add `--generator-path /path/to/generator-baseline.py` to
compare a source snapshot using the same finite sample range (`sample-stop` is
exclusive). In a review packet use `WORK/run_with_racket.py` as the wrapper;
payload paths and output paths are relative to `WORK/repo`. The probe finds its
own library or copied-runtime root independently of the current directory. In
a copied runtime, copy this probe anywhere under that root; its default source
is `puzzle_generators/per_puzzle/7494855fa379/generator.py`.

JSON retains source/probe/canonical-pair hashes, exact replay settings, canonical
fit, per-difficulty counts, and each first witness input. Production counts use
an independent **Python mirror** of the rule. `--verify-racket` executes only
retained first witness grids through public `Catalog.apply` and attaches the
actual Racket outputs/receipt; these selected labels do not certify all draws.
A copied runtime without a Catalog library reports reference execution as
`skipped_unknown` and fetches nothing. Exit 2 means execution/scoring error;
exit 1 means `--require-observed` found a required missing witness; otherwise
exit 0 means the finite report completed, including reports with unknown gaps.

This is a cheap optional contrast-support gate for canonical-fitting rivals.
A missing witness is an **unknown/gap**, not proof of absent support. Small or
poorly chosen ranges, rare contrasts, intentionally ordered curricula, and
answer-equivalent rival declarations can create false alarms. Observing all
four contrasts does not prove generalization, full rule coverage, identifiable
lessons, safety approval, or value for model training. Inspect those questions
separately. The probe adds no mandatory intake gate or battery stage.
