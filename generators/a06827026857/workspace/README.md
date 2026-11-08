# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Exhaustive lesson-window probe

From the packet's `WORK/` directory, run:

```bash
python3 run_with_racket.py python3 generators/a06827026857/workspace/probe_lesson_windows.py --out ../checks/lesson-windows.json
```

The default is eight explicit seeds (`0` through `7`), all three difficulties,
and every consecutive start `0` through `3`: **96 four-pair lessons and 384
query rotations**. Use `--seeds 0 1 17` to select another seed set. Output paths
must be new. Explicit relative paths use the payload's working directory
(`repo/` under the packet wrapper); the default report is beside this script.
`--batch-size` and `--timeout` control batched Racket reference execution.

The probe directly calls the selected `generate()` at consecutive indices,
validates deterministic draws and `self_check`, and rejects duplicate inputs
within a lesson. It does not emulate production rejection or retry sampling;
run the shared `arcpuzzles lesson-census` separately for that coverage. Every
three-demo, one-query lesson is scored in its original order and with each of
the four labeled pairs held out once.

The report contains exact unique inputs and Racket labels, canonical pair
identities, source/rule hashes, seeds and indices, every declared rival's
predictions and canonical fit, lesson/rotation counts, and the first ambiguity
or error. Rival names come dynamically from all three required generator
mappings, with their namespaces preserved. A one-cell corner-attachment
witness checks the actual declarations without a copied rival list. Missing
or malformed contracts, incorrect `CANONICAL_SHORTCUTS`, malformed grids,
source drift, and execution errors fail visibly. Exit codes are `0` for complete
evidence with no measured ambiguity, `1` for ambiguity, and `2` for errors.
Checkpointed reports contain authoring answers and must stay separate from
visible-only solve challenges. These finite checks do not prove universal
identifiability or grant training approval.
