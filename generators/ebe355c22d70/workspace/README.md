# Workspace

The selected implementation is `../generator.py`; workspace files are diagnostics and are not automatically selected.

`probe_schedule.py` is an opt-in, source-bound audit for this generator's finite teaching schedule. It imports the live `SCHEDULE_PROFILES` and rival declarations, enumerates every cyclic start in every difficulty band, rotates every labelled pair through the query position, validates rival outputs, and checks the declared output codomain. Example from the packet root:

```bash
python3 review.py run python3 generators/ebe355c22d70/workspace/probe_schedule.py --out ../checks/schedule-probe.json
```

Its guarantee is deliberately bounded to the declared finite schedule and declared competitors; it does not prove universal rule identifiability.
