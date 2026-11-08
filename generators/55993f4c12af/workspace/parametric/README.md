# Proposed Boolean-operator variant for 55993f4c12af

**Status: proposed task-local prototype, unapproved.** The episode-level parameter is
`operator ∈ {or, xor, and}`. The canonical/default `or` setting returns the canonical
Racket source byte-for-byte. The alternatives replace only the unique aligned-cell
Boolean condition; panel alignment, foreground roles, yellow output, dimensions, and
all other reasoning steps remain unchanged.

Every prototype input comes from the selected production generator and contains all
four aligned occupancy states: both empty (`00`), top only (`10`), bottom only (`01`),
and overlap (`11`). Consequently OR, XOR, and AND produce pairwise different outputs
on every retained demonstration. The operator is selected once from the episode seed
and reused for three demonstrations and one query.

All retained labels, rival predictions, and canonical replay outputs are executed by
the bundled Racket runtime. Public challenges contain labeled demonstrations and a
masked query input only. Private evidence retains the seed, selected parameter, query
answer, exact Racket source, source hashes, and cross-setting witness.

From the outer packet directory:

```bash
python3 review.py run python3 \
  generators/55993f4c12af/workspace/parametric/prototype.py \
  --seeds 1 0 5 \
  --out ../checks/parametric/boolean-operator-v1

python3 review.py run python3 -m pytest -q \
  generators/55993f4c12af/tests/test_parametric_variant.py
```

Seeds `1`, `0`, and `5` cover OR, XOR, and AND respectively under the pinned Python
RNG. This bounded three-setting study is not production approval, training admission,
or proof of uniqueness against undeclared interpretations.
