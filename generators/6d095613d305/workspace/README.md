# Workspace

The selected implementation is `../generator.py`. Workspace tools are diagnostic;
they are not imported by the generation runtime.

## Curriculum probe

`curriculum_probe.py` samples the final generator, iterates the generator's actual
`LESSON_COMPETITORS`, and audits every cyclic start of its three-slot schedule.
It records the generator SHA, seed/index denominator, profile counts, strict-profile
hits, rival-witness counts, and any invalid or unidentifiable lesson windows.

From the repository root:

```bash
python3 generators/6d095613d305/workspace/curriculum_probe.py \
  --seed-start 0 --seed-count 24 --bands easy medium hard \
  --out generators/6d095613d305/workspace/curriculum_probe_final.json
```

The retained final report covers 432 draw records and 216 complete lesson windows.
