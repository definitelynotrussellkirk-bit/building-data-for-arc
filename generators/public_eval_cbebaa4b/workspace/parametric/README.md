# public_eval_cbebaa4b: native authoring family

The default solves translation-only red-connector assembly anchored on the yellow piece. The alternative selects the unique deepest piece in the solved red-contact graph, not the smallest piece or most distant coordinates.

## API and public data

`generate(seed, settings, demos, queries)` returns a private full episode.
The episode parameter `assembly_policy` is fixed for that episode. `program(settings)`
materializes its Racket program; the default is byte-identical to `canonical.rkt`
and the task root's `reference.rkt`. `predict` is the independent Python model.

Request demonstrations in 2..6 and queries independently in 1..4. Generation
builds six demonstrations and four privately shuffled queries before prefix
selection; matching seeds/counts have identical inputs across both settings.
The demos teach the setting. Do not expose the private episode directly.
`public_turn(episode, index)` whitelists demonstration input/output and only the
current query input. It excludes programs, settings, private fields, answers,
future queries and query-count hints, even when pair dictionaries carry metadata.

## Repeat verification

From the packet's `WORK/repo`, after its Python/Racket setup:

```sh
export PYTHONPATH=src:shared/runtime
export RACKET_PATH=../.review/racket-runtime/racket/bin/racket
python -m pytest --import-mode=importlib -q generators/public_eval_cbebaa4b/tests
python generators/public_eval_cbebaa4b/workspace/parametric/audit.py --seeds 20 --out ../checks/public_eval_cbebaa4b/new-audit
python -m arcpuzzles.review_public_creation preflight public_eval_cbebaa4b --root . --out ../checks/public_eval_cbebaa4b/new-preflight
```

Output directories must be new. Tests and audits should be invoked per target;
combined invocations exceeded this session's execution-tool timeout. The audit
executes selected and rival Racket programs through the protected evaluator,
checks all count/setting/prefix combinations, and writes public files physically
in visible-content-hash order. `public/` is solver-safe; `private/` and receipts
are not. Source-bound causal replay is in `checks/public_eval_cbebaa4b/build_witness.py`;
its retained paths name the final `preflight-v2` and `causal-v2` evidence.

## Scope and acceptance

Both settings have a meaningful 30x30 case. The 20-seed sweep counts 800 requests
and 5,200 repeated-prefix pair instances but only 200 distinct inputs. Protected
Racket evaluation is bounded to the explicit originals/preflight/rival cases;
the large count sweep is not 5,200 separate protected executions.

These are authored, reviewer-ready prototypes. Owner registration, native
qualification, source review and fresh exact-source acceptance remain required.
No training admission is included. Finite rivals and seeds do not prove universal
identifiability or coverage of every lawful public-parent geometry. Consult
`../../notes.md` for family-specific scope and counterexamples.
