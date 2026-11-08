from __future__ import annotations
import hashlib, importlib.util, json, pathlib, sys
root = pathlib.Path.cwd()
task = 'cf42d4eb3e09'
path = root / 'generators' / task / 'generator.py'
spec = importlib.util.spec_from_file_location(f'audit_{task}', path)
mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
grid = mod.generate(123, 0, texture='no_motifs')
obs = {
    'task_id': task,
    'generator_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'call': {'seed': 123, 'sample_index': 0, 'difficulty': None, 'overrides': {'texture': 'no_motifs'}},
    'shape': [len(grid), len(grid[0])],
    'nonzero_cells': sum(v != 0 for row in grid for v in row),
    'self_check': mod.self_check(grid),
    'grid': grid,
}
outdir = root.parent / 'checks' / 'audit' / task
(outdir / 'input.json').write_text(json.dumps(grid, indent=2) + '\n')
(outdir / 'generator_observation.json').write_text(json.dumps(obs, indent=2, sort_keys=True) + '\n')
print(json.dumps(obs, sort_keys=True))
