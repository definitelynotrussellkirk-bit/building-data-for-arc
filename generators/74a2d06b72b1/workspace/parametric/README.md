# Parametric nested-frame family

`frame_order=outer_first` is the exact canonical rule. It counts color-2
markers from the largest frame inward, then fills the selected ring.
`frame_order=inner_first` counts the same markers from the smallest frame
outward and applies the same ring construction. In both settings the selected
frame is an input-dependent intermediate consumed by the fill step.

The deterministic sampler supports 2–6 demonstrations and 1–4 queries. Inputs
are matched across settings, vary frame count/geometry and marker count, and the
four-query bank includes a substantive 30×30 five-frame case. The first two
teaching profiles use different marker counts, so fixed outermost/innermost
shortcuts cannot fit the complete two-example lesson.

From `WORK/repo`, run the focused checks through the packet runtime:

```sh
python3 ../run_with_racket.py python3 -m pytest -q --import-mode=importlib \
  generators/74a2d06b72b1/tests/test_parametric_frame_order.py
```

The default program is preserved byte-for-byte. This prototype and its evidence
do not approve the repaired base, accept the family, or admit generated data.
