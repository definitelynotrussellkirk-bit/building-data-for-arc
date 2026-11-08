# Aligned-state parametric prototype

This source-bound prototype varies one rule parameter while retaining the
canonical two adjacent four-column panels:

- `both_zero` (the exact canonical program): output `4` where both aligned
  panel cells are zero.
- `both_nonzero`: output `4` where both aligned panel cells are nonzero.

A hidden setting is fixed once per episode. Episodes contain 2–6
Racket-labelled demonstrations and exactly four private Racket-labelled
queries. Inputs are setting-neutral and explicitly cover all four aligned
occupancy states. The largest lawful source-shaped query is 30×8; widening it
to 30×30 would silently change the canonical 4+4 panel geometry.

`adapter.py` and `promotion.json` provide the bounded native qualification
contract. This directory proposes no approval or training admission.
