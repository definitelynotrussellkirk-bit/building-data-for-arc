# Proposed extension-length component

This **unapproved prototype** keeps the production generator and canonical
`extension_length=1` Racket program unchanged.  A hidden, episode-fixed setting
chooses whether the ray paints one exterior cell (`1`, canonical) or two
consecutive exterior cells (`2`).  Inputs are setting-neutral, each retained
lesson has two demonstrations and four distinct queries, and labels plus rival
predictions are executed by the protected Racket runtime.

From the packet root:

```bash
python3 review.py run python3 \
  generators/b8e2a07c1b6c/workspace/parametric/prototype.py \
  --out ../checks/parametric/extension-length-v1 \
  --seeds 0 1 --demo-count 2 --query-count 4

python3 review.py run python3 -m pytest -p no:cacheprovider -q \
  generators/b8e2a07c1b6c/tests/test_parametric_extension_length.py
```

Files under `public/` contain only demonstrations and query inputs.  The root
evidence manifest is administrative; seeds, settings, programs, rival
predictions, and query answers are never written into a public challenge file.
`promotion.json` and `adapter.py` are a component contract only; they do not
promote or alter production authority.
