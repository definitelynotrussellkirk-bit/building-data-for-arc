# Forward/reverse marker-scan family

This native parametric proposal leaves production `generator.py` and its
canonical authority unchanged. The episode-fixed private parameter is:

- `marker_scan=forward` — the exact selected canonical Racket program;
- `marker_scan=reverse` — scan the same non-key, non-0/8 body cells in reading
  order but retain the last eligible color instead of the first.

Both settings preserve the original reasoning. **A** scans the lawful body and
produces the input-dependent selected marker color. **B** can then choose the
matching spatial subset and recolor it by the 2x2 key's TL/TR/BL/BR colors using
the full body bounding box. Choosing the wrong intermediate color changes which
objects are transformed; it is not a post-hoc palette remap.

The matched input sampler supports 2–6 demonstrations and 1–4 queries. The
ordinary and qualification request is 3 demonstrations / 4 queries. Input
streams depend on seed, split, and pair index, not on the hidden setting or the
requested totals; increasing either count preserves earlier pairs. Every scene
contains distinct forward and reverse endpoint colors, both spanning all four
quadrants, plus genuine nonselected distractors. The first two demonstrations
reverse scan order's correlations with numeric order, frequency, and key
membership, and contain exact-midpoint witnesses where geometrically possible.

The four query sizes are 9×11, 16×19, 24×27, and 30×30. The exact 30×30 query
contains at least 108 distributed body-color cells across three colors, including
body-boundary contact; it is not a padded small task. Exact midpoint cells do not
exist in a 28×28 body, so that boundary convention is taught on other profiles.

`audit.py` is a reusable bounded tool. Before qualification it checks matched
inputs and finite rivals over seeds and demo-count boundaries. After native
qualification it reuses the protected-Racket-verified episodes, checks the same
rivals against those labels, and writes hash-named public challenges that expose
all demonstrations plus four input-only queries. Its no-finding result is finite,
not a universal uniqueness proof.

From the packet outer directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/0a9e3d364bb3/tests/test_parametric_marker_scan.py
python3 review.py run python3 \
  generators/0a9e3d364bb3/workspace/parametric/audit.py \
  --out generators/0a9e3d364bb3/workspace/parametric/evidence/current/audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify 0a9e3d364bb3 \
  --out ../checks/0a9e3d364bb3/qualification --summary
```

Reviewer qualification is not owner acceptance or training admission. The owner
must integrate these exact bytes, replay native qualification/causal evidence,
and explicitly accept the family before it is usable.
