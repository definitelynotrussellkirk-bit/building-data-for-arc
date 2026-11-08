# Proposed parametric extension: period factor

This prototype leaves the selected production generator and canonical Racket
rule unchanged. It varies one meaningful rule parameter:

- `period_factor`: allowed values `2` and `3`; canonical/default value `2`.
- Marker selection remains color-major then row-major.
- Row-versus-column choice, the blank prefix, and the two phase colors remain
  unchanged.
- Only the repeating period changes from `2 × active separation` to
  `period_factor × active separation`.
- The factor is chosen once per episode and reused for all three demonstrations
  and the query.

`prototype.py` builds lawful row and column scenes long enough that both factor
settings produce different answers. The probe executes the exact Racket source
for each setting through the packet's protected bridge, compares an independent
Python mirror, overwrites retained labels with the Racket outputs, and verifies
that the alternative factor changes every demonstration and query. Public
challenge JSON omits the hidden factor and query answer.

From the outer extracted packet, run:

```sh
python3 review.py run python3 generators/c739fcbc6cbd/workspace/parametric/prototype.py \
  --out ../checks/parametric/period-factor
```

The evidence is finite and source-bound to the retained seeds. It does not
approve the variant, prove uniqueness against arbitrary rival rules, or alter
the selected canonical authority hash.
