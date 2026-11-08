# Size-palette marker-echo family

The canonical `echo_mode=none` setting is byte-for-byte the selected ARC rule:
measure each orange body component by area, use that 1-based area to select the
left-to-right legend color, and recolor the component in place.

`echo_mode=matching_marker` preserves that first stage and adds a causal second
stage.  The selected legend color identifies a unique singleton body marker; the
normalized orange shape is echoed at that marker in the selected color.  Changing
the area-derived color changes both the source recoloring and the destination
marker, so the second operation cannot be chosen before the first produces its
input-dependent intermediate.

Every input contains all areas `1..N`, randomized source and marker order, varied
connected shapes, crossed positions, boundary contacts, and (when space permits)
a multi-cell decoy.  Inputs are identical across settings.  The adapter supports
2–6 demonstrations and 1–4 query prefixes; native authoring qualification stores
four distinct queries, including a substantive boundary-spanning 30x30 scene.
Public projection reveals one unlabeled query at a time and keeps settings,
programs, answers, source order, and future queries private.

## Retained verification tool

`adversarial_probe.py` exercises the minimum lesson over fresh seeds, relevant
proxy/rank/position bypasses, strict malformed requests, crossed controls, base
row-1 morphology, all supported demo extremes, and protected-Racket execution.
It writes one compact `evidence/current/report.json`, which is source-bound by the
manifest and final preflight.

Focused checks from the packet root:

```bash
python3 review.py run python3 -m pytest -q   generators/01f4294de005/tests/test_generator_01f4294de005.py   generators/01f4294de005/tests/test_parametric.py
```

The returned evidence is authoring evidence, not owner acceptance or training
admission.  Finite rival and seed sweeps do not establish universal uniqueness.
