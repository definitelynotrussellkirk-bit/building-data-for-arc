# Proposed selector parameter for `d1dd527dba87`

This opt-in prototype preserves the canonical normalized-XOR composition and
varies one semantic step: select each color's **largest** component (canonical)
or **smallest** component.  It is proposed and unaccepted; production generator,
canonical rule, and approval state remain unchanged.

The input sampler is setting-neutral.  Every scene contains a unique small and
large component of colors 1 and 2.  Across the first three demonstrations the
large/small objects reverse both top/bottom and left/right order, directly
blocking the reproduced bottommost/rightmost lesson shortcut.  Demo and query
counts are independent (2–6 and 1–4); the fourth query is substantive 30×30.

Focused check:

```bash
python3 review.py run python3 -m pytest -q generators/d1dd527dba87/tests/test_parametric.py
```

Protected qualification is run with `arcpuzzles.parametric_worker` because the
canonical production generator is not approved; owner acceptance remains a
separate action.  Public turns are projected only from visible demonstrations
and the current query input, never settings, Racket, or query labels.
