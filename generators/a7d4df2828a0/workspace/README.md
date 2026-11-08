# Task-local verification tools

`../generator.py` is the selected implementation. This workspace contains a reviewer probe, not a replacement labeler. It is returned inside the ordinary selected-task patch; no external service or new training dependency is needed.

## Real-Racket conservation probe

From the review packet root, after `python3 setup_racket.py`:

```sh
python3 run_with_racket.py python3 generators/a7d4df2828a0/workspace/probe_conservation.py --out ../checks/new-conservation.json
```

From any directory using a normal ARCpuzzles checkout and an installed Racket:

```sh
RACKET_PATH=/path/to/racket python3 /path/to/repo/generators/a7d4df2828a0/workspace/probe_conservation.py --library /path/to/repo --samples-per-band 1000 --racket-per-band 1000 --out /path/to/new-conservation.json
```

For the immutable baseline in a review packet, pass `--generator-source ../.review/baseline/repo/generators/a7d4df2828a0/generator.py` through the packet wrapper. This evaluates that generator against the current unchanged canonical rule. Use `--racket-per-band 0` for cheap geometry-only checking; a geometry-only PASS is not a label-validation PASS. The normal default performs 3,000 generated-input checks and 3 canonical target checks with actual Racket labels.

The tool copies a fresh runtime through the library's public runtime builder, records source/rule/ledger/runtime hashes, batches Racket calls, preserves a bounded number of failure grids, and refuses to overwrite evidence. Exit 0 means no failure in the requested checks; exit 1 means an observed failure; argument/setup/runtime errors also exit nonzero rather than producing a false pass.

Interpretation: in the v1 JSON schema, failed_cases is the number of failed validation events, potentially two for the same input (geometry and Racket). Use racket_pair_failures for the number of labeled pairs failing conservation. First-failure examples are capped at 24; full counters are retained. Canonical fixtures belong to this task and currently use lists of integer grids; this script is task-specific, not a generic multi-task canonical parser.

The contract ignores background 0 and the **input** control coordinate only. A motif repainted onto (0,0) in the output still counts. It detects canvas changes, malformed grids, missing motif cells, and color-count changes; it does not prove the transform coordinates are correct. Port the Counter idea only to another task with a separately reviewed lossless contract and appropriate masks. Intentional deletion/cropping/recoloring/duplication tasks must not inherit it.

## Focused regressions

```sh
# Packet root; on a plain repo checkout omit the leading repo/.
python3 -m pytest -q repo/generators/a7d4df2828a0/tests
```

There are 31 generator regressions and 10 probe regressions. The generator tests include a 3,000-draw sweep, 3,072 axis combinations, canonical-T reachability, all-edge reachability, malformed inputs, and strict override behavior. Racket is not needed for these unit tests; use the probe for authoritative label execution. The inherited battery does not automatically discover this new tests directory, so run both checks explicitly.
