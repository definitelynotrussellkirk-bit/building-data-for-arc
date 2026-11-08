# Parametric prototype evidence

`period-factor/` is the retained output of the packet-isolated command:

```text
python3 review.py run python3 generators/c739fcbc6cbd/workspace/parametric/prototype.py \
  --out ../checks/parametric/period-factor
```

The evidence covers both allowed episode-wide settings (`period_factor=2` and
`period_factor=3`), four pairs per setting (three demonstrations and one query),
Racket/Python equality for every label, and an explicit disagreement with the
other setting for every pair. Public challenge JSON files omit both the hidden
parameter and the query answer.
