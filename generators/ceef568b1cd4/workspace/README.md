# Review tools for ceef568b1cd4

The selected implementation is `../generator.py`. `reference_probe.py` is an
independent authoring oracle and source-bound Racket comparison tool. It reads
canonical answers; never use it in either visible-only solve phase.

From an extracted review packet, create and activate its own environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install 'numpy>=1.26' 'Pillow>=10' 'pytest>=8'
python setup_racket.py
```

Installing pytest only in the user site can leave isolated child processes
without it. A packet-local environment also works when user-site imports are
disabled by the runtime.

Run the portable regression stage and the exact reference probe:

```sh
python run_with_racket.py python -m arcpuzzles check ceef568b1cd4 \
  --stage task_tests --phase after --timeout 600 --out ../checks/new-task-tests
python run_with_racket.py python generators/ceef568b1cd4/workspace/reference_probe.py \
  --out ../checks/new-reference-probe.json
```

The probe retains 54 canonical, generated, boundary, contact, transformed,
recolored, and repeated cases, complete public authority receipts, and source
hashes. Test helpers use their own BFS; they do not call private generator
geometry functions to establish expected labels. Seven actual rival declarations
are checked, including two conjunction rules that defeated the first repair.

For production-shaped lessons, use the existing shared census:

```sh
python run_with_racket.py python -m arcpuzzles lesson-census ceef568b1cd4 \
  --per-band 100 --rotate-query --timeout 1800 --out ../checks/new-census.json
```

Use new output paths. Return the resulting reports with their source hashes.
The packet's `REVIEW.md` and `RESULTS.json` identify final versus intermediate
evidence; `checks/COMPRESSED-EVIDENCE.json` restores the compressed earlier census.
