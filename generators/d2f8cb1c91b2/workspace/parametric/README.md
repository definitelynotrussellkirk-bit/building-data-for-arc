# D4 merge conflict-policy prototype

**Status: proposed, not accepted.** The production generator and canonical
Racket authority remain separate. Every setting infers the demonstrated D4
transform, applies it to panel X, and merges with panel Y. The episode-fixed
parameter controls only unequal nonzero overlaps: `marker` emits 9 and is the
exact canonical program, `keep_x` preserves transformed X, and `keep_y`
preserves Y.

Inputs are identical across settings for a given seed and request. The source
sampler guarantees x-only, y-only, matching, and unequal-overlap branches in
every item, so labels—not input statistics—identify the conflict policy.
Requests support 2–6 demonstrations and 1–8 queries independently. The
canonical grammar is exactly four 3×3 panels plus three separator columns, so
all lawful inputs are 3×15; a 30×30 stress case would change the task rather
than extend it. Settings, seed, Racket source, certificates, and query answers
are controller-private; the public projection exposes only demonstrations and
masked query inputs.

From the outer packet directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/d2f8cb1c91b2/tests/test_parametric_conflict_mode.py
```

The focused test executes every retained label for all three settings through
the bundled protected Racket runtime. Finite identification is only against
the declared policies; it is not unrestricted program uniqueness, variant
acceptance, or training admission.
