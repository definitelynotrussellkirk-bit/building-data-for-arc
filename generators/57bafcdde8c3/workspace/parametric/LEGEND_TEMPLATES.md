# Legend/template authoring prototype

**Status: proposed.** This is a task-local family inspired by public evaluation task `edb79dae`. Its relationship to the assigned production task is unverified. Production code and canonical labels are unchanged; no owner qualification, hidden-answer accuracy, learning benefit or training admission is claimed.

## Rule and the source ambiguity

Find the unique hollow rectangular frame and crop it inclusively. Read each exterior 3×4 arrow tile as a directed source-to-target color map. Group remaining exterior template cells by their original color, retaining disconnected pieces. Replace each solid square inside the frame with the matching source-color template at its original scale and location; clear missing template cells to background. Recolor the resulting shape according to the episode's policy:

| `mapping_policy` | Meaning |
|---|---|
| `once` | Apply one source-to-target step; the Python prediction helper's default. |
| `terminal` | Follow the acyclic map to its terminal color. |

The policy is fixed across all demonstrations and queries. It changes the transformation, not the input sampler. Both policies reproduce both original demonstrations in Racket, because those examples do not distinguish one mapping step from a chain. Their visible-query predictions differ in **88 cells**. The source query includes chain `3→9→2→1→6` and map `8→7`; the color-8 template has 15 cells split into components of 13 and 2. The reference implementation preserves both pieces. Neither generated prediction is presented as the unknown hidden answer.

`source_probe.json` contains both predictions and the exact public-source binding. No hidden query-answer file is read. The source challenge hash is `c9190b5e5bdd993afe9b9048180eebf462a222b6597f33d4d8da0ac950544a85`.

## Generate and replay

Run from the extracted packet's outer directory, containing `review.py`. Initialize its normal pinned runtime if it is not already installed. Use a new output directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B review.py run python3 -B \
  generators/57bafcdde8c3/workspace/parametric/legend_templates.py build \
  --seed 17 --seed 29 --demos 2 --queries 4 \
  --out ../checks/legend-example

PYTHONDONTWRITEBYTECODE=1 python3 -B review.py run python3 -B \
  generators/57bafcdde8c3/workspace/parametric/legend_templates.py verify \
  --out ../checks/legend-example

PYTHONDONTWRITEBYTECODE=1 python3 -B review.py run python3 -B \
  -m unittest discover -s generators/57bafcdde8c3/tests \
  -p test_legend_templates.py -v
```

The build emits both policies for each supplied seed, derives every label through the protected Racket bridge, compares the Python mirror, checks the original public demonstrations and verifies the resulting export. Verification re-executes every saved label and recomputes public bytes, IDs, exact source/program identities, counts and finite-rival certificates. Racket and the packet's existing NumPy/Pillow dependencies are required; the tests use standard-library `unittest`. A normal repository checkout can run the same payload after putting its existing `src` and reviewer support on the import path and exposing Racket.

The Python API `generate_episode(seed, policy, demos=2, queries=4, *, bridge, max_attempts=32)` uses exact integer seeds 0 through 2^63−1, independent demo/query counts 1–8, and bounded distinct-input attempts 1–256. An output directory must not already exist. Inputs are distinct within each episode; independent episodes can intentionally share inputs while teaching different transformations.

## Declared input grammar

Inputs are rectangular integer-color grids no larger than 30×30, with a unique modal background, one hollow frame, non-overlapping exterior legend tiles and one complete source template per legend source. Legend mappings are acyclic. Occupied frame objects are solid source-colored squares of one common side length 3–5. Each template spans the corresponding square box and is non-solid. Every legend source occurs inside the frame.

The sampler draws 2–4 source colors plus a terminal, with a first sample containing a four-source chain. It uses a 3×3 frame slot lattice, repeated labels and empty slots. Palettes, template masks and ordering vary. Two layouts place the frame on the left with templates to its right, or on the right below the templates. One template intentionally contains a detached piece. Subsequent random masks are distinct; bounds and parsing are checked. Randomness is local to the seed and candidate index, independent of the policy and Python's global RNG.

This is a bounded synthetic grammar. It does not cover arbitrary arrow shapes, multiple frames, mixed-size blocks, overlapping legends, cyclic maps or unrestricted spatial layouts. The parsed public examples include a broader existing composition, while generated scenes use the documented 3×3 lattice.

## Finite lesson certificate and public export

The declared rivals are `once`, `terminal`, `two_hops`, `three_hops`, `no_recolor`, `full_blocks`, `first_template`, `destination_template` and `largest_component`. Only demonstrations determine which rivals survive. Every requested query must have the same answer under all demo-fitting rivals. A remaining disagreement or count shortfall fails; the generator does not clone a query. Rival fitting is a Python diagnostic; retained chosen-rule labels come from Racket. This finite list is not universal rule identification.

Solver-facing files are only `public/<visible-byte-sha256>.json`. They contain demonstration inputs/outputs and query inputs serialized using `reviewer_support.public_challenge_bytes`. Names and sorting use only these visible bytes, never seeds, policy, programs or query answers. Duplicate visible payloads are rejected. Private/controller files are:

- `private.jsonl`: seeds, policy, all labels, exact Racket programs, source bindings and per-query certificates.
- `manifest.json`: nonempty sorted identity inventory and exact private/public content hashes.
- `source_probe.json`: source demonstration checks and both visible-query predictions.

The verifier rejects stale source/program/certificate data, invalid numeric types, duplicate inputs, incorrect public projections, missing hashes and empty exports. Thirteen focused tests exercise these boundaries, source ambiguity, disconnected template preservation, deterministic structured sampling, count independence, and live Racket export/replay.

Retained evidence uses seeds 17/29 and both policies: four episodes, 24 labeled pairs and 16 queries. The build also checks four source demonstration-policy combinations. These are reproducible bounded examples; production promotion and training admission require the owner's separate process.
