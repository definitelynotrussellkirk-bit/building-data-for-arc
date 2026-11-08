# Review: 424c822d69f3 rectangle-anchor prototype

Task/source: `424c822d69f3`, approved generator v2.2.0, source parent `training:ddf7fa4f`.
Status: **routine proposed prototype**; production generator, canonical rule, rule hash `5abbdbb61293`, and approval state are unchanged.
Missing extension → added a task-local fixed-per-episode `anchor=midpoint|left_edge|right_edge` family.
The `midpoint` program is byte-identical to canonical; alternatives change only the bbox column used for nearest-marker selection.
Focused prototype contract: **24 passed**; unchanged canonical task contract: **80 passed**.
Retained comparison: 3 settings × (3 demonstrations + 4 distinct queries), **21 real Racket executions**, all independent-oracle matched.
All 12 retained queries are identified from demonstrations only; shared inputs isolate the parameter effect.
Adversarial pass: supported 16/16 counts produced 32 distinct inputs and 32 checked labels; retry exhaustion and tampered labels fail explicitly.
Public export contains only train pairs and query inputs, uses visible-byte hash filenames, and keeps settings/programs/query answers private.
Remaining limit: identifiability is finite over the three declared anchor programs and retained comparative evidence uses seed 17; this is not promotion or training admission.

## Built artifact

- `generators/424c822d69f3/workspace/parametric/prototype.py`: deterministic sampler, fixed-setting episode generation, real-Racket execution, demonstration-only rival fitting, and public/private writer.
- `oracle.py`: independent component/bbox/nearest-marker semantics.
- `rules/*.rkt`: exact canonical/default program plus two one-expression derivations.
- `adapter.py` and `promotion.json`: bounded future qualification surface; 2–16 demos and 1–16 queries.
- `README.md`: exact commands, semantics, limits, and proposed-only status.
- `tests/test_parametric_anchor.py`: source drift, domain, sampling, Racket/oracle, identification, projection, and rejection regressions.

## Evidence

- Three-setting export and summary: `checks/parametric-anchor/final-evidence/summary.json`
- Racket execution receipt: `checks/parametric-anchor/final-evidence/private/racket-executions.json`
- Export manifest: `checks/parametric-anchor/final-evidence/manifest.json`
- Focused tests: `checks/parametric-anchor/focused-final.log`
- Unchanged canonical tests: `checks/parametric-anchor/canonical-task-tests.log`
- Boundary/export/rejection probe: `checks/parametric-anchor/adversarial-probe.json`

The development record retains the expected red tests and the discovered `demos=2` filler-loop regression; the fix stops filler selection when the two mandatory witnesses already satisfy the requested count.
