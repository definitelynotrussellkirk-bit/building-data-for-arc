# Working notes: a23328d45092

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 base repair and native parametric build (review-b0545ca002f965c6)

- Repaired the ordinary teaching schedule so each consecutive three-example window explicitly demonstrates `TL>TR`, `TR>BL`, and `BL>BR` for the canonical zero-transparent overlay.
- A wider audit exposed a rare tiny-grid defect: the nonempty-quadrant repair could repaint the scheduled conflict coordinate and mask `BL>BR`. Added a regression for seed 110 / easy / indices 7–9 and moved repairs away from the protected coordinate.
- Preserved the exact canonical Racket default and added `postprocess=highlight_visible_majority`: build the canonical overlay, select the most frequent visible nonzero color (lowest color wins ties), then recolor it to 9.
- Added an executable wrong-order rule that selects from raw source-cell counts before occlusion; retained generated cases make that source majority disagree with the visible majority.
- Added strict controls, deterministic 2–6 demonstration and 1–4 query generation, four distinct private queries including a substantive 30x30 case, sequential public projection, reusable native/base audits, protected-Racket qualification evidence, and a source-bound causal witness.
- Reviewer status is ready only. Owner native qualification/acceptance and training admission remain separate and were not performed here.
