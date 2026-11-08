# public_eval_b5ca7ac4: runnable native authoring family

Run from the extracted packet's outer directory (the folder containing `review.py`).
The payload working directory is `WORK/repo`. Use fresh evidence directories on repeat runs.

```sh
python3 review.py run python3 -m pytest generators/public_eval_b5ca7ac4/tests -q --import-mode=importlib
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_b5ca7ac4 --root . --out ../checks/public_eval_b5ca7ac4/new-preflight
python3 review.py run python3 generators/public_eval_b5ca7ac4/workspace/parametric/audit_native.py --out ../checks/public_eval_b5ca7ac4/new-audit --preflight ../checks/public_eval_b5ca7ac4/new-preflight/preflight.json
python3 WORK/check_public_exports.py WORK/checks/public_eval_b5ca7ac4/new-audit/public --queries 1 --summary
```

The generator is canonical-only. `adapter.generate(seed, settings, demos, queries)`
returns private labelled episodes; `adapter.program(settings)` returns executable Racket.
Settings are strict, with defaults defined in promotion.json. No original grids are
looked up by the rule or native sampler. Audit originals come from the owner's private fixtures.

`presentation.prepare` needs all four private queries, shuffles before truncation, and
returns a controller-only bundle. Send only one `views[i]['challenge']` to the model.
`presentation.write_views` saves canonical visible bytes under their SHA-256 identities;
it rejects duplicate IDs, identifier drift and an existing destination directory.
Do not publish the private answer bundle or reveal the complete query directory.

`audit_native.py` retains runnable rival programs, finite demonstration-survivor results,
count/prefix and sampler sweeps, a source-bound causal witness, independent protected
replay, and public/private checks. Any rival interpreter failure aborts the audit.
Causal witness schema validation uses the existing owner validator but does not confer
owner acceptance. Any `.py`, `.rkt`, promotion or parent-source change invalidates the
retained binding and requires a fresh authoring preflight and audit.

Final accepted-by-authoring evidence: `WORK/checks/public_eval_b5ca7ac4/preflight-final/`,
`WORK/checks/public_eval_b5ca7ac4/audit-release-complete/`, `public-export-check.json`, `deterministic-replay.json`.
See task `notes.md` for domain limitations and owner next steps.

## Reproduce the repaired phantom-frame defect

```sh
python3 review.py run python3 generators/public_eval_b5ca7ac4/workspace/parametric/reproduce_void.py --out ../checks/public_eval_b5ca7ac4/new-void-regression.json
```

The retained pre-void-filter files are historical regression inputs, never candidate rules.
