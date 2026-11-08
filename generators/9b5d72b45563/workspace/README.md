# Reviewer workspace for 9b5d72b45563

`cyclic_lesson_probe.py` extends the shared census's one-fixed-seed schedule mode across a bounded seed range. It exhaustively enumerates every start of the generator's finite deterministic schedule, rotates each five-pair bundle through every query position, and scores the generator's current `LESSON_COMPETITORS` plus `lesson_identifiable` hook.

Example from the repository root:

```bash
python3 generators/9b5d72b45563/workspace/cyclic_lesson_probe.py \
  --seed-start 730000 --seed-count 25 --bands easy,medium,hard \
  --out ../checks/cyclic-lesson-probe.json
```

The report binds the generator SHA-256 and rule hash and retains the first ambiguity, hook warning, or rival exception. A clean run is evidence only against the declared finite rival set; it is not universal identifiability proof.
