# Expansion-side parametric prototype

This isolated prototype leaves the selected production `generate()` path,
canonical Racket authority, `RULE_HASH`, and approval identity unchanged. It adds
one episode-level rule parameter:

- `left` (original/default): after choosing the winning component, erase the
  color and fill the winner's bounding rectangle plus one column on its left.
- `right` (alternative): perform the same component selection, erasure, and
  rectangle fill, but add the adjacent column on the right.

The parameter is selected exactly once per episode. Inputs retain all four
selected scene profiles and are deterministically resampled only when a winner
lacks clear in-bounds columns on both sides or when expanded rectangles would
interfere. Three demonstrations and one query use the same setting. Every label
and rival prediction is produced by executing an exact, materialized Racket
program through the protected bridge. Public challenges omit the parameter,
program, seed, rival predictions, and query output.

From the packet root, create fresh evidence with:

```bash
python3 review.py run python3 \
  generators/ad5a6c1521b3/workspace/parametric/prototype.py \
  --out ../checks/parametric/expansion-side-v1
```

Run the focused regressions with:

```bash
python3 review.py run python3 -m pytest -q \
  generators/ad5a6c1521b3/tests/test_call_contract.py \
  generators/ad5a6c1521b3/tests/test_parametric_expansion_side.py
```

The evidence directory contains both complete private episodes, matching public
challenges, both exact Racket programs, a direct differing witness, a report,
and a SHA-256 manifest. This is proposed prototype evidence, not production or
training approval.
