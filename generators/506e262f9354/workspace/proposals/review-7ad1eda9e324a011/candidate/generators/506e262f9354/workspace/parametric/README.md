# Proposed expansion-direction prototype

This task-local prototype adds one **proposed, unapproved** episode-level rule
parameter to ARC family `training:db3e9e38` / generator `506e262f9354`.
It does not modify the canonical generator, canonical Racket authority,
approval state, or training admission.

## Parameter

| name | values | canonical/default | episode behavior |
|---|---|---|---|
| `expansion_direction` | `up`, `down` | `up` | fixed once per episode |

`up` returns the exact canonical Racket source byte-for-byte (raw SHA-256
`7d00cd1a50d3b572eb7a50d096cb5d01f0e7af4d8f9bc403d42a3b905b20dc6f`).
It uses the bottom endpoint of the vertical color-7 source as the apex and
expands upward. `down` uses the top endpoint as the apex and expands downward.
No input constraint depends on this parameter.

Both settings preserve the same reasoning steps:

1. locate one contiguous vertical color-7 source;
2. select the endpoint facing the expansion direction as the apex;
3. paint a canvas-clipped triangle whose horizontal reach grows one cell per row;
4. alternate colors 7 and 8 by horizontal distance from the source column;
5. write zero outside the triangle.

## Evidence writer

Run from the outer extracted packet directory:

```bash
python3 review.py run python3 generators/506e262f9354/workspace/parametric/prototype.py \
  --seed 17 --difficulty medium --train 3 --test 4 \
  --out ../checks/parametric/506e262f9354-direction-v2
```

The writer executes every canonical check, demonstration, query, rival, and
retained witness with the bundled Racket bridge. Before writing any public file,
it computes the complete public batch, proves each identifier hashes the exact
visible bytes, rejects duplicate visible identifiers, and sorts emission by
identifier. Existing output directories are rejected rather than overwritten.

Output includes source-bound private episodes, exact Racket programs, four
answer-free queries per setting, a canonical-default receipt, a setting witness,
and a byte/hash manifest. Public challenges contain demonstrations plus query
inputs only; hidden settings, seeds, programs, and query answers cannot affect
their IDs.

## Promotion qualification adapter

`promotion.json` declares the finite setting space and supported counts.
`adapter.py` returns deterministic Python label claims and exact Racket source;
the repository's isolated qualification worker independently replays every claim
through protected Racket. The adapter does not accept or enable the variant.

A bounded qualification run is:

```bash
python3 review.py run python3 -m arcpuzzles.cli --library . \
  parametric qualify 506e262f9354 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/parametric/qualification-506e262f9354
```

Qualification covers both settings on both seeds, requires four distinct query
claims per episode, checks the demo-only survivor certificate, and binds the
current generator, canonical rule, adapter closure, and protected executor.
Owner acceptance is a separate explicit operation and is not performed here.

## Limits

The prototype retains the selected generator's current input domain and source
constraints. Finite evidence against the one declared rival does not prove a
unique induction against every imaginable program. The extension remains
separate from production `generate(...)`, canonical approval, and training use.
For direct evidence writing, pass one live `RacketBridge` to avoid repeated
runtime startup; the promotion worker owns its own isolated protected runtime.
