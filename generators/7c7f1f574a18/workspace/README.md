# Task-local review workspace

`semantic_census.py` is a source-bound, independently implemented teaching-quality probe for generator `7c7f1f574a18`. It does not call `generator.rule_true`; it recomputes modal background, same-colour 4-connected components, bounding-box gap topology, and docking outputs, then scores the generator's actual `SEMANTIC_WITNESSES` and `LESSON_COMPETITORS` declarations.

From the packet root:

```bash
python3 run_with_racket.py python3 generators/7c7f1f574a18/workspace/semantic_census.py \
  --lessons-per-band 100 \
  --json-out ../checks/semantic-census/report.json
```

The pinned sampler uses bands `easy, medium, hard`, seed `700000 + 10000*band_index + lesson_index`, four inputs per lesson (three demos plus one query), and sample indices `lesson_index*4 + offset`. The report includes source hashes, unique-input counts, strict-profile counts, domain limits, invalid-input counts, witness firings, rival disagreements, canonical-oracle parity, and unidentifiable lessons.

Limit: the census tests a finite deterministic sample and the declared rival family. It is not a universal proof that every possible learner must infer the intended rule.
