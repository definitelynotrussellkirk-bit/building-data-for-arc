from __future__ import annotations
import hashlib, importlib.util, json, pathlib, sys
root = pathlib.Path.cwd()
task = '69b886e1df03'
path = root / 'generators' / task / 'generator.py'
spec = importlib.util.spec_from_file_location(f'audit_{task}', path)
mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
requests = [
    ('height_only', {'grid_h': 4}),
    ('width_only', {'grid_w': 5}),
    ('count_only', {'n_objects': 6}),
    ('height_plus_count', {'grid_h': 4, 'n_objects': 6}),
    ('width_plus_count', {'grid_w': 5, 'n_objects': 6}),
    ('all_three', {'grid_h': 4, 'grid_w': 5, 'n_objects': 6}),
]
rows = []
for name, overrides in requests:
    for seed in range(3):
        row = {'name': name, 'seed': seed, 'sample_index': 0, 'difficulty': 'easy', 'overrides': overrides}
        try:
            grid = mod.generate(seed, 0, difficulty='easy', **overrides)
        except Exception as exc:
            row.update(status='error', error_type=type(exc).__name__, error=str(exc))
        else:
            row.update(status='accepted', shape=[len(grid), len(grid[0])], observed=mod.observe_overrides(grid), self_check=mod.self_check(grid))
        rows.append(row)
report = {
    'task_id': task,
    'generator_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'declared_axes': mod.AXES,
    'has_incompatibility_declaration': hasattr(mod, 'INCOMPATIBLE_OVERRIDE_COMBINATIONS'),
    'results': rows,
}
outdir = root.parent / 'checks' / 'audit' / task
(outdir / 'override_joint_probe.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps(report, sort_keys=True))
