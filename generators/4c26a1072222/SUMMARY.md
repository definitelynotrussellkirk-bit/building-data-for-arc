# 4c26a1072222

Three or four independent two-row A/B/C bands. In each band the selected
authority searches all eight 2x2 D4 transforms, keeps functional A→B color maps,
maximizes exact color matches, breaks ties by transform index, and applies the
selected transform and map to C. The generator constructs against that actual
selector, covers every D4 branch, emits canonical-size/palette profiles, and no
longer lets the two/three-color A count identify the transpose family.

Kind: `per_puzzle`. Reviewed version: `2.1.0`.
Rule hash: `a86a18b84011`.
Final reviewed generator SHA-256:
`5816599d9ed224a6d95f56745292449c464b6e708cac9373db58e8671b8aa22d`.

A task-local forward/inverse application-direction prototype is retained under
`workspace/parametric/`. It has four demonstrations and four distinct queries,
protected-Racket labels for both settings, and separate public/private exports.
It is proposed evidence only: canonical behavior, catalog approval, and
production wiring remain unchanged and catalog-owned.
