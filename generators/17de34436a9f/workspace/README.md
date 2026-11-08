# Review workspace

`lesson_probe.py` is a reusable, source-bound curriculum audit for the selected
implementation in `../generator.py`.

Run from the extracted packet root:

```bash
python3 repo/generators/17de34436a9f/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --out checks/17de34436a9f_final_lesson_probe.json
```

The probe:

- verifies its generator, canonical-rule, and own source hashes;
- checks the Python mirror against every canonical pair;
- dynamically reads the generator's actual `CANONICAL_SHORTCUTS`,
  `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and schedule declarations;
- confirms each declared canonical shortcut really fits every canonical pair;
- assembles 4-demo + 1-query lessons with every cyclic schedule start;
- records unique inputs and lessons, strict-profile support, witness coverage,
  rival survivors, and generated disagreements with canonical shortcuts.

It is a finite Python-side curriculum probe, not an authority replacement or a
claim of universal induction. The final battery independently checks Racket
parity.
