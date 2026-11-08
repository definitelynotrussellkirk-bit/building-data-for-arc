"""Source-bound findings-only probe; run through the public review.py wrapper.

Generated-sample labels are the task's Python mirror, explicitly not Racket.
The separate public arcpuzzles apply invocation supplies witness authority.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = '3ae696dbdba9'
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def repeated_row_bridge(grid):
    """Bridge only identical row footprints of each monochrome 4-component.

    This never uses generator profiles, dimensions, colors, or output labels.
    Distinct endpoint footprints do not provide a bridge under this rival.
    """
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    seen = set()
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            seen.add((sr, sc))
            stack = [(sr, sc)]
            rows = defaultdict(set)
            while stack:
                r, c = stack.pop()
                rows[r].add(c)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            patterns = defaultdict(list)
            for r, cols in rows.items():
                patterns[tuple(sorted(cols))].append(r)
            for cols, occupied_rows in patterns.items():
                if len(occupied_rows) >= 2:
                    for r in range(min(occupied_rows), max(occupied_rows) + 1):
                        for c in cols:
                            out[r][c] = color
    return out


def dump(name, obj):
    path = HERE / name
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def compact_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()


def main():
    gen, source, source_sha = load_selected_generator(TASK, root=ROOT)
    canonical = canonical_pairs(TASK, root=ROOT)
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
            if json.loads(line).get('task_id') == TASK]
    assert len(rows) == 1
    rule = rows[0]['program_solution']
    rule_sha = hashlib.sha256(' '.join(rule.split()).encode()).hexdigest()
    assert gen.RULE_HASH == rule_sha[:12]
    declared = dict(gen.LESSON_COMPETITORS)
    assert set(declared) == set(gen.SEMANTIC_RIVALS)
    rivals = {**declared, 'audit_repeated_row_bridge': repeated_row_bridge}
    canonical_fit = {name: sum(fn(p['input']) == p['output'] for p in canonical)
                     for name, fn in rivals.items()}
    report = {
        'schema': 'arc-source-bound-audit-v1', 'task_id': TASK,
        'source_path': str(source.relative_to(ROOT)), 'source_sha256': source_sha,
        'rule_hash': gen.RULE_HASH, 'normalized_rule_sha256': rule_sha,
        'rival_definition': 'Within each monochrome cardinal component, find identical sets of occupied columns on multiple rows; copy each such set into every intervening row. All remaining cells stay unchanged.',
        'canonical_pair_count': len(canonical), 'canonical_fit': canonical_fit,
        'canonical_python_mirror_matches': sum(gen.rule_mirror(p['input']) == p['output'] for p in canonical),
        'declared_rivals_loaded_from_current_module': list(declared),
        'sampling': {
            'method': 'Direct task-local generated sample census, not the production lesson sampler',
            'label_authority': 'Python mirror only for generated samples; supplied canonical labels for canonical fit',
            'bands': ['easy', 'medium', 'hard'], 'lessons_per_band': 100,
            'lesson_seed_formula': '810000 + band_index * 1000 + lesson_index',
            'sample_index_formula': '(lesson_index % len(SCHEDULE_PROFILES)) + offset',
            'lesson_index_range': [0, 99], 'offset_range': [0, gen.EXAMPLES_NEEDED],
            'demo_count': gen.EXAMPLES_NEEDED, 'query_count': 1,
            'overrides': {}, 'schedule_profile_names': list(gen.SCHEDULE_PROFILES),
        },
        'bands': {}, 'failures': [], 'override_probe': {},
        'limitations': [
            'Generated census outputs are Python-mirror labels, not a Racket rerun of all draws.',
            'The rival agrees with the sampled queries too; this is an uncovered-lawful-morphology shortcut, not a demonstrated mislabeled generated example or an in-sample differing-query teaching failure.',
            'Finite seeds do not establish universal behavior or downstream model exploitation.',
            'This audit changes no generator, reference rule, approval, or earlier audit status.',
        ],
    }
    all_unique = set()
    for band_i, band in enumerate(report['sampling']['bands']):
        agreements = Counter({name: 0 for name in rivals})
        demo_survivors = Counter({name: 0 for name in rivals})
        ambiguous_queries = Counter({name: 0 for name in rivals})
        profiles = Counter()
        starts = Counter()
        unique = set()
        for lesson in range(100):
            seed = 810000 + band_i * 1000 + lesson
            start = lesson % len(gen.SCHEDULE_PROFILES)
            starts[start] += 1
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                index = start + offset
                grid = gen.generate(seed, index, difficulty=band)
                errors = gen.self_check(grid)
                if errors:
                    report['failures'].append({'kind': 'self_check', 'seed': seed, 'sample_index': index,
                                               'band': band, 'overrides': {}, 'errors': errors, 'input': grid})
                expected = gen.rule_mirror(grid)
                pairs.append({'input': grid, 'output': expected})
                profiles[gen.schedule_profile(seed, index, band)] += 1
                unique.add(compact_hash(grid))
                for name, fn in rivals.items():
                    agreements[name] += fn(grid) == expected
            for name, fn in rivals.items():
                survives = all(fn(p['input']) == p['output'] for p in pairs[:-1])
                demo_survivors[name] += survives
                ambiguous_queries[name] += survives and fn(pairs[-1]['input']) != pairs[-1]['output']
        all_unique.update(unique)
        report['bands'][band] = {
            'generated_input_count': 100 * (gen.EXAMPLES_NEEDED + 1),
            'unique_inputs': len(unique), 'schedule_profile_counts': dict(profiles),
            'cyclic_start_counts': dict(starts), 'rival_agreements': dict(agreements),
            'visible_demo_survivals_out_of_100': dict(demo_survivors),
            'differing_query_ambiguities_out_of_100': dict(ambiguous_queries),
        }
    report['generated_input_count'] = sum(b['generated_input_count'] for b in report['bands'].values())
    report['generated_unique_inputs'] = len(all_unique)

    # Focused exact-axis probes, not a rerun of the inherited full matrix.
    override_cases = [
        {'grid_h': 10}, {'grid_h': 16}, {'grid_w': 12}, {'grid_w': 20},
        {'component_count': 2}, {'component_count': 5}, {'max_gap_columns': 1}, {'max_gap_columns': 3},
        {'gap_profile': 'short'}, {'gap_profile': 'mixed'}, {'gap_profile': 'long'},
        {'control_mode': 'none'}, {'control_mode': 'one'}, {'color_mode': 'distinct'},
        {'color_mode': 'reused'}, {'edge_profile': 'interior'}, {'edge_profile': 'touching'},
    ]
    for band_i, band in enumerate(report['sampling']['bands']):
        cases = []
        for case_i, overrides in enumerate(override_cases):
            seed, index = 820000 + band_i * 1000 + case_i, case_i
            grid = gen.generate(seed, index, difficulty=band, **overrides)
            observed = gen.observe_overrides(grid)
            cases.append({'seed': seed, 'sample_index': index, 'overrides': overrides,
                          'self_check': gen.self_check(grid),
                          'observed_overrides': {k: observed[k] for k in overrides},
                          'rival_matches_python_mirror': repeated_row_bridge(grid) == gen.rule_mirror(grid)})
        report['override_probe'][band] = cases

    # 10x15 canonical-profile scene: replace the ring by an asymmetric eight-cell
    # connected shape with unequal endpoint footprints, retain C and T controls.
    grid = [[0] * 15 for _ in range(10)]
    asymmetric = ((0, 0), (0, 1), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (3, 2))
    c_shape = ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2))
    t_control = ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))
    for cells, r0, c0, color in ((asymmetric, 1, 1, 2), (c_shape, 1, 8, 3), (t_control, 6, 5, 4)):
        for dr, dc in cells:
            grid[r0 + dr][c0 + dc] = color
    rival = repeated_row_bridge(grid)
    mirror = gen.rule_mirror(grid)
    differences = [[r, c, mirror[r][c], rival[r][c]] for r in range(len(grid))
                   for c in range(len(grid[0])) if mirror[r][c] != rival[r][c]]
    report['witness'] = {
        'construction': 'Deterministic hand-constructed grammar-valid 10x15 scene; no seed, sample index, or override draw is claimed.',
        'seed': None, 'sample_index': None, 'overrides': None,
        'input_path': 'WORK/checks/audit/3ae696dbdba9/input.json',
        'input_grid_sha256_compact_json': compact_hash(grid),
        'self_check': gen.self_check(grid),
        'strict_canonical_like': gen.strict_canonical_like(grid),
        'observed_axes': gen.observe_overrides(grid),
        'python_mirror_output': mirror, 'rival_output': rival,
        'python_mirror_vs_rival_differences_zero_based_row_col_expected_rival': differences,
        'racket_verification': 'Pending public arcpuzzles apply; no Racket claim from this probe.'
    }
    dump('input.json', grid)
    dump('probe_report.json', report)
    assert canonical_fit['audit_repeated_row_bridge'] == len(canonical)
    assert all(b['rival_agreements']['audit_repeated_row_bridge'] == b['generated_input_count'] for b in report['bands'].values())
    assert not report['failures']
    assert all(not c['self_check'] and c['rival_matches_python_mirror'] for cases in report['override_probe'].values() for c in cases)
    assert gen.self_check(grid) == [] and gen.strict_canonical_like(grid) == []
    assert differences == [[2, 2, 2, 0]]
    print(json.dumps({'source_sha256': source_sha, 'rule_hash': gen.RULE_HASH,
                      'canonical_rival_fit': f'{canonical_fit["audit_repeated_row_bridge"]}/{len(canonical)}',
                      'generated_mirror_agreement': report['generated_input_count'],
                      'unique_inputs': report['generated_unique_inputs'], 'override_mirror_agreement': 51,
                      'witness_self_check': report['witness']['self_check'],
                      'witness_strict_canonical_like': report['witness']['strict_canonical_like'],
                      'witness_differences_python_only': differences}))

if __name__ == '__main__':
    main()
