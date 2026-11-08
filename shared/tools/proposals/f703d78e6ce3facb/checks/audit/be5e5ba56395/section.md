## be5e5ba56395

**Independently reproduced the existing unresolved validator defect on unchanged source.** `self_check` accepts a grid containing one valid filled rectangle plus a malformed component, violating the stated invariant that every colored component is a filled axis-aligned rectangle. This is a documented-domain false acceptance; it is not a demonstrated in-domain wrong label or complete-lesson ambiguity.

Audited generator: v1.1.1, SHA-256 `1f7dc969ae2a45b93d933594b50e8185cfc01b7c4cd76f40a8626475c307a6e3`. Selected canonical and executed rule hash: `8f9e53b42241`. The current review index already retains this concern against the same source. This replay provides independent current execution evidence and a smaller witness; no audit disposition was changed.

The 5×7 hand-authored witness contains one solid color-1 3×3 rectangle and one color-2 L with a 3×3 bounding box:

```json
[[1,1,1,0,2,2,2],
 [1,1,1,0,2,0,0],
 [1,1,1,0,2,0,0],
 [0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0]]
```

`Catalog.apply(..., reference="canonical", check_generator_domain=True)` reports `generator_domain={"status":"valid","errors":[]}` for this input. The Racket output clears the first rectangle's center and paints the L's full bounding-box border, adding color 2 at zero-based coordinates `(1,6)`, `(2,5)`, and `(2,6)`. A pure diagnostic comparison that outlines already-solid components and preserves a malformed component differs at exactly these three cells. This disagreement is outside the written solid-rectangle domain and is not evidence of a competing rule within that domain.

Matched controls isolate the validator's existential check: replacing the L with a filled 3×3 rectangle is accepted, while removing the good rectangle and leaving only the L is rejected with `no solid filled rectangle ≥3×3 found`. The source groups nonzero cells by color and records success when **any** color fills a qualifying bounding box; it never rejects another color's malformed component. The appropriate repair is to validate each nonbackground connected component against the declared filled-rectangle and size requirements, with a regression containing one good component and one bad component.

The focused run used one `Catalog.apply` batch of nine inputs: the three hand-authored fixtures, one native default draw (`seed=0`, `sample_index=0`, `difficulty=None`, no overrides), and all five canonical pairs. The native draw was accepted and contained only solid rectangles; all five executed canonical outputs matched their saved labels. The malformed witness was not produced by the sampler. One native draw supplies a control, not a frequency estimate or a broad sampling claim.

Evidence and portable reproduction: `checks/audit/be5e5ba56395/` contains `reproducer.py`, exact outer command/cwd/environment/exit-code records in `commands.jsonl`, real output in `run.log`, and `replay/report.json`, `replay/racket.json`, `replay/minimal_witness.json`, and source snapshots under `replay/source/`. The reproduction exited 0 with every focused observation confirmed; the source hash guard prevents silently attributing the finding to changed bytes. No target generator, tests, rule, approval, or audit status was edited.
