# Working notes: da16b5bf7632

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 native parametric review

- Preserved `generator.py` byte-for-byte at SHA-256 `7d26a4654f01cb85c8a6fc64edf1baad2abd80106bfa40e501218e039541e3c1`.
- Added episode-fixed `sort_direction`: canonical `most_holes_first` and meaningful `fewest_holes_first`. Both derive exact enclosed-hole counts before packing the ordered crops.
- Native qualification is at `checks/da16b5bf7632/qualification/qualification.json`; the protected counterfactual witness is at `checks/da16b5bf7632/causal/witness.json`.
- Bounded evidence covers 2–6 demonstrations, four sequential queries, a structural 30x30 query, ten declared rivals, and a 256-seed count-boundary census. This is finite evidence, not universal uniqueness.
- Current state is reviewer-ready only. Exact-source owner acceptance remains pending and no training admission is claimed.
