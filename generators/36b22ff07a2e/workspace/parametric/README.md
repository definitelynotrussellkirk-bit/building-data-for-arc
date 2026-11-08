# Minimum marker area — proposed variant

This preserves `36b22ff07a2e` / `training:ac6f9922`: infer the background and
field, find enclosed rooms, and compress their row/column arrangement. A room
contributes its marker color only when that marker's area is at least the
episode's `minimum_marker_area`; otherwise it contributes the observed outer
background. Room positions and output dimensions are retained.

| Parameter | Values | Canonical default |
|---|---|---|
| `minimum_marker_area` | exact integers `1`, `2`, `4` | `1` |

The default returns the exact canonical Racket string. Alternate programs
replace only its empty-marker predicate with a marker-cell-count threshold.
Production `generator.py`, its canonical authority and its approval are untouched.
This workspace and its adapter remain a proposal until explicit owner acceptance;
qualification and training admission are separate decisions.

## Generate and replay

From the **outer extracted review packet**:

```bash
python3 review.py setup
python3 review.py run python3 generators/36b22ff07a2e/workspace/parametric/prototype.py build --seed 0 --seed 17 --demos 2 --queries 4 --out ../checks/marker-area-new
python3 review.py run python3 generators/36b22ff07a2e/workspace/parametric/prototype.py verify ../checks/marker-area-new
python3 WORK/check_public_exports.py WORK/checks/marker-area-new/public --demos 2 --queries 4
```

Use a new output directory. Omitting `--minimum-marker-area` builds all three
settings on each seed; specifying it selects one. The retained demonstration
batch is `WORK/checks/parametric/final-batch/`: six episodes, two demonstrations and
four distinct queries each. Labels and all three parameter predictions are
checked using the protected Racket bridge. The standalone `verify` command
re-executes the stored labels in a fresh Racket process.

Python interface (under the same launcher):

```python
episode = generate(seed=17, settings={"minimum_marker_area": 2}, demos=2, queries=4)
```

`generate` is the adapter's deterministic proposal with Python label claims.
Use `generate_verified`, the CLI, or protected native qualification to establish
Racket execution. `write_batch` only serializes; it does not approve labels.

## Grammar, support and identifiability

- Seeds are exact integers `0..2**63-1`; demonstration counts `2..8` and query
  counts `1..8` are independent. Invalid values fail explicitly. Sampling has a
  32-attempt budget for each distinct input and returns no partial episode.
- One setting is fixed across each episode. The input RNG and retry schedule
  never receive that setting. Equal seed/counts give identical ordered input
  grids across all settings. Demo and query streams have separate index ranges.
- Sampling reuses production room construction, then redraws rectangles strictly
  inside those rooms. Samples cover `2x3`, `3x2`, and `3x3` room matrices. They
  contain areas `1`, `2`, `3`, and `4`, both `1x2` and `2x1` markers, and at least
  one empty room. Alternating scenes repeat a color across area-1 and area-3
  rooms, requiring per-room counting. The default also reproduces all four
  distinct canonical pairs; eight ledger entries contain duplicated pairs.
- Each certificate fits the three threshold settings and seven named rivals
  against demonstration inputs/outputs only. Rivals are width, height, strict
  `>` instead of `>=`, room area, global-per-color area, hardcoded background 0,
  and transposition. Query answers are not read by the certificate. At threshold
  1 some rivals are equivalent over this grammar; surviving equivalent rivals
  are allowed when they agree on every query. This is finite-rival evidence,
  not uniqueness against arbitrary programs.
- The examples include meaningful larger inputs (up to `26x22` and `26x20` in
  the retained seeds). Outputs remain room matrices of at most `3x3`. This work
  does not add a production size override or address the large-output training
  gap. No new production generation option is advertised.

## Public/private boundary

`public/` contains only demonstration input/output grids and query inputs. Each
filename is the SHA-256 of the exact bytes produced by the shared public
projection helper. Public files, IDs and ordering are independent of seeds,
private settings, programs, query answers and incoming batch order. Duplicate
visible episodes and repeated input grids are rejected before publication.
Private labels, programs, source hashes and certificates are under `private/`.

The verifier checks the exact file/directory inventory, visible-byte identities,
strict grid and certificate types, seed/count replay, private source/program
identity, Racket labels for all parameter settings, and the demonstration-only
certificate. Source hashes cover the same-checkout Python/Racket runtime and its
external rule parser. A stored runtime identity must match the live executable
hashes and protection properties; machine-local paths may change on relocation.
It rejects changed labels, sources, false provenance, and extra entries; it is not
a signature or authentication mechanism for untrusted archives. Give models only
`public/`.

## Promotion handoff

`adapter.py` and `promotion.json` implement the native bounded contract. The
source/evidence inventory under `evidence/manifest.json` is created by
`arcpuzzles parametric manifest`; see its recorded checks and current source hashes.
Owner-side fresh qualification can use:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify 36b22ff07a2e --seed 0 --seed 17 --demos 2 --queries 4 --out ../checks/marker-area-qualification-new
```

The returned exact source passed that native qualification: six setting/seed
jobs, 60 protected Racket evaluations, and the requested setting as the sole
parameter survivor in every job. Its portable receipt and execution record are
retained under `evidence/current/qualification/`. All 21 new focused tests pass.
The separate full task-test wrapper stopped before staging because pytest was
absent; a dependency-install attempt had no available package-index distributions.
That aggregate is explicitly blocked, not reported as passing.

Do not infer variant acceptance or training admission from an export, manifest,
test pass, or qualification receipt.
