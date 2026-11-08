# Source-bound review tools

These tools support future generator reviewers. They are **not solve-time tools**;
keep them closed during answer-masked Python solve phases. They do not send data
to any service. Reports refuse overwrite so failed evidence is retained.

`reference_probe.py` accepts a JSON list of cases (or `{ "cases": [...] }`). Each
case specifies `input`, or seed/sample_index with optional difficulty/overrides.
Optional expected_output and rival_output are checked against actual protected
Racket execution. Reports retain source and runtime identities, validator results,
full grids and command cwd. Source checkouts are staged with the official runtime
builder; relocated runtimes execute locally without original-source import aliases.
A zero report failure count does not erase intentionally invalid diagnostic grids.

`distribution_probe.py` measures five selected-task seed groups and emits hashes,
count distributions, exact pin mismatches, color/boundary coverage and witnesses.
Its L-count metric is foreground cells / 3, not a generic object-count oracle.
Use independent component tests as well. It can load the immutable original
source path without replacing the current task file.

`build_review_cases.py` rebuilds the main parity set, complete-frame rival cases,
and both drawn audit requests. It is tied to this review assignment; the runner
itself is task-independent. Canonical historical bare test pairs and digit-string
grids are normalized before reference execution.

From extracted packet root, after applying the source patch:

```bash
python3 -m pytest -q repo/generators/3ab9aab86992/tests/test_generator_3ab9aab86992.py
python3 repo/generators/3ab9aab86992/workspace/build_review_cases.py --root repo --out checks/replay-cases
python3 run_with_racket.py python3 generators/3ab9aab86992/workspace/reference_probe.py --root . --task 3ab9aab86992 --cases ../checks/replay-cases/main-parity-cases.json --canonical --out ../checks/replay-parity.json
python3 repo/generators/3ab9aab86992/workspace/distribution_probe.py --root repo --generator repo/generators/3ab9aab86992/generator.py --seeds 200 --out checks/replay-census.json
python3 run_with_racket.py python3 -m arcpuzzles check 3ab9aab86992 --battery --timeout 4000 --phase after --out ../checks/replay-battery
```

`run_with_racket.py` changes directory to `repo` and supplies the runtime binary;
therefore its argument paths differ from direct packet-root Python commands.
Create neither the battery output directory nor its log file inside that output
directory before starting the battery. Use fresh paths on reruns.

The returned `checks/portable/verify_portable.py` additionally rebuilds a declared
runtime under `repo/var/review-portable-3ab9aab86992` and invokes an isolated child.
It retains the actual cwd, copied hashes and project-module import paths. Remove
only that generated runtime after verification and before packaging, since a
review delta must not include another runtime or out-of-scope source files.

Known review limitations: no full lesson-identifiability proof, no hidden solve
score, no audit-source fixes, and one unmodified repository streaming-timeout
failure. Read the root REVIEW/DECISIONS/AUDIT files rather than treating this
workspace as an independent approval record.
