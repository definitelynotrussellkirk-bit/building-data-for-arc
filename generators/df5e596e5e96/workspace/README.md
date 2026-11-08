# Workspace

`semantic_census.py` is a reusable, source-bound curriculum probe for this task. It assembles complete three-demo-plus-query lessons over every cyclic start of the four-slot schedule, iterates the generator's actual `LESSON_COMPETITORS`, records witness/rival disagreement rates and unique inputs/outputs, and checks that declared canonical shortcuts really fit every canonical pair.

From the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/df5e596e5e96/workspace/semantic_census.py \
  --lessons-per-band 100 \
  --seed-base 17000 \
  --json-out ../checks/semantic_census/report.json
```

The tool also runs from an explicitly copied portable runtime at `workspace/semantic_census.py`; it locates the frozen generator and canonical reader without relying on the original repository.

The selected implementation is `../generator.py`. Workspace drafts and tools are never automatically selected as training generators.
