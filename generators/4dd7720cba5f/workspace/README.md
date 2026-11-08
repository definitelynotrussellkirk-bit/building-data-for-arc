# Workspace

Reusable review probe:

```bash
python3 generators/4dd7720cba5f/workspace/probe_semantic_curriculum.py \
  --starts 12 --out ../checks/semantic-curriculum-probe.json
```

It verifies that every declared canonical shortcut fits all canonical pairs,
then audits cyclic consecutive lesson starts in every difficulty band.  The
selected implementation remains `../generator.py`; workspace files are never
automatically selected.

Parametric prototype and exact four-query command:

- [`parametric/README.md`](parametric/README.md)
- `parametric/prototype.py`

The prototype is proposed and unapproved; it does not replace `../generator.py`.
