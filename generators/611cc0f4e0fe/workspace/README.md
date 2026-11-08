# Workspace: semantic curriculum audit

The selected implementation is `../generator.py`. `audit_curriculum.py` is a
portable task-local probe for checks that the shared lesson census does not
fully cover.

From the repository root:

```sh
python3 generators/611cc0f4e0fe/workspace/audit_curriculum.py \
  --seeds 16 \
  --json ../checks/task-local/curriculum-audit.json
```

The probe:

- forces every declared `SCENE_PROFILES` value in easy, medium, and hard bands;
- checks `observe_overrides`, `self_check`, `rule_mirror`, witnesses, and every
  rival declared by the generator rather than a copied name list;
- verifies that each declared canonical shortcut fits every canonical pair;
- assembles all cyclic starts of the four-profile schedule so every profile is
  tested in the query position; and
- exits nonzero with a machine-readable failure list.

This is complementary evidence, not a replacement for the supported battery or
`arcpuzzles lesson-census`.
