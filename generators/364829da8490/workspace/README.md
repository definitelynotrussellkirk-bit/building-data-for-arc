# Reviewer workspace: 364829da8490

`probe_topology_curriculum.py` is a source-bound diagnostic for this task. It
enumerates every declared schedule start in easy, medium, and hard, holds out
every pair once, and scores the task's current `LESSON_COMPETITORS`. It also
reports which explicit scene profiles refute each rival.

From the extracted packet root:

```sh
python3 review.py run python3 generators/364829da8490/workspace/probe_topology_curriculum.py \
  --seed 0 --profile-seeds 12 --out ../checks/topology-curriculum-probe.json
```

The probe uses the Python mirror only. Use `arcpuzzles apply` or
`lesson-census` for authoritative Racket labels.
