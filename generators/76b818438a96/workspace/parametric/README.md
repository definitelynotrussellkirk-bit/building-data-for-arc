# Native recolor-origin family

Status: **native adapter prepared for exact-source owner qualification and acceptance**.
The canonical generator and both existing Racket rule files remain unchanged.
No training admission is implied.

| Private episode setting | Executed behavior |
| --- | --- |
| `recolor_origin=opposite` | Canonical rule: extend toward the associated marker, then recolor from the opposite original endpoint. |
| `recolor_origin=aligned` | Recolor from the marker-facing original endpoint; retain the same extension plan, count, color and path traversal. |

`adapter.py` implements the native `program(settings)` and
`generate(seed, settings, demos, queries)` interface. Its promotion contract
supports **2–6 demonstrations and 1–4 independent queries**, normally three and
four. Seeds are exact integers in `0..2**63-1`; booleans and invalid settings/counts
are rejected before sampling. The program for `opposite` matches the selected
canonical reference byte-for-byte. Settings affect labels, never sampled inputs.

## Runnable reviewer entry points

From the packet root, using its activated Python environment:

```bash
python3 review.py run python3 generators/76b818438a96/workspace/parametric/prototype.py \
  --seed 17 --parameter aligned --n-train 3 --n-test 4 \
  --out-dir ../checks/76b818438a96/example-aligned
python3 review.py run python3 generators/76b818438a96/workspace/parametric/verify_native.py \
  --out ../checks/76b818438a96/native-replay
python3 review.py run python3 -m arcpuzzles parametric qualify 76b818438a96 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/76b818438a96/qualification-replay --summary
```

Use new output directories. `verify_native.py` creates two Racket-labelled
four-query episodes, source/rule identities, finite-rival checks, size/content
measurements, and a replayable capped-count counterexample. Labels execute in
one protected Racket bridge per episode; generation does not copy a runtime tree
or import the old parent `reference_probe.py` helper. Native qualification
independently re-executes labels and demonstration-only setting identification.
Owner acceptance must run after integration against the exact live source.

## Input grammar and teaching

The source puzzle's two bent simple paths and two distinct singleton markers
remain. Native scenes require one geometric endpoint-to-marker ray per path,
no intersecting extension plans, and `1 <= extension_count < path_size`.
The strict upper bound prevents both settings from recoloring the whole path.

The first two demonstrations are constructive 14×14 and 30×30 scenes. They
include near/far marker distances and a long traversal crossing a bend, so short
teaching contexts reject fixed lengths and truncated walks. Remaining demos mix
20×20 and 24×24 canonical samples with bounded rejection. Four query sizes are
14×14, 20×20, 24×24 and 30×30. Large scenes contain at least 60 occupied cells,
three-turn paths, and content spanning all four boundaries; paths and corridors
scale with the canvas. Their four foreground colors are sampled from 1–9, and
all eight rotations/reflections can occur. This broadens the separate native
family, not the unchanged canonical sampler's overrides.

Each input has at most 32 proposals. Failure raises explicitly; no short episode
is returned. All episode inputs must be distinct. Separate demonstration/query
streams preserve query prefixes when counts change.

Every lesson checks 11 declared rivals: the other origin, ignored near markers,
extend-only, one-cell recoloring, caps at 3/6/10, including the marker in the count,
one-too-few cells, stopping at the first bend, and swapped marker roles. Rivals
fit demonstrations only; a survivor is unsafe only when it changes at least one
query. These Python diagnostic rivals supplement native Racket setting checks.
A real-Racket cap-six counterexample verifies the rejection and a same-count
teaching repair. Finite rivals do not establish universal uniqueness.

## Causal dependency

A traces the matched endpoint-to-marker ray and constructs `ext-cells`; its
input-dependent intermediate is the extension plan and `ext-count`.
B walks the original path from the selected endpoint and recolors exactly
`ext-count` cells using the associated marker color. The materialized Racket
program computes the count from that plan. The retained protected-Racket witness
changes the intermediate and identifies changed cells on the original path,
showing a downstream recoloring effect. This is a derived geometric dependency,
not a claim of iterative simulation or stateful obstacle motion.

## Public export and sequential reveal

`write_episode` stores exact `reviewer_support.public_challenge_bytes` under
`public/<public_challenge_id>.json`; IDs depend only on visible grids. Private
settings, seed, programs, query labels, certificates and runtime hashes go under
`private/`. Existing destinations are refused. The evidence tool orders its
batch by public ID and rejects duplicate visible payloads.

The full four-query public container is **controller storage**, not a model
prompt. The existing consumer reveals demonstrations plus query one first,
then one new query after each answer, without a total-count or final-turn hint.
For the same seed/demo count, one-query and four-query requests have identical
first-turn content. Tests verify the projection and input prefixes; no trainer
or turn controller is implemented or validated by this patch.

## Confirmed canonical limitation

The unchanged canonical sampler at seed `987076`, index `76`, difficulty `hard`
admits a second marker ray hidden behind another path. Racket's scanner ignores
obstructions and chooses that ray, yielding 24 differences from the diagnostic
Python mirror. The native guard rejects this input and all such extra rays.
The source-bound six-case probe is retained in
`checks/76b818438a96/canonical-ray-probe/` in the return packet. The canonical
sampler itself still needs the separately scoped guard repair; this native
qualification does not certify arbitrary canonical draws.
