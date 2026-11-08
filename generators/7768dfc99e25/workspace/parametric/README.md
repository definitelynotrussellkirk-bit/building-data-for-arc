# Border-object target-color prototype

**Status: proposed, not accepted.** The production generator and canonical
Racket authority remain separate. This prototype preserves the original
4-connected object selection, border predicate, and bounding-box crop while
making the selected object color episode-fixed. `target_color=2` is the exact
canonical program; `target_color=3` applies the same rule to color 3.

Inputs are identical across settings for a given seed and request. Every scene
contains exactly one border-touching component and at least one interior
component for each candidate color, plus non-target border markers. Labels,
not input distributions, identify the setting. Requests support 2–6
demonstrations and 1–8 queries independently. The first four query profiles
are 12×14, 18×20, 24×24, and a substantive 30×30 scene with occupied cells on
all four outer boundaries. Settings, seed, Racket source, certificates, and
query answers are controller-private; the public projection exposes only
training pairs and masked query inputs.

From the outer packet directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/7768dfc99e25/tests/test_parametric_target_color.py
```

The focused test executes every retained label for both settings through the
bundled protected Racket runtime. Finite identification is only against the
two declared settings; it is not unrestricted program uniqueness, variant
acceptance, or training admission.
