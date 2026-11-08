# Workspace

The selected implementation is `../generator.py`. This folder contains a
reusable independent authoring probe; it is not a selected alternate generator.

From an extracted packet root:

```sh
python3 review.py setup
python3 review.py run python3 generators/1ee7274bdbb0/workspace/reviewer_rival_probe.py --out ../checks/new-rival-probe
python3 review.py run python3 -m pytest -q generators/1ee7274bdbb0/tests
python3 review.py run python3 -m arcpuzzles lesson-census 1ee7274bdbb0 --per-band 100 --rotate-query --out ../checks/new-lesson-census.json
```

Use a new output path per source revision. Install pytest in the interpreter's
environment for portable `--stage task_tests`; that runtime intentionally
disables user-site packages. In this return a local venv resolved that setup
issue without changing protected runtime code.

The probe loads the selected source via `reviewer_support.find_root`, extracts
tile features independently, verifies labels through public `Catalog.apply`,
and dynamically enumerates the current canonical-shortcut and rival namespaces.
It reports unique input hashes separately from requested sample counts. The
authoring probe exposes reference answers; never run it during a visible-only
solve. The default lesson has six demonstrations and one query; named-rival
rotation guarantees concern seven consecutive non-overridden default draws.

Exact replay inputs are in `../counterexamples/`. Source-bound review receipts
and the retained failed iterations live in return `review-5339bc49ee268b8b`.
