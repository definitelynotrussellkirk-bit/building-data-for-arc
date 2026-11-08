# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Executable authoring tools

- `shortcut_probe.py` replays the retained seed-61 teaching counterexample,
  calls the public selected-Racket API, iterates the generator's actual rival
  declarations, and checks every holdout of a repaired five-pair window.
- `parametric/connectivity.py` materializes and executes the proposed `{4,8}`
  connectivity settings and exports public challenges separately from private
  parameter/rule/answer evidence. See its README for the bounded contract.
- `review_tools/compress_evidence.py` losslessly compresses an existing JSON
  receipt into the native evidence format with sizes, hashes and restoration
  instructions. It preserves the original and refuses to overwrite evidence.

From the outer packet directory, with the packet Python environment activated:

```bash
python3 review.py run python3 generators/48283e01e8ab/workspace/shortcut_probe.py --out ../checks/shortcut-replay.json
python3 review.py run python3 generators/48283e01e8ab/workspace/parametric/connectivity.py --out ../checks/parametric-replay --seeds 0 1 17 83 --difficulties easy medium hard
```

Choose unused output paths. These are authoring tools that can expose canonical
answers; they do not belong in a visible-only solve session. The full review
retains exact executed commands and measurements in `RESULTS.json`.
