# Working notes: c130e51c4310

## 2026-10-24 parametric prototype

The canonical sampler was already strong and remained unchanged. The useful extension was a separate rule-changing family rather than another canonical sampling axis: `edge_shift` rotates the set of full cue-bounding-box edges clockwise by 0, 1, 2, or 3 frame sides. Setting 0 returns the selected canonical Racket program byte-for-byte; the all-four-edge fill case is rotation invariant.

The prototype lives under `workspace/parametric/` with a thin adjacent-path adapter and `promotion.json`. It supports 2–6 demonstrations and 1–4 queries on domain-separated RNG streams, so changing demonstration count does not change query prefixes. The retained four-query schedule uses 14×17, 18×22, 24×27, and a genuine 30×30 scene rather than inert padding. Sequential projections reveal one query at a time and omit the setting, seed, program, answers, future inputs, index, and total count.

Protected Racket generated eight retained episodes (four settings × seeds 0 and 17), executed 24 demonstrations against all four programs (96 rival executions), required one surviving setting, and executed 32 selected-rule queries. The finite adversarial sweep then checked 240 generated episodes across all supported demo/query counts and seeds 0, 17, and 999; it also checked matched inputs across settings, query-stream prefixes, public/private separation, and duplicate-publication refusal. Current prototype source SHA-256 is `c9f8517ca9cc99cc9a64259fd2d75d0e19bd311529ef385296c90562d6d7f863`; retained export-manifest SHA-256 is `bacb10891b1d5fc75201bbf4f88bb5935871993b7f73c0e1b0869f29c7eb8736`.

A final publication-boundary regression found that equal public challenges with different private dictionaries could fall into Python tuple comparison and raise an incidental `TypeError`. Sorting now uses only public identity and bytes, so the duplicate is rejected deterministically with `ValueError` before the output root is created. The README replay command was also changed to require a fresh output path; exact replay reproduced all eight public IDs and `public.jsonl` bytes.

The existing canonical test had two stale assumptions: a machine-specific canonical-data path and byte equality between archival source representations that are already textually different. The test now resolves data portably and binds the selected canonical program by rule hash/behavior instead. No shared authority file was edited; the archival representations remain divergent and should be reconciled separately only if exact textual synchronization becomes a requirement.

**Status and next action.** This is proposed authoring evidence, not qualification, variant acceptance, or training admission. The certificate distinguishes only the four declared programs; an undeclared shortcut may still survive. The next useful action is an independent promotion worker replay using `promotion.json`, followed by explicit owner acceptance if its fresh protected-Racket evidence is satisfactory.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
