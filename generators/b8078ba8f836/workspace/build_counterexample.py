from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

home = Path('generators/b8078ba8f836')
source = home / 'generator.py'
spec = importlib.util.spec_from_file_location('b8078_fixture', source)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
grid = module.generate(911, 1, difficulty='medium')
fixture = {
    'schema': 'b8078ba8f836-counterexample-v1',
    'task_id': module.TASK_ID,
    'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'rule_hash': module.RULE_HASH,
    'seed': 911,
    'sample_index': 1,
    'difficulty': 'medium',
    'observed_overrides': module.observe_overrides(grid),
    'witnesses': [name for name, predicate in module.SEMANTIC_WITNESSES.items() if predicate(grid)],
    'input': grid,
    'intended_output': module.rule_mirror(grid),
    'rival_outputs': {name: rival(grid) for name, rival in module.CANONICAL_SHORTCUTS.items()},
}
path = home / 'counterexamples' / 'exact_count_and_alignment.json'
path.write_text(json.dumps(fixture, indent=2) + '\n')
print(path)
