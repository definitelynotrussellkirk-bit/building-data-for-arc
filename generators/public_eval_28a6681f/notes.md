# 28a6681f — liquid redistribution (authoring)

Design: blue (1) is conserved liquid; other nonzero cells are fixed solid.
Settle lower droplets first. A droplet descends through the nearest opening below
its contiguous horizontal fluid/air span; equal distances prefer left. Each move
strictly increases its row, so the process terminates. The four supplied labelled
pairs determine the liquid/solid roles; unobserved ties are an explicit extension.

Native parameter `mode=settle|largest_pool`: the alternate first settles all liquid,
then keeps the largest four-connected blue pool, with row-major ties. It must not
choose the original largest blue component before settling.

Plan: (1) independent original/hand-case tests, canonical and Python claims;
(2) matched-input terrain sampler, short finite-rival teaching lessons, adapter;
(3) Racket/preflight, bounded audit, private one-turn projections, causal ablation;
(4) source replay and return. Original labels are test-only authoring data.
Owner registration, source review, native qualification and acceptance remain pending.

## Current implementation and limits

The canonical implementation matches all three supplied train labels and the
provided official test label. These are authoring gold, not a blind benchmark.
Ties among nearest downhill openings prefer left; original labels do not uniquely
determine all physics on novel terrains. The generated grammar makes that choice
explicit. Canvas edges are closed, droplets never leave, solids are immutable.

The native curriculum uses 3–6 demonstrations and exactly four private queries.
A deterministic 97-scene teaching pool (96 varied terrains plus a diagonal-pore
counterexample) is scored using only demo labels against 17 declared policies.
Queries are independently drawn, fixed across demo counts/settings; the fourth
is substantive 30×30 terrain, not empty padding. A surviving query-disagreeing
policy raises rather than silently certifying the episode. This finite audit is
not universal rule identifiability or an all-seeds totality proof.

The first 32-seed audit found seed 25 admitted an 8-connected pool rival. A
constructive diagonal-pore scene repairs it at the same demo count. The exact old
lesson and Racket rival are retained in regression-eight-connected.json, with a
Racket before/after replay in the audit. An earlier alternative-rule parenthesis
error and a test's comment-handling mistake were repaired; failed logs are retained.

Only authoring preflight is available here. No catalog approval, owner native
qualification, native acceptance, or training admission is claimed. The original
public-parent.json is unchanged. Production generator has no external-data imports.
