# Workspace

The selected implementation is `../generator.py`. Workspace tools and drafts are
not automatically selected.

## `probe_curriculum.py`

A fast, source-bound authoring probe for the finite four-profile lesson schedule.
It checks every requested cyclic start in all three bands, all four query
rotations, the generator's declared lesson competitors, both semantic witnesses,
and the same pinned 20-draw profile-floor recipe used by the native gate.

From the repository root:

```bash
python3 generators/ffdc0ddb44bd/workspace/probe_curriculum.py \
  --starts 32 \
  --out ../checks/curriculum-probe.json
```

The probe intentionally uses the Python mirror and only declared rivals. It is a
cheap regression detector, not a substitute for the Racket battery or the
source-bound `lesson-census` command, and it cannot prove uniqueness against
undeclared hypotheses.
