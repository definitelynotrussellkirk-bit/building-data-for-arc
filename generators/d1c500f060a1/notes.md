# Working notes: d1c500f060a1

Current source review repaired the documented unseen-code ambiguity and inactive controls. The ordinary generator now emits only the five transform codes explicitly defined by the canonical rule, validates exact call types and known axes, varies connected two-color motifs with a singleton accent, rejects two-color motifs without exactly one singleton, gives `palette_kind` and `texture` visible semantics, and supports exact 30×30 overrides. The canonical Racket program and all original labels are unchanged.

The native family keeps `pack_order=as_found` as the exact canonical default and adds `pack_order=accent_scan`. The alternate first applies each header transform, derives an accent key `(row, column, height, width)` from the transformed singleton, sorts pieces lexicographically by those keys, and only then packs them left-to-right. Three demos qualify the family; 2–6 demos are supported, inputs are matched across settings, and each episode has four distinct private queries including a substantive 30×30 case.

Protected authoring preflight and the source-bound wrong-intermediate witness passed. Remaining action is owner-side source review, native qualification, and exact-source acceptance; no training admission is claimed.
