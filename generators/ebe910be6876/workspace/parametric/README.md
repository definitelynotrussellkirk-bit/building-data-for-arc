# Native parametric family for `ebe910be6876`

This directory contains a source-bound native adapter with one episode-fixed
parameter:

| Parameter | Values | Canonical default |
|---|---|---|
| `finish` | `expand_only`, `mark_largest_cluster` | `expand_only` |

`expand_only` is the selected canonical Racket program byte-for-byte. It doubles
the input canvas and expands each nonzero input marker into a clipped 4×4 tile
whose top-left corner is `(2r-2, 2c-2)`.

`mark_largest_cluster` adds a non-collapsing second stage:

1. **A — expansion:** execute the canonical expansion to create the doubled
   multicolor intermediate.
2. **Intermediate:** recompute all four-connected nonzero components created by
   contacts among the expanded tiles.
3. **B — selection:** choose the unique largest resulting component, using
   row-major first on an exact tie, and recolor the complete component to 9.

B cannot be chosen from the sparse input markers: the component contacts and
sizes exist only after A constructs the expanded canvas. The protected-Racket
causal witness compares the composed program with a wrong-intermediate program
that recolors the first input marker's tile; the final outputs differ.

## Episode contract

- independently selected 2–6 demonstrations and 1–4 queries;
- normal native qualification uses 3 demonstrations and 4 queries;
- four deterministic, distinct, prefix-stable query inputs;
- identical inputs for both settings;
- one query per public turn, with no setting, program, answer, total-count, or
  future-query leakage;
- minimum 12×16 output and substantive 28×30 and 30×30 outputs.

The constructive two-demonstration curriculum rejects the canonical/composed
confusion and four declared composed-rule shortcuts: first input marker,
smallest component, largest same-color component, and largest eight-connected
component. This is a finite executable audit, not a uniqueness proof.

## Important files

- `adapter.py` — native loader exposing `program` and `generate`.
- `promotion.json` — parameter, count, resource, and qualification contract.
- `prototype.py` — sampler, Python semantic mirrors, public projection, and
  finite rival definitions.
- `canonical.rkt` — exact selected canonical source.
- `largest_cluster.rkt` — sequential alternative.
- `verify.py` — reusable protected-Racket teaching/publication audit.
- `evidence/manifest.json` — current source-bound inventory.

## Retained verification

The current packet retains:

- 22 focused tests plus 35 subtests;
- 72 protected-Racket evaluations in the finite teaching audit;
- a 128-seed structural sweep covering 2,560 generated pairs;
- four native qualification jobs (two settings × seeds 0 and 17), with 40
  protected-Racket labels;
- 16 strict one-query public projections;
- an independently replayed protected-Racket causal witness.

The public writer precomputes and validates every visible payload and identifier,
rejects duplicate visible challenges, sorts the complete batch by public ID,
then physically writes files in that order through a staging directory.

This artifact is reviewer-ready, not owner-accepted. Exact-byte integration,
fresh owner qualification and acceptance replay, and any training admission
remain outside this return. `training_admitted` is false.
