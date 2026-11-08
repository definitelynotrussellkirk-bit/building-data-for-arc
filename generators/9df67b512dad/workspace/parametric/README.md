# Zone-selector parametric prototype

Status: **proposed prototype**, separate from the selected canonical generator and its approval. This does not register rule variants with the production parametric API or admit data to training.

## Rule and parameters

Compress the same nine zones into a 3×3 grid: four corner singletons, four boundary strips excluding corners, and the rectangular interior. Empty zones return 0. Otherwise select the first or last nonzero cell under the episode's scan order.

| Parameter | Allowed values | Original/default |
|---|---|---|
| `scan_order` | `row_major`, `column_major` | `row_major` |
| `pick` | `first`, `last` | `last` |

The default returns the **exact canonical Racket source** from the source-bound `9df67b512dad` ledger row (ARC parent `bc1d5164`). The other three programs change the reduction's traversal nesting or selection condition. Zone roles, output size, zero handling, and the rule throughout an episode remain fixed. Scan order agrees on single rows/columns but differs within the two-dimensional interior.

`generate_episode(seed, settings=None, input_seed=None, demos=2, queries=4)` uses the canonical setting when settings are omitted. Explicit settings are fixed for the whole episode. Counts are independently supported from 1 to 8. All demonstration/query inputs are distinct. `input_seed` allows four settings to use the same input sequence; otherwise it defaults to `seed`. Sampling uses a local `random.Random`, leaving global RNG state unchanged. Numeric API arguments and cells require literal Python integers; booleans, floats and numeric strings are rejected.

## Exact runnable commands

From the extracted packet's outer directory after included Racket setup:

```bash
python3 review.py run python3 generators/9df67b512dad/workspace/parametric/prototype.py \
  --all-settings --seed 23 --input-seed 91 --demos 2 --queries 4 \
  --out ../checks/parametric/four-settings
```

This exports **four complete episodes**, each with two demonstrations and four distinct queries, through its matching protected Racket program. The destination must not exist. For one alternative replace `--all-settings` with `--scan-order column_major --pick first`.

Focused prototype tests, with pytest installed in the selected Python runtime:

```bash
python3 review.py run python3 -m pytest \
  generators/9df67b512dad/tests/test_parametric_9df67b512dad.py -q
```

An ordinary checkout can run the script directly with Python 3.12+ and Racket on PATH or `RACKET_PATH` set. It discovers its own included runtime and canonical ledger from its file location, supporting both repository and staged runtime layouts; no predecessor or sibling checkout is imported.

## Sampling and demonstration-only inference

Inputs have 5–14 rows, 7–16 columns, 4–8 occupied zones, and no solid foreground 2×2 block. A sparse interior diamond has four different colors at its topmost, leftmost, rightmost and bottommost positions. Consequently all four selectors yield different center outputs on the same input. Boundary markers vary in location, count, zone occupancy and color; occupied and empty zones remain visible.

Five foreground colors are sampled without replacement from 1–9. This is a **prototype palette extension** beyond the canonical generator's current 1–3-color sampling range. At least one top boundary zone is occupied in every sample, with a distinct fifth color that refutes the rival assigning the globally first color to every occupied zone. The sampler is narrower than the admitted sparse-marker grammar: every sampled interior has the four-point diamond, and the top boundary is never entirely empty.

`infer_from_demonstrations` accepts only demonstration pairs. It executes all four settings plus the global-first occupancy rival through the included protected Racket bridge. `require_identifiable` requires the declared setting alone to survive and rejects the occupancy rival. Generation completes that check **before executing query labels**. Since every declared alternative is eliminated by the demonstrations, each query is supported without using its answer to infer the rule. This is a finite-rival certificate; arbitrary program uniqueness and measured learning benefit are unproved.

Every label comes from exact emitted Racket. Before creating a destination, the writer replays labels and recomputes the certificate, refusing to trust supplied execution receipts. It rejects underidentified lessons, mismatched query labels, repeated inputs and duplicate visible batch payloads. Uniqueness sampling is bounded at 128 attempts per input and fails explicitly if insufficient.

## Public/private output

Only `public/` is model visible:

- `<id>.json` contains exactly the shared `public_challenge_bytes` projection: demonstration inputs/outputs and query inputs.
- `index.json` contains the sorted list of visible-content SHA-256 IDs.

Each public filename hashes exactly its visible bytes. Settings, seeds, code, query answers and private metadata do not affect its ID. Sorting by that ID also prevents input batch order from encoding setting order.

`private/episodes/<id>.json` keeps complete labeled episodes, settings, seeds, source hashes, exact Racket text/hash, runtime identity and demonstration certificates. `private/rules/<program-sha>.rkt` materializes exact programs. `private/manifest.json` holds the private settings map, source hashes, command and limits. Keep the entire private directory away from the learner.

Retained receipts and the four-episode export are under `WORK/checks/parametric/`. They are bounded source-specific evidence, separate from canonical repair coverage and variant approval.
