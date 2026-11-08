from __future__ import annotations
import hashlib, importlib.util, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2] / 'repo'
sys.path.insert(0, str(REPO / 'shared/runtime'))
GEN_PATH = REPO / 'generators/9d488d6a3875/generator.py'
spec = importlib.util.spec_from_file_location('audit_9d488d6a3875', GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)


def fill(grid, orientation_order):
    original = [row[:] for row in grid]
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for orientation in orientation_order:
        if orientation == 'row':
            for r in range(h):
                for color in dict.fromkeys(v for v in original[r] if v):
                    hits = [c for c in range(w) if original[r][c] == color]
                    if len(hits) == 2:
                        a, b = min(hits), max(hits)
                        if all(original[r][c] in (0, color) for c in range(a, b + 1)):
                            for c in range(a, b + 1):
                                out[r][c] = color
        else:
            for c in range(w):
                for color in dict.fromkeys(original[r][c] for r in range(h) if original[r][c]):
                    hits = [r for r in range(h) if original[r][c] == color]
                    if len(hits) == 2:
                        a, b = min(hits), max(hits)
                        if all(original[r][c] in (0, color) for r in range(a, b + 1)):
                            for r in range(a, b + 1):
                                out[r][c] = color
    return out

crossing = json.loads((HERE / 'crossing_input.json').read_text())
racket = json.loads((HERE / 'crossing_racket.json').read_text())
row_first = fill(crossing, ('row', 'col'))
col_first = fill(crossing, ('col', 'row'))
assert row_first == racket['results'][0]['output']
assert row_first != col_first

bands = ('easy', 'medium', 'hard')
samples = []
all_equal = True
all_valid = True
for band_index, band in enumerate(bands):
    for offset in range(100):
        seed = 910_000 + band_index * 10_000 + offset
        grid = gen.generate(seed, seed * 37 + 9, difficulty=band)
        canonical = fill(grid, ('row', 'col'))
        rival = fill(grid, ('col', 'row'))
        errors = gen.self_check(grid)
        all_equal &= canonical == rival
        all_valid &= errors == []
        samples.append({
            'band': band,
            'seed': seed,
            'sample_index': seed * 37 + 9,
            'input_sha256': hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest(),
            'row_first_equals_col_first': canonical == rival,
            'self_check_errors': errors,
            'observed': gen.observe_overrides(grid),
        })

result = {
    'schema': 'audit-probe-v1',
    'task_id': gen.TASK_ID,
    'generator_sha256': hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'version': gen.VERSION,
    'declared_rule_hash': gen.RULE_HASH,
    'finding': 'The production domain forbids crossing spans, so column-before-row is indistinguishable from row-before-column on every generated sample even though the canonical rule differs at crossings.',
    'sample_count': len(samples),
    'all_generated_samples_valid': all_valid,
    'all_generated_samples_match_column_first_rival': all_equal,
    'samples': samples,
    'crossing_witness': {
        'input_path': 'WORK/checks/audit/9d488d6a3875/crossing_input.json',
        'racket_path': 'WORK/checks/audit/9d488d6a3875/crossing_racket.json',
        'generator_domain_status': racket['results'][0]['generator_domain'],
        'row_first_output': row_first,
        'column_first_output': col_first,
        'differing_cell': {'row': 3, 'col': 4, 'row_first': row_first[3][4], 'column_first': col_first[3][4]},
    },
}
(HERE / 'audit_probe.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('task_id','generator_sha256','sample_count','all_generated_samples_valid','all_generated_samples_match_column_first_rival')}, indent=2))
