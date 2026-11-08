# Reflection lesson probe

`probe_reflection_lessons.py` is an authoring probe for this task. It loads the
selected generator through `reviewer_support`, reads live `CANONICAL_SHORTCUTS`
and `LESSON_COMPETITORS`, and checks canonical fits, distinct inputs, witness
counts, all cyclic starts, and all single-query holdouts. Missing, empty, or
malformed declarations fail explicitly. Newly named rivals are discovered
without editing a second inventory.

Run from the outer packet directory with fresh evidence filenames:

```bash
python3 review.py run python3 generators/b1972482cb43/workspace/probe_reflection_lessons.py --write-oracle-inputs ../checks/probe-inputs.json
python3 review.py run python3 -m arcpuzzles apply b1972482cb43 --input ../checks/probe-inputs.json --check-generator-domain --out ../checks/probe-labels.json
python3 review.py run python3 generators/b1972482cb43/workspace/probe_reflection_lessons.py --oracle-labels ../checks/probe-labels.json --out ../checks/probe-report.json
```

The small fixtures receive fresh Racket labels. Generated comparisons inside this
probe use an independent reflection model calibrated against those labels and
canonical pairs. Use public `lesson-census` for broad authoritative generated-label
verification. This bounded probe complements that census.

The sufficient condition is two distinct refuting inputs for every rival in each
five-pair window. Any one held-out query then leaves a refuting demonstration.
Five distinct inputs also protect against duplicate filtering. The claim assumes
one fixed seed and constant valid overrides within a lesson.

Final evidence, commands, declaration negative controls, and limitations are under
`WORK/checks/lesson-design/` in review return `review-94649ff728f83147`. Stable
conclusions are in `../notes.md`; compact authority-checked fixtures are in
`../counterexamples/`. Workspace scripts are never automatically selected as
production generators.
