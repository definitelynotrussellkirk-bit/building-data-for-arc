# Task workspace

The selected implementation is `../generator.py`; workspace tools are not selected as label authority.

## `lesson_probe.py`

A reproducible source-bound curriculum census. It loads the exact generator path, computes outputs with an independent monochromatic-component oracle, evaluates every declared `LESSON_COMPETITORS` function on full four-demo lessons, records input uniqueness/profile coverage/sampler details/domain limits, and optionally requires parity with the real selected Racket program.

Run from the packet root with the verified local Racket:

```bash
python3 run_with_racket.py python3 \
  generators/8a2e39528187/workspace/lesson_probe.py \
  --lessons-per-band 100 --racket \
  --out ../checks/final_lesson_probe.json
```

The command audits 100 lessons in each of `easy`, `medium`, and `hard`; each lesson contains four visible demonstrations plus one held query. It exits nonzero for any validator error, lesson with a surviving declared rival, unidentifiable lesson, unavailable Racket execution when requested, or Racket mismatch. Its conclusion is limited to the declared finite rival set and sampled task domain.
