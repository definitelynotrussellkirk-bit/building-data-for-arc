# Reviewer workspace

`probe_schedule_phases.py` replays one Racket-labelled four-pair lesson for every
`easy|medium|hard × canonical_profile|broad|dense` start phase, then checks the
production query and all query rotations against the generator's declared
`LESSON_COMPETITORS`.

Run from the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/ff5eb7af92e7/workspace/probe_schedule_phases.py \
  --out ../checks/schedule-phase-probe.json
```

The report is exhaustive over the three finite profile phases only. It uses one
representative seed per phase and cannot rule out undeclared hypotheses.
