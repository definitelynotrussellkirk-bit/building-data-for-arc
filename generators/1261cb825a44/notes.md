# Working notes: 1261cb825a44 — reviewer build 2026-10-26

## Decision and source integrity

The ORIGINAL Racket program is the exact default `view=isolated`, unchanged byte-for-byte. It obtains the color from the single nonzero corner, discards all corner positions, filters to that color, and renders the selected cells in their tight bounding box. The new, optional `view=context` uses the same corner key, selected noncorner footprint and input-dependent bbox, but crops the full multicolored content within that bbox after deleting corner metadata. This is a rule-level change, not a sampler or palette variation. The exact canonical source remains selected by the `isolated` setting. Neither the owner source authority nor approval flags were edited.

## Base defects and repairs

The pre-change generator silently returned partially constructed boards after failing to place the key blob, or omitted all distractors after failed placement. A deterministic 100-seed × 4-index probe observed 10/400 invalid ordinary samples: four empty keyed interiors and six with no different-colored distractor. The repaired generator forbids all four corners for blob growth, retries a complete scene up to a fixed bound, and raises on exhausted attempts instead of exporting a partial label. It also draws a supported 1–3 distractor count and checks ordinary key, payload, and distractor existence, preserving deliberate degenerate texture overrides.

## Sampler/teaching repairs discovered in self-review

Initial two-demo lessons let the global-minority-color shortcut survive, and the first construction sometimes grew keyed pixels into a second grid corner. Corrective changes enforce a high-density, broad key footprint for the second demo while the first demo deliberately keeps the key relatively rare; both still vary geometry, palette, corner, and inside/outside distractors. The growth frontier and embedded-distractor sampling explicitly forbid all corners. The final first-two-demo lessons reject canonical/context confusion, global-minority/majority selection, selecting all nonzero pixels, retaining the corner glyph, fixed-center cropping, and other declared finite rivals.

The key footprint is a four-connected irregular path/branch shape of variable width and height, including a substantial 30×30 episode. The parametric query profiles are 9×10, 16×19, 25×27, and 30×30; 30×30 queries contain between 290 and 533 occupied cells in the 140-seed audit. Input generation is identical for both settings and independent of the requested demonstration count. There are 2–6 demonstrations and exactly four distinct private queries. The existing standard exporter shuffles their presentation and reveals just one query per turn, without future-input or private-label leakage.

## Results and remaining limits

- `tests/test_parameters.py`: 21 passed; regression, counts/settings, matched inputs, two-demo rival elimination, crossed bbox/content controls, and 12 Racket label checks.
- `workspace/parametric/evidence/adversarial.json`: 140 seeds × 3 supported demo counts × 2 settings = 840 finite-rival lessons, no observed ambiguity; 420 matched-input comparisons and genuine rule-output differences.
- `WORK/checks/1261cb825a44/qualification/qualification.json`: authoring preflight passed on 2 settings × 2 seeds, 32 protected Racket evaluations including canonical checks, **not** owner approval.
- `WORK/checks/1261cb825a44/causal/witness.json`: context setting, selected-key bbox `[1,1,7,7]` versus wrong-intermediate color bbox `[0,0,8,9]` — executed final grids 7×7 versus 9×10; protected replay passed.
- Public preview: 16 views verified; first-turn checker passed all 24 private-field invariance checks. These are projection checks, not another Racket replay.

Finite rival checks cannot exclude arbitrary programs; no universal uniqueness, training gain or acceptance is claimed. The extended parametric grammar is deliberately separate from the legacy small ordinary generator. Next action: owner integration, native qualification, code/semantic review, fresh acceptance; only then consider training admission.
