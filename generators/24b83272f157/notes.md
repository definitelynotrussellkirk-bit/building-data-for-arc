# Working notes: 24b83272f157

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 native parametric review

- Preserved `generator.py` byte-for-byte at SHA-256 `356af3ba309ece3c2b4b4250b8a2ba5ac421622504758944b99aee8a1117c2a0`.
- Added episode-fixed `finish`: canonical `degree_palette` and meaningful `highlight_max_degree`. The alternative builds the object contact graph, derives every graph degree, and recolors the complete maximum-degree class.
- A 256-seed minimum-demonstration census found nine seeds where highest input color accidentally fit both visible examples. The sampler now constructively assigns the highest source color to a non-maximum-degree object; the retained regression and post-repair census have zero survivors.
- Native qualification is at `checks/24b83272f157/qualification/qualification.json`; the protected counterfactual witness is at `checks/24b83272f157/causal/witness.json`.
- Bounded evidence covers 2–6 demonstrations, four sequential queries, a structural 30x30 query, ten declared rivals, and 1,024 episodes. This is finite evidence, not universal uniqueness.
- Current state is reviewer-ready only. Exact-source owner acceptance remains pending and no training admission is claimed.
