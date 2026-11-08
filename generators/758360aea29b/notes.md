# Working notes: 758360aea29b

## Current decision

The base generator is repaired rather than merely wrapped. Canonical inputs are interpreted as row-major monochrome 4-connected objects, including irregular shapes and repeated colors on disconnected components. Input validation is strict for seed, sample index, difficulty, dimensions, object count, palette aliases, and unknown overrides. A scheduled 10×12 / three-object canonical anchor remains available in every difficulty band while explicit axes retain the full declared domain.

The selected authority record was synchronized to the byte-exact canonical Racket program; archival raw code was preserved.

## Parametric family

The finite family has exactly two settings. `pairwise_width` is the byte-exact canonical default. `pivot_distance` first selects the unique tallest sampled object, records its bounding-box width, converts every object width to absolute distance from that pivot, and then emits the same 1/2/3 ordered comparison matrix over those derived scores. The sampler is setting-independent, count-prefix independent, supports 2–6 demonstrations and 1–4 queries, and includes a 30×30 query input.

## Verification retained

- Native generator battery: 12/12 green on generator SHA-256 `d663a62c889d551711b73dbb49d67c4449a9d264b75b84b367d4ae139e34fe22`.
- Focused tests: 8/8 passed.
- Adversarial family probe: 10 episodes, 100 labelled pairs, zero findings.
- Protected Racket family worker: four jobs and 40 Racket evaluations, with the intended setting the sole finite survivor in every episode.
- Authoring preflight: four jobs across both settings; 24 parametric labels plus all five canonical pairs; status passed.
- Sequential witness: protected-Racket replay passed and the wrong-intermediate ablation changed the final output.
- Public projection: four qualified episodes exported as 16 independent one-query views and verified without exposing private settings, programs, future queries, or answers.

## Remaining policy step

No reviewer-side failure remains. Owner-side exact-source qualification/acceptance and any training admission are intentionally still pending; the next useful action is the owner's native acceptance replay against the packaged source and evidence inventory.
