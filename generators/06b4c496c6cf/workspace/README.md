# Workspace

The selected implementation is `../generator.py`. Workspace drafts are never
automatically selected.

## `probe_curriculum.py`

A source-bound task probe for future reviewers. It verifies that every declared
canonical shortcut fits all canonical pairs, enumerates every cyclic schedule
start and every held-out query rotation across several seeds and all three
bands, and exercises legal joint override boundaries plus declared
incompatibilities.

From the packet root:

```sh
python3 review.py run python3 generators/06b4c496c6cf/workspace/probe_curriculum.py \
  --out ../checks/curriculum-probe.json
```

This is supplementary evidence; the shared battery, task-test stage, and lesson
census remain authoritative for their own contracts.
