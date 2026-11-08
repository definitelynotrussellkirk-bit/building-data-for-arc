# Section-frequency parameter

Task `0ee358bd9d75`, original family `training:780d0b14`.

Full-zero rows and columns partition the input into rectangular sections. The
output contains one selected nonzero color for each section, in the same spatial
order. The episode fixes one private `selection` value:

| Selection | Behavior |
|---|---|
| `most_frequent` (canonical default) | Select each section's unique most frequent nonzero color. |
| `least_frequent` | Select each section's unique least frequent nonzero color. |

`programs/most_frequent.rkt` remains byte-identical to the canonical program.
The alternative changes its frequency sort direction. Both programs first find
input-dependent divider positions, then use those positions to form section
histograms before selecting colors. `verify_causal.py` executes a same-shape
wrong-divider ablation through protected Racket; it does not substitute a Python
label for either execution.

## Counts, teaching, and common input grammar

`generate_episode(seed, selection=..., demos=3, queries=1)` supports **2–6 demos
and 1–4 queries independently**. `sample_inputs` accepts the same count keywords.
The omitted selection is canonical; `selection=None` chooses once from the seed.
The native `adapter.py` exposes `program(settings)` and
`generate(seed, settings, demos, queries)`, with exactly one settings key,
`selection`. `promotion.json` declares the same bounds.

Sampling uses a bounded pool with separate demo and query streams. Increasing a
count preserves existing prefixes; changing the demo count leaves all query
inputs unchanged. Both settings use identical inputs for the same seed and
counts. Every pool input is distinct. The first demo is 8×8, the first query is
30×30, and the other profiles cover rectangular and intermediate sizes. Active
sections extend across the large canvas; each contains at least 40% nonzero
cells, subject to the stronger local row/column coverage requirement.

Inputs have 8–30 rows and columns, 1–3 internal full-zero divider rows and
columns, and section sides of at least two cells. Every section contains zeros,
has nonzero coverage in every local row/column, and has at most three nonzero
colors with unique least and greatest frequencies. Generated sections always
have two or three colors. The validator also admits the canonical one-color
sections. Tied extrema are outside the prototype grammar.

Each sampled demonstration independently distinguishes both frequency settings
and rejects first-nonzero, last-nonzero, minimum-color, and maximum-color
shortcuts under either setting. This finite pixel-based input filter never sees
query labels. Every emitted label comes from Racket. Sampling permits at most
256 candidates per pool position and raises on exhaustion; it never emits a
short episode. The original `rotate_episode(episode, query_index)` remains
available for exactly three demos and one query.

## Run from the outer extracted packet directory

These commands use the prepared `WORK/.venv` and bundled Racket wrapper. Output
directories must be new.

```bash
# Four novel, labeled queries; only the first query is published initially.
WORK/.venv/bin/python review.py run python3 \
  generators/0ee358bd9d75/workspace/parametric/prototype.py \
  --seed 17 --selection least_frequent --demos 3 --queries 4 \
  --out ../checks/0ee358bd9d75/example-new

# Focused current prototype tests; production generator behavior is separate.
WORK/.venv/bin/python review.py run python3 -m pytest -q -p no:cacheprovider \
  generators/0ee358bd9d75/tests/test_parametric_extension.py \
  generators/0ee358bd9d75/tests/test_parametric_counts.py \
  generators/0ee358bd9d75/tests/test_causal_witness.py

# Optional legacy 3-demo/1-query census, including all four holdout rotations.
WORK/.venv/bin/python review.py run python3 \
  generators/0ee358bd9d75/workspace/parametric/audit.py \
  --seeds 0 50000 --out ../checks/0ee358bd9d75/census-new

# After native qualification, bind and replay the causal witness.
WORK/.venv/bin/python review.py run python3 \
  generators/0ee358bd9d75/workspace/parametric/verify_causal.py \
  --qualification ../checks/0ee358bd9d75/qualification/qualification.json \
  --out ../checks/0ee358bd9d75/causal-witness.json
```

The causal witness keeps the output dimensions fixed: on its lawful 8×8 input,
the real divider row is 2; substituting row 5 changes the executed answer from
`[[1,5],[5,7]]` to `[[5,7],[5,7]]`. Repeated color 5 prevents a per-color lookup
from replacing section membership. The witness retains the actual section
bounds and the exact qualified default program privately.

## Public and private delivery

`write_episode` and the CLI write only `public/<sha256>.json` plus a `private/`
directory. The filename hashes **exactly** `reviewer_support.public_challenge_bytes`
for the first visible turn, including its trailing newline. All programs,
settings, seeds, source bindings, query outputs, and later query inputs stay in
`private/episode.json` and `private/program.rkt`. The legacy audit writer uses the
same hash-named public format and keeps its reports/programs under `private/`.

A private controller calls `public_turn(episode, query_index)` only after the
preceding answer, and names that turn with `public_challenge_id(turn)`. Each turn
contains the original labeled demos and one query input; it contains no index,
total count, final-turn flag, or future input. One-query evaluation and
four-query training have byte-identical first turns at equal seed, selection,
and demo count. Previous submitted answers remain controller state. The
whole-episode `public_challenge` function is retained for compatibility; use
`public_turn` for sequential solver delivery.

## Evidence boundary

Current scoped checks are under `WORK/checks/0ee358bd9d75/`; the native source
inventory is `evidence/manifest.json`. Retained earlier evidence describes its
own source revision. Finite shortcut checks and protected Racket execution do
not prove universal identifiability, model learning, or training admission.
Native qualification and exact-source owner acceptance are separate from this
prototype, its canonical generator approval, and its diagnostic census. See
`repo/docs/parametric-promotion.md` for that handoff.
