# Workspace

`curriculum_probe.py` is a source-bound reviewer probe for this task. It checks:

- all canonical inputs are accepted and match the independent Python mirror;
- the plausible left-to-right-only shortcut still fits every canonical pair;
- every declared `scene_profile` is generated, accepted, and observable from pixels;
- every cyclic lesson start and every held-out query rotation leaves demonstrations with both left- and right-side sources;
- no declared lesson competitor survives those demonstrations while disagreeing on the query.

Run from the repository root in a portable check runtime:

```bash
python3 generators/c4155b3fcecd/workspace/curriculum_probe.py \
  --out ../checks/c4155b3fcecd-curriculum-probe.json
```

The selected implementation is `../generator.py`; workspace files are reviewer tooling and are not selected as generators.
