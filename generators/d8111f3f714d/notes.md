# Working notes: d8111f3f714d

## Current decisions

- Production version 3.0.0 remains unchanged at SHA256
  `31cd4a04282f3a8dd56008ccd12895aa2879cd8ed0a7c5161029cd7a5b21f4ab`,
  with canonical rule hash `2a9d26bd68ef`. Its five-rival semantic contract and
  previously retained one-sided lesson remain intact.
- The native adapter reuses the unchanged prototype's exact programs for
  `branch_direction=toward_trunk|away_to_edge`. The original ledger row is pinned
  by content hash `d8111f3f714d`; both task-ID rows have identical program bytes,
  but the augmented row includes the original held-out pair in its training set.
  Canonical demonstration-only analysis therefore selects the original row.
- Native sampling uses a fixed six-demo/four-query input bank before independent
  slicing, supports 2–6 demos and 1–4 queries, and defaults to 3/4. Inputs match
  across settings. The opt-in grammar extends dimensions to 10..30 and branches
  to 1..27 where coordinates permit; actual sampled profiles reach22 branches.
  Production remains10..24 and 1..5. Construction uses one attempt per scene.
- Core demos use both orientations, both sides, unequal rays, off-center trunks,
  internal endpoints and 6–8 branches. A branch between trunk and canvas midpoint
  distinguishes away-from-trunk routing from nearest-edge routing. Four queries
  include 10×10, medium, tall/wide and 30×30; large query profiles have 14–18 branches
  and nonzero painting in all four quadrants under both settings.
- Only `turns/<sha>.json` is actor-visible, with one masked query. Four-query
  controllers and complete native/adapter provenance stay private. IDs depend
  only on visible bytes, and the first turn is invariant to future queries and
  private metadata. The consuming controller owns sequencing; no controller was
  implemented or tested. The legacy prototype's multi-query `public/` format is
  controller-only.

## Current evidence and remaining scope

- Focused tests: 35 family,14 independent-audit and 8 export tests passed. The
  sampler probe passed 96/96 requests over 16 seeds, with 160 distinct inputs and 64
  distinct queries. Its independent Python parity is separate from native Racket
  qualification. A hand-constructed27-branch boundary was also Python-checked;
  that boundary is not claimed as a protected reference replay.
- `checks/d8111f3f714d/native-branch-teaching-audit/report.json` retains112
  protected Racket evaluations: both settings, seeds 0/17, two demos and four
  queries. All 13 declared non-equivalent rivals are refuted by the core demos;
  every query distinguishes the two settings. Coverage is finite.
- The assigned canonical-shortcut proof is
  `checks/d8111f3f714d/canonical-rival-proof/report.json`. Only `first_five_only`
  survives the 13-rival screen on the four original demos. Current native seed 0,
  toward_trunk, train[0] has 8 branches; this rival omits20 required green cells.
  Eight fresh protected applications check the canonical demos, and two exact
  previous native-audit applications supply the retained counterexample labels.
- `checks/d8111f3f714d/qualification/qualification.json` qualifies both settings
  at seeds 0/17 with 6 demos and 4 queries (64 protected evaluations), exercising the
  full bank. Native examples use the normal3/4 count and 20 protected evaluations;
  their saved projections, all payload hashes and 13 source bindings passed the
  export inspection with no findings.
- `checks/d8111f3f714d/causal/witness.json` and sibling replay retain two
  wrong-intermediate cases. Substituting the canvas midpoint for the inferred
  line in the exact native program changes 53 and 70 cells. Four construction and
  four replay evaluations verify the final labels. The geometry interpretation
  is authored metadata, not a universal depth or iterative-state claim.
- The inherited old-source assurance finding remains `needs_triage` in the
  review index. No index, approval, canonical authority or production code was
  changed. The unchanged production battery and historical legacy collection
  failure were not rerun; previous receipts are not new passing claims.
- Reviewer status is native ready, owner acceptance pending, training admission
  false. Next useful owner action is exact-source integration followed by native
  qualification and acceptance, preserving the stated findings and finite scope.
