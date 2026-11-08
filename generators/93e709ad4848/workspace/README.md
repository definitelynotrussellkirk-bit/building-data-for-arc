# Reproduction and next-agent handoff

Task: `93e709ad4848`, Nearest-Corner Dock. Racket authority is unchanged.
The selected generator is `../generator.py`; do not import a predecessor checkout.

Run these commands from an extracted review packet root. Output directories and
files must be new. Python 3.12+, NumPy, Pillow and the supplied offline Racket
runtime are sufficient for the generator workflow; the focused tests use stdlib.

```bash
python3 setup_racket.py
python3 -m unittest discover -s repo/generators/93e709ad4848/tests -v
python3 repo/generators/93e709ad4848/workspace/probe_review.py --seed-start 0 --lessons-per-band 100 --out checks/reprobe
python3 repo/generators/93e709ad4848/workspace/verify_racket_pairs.py --probe checks/reprobe --out checks/reprobe-racket --workers 3
python3 run_with_racket.py python3 -m arcpuzzles check 93e709ad4848 --battery --timeout 4000 --phase after --out ../checks/recheck
```

`probe_review.py` dynamically reads the generator's shortcut/competitor contracts,
checks canonical fit, and measures complete three-demo/two-query lessons under
the public worker's actual rejection policy. It checks all three cyclic starts
and records distinct tuples, unique input hashes, overlapping windows, shape and
corner coverage, rejected draws, both-query ambiguities, and all failures.
`--require-no-rejections` is an optional stricter diagnostic, not the public
worker's admission rule. Do not relabel accepted duplicate retries as semantic
failures or silently drop them from sampling-cost reports.

`verify_racket_pairs.py` binds the final probe/source hashes and sends its unique
inputs through the supported public `apply` command in batches of at most 64.
Keep its actual Racket outputs and provenance alongside the diagnostic probe.
It never imports private runner internals.

The cheap extra admission check is:

```bash
python3 repo/generators/93e709ad4848/workspace/conservation_gate.py --receipts checks/reprobe-racket/batch-*/racket.json --out checks/conservation.json
```

The shell expands this pattern to all batch receipts (`batch-0000` onward).
Alternatively pass explicit receipt paths after `--receipts`. This gate is specific to a
declared one-object rigid-translation contract. It detects foreground loss,
changed canvas, recoloring, shape/hole loss and component-domain mismatch without
another Racket or GPU run. It does not prove the destination corner is correct.

## Open maintainer decision

The final candidate has a retained `selfcheck-minimal-impostor` admission failure because
the shared linter treats lawful tiny shapes as invalid. Inspect the 18 Racket
witnesses under `checks/linter-lawful-shapes/` in the return and fix or formally
resolve the shared-tool classification, then rerun the candidate battery. Keep
approval labels unchanged until the normal review/admission process succeeds.

The return includes failed intermediate checks, the original wrong-domain
counterexamples, both genuine solve records, the two findings-only audits, exact
commands, and an automatically generated INTAKE index. Preserve those records.
Use a refreshed full packet for the next assigned review; do not reroll or reuse
this immutable assignment to claim a different task.

For the delta return, first restore the automatic evidence bundle as described
by its bundled instructions. Older bulk probe data has one additional documented
compression layer under `checks/archives/`; its manifest retains each original
path, byte count and SHA256, and its restore tool verifies the bytes before writing.
Final probe data, all failed reports and counterexamples remain directly available
after restoring the automatic bundle.
