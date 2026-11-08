# Waypoint history prototype

This proposed family is inspired by public-evaluation task `5545f144`. It is a
semantic variant, with no claim to reproduce that original task or its measured
difficulty. The production generator remains unreviewed with zero mix weight.
Its source, canonical authority and three-demo/one-query API are unchanged.
The promotion contract is a future integration entry point; the unapproved base
blocks qualification and acceptance. No variants are approved or training-admitted.

An episode fixes one setting:

| `mode` | Rule |
|---|---|
| `finish` | Execute the exact existing canonical Racket program: follow every remaining aligned waypoint and return the clean final cursor. |
| `history` | Count the waypoints consumed between the earlier and final panels; advance the final cursor by that many hops, retaining the remaining waypoints. |

The two first demonstrations share their entire final panel. One earlier panel
shows one consumed hop and the other shows two. Their history outputs differ,
so a deterministic function of the final panel alone cannot fit both examples.
Following each route also requires using the previous landing position to find
the next aligned waypoint. This establishes dependence on earlier information;
it does not establish universal identifiability or a circuit-complexity bound.

Three demonstrations distinguish the two settings and nine declared shortcuts.
Only demonstration labels enter this inference. The finite certificate predicts
query outputs from query inputs; it never receives the supplied query labels.
The Racket exporter independently labels both settings on the demonstrations
and checks the selected setting on every query.

From a prepared checkout, with NumPy, Pillow, pytest and Racket available:

```bash
export PYTHONPATH=src:shared/runtime
python3 generators/generic_waypoint_route_gen2/workspace/parametric/exports.py \
  export --out var/datasets/waypoint-history --seed 17 --count 2 \
  --mode cycle --demos 3 --queries 4
python3 generators/generic_waypoint_route_gen2/workspace/parametric/exports.py \
  verify var/datasets/waypoint-history
python3 -m pytest -q \
  generators/generic_waypoint_route_gen2/tests/test_history_prototype.py
```

Set `RACKET_PATH` to the executable unpacked from a review packet when Racket is
not installed. The bridge requires protected Racket execution from this checkout;
it rejects cached runtime modules imported from another checkout. The prototype
does not import either production waypoint sampler or borrow a sibling runtime.

Demonstrations and queries are independently configurable: 3–16 and 1–32,
respectively. Defaults are three demonstrations and four distinct queries.
Seeds are exact integers in 0–2^63−1. Settings use identical inputs for the same
seed/counts. The sampler has a local, domain-separated RNG. It constructs spaced
zigzag routes with distinct row and column choices, varied colors and directions.
The four default query shapes are 20×25, 24×27, 28×29 and 30×29. The latter uses
the larger geometry for route placement, rather than padding a small scene.

The admitted grammar has exactly two equal panels and one full-height separator,
a dominant background, one two-color domino cursor per panel, and separated
singleton waypoints of the head color. Every hop has one aligned successor.
The earlier state must lead to the final state after one or two hops, and that
final state must retain at least three waypoints. Other grammars fail explicitly.
The Racket rules are authorities over this grammar, not arbitrary-grid validators.

Give a model only files under `public/`. Each public filename hashes its exact
visible challenge bytes. Settings, seeds, programs, labels and certificates live
under `private/`; the root manifest is controller-only. Existing outputs and
duplicate public payloads are rejected. Saved replay checks the exact file
inventory, lineage, source/program hashes, seed reproduction, integer grid types,
public projection, certificates and protected Racket labels. Replay requires the
same recorded source snapshot; it does not authenticate a hostile rewritten
bundle. `evidence/manifest.json` indexes the retained bounded checks and examples.
