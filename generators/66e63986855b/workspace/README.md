# Reusable row-front review probes

The selected implementation is `../generator.py`; this directory is not an alternate
selected generator. The probe uses the installed public review API, not private
Racket runner functions. It derives rival names from the generator declarations.

## Full probe (run from the extracted packet root)

```bash
python3 run_with_racket.py python3 generators/66e63986855b/workspace/review_probe.py --seed-count 64 --axis-sweep --racket-samples 64 --out ../checks/my-rowfront-probe.json
```

The wrapper's actual payload directory is `repo`. The probe refuses to overwrite
an existing report. Exit 0 means no measured failure, 1 a retained counterexample,
and 2 an execution error; read status rather than treating output-file existence
as success. All exact inputs and labels for the raw lessons are retained.

The default seed base is 700000. For each seed and easy/medium/hard band, generate
indices 0..8; examine six starts of the 2-by-3 schedule and all four holdouts.
Fast window labels use the Python rule mirror. `--racket-samples 64` independently
checks 4 canonical and 60 selected generated inputs with public Catalog.apply.
`--axis-sweep` checks the 67,392 combinations of h6..14, w6..18, colors1..9,
4 profiles, 4 placements, and None/easy/medium/hard at seed983. Its case-stream
hash permits exact replay; this is not a sweep of all possible random seeds.

## Actual production lesson assembly

```bash
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 66e63986855b --per-band 100 --rotate-query --timeout 1800 --out ../checks/my-production-census.json
```

Unlike the fast raw probe, this command uses the production materializer and actual
Racket labels. It retains accepted indices, rejection records, seeds, and rotations.
Use a new output path. Check materialization/scoring errors, hook warnings, and
ambiguous rotations, not just the process status. Three underlying competitors
appear under eight namespaced declarations; that is not eight distinct theories.

## Tests

```bash
python3 run_with_racket.py python3 -m pytest -q generators/66e63986855b/tests
python3 run_with_racket.py python3 -m arcpuzzles check 66e63986855b --stage task_tests --timeout 600 --phase after --out ../checks/my-task-tests
```

The first directly runs the 34 selected tests. The second adds the nine frozen
root fixtures in a portable snapshot (43 total in this return). The root pytest
suite and general battery do not replace these explicit task-local checks.

These are finite declared-rival checks. Arbitrary subsampling, explicit profile
controls, or rejected draws can invalidate the raw-schedule witness guarantee.
Do not use canonical_pairs or any reference utility during a visible-only solve.
