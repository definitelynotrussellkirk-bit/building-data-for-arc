# Working notes: 953db766893d

## Current decision

Build a separate native parametric family with episode-fixed `extreme=minimum|maximum`. `minimum` returns the exact canonical Racket source; `maximum` changes only the selected input-derived component-area extreme. The production generator and canonical authority remain unchanged.

The sampler deliberately separates room size from wall openings. Demo 1 is an intact unequal lattice. Demo 2 introduces an opening while reusing absolute room areas whose labels change across the two lessons. This repairs the retained teaching shortcut for the parametric family without claiming that the existing production-generator audit is cleared.

## Bound evidence

- Source inventory: `workspace/parametric/evidence/manifest.json` (`260f6b1e07c4cd4e6ea427b166d207af62f45ef38d38894102d0f1b347d93f49`).
- Native qualification: `checks/953db766893d/qualification/qualification.json`; both settings, seeds 0 and 17, 3 demos and 4 queries, protected Racket.
- Causal witness: `checks/953db766893d/causal/witness.json`; for the qualified maximum rule, replacing the selected maximum area 51 with the minimum-area intermediate changes the protected-Racket final grid.
- Lesson audit tool: `workspace/parametric/audit_lessons.py`; retained seed-0 and seed-17 reports execute 12 labels each through protected Racket.
- Final checks: 26 focused tests, 35 portable task tests, public 3-demo/4-query export check, and a bounded seeds 0–255 count-boundary sampler probe.

## Remaining owner action and limits

Integrate these exact bytes, rerun native qualification and causal replay against the live source binding, then perform owner acceptance. Until that succeeds, status is reviewer-ready only: no accepted variant and no training admission. The finite lesson audits do not prove universal rule uniqueness or measured learning gain. The prior `review_index.json` production-generator shortcut finding remains `needs_triage` because `generator.py` was not changed.
