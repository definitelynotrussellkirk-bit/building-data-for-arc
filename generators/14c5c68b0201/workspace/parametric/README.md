# Native `tiling_axes` candidate

The root `adapter.py` and `promotion.json` expose the retained three programs
through the packet's native contract. `both` remains the exact canonical default;
`horizontal` and `vertical` reuse the historical materializer unchanged. The
production generator and all three retained program definitions are unchanged.
This is a reviewer candidate; owner acceptance and training admission are pending.

## Native API

`generate(seed, settings, demos=3, queries=4)` takes settings exactly
`{"tiling_axes":"both"}`, `{"tiling_axes":"horizontal"}`, or
`{"tiling_axes":"vertical"}`. Seeds are exact integers from 0 through 2**63-1;
independent counts support 2–6 demonstrations and 1–4 queries. Ordinary use is
three demonstrations/four queries. Inputs match across settings, and separate
per-split/index streams preserve both prefixes when counts change.

The first demonstration is 8×10 with an offset 2×3 sparse stamp. The second is
12×16 with two holes, 3×4 and 3×5 stamps, background 9 and offset origins. Together
they refute eleven explicitly defined Python rivals for `both`/`vertical`, and
ten for `horizontal`: the two other
axis rules plus identity, solid fill, hole/canvas phase, fixed 2×2 period,
first-hole-only, fixed background 8 and transposed stamp, plus a fixed three-row
period when rows expand. These are finite
demonstration-only checks. Native qualification separately executes all three
exact setting programs and requires the chosen setting to be the sole survivor.

The mixed two-row/three-row demonstrations repair an observed teaching gap:
an earlier minimum lesson used only three-row stamps, allowing a fixed-height
Racket rule to fit both demonstrations and fail on a two-row query. The final
regression executes that rival and its Python mirror; it is rejected before
query answers are seen. The demo count stays at two.

The four query shapes are 19×13, 26×22, 24×24 and 30×30. Large scenes are freshly
constructed with two separated holes; the 30×30 scene has two 12×12 holes
covering 288 cells, extending to one-cell outer margins on opposite sides of the
canvas. Sparse motifs, distinct active colors, phase offsets and a boundary
stamp make the full scene substantive. The 612 background cells keep a unique
modal background. Only parametric geometry is extended; declared production
layout overrides are unchanged.

## Replay and actor-safe examples

From the outer packet directory:

```sh
WORK/.venv/bin/python review.py run python3 \
  generators/14c5c68b0201/workspace/parametric/native_probe.py \
  --out ../checks/14c5c68b0201/self-audit-new
```

The reusable probe checks seeds 0/17, demo counts 2/6, all three settings and four
queries: 12 episodes and 96 labels through native `wrap_rule` and protected
Racket. Its example export retains one two-demo/four-query episode per setting.
`examples/public/` contains controller-side challenges. Send only one file from
`examples/turns/`, or `visible_turn(episode,index)`, to the actor: demonstrations
plus the current query, with no future input, total count, program, private
setting or answer. First-turn bytes match single-query generation. IDs hash
exact visible bytes, and duplicate episodes/turns are rejected before creating
the destination. Private material stays in `examples/private.json`.

The native inventory uses the packet's guarded manifest command. Qualification
and protected causal evidence live under `WORK/checks/14c5c68b0201/`. The causal
witness uses canonical `both` episodes and changes stamp-origin modulo phase to
hole-origin phase. Its painted positions depend on the recovered stamp
intermediate; changing that intermediate changes the output. One-axis Python
phase rivals remain separately defined alternatives, not claims of equivalence
to that particular Racket substitution.

## Historical standalone prototype

Status: **proposed and unapproved**. This task-local prototype does not change
`generator.py`, the canonical ledger, the approved rule hash, or training
admission.

The canonical task finds each sparse colored stamp inside its rectangular hole
and repeats the stamp's exact bounding-box pattern across the hole. The
prototype keeps all extraction, color, phase-origin, and hole semantics fixed
and varies only the axes along which that repetition expands. One setting is
chosen once per episode and remains fixed across every demonstration and query.

| `tiling_axes` | Executed transformation | Canonical/default |
|---|---|---|
| `both` | Repeat the stamp period across rows and columns over the full hole. | yes |
| `horizontal` | Repeat across columns only, restricted to the stamp's original rows. | no |
| `vertical` | Repeat across rows only, restricted to the stamp's original columns. | no |

Allowed values are exactly `both`, `horizontal`, and `vertical`. The prototype
hash-pins the canonical Racket source and derives each alternative by one
fail-closed, reversible replacement at the unique paint predicate. Every label
and rival prediction is executed by the corresponding exact Racket program.

## Input and episode contract

Inputs come from the selected approved generator with exact scene overrides.
For retained evidence, every stamp bounding box is strictly smaller than its
hole on both axes; therefore all three settings are lawful and produce distinct
outputs on every retained input. Inputs are sampled without consulting the
hidden setting.

Demonstration and query counts are independent plain integers in `1..12`.
Defaults are 3 demonstrations and 4 queries. All pairs in an episode are
distinct. The analyzer requires the demonstrations alone to refute both rival
settings before a query is counted as identified.

Public files contain only demonstration inputs/outputs and query inputs. Their
opaque names are the repository `public_challenge_id` of the exact visible bytes;
seeds, settings, Racket, private hashes, and query answers are excluded. Batch
rows and files are emitted in ascending public-ID order, and the writer fails
closed before publication if visible payloads repeat or identifiers collide.

## Reproduce the retained 3 × (3 demo + 4 query) evidence

Run from the outer extracted packet directory:

```bash
python review.py run python3 generators/14c5c68b0201/workspace/parametric/prototype.py \
  materialize --out ../checks/parametric/14c5c68b0201-tiling-axes-v1 \
  --seed 0 --demos 3 --queries 4

python review.py run python3 generators/14c5c68b0201/workspace/parametric/prototype.py \
  verify --out ../checks/parametric/14c5c68b0201-tiling-axes-v1
```

The writer refuses to overwrite an existing output directory, duplicate visible
payloads, or public-ID collisions. The verifier
rechecks current source hashes, every retained file receipt, all eight labeled
canonical pairs, exact canonical public bytes and public/private projection,
opaque filenames, tree-contained stored Racket programs, labels, and
demonstration-only rival analyses.

Focused tests:

```bash
python review.py run pytest -q \
  generators/14c5c68b0201/tests/test_parametric_tiling_axes.py
```

## Boundaries

Evidence covers three retained episodes, the declared three settings, and the
recorded deterministic input schedule; it is not an exhaustive proof over all
seeds or grids. The variants remain separate from the canonical production rule
and have no approval or training status.
