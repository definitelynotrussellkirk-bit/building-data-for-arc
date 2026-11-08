# Current decisions — 9aed2df94248

Canonical `generator.py` and the canonical Racket authority were retained unchanged: base original and two staged ordinary draws passed the native authoring preflight. Parametric `once` is byte-exact canonical; `twice` applies the input-inferred A→B transform twice to C, and `mirror_after` reflects the transformed C. All settings share the same input for matching seed/count; no setting/presentation metadata is visible in the grid.

**Adversarial repair:** An earlier prototype assigned predictable A→B transforms by sample index. Current code independently samples transform identity from the seed and scene, guarantees two distinct demonstration transform codes, and requires the first demo to distinguish all three transfer policies. The `flip-lr` source transform can make `twice` and `mirror_after` coincide on one individual pair; at least one other demonstration always separates them. Tested independently across sample counts 2/3/6, with a connected, asymmetric, substantive 30×30 image in each episode.

Owner action: inspect the three source-bound settings and witness; replay the current `qualification-v2` under the native owner gate, then decide exact-source acceptance. The helper preflight is *not* approval or training admission. Limits: no exhaustive proof of generalization, no complete distributional adversarial search.

Owner follow-up: the original twice-setting lesson at seed 0 admitted “copy C” on both demonstrations and disagreed on query 3 by 12 cells (protected Racket). Minimum lessons now include a quarter-turn and a different transform in privately randomized order. The rule programs are unchanged. Reproducer: `counterexamples/owner-copy-c-shortcut/witness.json`; repair evidence: `evidence/owner-copy-c-repair/`.
