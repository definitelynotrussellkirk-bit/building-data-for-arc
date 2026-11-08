# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Source-bound topology audit

From an extracted packet root:

```sh
python3 setup_racket.py
python3 run_with_racket.py python3 generators/9e80ef661ecc/workspace/lesson_probe.py \
  --lessons-per-band 100 --out checks/hole-topology.json
python3 run_with_racket.py python3 -m pytest -q generators/9e80ef661ecc/tests
```

`reference_probe.py` supplies an independent Python oracle and real Racket
application. `topology_probe.py` supplies independent shortcut implementations
and D4-normalized shape diagnostics. `lesson_probe.py` hashes all three tools,
the selected generator and its rule identity; it audits 100 independently seeded
four-demo lessons per band, with one query each. Task-local per-band floors are
50 normalized scene multisets and 40 object shapes. They are regression gates,
not general sufficiency criteria.

`normalized_scene_topology_uniqueness` counts multisets of object shapes modulo
color, translation, rotation and reflection. It does not capture relative
placement, contact or color relationships. Raw uniqueness is reported separately.
All identifiability results are **against the declared finite rival set**.
