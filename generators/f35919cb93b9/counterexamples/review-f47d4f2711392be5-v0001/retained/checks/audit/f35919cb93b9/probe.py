"""Reproduce validator/override findings without changing the audited source."""
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK = 'f35919cb93b9'
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_HASH = load_selected_generator(TASK, root=ROOT)


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def main():
    authority = set()
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get('task_id') == TASK:
            authority.add(row['program_solution'])
    assert len(authority) == 1
    rule = authority.pop()
    result = {'task_id': TASK, 'generator_sha256': SOURCE_HASH,
              'rule_source_sha256': hashlib.sha256(rule.encode()).hexdigest(),
              'rule_hash_declared': GEN.RULE_HASH, 'default_draws': 0,
              'default_failures': [], 'default_shapes': [], 'canonical': [],
              'overrides': [], 'degenerate': []}
    shapes = set()
    for band in ('easy', 'medium', 'hard'):
        for seed in range(32):
            for index in range(4):
                grid = GEN.generate(seed, index, difficulty=band)
                result['default_draws'] += 1
                shapes.add((len(grid), len(grid[0])))
                errors = GEN.self_check(grid, difficulty=band)
                if errors:
                    result['default_failures'].append({'seed': seed, 'sample_index': index,
                        'difficulty': band, 'input': grid, 'validation': errors})
    result['default_shapes'] = [list(s) for s in sorted(shapes)]
    for pair in canonical_pairs(TASK, root=ROOT):
        grid = pair['input']
        result['canonical'].append({'variant_index': pair.get('variant_index'),
            'split': pair['split'], 'pair_index': pair['pair_index'],
            'shape': [len(grid), len(grid[0])], 'self_check': GEN.self_check(grid)})
    base = GEN.generate(0, 0, difficulty='medium')
    cases = [{'unknown_review_axis': 9}, {'palette_kind': 'not-a-palette'},
             {'palette_size': 9}, {'n_distinct_colors': 9},
             {'position_bias': 'corner'}, {'density': 'dense'},
             {'texture': 'unknown-texture'}]
    for overrides in cases:
        row = {'overrides': overrides}
        try:
            grid = GEN.generate(0, 0, difficulty='medium', **overrides)
            row.update({'accepted': True, 'unchanged_from_control': grid == base,
                        'input_sha256': digest(grid), 'self_check': GEN.self_check(grid)})
        except Exception as exc:
            row.update({'accepted': False, 'error': type(exc).__name__ + ': ' + str(exc)})
        result['overrides'].append(row)
    for texture in GEN.DEGENERATE_TEXTURES:
        grid = GEN.generate(0, 0, difficulty='medium', texture=texture)
        result['degenerate'].append({'texture': texture, 'input': grid,
            'self_check_without_meta': GEN.self_check(grid),
            'self_check_with_meta': GEN.self_check(grid, meta={'texture': texture})})
        if texture == 'no_pivot':
            (OUT / 'no-pivot-input.json').write_text(json.dumps(grid) + '\n')
    (OUT / 'probe.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'generator_sha256': SOURCE_HASH,
        'default_draws': result['default_draws'],
        'default_failures': len(result['default_failures']),
        'silent_override_acceptances': sum(r['accepted'] and r.get('unchanged_from_control', False)
                                          for r in result['overrides']),
        'metadata_bypass_cases': sum(not r['self_check_with_meta'] and bool(r['self_check_without_meta'])
                                     for r in result['degenerate'])}))


if __name__ == '__main__':
    main()
