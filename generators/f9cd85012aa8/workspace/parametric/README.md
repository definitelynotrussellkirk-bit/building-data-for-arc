# f9cd85012aa8 native parametric family

This task-local adapter exposes two matched-input settings:

- `target_mode=canonical_target`: the exact selected canonical rule, filling the sole color-6 object's bounding box with 6.
- `target_mode=anchor_size_relay`: count the color-6 anchor cells, use `(size - 3) mod N` to select one of the `N` row-major non-6 objects, and fill that object's bounding box with its own color.

The sampler supports 2–6 demonstrations and 1–4 queries. Query four is a 30×30 boundary-spread stress case. `audit.py` checks a finite declared rival set and protected-Racket labels; it does not prove universal identifiability or training benefit.
