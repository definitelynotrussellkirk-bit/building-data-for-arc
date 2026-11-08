# aad4e3a1d5e3 parametric authoring

This task-local family preserves the exact canonical program as
`mode=complete_orbit`. The alternative `mode=chain_only` performs the same
vertical reflection first, derives the cells created in that intermediate, and
reflects only those new cells across the horizontal guide. The result keeps the
source, vertical copy and diagonal copy while omitting the source's direct
horizontal copy.

The input bank is deterministic and setting-neutral. It supports 2–6
independent demonstrations and 1–4 queries; requesting one query returns the
same first query as requesting four. The fourth query is a substantive 30×30
boundary case with two separated motif components.

Focused tests:

```bash
python3 review.py run python3 -m pytest \
  generators/aad4e3a1d5e3/tests/test_parametric_prototype.py -q
```

Build and replay compact authoring evidence with protected Racket:

```bash
python3 review.py run python3 \
  generators/aad4e3a1d5e3/workspace/parametric/audit.py build \
  --out ../checks/aad4e3a1d5e3/authoring-audit --seed 0 --seed-count 4 \
  --demos 3 --queries 4
python3 review.py run python3 \
  generators/aad4e3a1d5e3/workspace/parametric/audit.py verify \
  ../checks/aad4e3a1d5e3/authoring-audit
```

Every public file is named by the SHA-256 of its exact bytes and contains all
demonstrations plus one current query input. Settings, programs, query answers
and future queries remain in private files. This is reviewer evidence only; it
does not accept the family or admit data to training.
