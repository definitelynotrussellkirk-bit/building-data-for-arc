# Reusable authoring tools

Run these from the outer extracted packet directory. They read authoring data and are not permitted during visible-only solve episodes.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 review.py run python3 -B generators/0eb4eaa46003/workspace/profile_probe.py --seed 0 --seed 37 --count 8
PYTHONDONTWRITEBYTECODE=1 python3 review.py run python3 -B generators/0eb4eaa46003/workspace/reference_probe.py --out ../checks/new-reference-witnesses
```

The independent probe reports its selected source hash, observable controls, canonical comparisons, phase-specific rivals, and complete rotated four-pair windows. It uses its own component traversal and profile calculations. Python oracle evidence is identified separately from actual Racket authority. The reference probe refuses an existing output directory and stores full inputs, actual Racket outputs, and a comparison receipt. Two seeded phases cover all fifteen declared rivals; a separate two-input fixture demonstrates that equal margins do not determine the target's pixel arrangement.

For oversized explicitly named evidence:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 review.py run python3 -B generators/0eb4eaa46003/workspace/compact_evidence.py compress ../checks/large-report.json --root ../checks --remove-original
PYTHONDONTWRITEBYTECODE=1 python3 review.py run python3 -B generators/0eb4eaa46003/workspace/compact_evidence.py restore ../checks/large-report.json.compression.json --root ../checks
```

Compression records the original relative path, sizes, both SHA-256 values, and a verified round trip before optional source removal. Existing archive/map destinations, dangling destination symlinks, corrupt archives, outside-root paths, and conflicting restored evidence are rejected. A matching restored file is left untouched. This tool handles only explicitly named evidence; it does not prune directories or alter the original upload.
