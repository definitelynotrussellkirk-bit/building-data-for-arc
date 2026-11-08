# Native parametric family — cardinal interior-count relay

This promoted task-local family exposes one episode parameter, `mode`:

- `canonical` materializes the selected canonical Racket program byte-for-byte.
- `interior_count_relay` first runs that exact local-neighbour transform, counts
  the produced colour-2 interior cells to the left of a colour-9 separator, and
  uses the count (1, 2, or 3) to select one of three ordered colour-3 payloads
  for recolouring to 8.

Inputs are identical across settings.  Demonstration and query counts are
independent (`2..6` and `1..4`), the four private queries are prefix-stable, and
the fourth query is 30×30.  The retained wrong-intermediate program counts the
single large raw colour-5 component instead; it therefore selects payload 1 and
changes the qualified 30×30 result when the true interior count is 3.

`verify.py` performs a finite named-rival audit plus protected-Racket parity.
`promotion.json` is the native adapter contract.  Evidence and exact source
bindings live under `evidence/`; qualification and causal-witness receipts live
under the packet's `WORK/checks/70205357c60a/` directory.

The earlier threshold prototype remains in `prototype.py` as historical work,
but it is not the promoted family because it did not establish the required
A→intermediate→B dependency.
