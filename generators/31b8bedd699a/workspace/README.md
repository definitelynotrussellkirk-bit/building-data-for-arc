# Reusable review tools for 31b8bedd699a

The selected implementation is `../generator.py`. These probes use the public
runtime API and keep independent semantic observations separate from canonical
Racket labels. They never change the selected implementation or approval state.

## Inspect the exact semantic choices

From the original packet's outer directory (the directory with `review.py`):

```sh
python3 review.py run python3 generators/31b8bedd699a/workspace/frame_semantics_probe.py --out ../checks/new-semantic-probe.json
```

`frame_semantics_probe.py` checks the four unique canonical examples and four
explicit semantic witnesses through `Catalog.apply`. It scores ten independent
design candidates, then loads and checks every live declaration in
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS` and `SEMANTIC_RIVALS` without freezing
a copied rival-name list. It checks fixed 4×4 normalization, top-left orientation,
horizontal ties, multiplicity, solid filtering and spatial order. `--describe`
prints its interpretation without running Racket or writing files.

The script locates `reviewer_support` within its own source/runtime tree and uses
`find_root` and `canonical_pairs`; it does not assume a fixed ancestor depth.
The same file was checked from an unrelated working directory and a relocated
minimal tree. Keep canonical helpers closed during visible-only solves.

## Replay the retained teaching failure

```sh
python3 review.py run python3 generators/31b8bedd699a/counterexamples/replay_include_solids_in_axis.py --out ../checks/new-solid-axis-replay
```

The fixture beside that script contains the exact six-pair lesson from the first
v3 draft. The wrong rule includes solid distractors when choosing the axis. It
fits the five demonstrations but changes the held-out query. The replay obtains
fresh Racket labels for those exact inputs and checks the saved labels and rival
predictions. A successful replay means the historical defect was reproduced,
not that the final generator still emits that lesson. Use a new output path.

## Run regressions and the production census

```sh
python3 review.py check --stage task_tests --phase after --timeout 600 --out ../checks/new-task-tests
python3 review.py run python3 -m arcpuzzles lesson-census 31b8bedd699a --enumerate-schedule-period --schedule-seed 17 --band easy --band medium --band hard --timeout 600 --out ../checks/new-schedule-census.json
```

The task suite contains 139 independent contract cases plus 49 schedule/reference
cases. Schedule tests inspect seeds 0–15, all three difficulty bands, all six
cyclic starts and every held-out position, loading the live fourteen rival
declarations. A separate 18-input subset is labeled by Racket. Python screening
alone is not authoritative label validation; the public census checks the actual
production materializer and retains accepted indices and labels.

The final return's `checks/code-review-shortcut.py` and `.json` also demonstrate
the remaining default-support correlation against eight authoritative cases.
See `../notes.md` for the two remaining distribution limits. The complete
assignment reports, exact commands, runtime manifests and lossless evidence
restoration mapping are in the returned review ZIP.
