# Runnable reviewer tools for d68b3843203e

The selected implementation is `../generator.py`. Workspace code does not replace the selected generator or label authority. These tools need the supplied packet/repository, Python >=3.12, and the supplied or locally installed Racket runtime. No external service is called.

From the packet root (the directory containing `repo/` and `run_with_racket.py`):

```bash
python3 setup_racket.py
python3 run_with_racket.py python3 -m pytest generators/d68b3843203e/tests -q
python3 run_with_racket.py python3 generators/d68b3843203e/workspace/strict_battery.py --out ../checks/new-strict
python3 run_with_racket.py python3 generators/d68b3843203e/workspace/review_probe.py --out ../checks/new-probe
python3 run_with_racket.py python3 generators/d68b3843203e/workspace/audit_probe.py --out ../checks/new-audit
```

Use fresh output paths.

`strict_battery.py` creates a fresh catalog-staged temporary runtime, explicitly chooses after policy, preserves manifests/logs, and returns the subprocess exit status. Default subprocess timeout is 600 seconds, adjustable by `--timeout`.

`review_probe.py` independently enumerates complete frame borders, normalizes integer grids, compact digit rows, and singleton test-pair dictionaries, computes a counting oracle and topology rival, and checks actual protected Racket outputs. Its report includes generated and canonical frame-count, cue-size, and joint-profile histograms; a 480-call census by default; 245 canonical/generated Racket comparisons; 40 D4 comparisons; and first examples for six coverage features. `--seed`, `--per-band`, `--racket-per-band`, and `--source` support controlled or frozen-source replay.

`audit_probe.py` is the findings-only reproducer for this assignment's immutable targets `4a3ababcaceb` and `cf60523d1603`. It executes each canonical-fitting rival on public and ordinary generated cases, verifies exact protected-Racket outputs, and records one `self_check`-accepted disagreement input per target. It edits neither audited target.

Racket runtime identity and source/rule hashes are written into evidence. Never treat a Python mirror or rival as production label authority. None of these runs approve or integrate a generator. Task-local tests are not automatically discovered by every shared battery path, so retain the explicit pytest command.
