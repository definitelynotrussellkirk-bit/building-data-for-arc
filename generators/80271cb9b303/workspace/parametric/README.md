# Native periodic-row continuation family

The prototype preserves task `80271cb9b303`'s exact canonical repeating program
and adds reverse-cycle and reflected-tail continuation. `adapter.py` loads the
adjacent `native_family.py` by exact path. `sampler.py` supplies inputs only;
Python outputs are claims independently executed through protected Racket by
the audit and native qualification.

## Semantics

For each row independently, find its rightmost nonzero column `R`. All-zero rows
remain zero. Infer the smallest positive period `p` satisfying
`row[c] == row[c % p]` for every observed column `0 <= c <= R`. The motif is the
first `p` cells and the observed phase is `q = R % p`.

Zeros inside this observed prefix are data. Neither divisibility of `R+1` by
`p` nor two complete observed copies is required. In particular, a single
nonzero at column zero has period one. Rows may have different periods.

All settings preserve the observed prefix. For a tail column `c > R`, let
`d = c - R` and select a motif index as follows:

| `continuation` | Tail motif index |
| --- | --- |
| `repeat` | `(q + d) % p`; exact canonical source |
| `reverse_cycle` | `(q - d) % p` |
| `bounce` | With `L = 2*(p-1)` and `t = (q+d) % L`, use `min(t, L-t)` |

Period one is explicitly constant, avoiding a zero-length bounce cycle. Bounce
does not duplicate either endpoint: for a motif of length four the traversed
indices are `0,1,2,3,2,1,0,1,...`. It starts from the actual observed phase,
initially moving forward. Reverse-cycle moves backward from that phase.
All three policies coincide for periods one and two; asymmetric motifs with
period at least three supply the distinguishing teaching evidence.

The required dependency is **infer motif/period/phase → choose tail positions**.
Changing the inferred period changes wrap points and reflection endpoints.
This is not a fixed flip of the completed canonical output. A native causal
witness compares the actual program with one that treats the entire observed
prefix as the motif, keeping the input and traversal code fixed.

## Domain and construction

The claim API accepts every rectangular list of lists of literal integers 0–9,
with both sides from 1 through 30. Booleans, floats, ragged rows and tuples are
rejected. Blank grids, period-one/two rows, observations without a repeat, and
rows already reaching the right edge are lawful. Outputs retain input shape.
This naturally extends the narrower production sampler's dimensions and shared
row-period restriction; the production generator and authority are unchanged.

The native sampler supports 3–6 demonstrations and 1–4 queries independently.
It constructs all six plus four input grids before slicing prefixes, using
local SHA-derived RNGs for each seed/split/slot/retry and a 64-attempt duplicate
bound. Inputs match across settings. Palette permutations and vertical
reflections preserve the intended horizontal observations.

Three constructive demonstrations teach mixed periods, leading and trailing
motif zeros, partial/aligned cutoffs, asymmetric motifs and tails extending
beyond a reflection turn. Their period profiles include 1 through 8. Queries
cover a 1×9 row, canonical-like 5×15 patterns, mixed larger periods on 16×26,
and dense 30×30 continuation. The latter has 28 active rows and extends visible
content through column 23, with blank suffixes awaiting continuation. Seeds
0/17 contain 523/515 occupied input cells; this is measured finite coverage.

## Reusable audit and export

`audit.py` checks the exact default and all four canonical labels, executes
intended labels and finite rival programs through protected Racket, and screens
only the first three demonstrations. Rivals include incorrect periods,
divisibility restrictions, trailing-blank inference, leading-zero shifts,
shared row periods/delimiters, phase resets and duplicated bounce endpoints.
Every screened demonstration is executed even after an earlier mismatch;
exceptions and malformed outputs fail the audit instead of counting as evidence.
Queries are examined for any surviving rival.

Public turns contain only visible demonstration input/output pairs and one
query input. Programs, settings, future queries, answers and count hints remain
private. The strict exporter/verifier checks exact serialized projections,
content-derived IDs, sorted records, private associations, hashes and missing
or orphaned files. Negative tests cover these boundaries. Everything is local
to this task and has no dependency on a previous review checkout.

From the outer packet directory:

```sh
WORK/.venv/bin/python review.py run python3 -B -m pytest -q \
  generators/80271cb9b303/tests/test_native_adapter.py \
  generators/80271cb9b303/tests/test_native_audit.py

WORK/.venv/bin/python review.py run python3 -B \
  generators/80271cb9b303/workspace/parametric/audit.py \
  --out ../checks/80271cb9b303/audit-new --seed 0 --seed 17
```

Choose a fresh evidence path after source changes. The return's `RESULTS.json`
identifies the current native inventory, qualification/execution and causal
witness. Refresh bound inventories and requalify after changing source or
resources. Finite regression/rival checks do not prove universal uniqueness;
reviewer readiness does not grant owner acceptance or training admission.
