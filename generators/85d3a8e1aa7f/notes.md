# Working notes: 85d3a8e1aa7f

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current native parametric work: direct / relay

The task-local `workspace/parametric/adapter.py` preserves the exact canonical
default and adds a relay rule: center-color centroid -> first eligible hit on
that ray -> selected color centroid -> final colored diagonal. Settings are
fixed per episode, with identical inputs across settings, 2–6 demos and 1–4
independent queries. Four-query episodes include substantive 30×30 inputs; the
separate family explicitly uses the canonical floor-center convention on even
sizes. No production generator, canonical authority or approval was changed.

Self-review repaired three prototype shortcuts: (1) the first two relay outputs
had the same final direction, (2) equal support counts exposed the relay as the
color with key count minus four, and (3) the intended first ray uniquely had two
eligible hits. The current sampler varies counts independently, balances ray
occupancy/depths, varies final direction and rejects declared rivals using only
demonstrations under both settings. Original Racket-labeled ambiguity witnesses
are retained in `workspace/parametric/evidence/current/*_before.json`.

A reliability probe also found that resampling only demonstration two can never
repair some fixed-ray aliases in demonstration one (seeds 4 and 11). The bounded
selector now replaces the entire teaching pair. Regressions retain those seeds.
`audit.py` is the reusable protected-Racket teaching/export checker; see its
README and evidence for the executed scope. Native exact-source owner
qualification/acceptance remains the handoff; no training admission is claimed.

The historical production-domain/validator audit below is not reclassified.

## Endpoint-control repair (version 1.2.2)

The prior generator advertised wider exact-control domains than its default sampling bands, but used `overrides.get(name, ctx.draw_int(...))`. Python eagerly evaluated the default draw even when an override existed, so valid endpoints were rejected against the narrower default ranges:

- `n_key_cells=15` against default 4–8;
- `n_distractors=0` against default 3–6;
- `distractor_palette_size=1` against default 2–5.

`_draw_advertised_int` now takes separate default and valid ranges. Explicit integer overrides are validated against the advertised domain and then recorded through `GenCtx`; absent controls retain the original default sampling ranges. No canonical Racket source or rule semantics changed.

Focused regression tests exercise each endpoint as an observable grid property. A bounded Racket probe executes the canonical program on all three repaired calls and compares it with an independently derived diagonal output; all three pass. Evidence is under packet `checks/85d3a8e1aa7f/`.

## Deliberate scope limit

The retained audit also discusses broader validator/domain and teaching-distribution questions. This repair does not resolve or reclassify those findings; it fixes only the reproducible eager-default endpoint defect assigned for this review.
