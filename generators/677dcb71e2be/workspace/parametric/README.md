# Parametric family: `677dcb71e2be`

`order_mode=size_desc` preserves the canonical Racket program byte-for-byte.
`order_mode=border_shift` adds a sequential dependency:

1. find the unique nonzero component whose bounding box touches the input border;
2. compute its occupied-cell count modulo the number of components;
3. rotate the canonical size-descending component sequence left by that offset,
   then emit the same colored bars and zero separators.

`adapter.py` deterministically materializes matched inputs for both settings,
2–6 demonstrations, and a stable four-query bank. At the two-demo minimum,
the demonstrations hold dimensions, border side, component count, and
non-selector sizes fixed while the selector changes the offset from 1 to 2.
The fourth query is a substantive 30×30 scene. `promotion.json` is the native
adapter contract.

Run the bounded source-local adversarial audit through the packet launcher:

```sh
python3 review.py run python3 generators/677dcb71e2be/workspace/parametric/probe.py
```

The probe attacks fixed offsets, selector position/size/rank proxies,
bounding-box area, top-left and extrema shortcuts, the two retained ordinary
curriculum shortcuts, request/type boundaries, matched-setting inputs, query
prefix stability, and same-dimension crossed causal controls. Its evidence is
finite and does not replace protected-Racket qualification or owner acceptance.
