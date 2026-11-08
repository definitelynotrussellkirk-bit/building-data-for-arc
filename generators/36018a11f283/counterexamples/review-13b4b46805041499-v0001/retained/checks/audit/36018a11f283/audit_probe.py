from __future__ import annotations
import hashlib, importlib.util, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2] / 'repo'
sys.path.insert(0, str(REPO / 'shared/runtime'))
GEN_PATH = REPO / 'generators/36018a11f283/generator.py'
spec = importlib.util.spec_from_file_location('audit_36018a11f283', GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)


def compact_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()


def marked_region_count(grid):
    count = 0
    for cells in gen._regions_not_wall(grid):
        counts = {color: sum(1 for r, c in cells if grid[r][c] == color) for color in (2, 3, 4)}
        if max(counts.values()) > 0:
            count += 1
    return count


def run_case(name, kwargs):
    try:
        grid = gen.generate(0, 0, **kwargs)
        return {
            'name': name,
            'kwargs': kwargs,
            'status': 'returned',
            'shape': [len(grid), len(grid[0])],
            'input_sha256': compact_hash(grid),
            'marked_region_count': marked_region_count(grid),
            'self_check_errors': gen.self_check(grid),
        }
    except Exception as exc:
        return {
            'name': name,
            'kwargs': kwargs,
            'status': 'raised',
            'exception_type': type(exc).__name__,
            'exception': str(exc),
        }

cases = [
    run_case('baseline', {}),
    run_case('advertised_grid_h_min', {'grid_h': 8}),
    run_case('advertised_grid_w_max', {'grid_w': 15}),
    run_case('advertised_n_compartments_9', {'n_compartments': 9}),
    run_case('advertised_palette_kind_warm', {'palette_kind': 'warm_markers'}),
    run_case('advertised_texture_warm', {'texture': 'warm_markers'}),
    run_case('advertised_texture_no_walls', {'texture': 'no_walls'}),
    run_case('advertised_texture_no_markers', {'texture': 'no_markers'}),
    run_case('advertised_texture_all_tied', {'texture': 'all_tied'}),
    run_case('unknown_override', {'not_an_axis': 17}),
]
by_name = {case['name']: case for case in cases}
assert by_name['advertised_grid_h_min']['status'] == 'raised'
assert by_name['advertised_grid_w_max']['status'] == 'raised'
assert by_name['advertised_n_compartments_9']['marked_region_count'] != 9
assert by_name['advertised_texture_no_walls']['self_check_errors']
assert by_name['advertised_texture_no_markers']['self_check_errors']
assert by_name['advertised_texture_all_tied']['self_check_errors']
assert by_name['unknown_override']['status'] == 'returned'

# Controls that are advertised as meaningful but are never consumed produce the
# exact same grid at a fixed seed/sample.
base = gen.generate(0, 0)
ignored_equalities = {}
for label, kwargs in {
    'palette_kind_warm': {'palette_kind': 'warm_markers'},
    'palette_kind_cool': {'palette_kind': 'cool_markers'},
    'texture_warm': {'texture': 'warm_markers'},
    'n_compartments_9': {'n_compartments': 9},
    'unknown_override': {'not_an_axis': 17},
}.items():
    ignored_equalities[label] = gen.generate(0, 0, **kwargs) == base

racket = json.loads((HERE / 'no_walls_racket.json').read_text())
result = {
    'schema': 'audit-probe-v1',
    'task_id': gen.TASK_ID,
    'generator_sha256': hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'version': gen.VERSION,
    'has_rule_hash_constant': hasattr(gen, 'RULE_HASH'),
    'declared_axes': gen.AXES,
    'finding': 'The advertised exact-control surface is not authoritative: valid endpoints raise, several controls are ignored, unknown controls are accepted, and all advertised degenerate textures return inputs rejected by self_check.',
    'cases': cases,
    'ignored_controls_equal_baseline': ignored_equalities,
    'no_walls_racket': {
        'input_path': 'WORK/checks/audit/36018a11f283/no_walls_input.json',
        'racket_path': 'WORK/checks/audit/36018a11f283/no_walls_racket.json',
        'generator_domain': racket['results'][0]['generator_domain'],
        'valid_racket_output': racket['results'][0]['valid_output'],
        'output_sha256': racket['results'][0]['output_sha256'],
    },
}
(HERE / 'audit_probe.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({
    'task_id': result['task_id'],
    'generator_sha256': result['generator_sha256'],
    'has_rule_hash_constant': result['has_rule_hash_constant'],
    'ignored_controls_equal_baseline': result['ignored_controls_equal_baseline'],
    'case_statuses': {c['name']: c['status'] for c in cases},
}, indent=2))
