"""Read-only source-bound audit; Python mirrors are not Racket evidence."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def component_rule(module, grid):
    h, w = len(grid), len(grid[0])
    output = [[0] * w for _ in range(h)]
    for color, cells in module._components(grid):
        if any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells):
            for r, c in cells:
                output[r][c] = color
    return output


def color_border_rival(grid):
    h, w = len(grid), len(grid[0])
    colors = {grid[r][c] for r in range(h) for c in range(w)
              if r in (0, h - 1) or c in (0, w - 1)} - {0}
    return [[color if color in colors else 0 for color in row] for row in grid]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--context', required=True, type=Path)
    parser.add_argument('--shared-runtime', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--racket-report', type=Path,
                        help='independently executed official report to verify, never generated here')
    parser.add_argument('--racket-exit-status', type=int,
                        help='exit status supplied by the official executor')
    args = parser.parse_args()
    sys.path.insert(0, str(args.shared_runtime.resolve()))
    source = args.context / 'generator.py'
    spec = importlib.util.spec_from_file_location('audited_generator', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    canonical = json.loads((args.context / 'canonical_task.json').read_text())
    generated = module.generate(0, 0, palette_size=3, n_distinct_colors=3)
    authored = [[0] * 7 for _ in range(5)]
    for r, c, color in [(0, 0, 1), (0, 6, 2), (2, 2, 1), (2, 4, 3)]:
        authored[r][c] = color
    rows = []
    for seed in range(5):
        a = module.generate(seed, 0, palette_size=3, n_distinct_colors=3)
        b = module.generate(seed, 0, palette_size=6, n_distinct_colors=6)
        rows.append({'seed': seed, 'sample_index': 0, 'difficulty': None,
                     'overrides': {'palette_size': 3, 'n_distinct_colors': 3},
                     'observed_nonzero_colors': sorted(set(sum(a, [])) - {0}),
                     'self_check': module.self_check(a), 'identical_to_controls_6': a == b})
    rejected_axes = []
    for overrides in [{'grid_h': 5}, {'grid_w': 7}, {'n_border': 1}, {'n_interior': 1}]:
        try:
            module.generate(0, 0, **overrides)
            error = None
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
        rejected_axes.append({'seed': 0, 'sample_index': 0, 'difficulty': None,
                              'overrides': overrides, 'exception': error})
    samples = []
    for band in ('easy', 'medium', 'hard'):
        errors, mismatches = [], []
        for seed in range(30):
            try:
                grid = module.generate(seed, 0, difficulty=band)
                errors.extend({'seed': seed, 'errors': module.self_check(grid)}
                              for _ in [0] if module.self_check(grid))
                if component_rule(module, grid) != color_border_rival(grid):
                    mismatches.append(seed)
            except Exception as exc:
                errors.append({'seed': seed, 'exception': str(exc)})
        samples.append({'difficulty': band, 'seeds': '0..29', 'sample_index': 0,
                        'attempts': 30, 'errors': errors,
                        'python_component_mirror_vs_color_rival_mismatches': mismatches})
    result = {'task_id': module.TASK_ID, 'generator_sha256': sha(source.read_bytes()),
              'canonical_task_json_sha256': sha((args.context / 'canonical_task.json').read_bytes()),
              'rule_program_sha256_utf8': sha(canonical['program_solution'].encode()),
              'racket_execution': 'Not performed by this probe; root must independently apply official runtime.',
              'palette_controls': rows, 'advertised_values_rejected': rejected_axes,
              'finite_support_probe': samples,
              'input_order': ['generated seed0 palette3 controls', 'authored repeated-color wider-rule-domain witness'],
              'witnesses': [
                  {'input_index': 0, 'origin': 'generated', 'seed': 0, 'sample_index': 0,
                   'difficulty': None, 'overrides': {'palette_size': 3, 'n_distinct_colors': 3},
                   'self_check': module.self_check(generated),
                   'component_rule_python_mirror': component_rule(module, generated),
                   'color_border_rival_output': color_border_rival(generated)},
                  {'input_index': 1, 'origin': 'authored wider rule domain; not generated or validator-accepted',
                   'self_check': module.self_check(authored),
                   'component_rule_python_mirror': component_rule(module, authored),
                   'color_border_rival_output': color_border_rival(authored)}]}
    if args.racket_report is not None:
        official = json.loads(args.racket_report.read_text())
        assert official['task_id'] == module.TASK_ID
        assert official['generator_sha256'] == result['generator_sha256']
        assert official['executed_rule_hash'] == result['rule_program_sha256_utf8'][:12]
        assert official['catalog_rule_hash'] == official['executed_rule_hash']
        assert official['rule_hash_matches_catalog'] is True
        assert len(official['results']) == 2
        input_grids = [generated, authored]
        for index, row in enumerate(official['results']):
            assert row['index'] == index and row['input'] == input_grids[index]
            assert row['valid_output'] is True and row['error'] is None
            for key in ('input', 'output'):
                expected_hash = sha(json.dumps(row[key], sort_keys=True,
                                               separators=(',', ':')).encode())
                assert expected_hash == row[key + '_sha256']
            assert row['output'] == result['witnesses'][index]['component_rule_python_mirror']
            result['witnesses'][index]['official_racket_output'] = row['output']
            result['witnesses'][index]['official_input_sha256'] = row['input_sha256']
            result['witnesses'][index]['official_output_sha256'] = row['output_sha256']
            result['witnesses'][index]['rival_agrees_with_official_output'] = (
                row['output'] == result['witnesses'][index]['color_border_rival_output'])
        result['racket_execution'] = 'Independently executed official report verified for these two inputs only.'
        result['official_reference_validation'] = {
            'report_sha256': sha(args.racket_report.read_bytes()),
            'executed_rule_hash': official['executed_rule_hash'],
            'catalog_rule_hash': official['catalog_rule_hash'],
            'rule_text_sha256': official['rule_text_sha256'],
            'generator_sha256': official['generator_sha256'],
            'command': official['command'], 'cwd': official['cwd'],
            'executor_reported_exit_status': args.racket_exit_status,
            'verified_inputs': 2, 'input_order_and_hashes_verified': True,
            'scope': 'Two official applies; the separate 90-draw support probe uses Python mirrors.'}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'input.json').write_text(json.dumps([generated, authored], indent=2) + '\n')
    (args.out / 'probe_results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'generator_sha256': result['generator_sha256'],
                      'rule_program_sha256_utf8': result['rule_program_sha256_utf8'],
                      'witness_count': 2, 'normal_draws': 90,
                      'palette3_seed0_colors': len(set(sum(generated, [])) - {0})}))


if __name__ == '__main__':
    main()
