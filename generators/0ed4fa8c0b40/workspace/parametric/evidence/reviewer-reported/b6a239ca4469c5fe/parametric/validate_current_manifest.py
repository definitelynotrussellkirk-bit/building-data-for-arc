#!/usr/bin/env python3
from pathlib import Path
import hashlib, json
from arcpuzzles import Catalog
from arcpuzzles.parametric_priority import _prototype

root = Path.cwd()
row = next(r for r in Catalog(root).query() if r['id'] == '0ed4fa8c0b40')
result = _prototype(root, row)
path = root.parent / 'checks/parametric/manifest-validation.json'
path.write_text(json.dumps({
    'schema': 'arcpuzzles-parametric-manifest-validation-v1',
    'task_id': '0ed4fa8c0b40',
    'result': result,
    'generator_sha256': row['generator_sha256'],
    'rule_hash': row['rule_hash'],
    'manifest_sha256': hashlib.sha256((root / result['manifest']).read_bytes()).hexdigest(),
}, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result.get('status') == 'current' else 1)
