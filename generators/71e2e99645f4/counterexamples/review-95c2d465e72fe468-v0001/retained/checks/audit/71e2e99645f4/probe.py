from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

root = Path(__file__).resolve().parents[3] / 'repo'
path = root / 'generators/71e2e99645f4/generator.py'
spec = importlib.util.spec_from_file_location('audit_71', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

malformed = [[1]]
malformed_errors = module.self_check(malformed, meta={'texture': 'no_holes'})
base = module.generate(123, 4)
forced = module.generate(123, 4, hole_patterns=['center_hole'] * 3)
unknown = module.generate(123, 4, typo_override='accepted')

payload = {
    'task_id': '71e2e99645f4',
    'generator_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'findings': {
        'metadata_validator_bypass': {
            'grid': malformed,
            'meta': {'texture': 'no_holes'},
            'self_check_errors': malformed_errors,
            'expected': 'reject non-4x14 grid regardless of metadata',
            'reproduced': malformed_errors == [],
        },
        'declared_hole_patterns_override_ignored': {
            'requested': ['center_hole'] * 3,
            'base_equals_forced': base == forced,
            'base': base,
            'forced': forced,
            'reproduced': base == forced,
        },
        'unknown_override_accepted': {
            'key': 'typo_override',
            'accepted': unknown is not None,
            'base_equals_unknown': base == unknown,
            'reproduced': unknown is not None,
        },
    },
    'command': ['python3', 'checks/audit/71e2e99645f4/probe.py'],
    'cwd': 'packet_root',
}
Path(__file__).with_name('counterexample.json').write_text(json.dumps(payload, indent=2) + '\n')
print(json.dumps({
    'metadata_validator_bypass': malformed_errors == [],
    'hole_patterns_override_ignored': base == forced,
    'unknown_override_accepted': unknown is not None,
}, sort_keys=True))
