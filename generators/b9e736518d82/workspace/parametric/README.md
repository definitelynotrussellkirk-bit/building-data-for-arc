# Parametric prototype: choose the turn-marker half

Status: **prototype / proposed**, not production-approved.

The fixed canonical generator and canonical Racket authority remain unchanged.
This task-local prototype adds one episode-level rule parameter:

| Parameter | Allowed values | Canonical/default | Effect |
| --- | --- | --- | --- |
| `turn_half` | `larger`, `smaller` | `larger` | At a bend marker, recolor the selected unequal channel half cyan. |

The latent adjacent-orange channel, orange walls, optional maroon marker, cyan
fill color, no-marker branch, and straight-marker branch are invariant. Only the
comparison between the two components created by removing a bend marker changes.
The existing generator already guarantees unequal halves for turn markers.

The parameter is selected once from the episode seed and held fixed for all four
demonstrations and the query. Each episode includes two turn-marker
demonstrations, so the larger-vs-smaller setting is observable before the
turn-marker query. `larger` materializes the exact canonical Racket program;
`smaller` changes only the final `half1`/`half2` length comparison.

## Reproduce the retained evidence

From the packet's outer directory:

```sh
python3 review.py run python3 \
  generators/b9e736518d82/workspace/parametric/prototype.py \
  --seed 314159 \
  --out ../checks/parametric/turn-half-evidence.json \
  --examples-dir generators/b9e736518d82/workspace/parametric/examples
```

The command executes both exact Racket programs through the included bridge,
checks every output against the task-local Python mirror, verifies that each
training episode rules out the opposite parameter setting, and retains one query
whose two setting outputs differ.

`examples/episode-a.json` and `examples/episode-b.json` are public-shaped
challenges: demonstrations contain labels, while hidden parameter metadata,
Racket code, and query answers are absent. The source-bound evidence file records
which setting generated each public challenge.

## Limits

This is bounded authoring evidence for one deterministic seed per setting. It is
not a production parametric API, does not alter the selected generator or rule
hash, and does not establish training admission or universal identifiability.
