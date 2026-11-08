"""Source-bound row-bridge audit; Python search, then public Racket confirmation."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = '2b3472c73d30'
EXPECTED = 'ad402fc1ed1aab6efd2cd5ffb3363ca4f0e0fae10ab6509a0fc45c18772e8bfa'
BASE = Path(__file__).resolve().parent


def audit_fill_any_span(grid):
    """Plausible audit-added rival: fill zero gaps between extrema of any repeated color.

    It omits the exact-two and no-blocker conditions but preserves nonzero cells.
    This rival is not falsely attributed to generator declarations.
    """
    result = deepcopy(grid)
    for r, row in enumerate(grid):
        for color in sorted(set(row) - {0}):
            columns = [c for c, value in enumerate(row) if value == color]
            if len(columns) >= 2:
                for c in range(min(columns), max(columns) + 1):
                    if grid[r][c] == 0:
                        result[r][c] = color
    return result


def main():
    root = find_root(__file__)
    module, source, digest = load_selected_generator(TASK, root=root)
    assert digest == EXPECTED, 'Audited source changed; choose a new evidence directory'
    description = Catalog(root).describe(TASK)
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    canonical_results = [{'variant': p['variant'], 'split': p['split'],
                          'pair_index': p['pair_index'],
                          'rival_matches': audit_fill_any_span(p['input']) == p['output'],
                          'mirror_matches': module.rule_mirror(p['input']) == p['output']}
                         for p in canonical]
    # Respect live declarations rather than silently substituting a copied list.
    declarations = {attr: list(getattr(module, attr, {}).keys())
                    for attr in ('CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS')}
    missing = [attr for attr in declarations if not hasattr(module, attr)]
    records, first = [], None
    unique = set()
    for seed in range(64):
        pairs = []
        for index in range(4):
            grid = module.generate(seed=seed, sample_index=index, difficulty='medium')
            errors = module.self_check(grid)
            assert not errors, (seed, index, errors)
            output = module.rule_mirror(grid)
            rival = audit_fill_any_span(grid)
            unique.add(hashlib.sha256(json.dumps(grid, sort_keys=True).encode()).hexdigest())
            pairs.append({'sample_index': index, 'input': grid,
                          'python_mirror_output': output, 'audit_rival_output': rival,
                          'rival_matches_mirror': rival == output,
                          'validator_errors': errors,
                          'scene_family': module.observe_overrides(grid)['scene_family']})
        fits = all(p['rival_matches_mirror'] for p in pairs[:3])
        disagreement = not pairs[3]['rival_matches_mirror']
        records.append({'seed': seed, 'sample_indices': [0, 1, 2, 3],
                        'demo_matches': [p['rival_matches_mirror'] for p in pairs[:3]],
                        'rival_fits_all_demos': fits,
                        'rival_disagrees_query': disagreement,
                        'ambiguous_under_audit_rival': fits and disagreement})
        if fits and disagreement and first is None:
            first = {'seed': seed, 'difficulty': 'medium', 'n_train': 3, 'n_test': 1,
                     'sample_index': 0, 'overrides': {}, 'pairs': pairs}
    result = {'task_id': TASK, 'generator_sha256': digest,
              'rule_hash': description['rule_hash'],
              'scope': 'Python mirror search; requires retained public canonical Racket confirmation',
              'canonical_results': canonical_results,
              'live_declarations': declarations, 'missing_declarations': missing,
              'lesson_hook_declared': hasattr(module, 'lesson_identifiable'),
              'audit_added_rival': 'audit_fill_any_span',
              'episodes_searched': len(records), 'seed_range_inclusive': [0, 63],
              'samples_per_episode': 4, 'total_grid_evaluations': 256,
              'unique_inputs': len(unique),
              'python_mirror_ambiguous_lessons': sum(p['ambiguous_under_audit_rival'] for p in records),
              'records': records, 'first_witness': first}
    (BASE / 'python-search.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    if first:
        (BASE / 'witness-inputs.json').write_text(json.dumps({'inputs': [p['input'] for p in first['pairs']]}) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','first_witness')}, sort_keys=True))
    print(json.dumps({'first_witness_seed': first['seed'] if first else None}))


if __name__ == '__main__':
    main()
