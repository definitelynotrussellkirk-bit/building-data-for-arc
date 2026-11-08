# Workspace for f705b8f51e62

The selected implementation is `../generator.py`. Workspace files are reviewer tools and are never selected automatically.

## `reference_probe.py`

This is an implementation-independent component oracle used by the task tests. It deliberately does not import private helpers from the generator. It provides:

- portable canonical-pair loading through `reviewer_support`;
- monochrome 4-connected component extraction and normalization;
- an independent intended-output function;
- the canonical-fitting `largest_component_rival`;
- observable signatures and pair construction for future regression probes.

A portable test can load either the selected generator or an alternate source with:

```python
from reference_probe import load_generator
module = load_generator()                 # selected generator
module = load_generator('/path/to/draft.py')
```

The final large source-bound lesson evidence is in `checks/lesson-census-final.json`. Re-run it after any schedule, rival, or lesson-assembly change:

```sh
python3 run_with_racket.py python3 -m arcpuzzles lesson-census f705b8f51e62 \
  --per-band 100 --rotate-query --timeout 1800 \
  --out ../checks/lesson-census-next.json
```
