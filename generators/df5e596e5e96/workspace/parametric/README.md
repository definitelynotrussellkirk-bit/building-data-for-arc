# `df5e596e5e96` relation-matrix ordering prototype

This opt-in prototype preserves the exact canonical Racket program for
`{"matrix_order":"input"}`.  The alternate setting
`{"matrix_order":"relation_signature"}` first computes the same canonical
pairwise relation matrix, then derives per-panel counts of exact, rotational,
and reflected relations from that matrix and uses those input-dependent
signatures to permute both output axes.

The hidden setting is fixed for an episode.  The adapter supports 2–6
demonstrations and 1–8 queries; qualification uses four distinct queries.
Inputs are shared across settings for a given seed so comparisons isolate the
rule change.  The sampler deliberately refutes five declared shortcut orders:
reverse input, total relation degree, row sum, rotation count, and panel color.
That is a finite rival audit, not a universal uniqueness proof.

From the packet's outer directory, replay the bounded source/Racket/public
probe with:

```sh
python3 review.py run \
  python3 generators/df5e596e5e96/workspace/parametric/evidence/current/build_evidence.py \
  --report generators/df5e596e5e96/workspace/parametric/evidence/current/probe.json \
  --public-out ../checks/parametric/public
python3 WORK/check_public_exports.py WORK/checks/parametric/public --queries 4 --demos 3
```

Run focused tests with:

```sh
python3 review.py run pytest -q \
  generators/df5e596e5e96/tests/test_generator_df5e596e5e96.py \
  generators/df5e596e5e96/tests/test_parametric_matrix_order.py
```

The grammar is a five-row strip of three to five width-five panels, so its
lawful size boundary is `5×17` through `5×29`; a `30×30` probe would be outside
the declared input grammar.  Prototype evidence is reviewer-reported and does
not itself approve, accept, or admit the family to training.
