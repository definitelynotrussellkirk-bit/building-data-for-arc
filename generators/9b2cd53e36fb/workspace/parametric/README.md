# Native parametric family: `9b2cd53e36fb`

This workspace preserves the accepted canonical rule as the default
`selection=all_holes` setting, byte-for-byte.  The alternate
`selection=largest_axis` setting introduces one structural decision:

1. Find the unique largest edge-touching zero component and derive its mirror
   axis (`rows` for top/bottom, `cols` for left/right, with canonical
   top/bottom priority).
2. Mirror and sweep every edge hole whose own axis matches that derived axis.

Inputs are sampled independently of the setting.  Every case includes edge
holes on both axes, a unique largest control hole, and at least one additional
hole on the selected axis, so the alternate is not reducible to "transform
only the largest hole."  Demonstration profiles alternate control axes and
all episodes contain exactly four queries, including a 30x30 stress case.

`prototype.py` contains a Python oracle and structural diagnostics only.
Qualification must execute both exact Racket sources with the packet's
protected runtime; Python output is not acceptance evidence.

## Reproduction

From the packet's outer directory, run the focused source checks:

```bash
python3 review.py run python3 -m pytest \
  generators/9b2cd53e36fb/tests/test_parametric_largest_axis.py -q
```

After regenerating task-local evidence, inventory the current bytes:

```bash
python3 review.py run python3 -m arcpuzzles parametric manifest 9b2cd53e36fb \
  --evidence generators/9b2cd53e36fb/workspace/parametric/evidence/current \
  --include generators/9b2cd53e36fb/tests/test_parametric_largest_axis.py \
  --reported-checks 'Focused pytest plus protected-Racket finite-rival audit; see evidence/current.'
```

From `WORK/`, qualify all declared settings on two fresh seeds:

```bash
python3 run_with_racket.py python3 -m arcpuzzles parametric qualify \
  9b2cd53e36fb --out ../checks/9b2cd53e36fb/qualification --summary
```
