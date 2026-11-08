# Reusable authoring checks

Keep these tools and canonical data closed during visible-only solve episodes.
From the **packet root**, not `repo`:

```sh
python3 run_with_racket.py python3 -m pytest -q generators/cdb267535df8/tests/test_voronoi.py
python3 run_with_racket.py python3 -m arcpuzzles check cdb267535df8 --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-new
python3 run_with_racket.py python3 generators/cdb267535df8/workspace/probe_voronoi.py --per-band 100 --out ../checks/probe-new.json
python3 run_with_racket.py python3 -m arcpuzzles lesson-census cdb267535df8 --per-band 100 --rotate-query --timeout 1800 --out ../checks/census-new.json
```

Use fresh output names. The probe refuses to overwrite retained evidence, binds
the current generator hash, iterates actual declared shortcuts and witnesses,
records exact seeds and profile counts, and obtains labels through public
`Catalog.apply`. It checks the first 12 default draws per band plus all four
canonical pairs against Racket, even when `--per-band` requests more input probes.
At `--per-band 100`, the input-only sample is 300 draws, while the Racket comparison
is 40 cases. Its counterexample JSON includes an exact generated input, rival
output, Racket output and differing coordinate. This separation prevents an
input-only probe from being misreported as a larger Racket verification.

The tests use the portable `reviewer_support.find_root` and `canonical_pairs`
helpers and an independently implemented per-seed oracle. The cyclic test checks
all four start residues, 32 overlapping windows per band and all query positions;
it complements rather than substitutes for the production census.

The packet's `checks/run_logged.py` captures real argv, wrapper cwd, exit status,
elapsed time and logs. Audit scripts and the strict semantic-stage workspace
workaround are also retained under `checks/`; they do not patch shared sources.
