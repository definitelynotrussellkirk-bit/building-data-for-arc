#!/usr/bin/env python3
"""Hash-bound, real-Racket color-role and counterfactual audit.

Run with review_checks.py palette. A nonzero exit signals semantic findings,
not an execution failure alone. Every count is scoped to the printed seed sweep.
The rival deliberately implements the *old* color shortcut independently of
GEN.SEMANTIC_RIVALS, so adding a rival name cannot make this audit pass.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import copy
import hashlib
import importlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash
from scripts.rule_smoke import rule_application

TASK_ID = 'd9d4f0ebb48b'
GEN = importlib.import_module(f'puzzle_generators.per_puzzle.{TASK_ID}.generator')


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def legacy_palette_bbox(grid, *, all_colors=False, component_size=None):
    out = copy.deepcopy(grid)
    visited = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 or (not all_colors and not 1 <= value <= 7) or (r, c) in visited:
                continue
            queue = deque([(r, c)])
            visited.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and (nr, nc) not in visited and grid[nr][nc] == value):
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            if component_size is not None and len(cells) != component_size:
                continue
            for rr in range(min(x[0] for x in cells), max(x[0] for x in cells) + 1):
                for cc in range(min(x[1] for x in cells), max(x[1] for x in cells) + 1):
                    out[rr][cc] = value
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=32)
    parser.add_argument('--phase', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.samples <= 0:
        parser.error('--samples must be positive')
    rule = canonical_rule_source(TASK_ID)
    counts = Counter()
    unique = set()
    roles = {p: {'trigger_occurrences': Counter(), 'distractor_color_presence_per_grid': Counter()}
             for p in GEN.SCENE_PROFILES}
    witnesses = {}
    per_profile = {p: Counter() for p in GEN.SCENE_PROFILES}
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for band in ('easy', 'medium', 'hard'):
            for seed in range(args.samples):
                lesson_survives = True
                five_cell_lesson_survives = True
                for index in range(4):
                    grid = GEN.generate(seed, index, difficulty=band)
                    profile = GEN.schedule_profile(seed, index, band)
                    output = bridge.eval_text(rule_application(rule, grid))
                    rival = legacy_palette_bbox(grid)
                    five_cell_rival = legacy_palette_bbox(grid, all_colors=True, component_size=5)
                    counts['generated_pairs'] += 1
                    counts['racket_calls'] += 1
                    unique.add(fingerprint(grid))
                    analysis = GEN._analysis(grid)
                    counts['original_validator_rejections'] += bool(GEN.self_check(grid))
                    counts['mirror_mismatches'] += GEN.rule_mirror(grid) != output
                    plus_colors = [t['color'] for t in analysis['triggers']]
                    extra_colors = {grid[r][c] for r, c in analysis['remainder']}
                    roles[profile]['trigger_occurrences'].update(plus_colors)
                    roles[profile]['distractor_color_presence_per_grid'].update(extra_colors)
                    if extra_colors:
                        counts['distractor_scenes'] += 1
                        counts['distractor_scenes_without_shared_trigger_color'] += not bool(set(plus_colors) & extra_colors)
                    agrees = rival == output
                    lesson_survives &= agrees
                    five_cell_agrees = five_cell_rival == output
                    five_cell_lesson_survives &= five_cell_agrees
                    counts["five_cell_rival_correct_pairs"] += five_cell_agrees
                    counts['legacy_rival_correct_pairs'] += agrees
                    per_profile[profile]['pairs'] += 1
                    per_profile[profile]['legacy_rival_correct_pairs'] += agrees
                    per_profile[profile]['five_cell_rival_correct_pairs'] += five_cell_agrees
                    if not five_cell_agrees and 'five_cell_counterexample' not in witnesses:
                        witnesses['five_cell_counterexample'] = {
                            'band': band, 'seed': seed, 'sample_index': index, 'overrides': {},
                            'input': grid, 'actual_racket_output': output, 'rival_output': five_cell_rival,
                            'validator_findings': GEN.self_check(grid), 'documented_domain': True,
                        }
                    if not agrees and 'ordinary_counterexample' not in witnesses:
                        witnesses['ordinary_counterexample'] = {
                            'band': band, 'seed': seed, 'sample_index': index, 'overrides': {},
                            'input': grid, 'actual_racket_output': output, 'rival_output': rival,
                            'validator_findings': GEN.self_check(grid), 'documented_domain': True,
                        }
                    shift = 1 + (seed + index) % 8
                    mapping = [0] + [1 + (v - 1 + shift) % 9 for v in range(1, 10)]
                    recolor = lambda g: [[mapping[v] for v in row] for row in g]
                    permuted = recolor(grid)
                    perm_output = bridge.eval_text(rule_application(rule, permuted))
                    perm_rival = legacy_palette_bbox(permuted)
                    findings = GEN.self_check(permuted)
                    counts['racket_calls'] += 1
                    counts['permuted_pairs'] += 1
                    counts['permutation_validator_rejections'] += bool(findings)
                    counts['racket_equivariance_mismatches'] += perm_output != recolor(output)
                    counts['mirror_mismatches'] += GEN.rule_mirror(permuted) != perm_output
                    counts['legacy_rival_correct_permuted_pairs'] += perm_rival == perm_output
                    if (findings or perm_rival != perm_output) and 'permutation_counterexample' not in witnesses:
                        witnesses['permutation_counterexample'] = {
                            'band': band, 'seed': seed, 'sample_index': index, 'overrides': {},
                            'source_input': grid, 'source_racket_output': output, 'color_mapping': mapping,
                            'input': permuted, 'actual_racket_output': perm_output, 'rival_output': perm_rival,
                            'validator_findings': findings,
                            'documented_domain': not bool(findings),
                            'rule_equivariant_on_this_pair': perm_output == recolor(output),
                        }
                counts['four_demo_lessons'] += 1
                counts['legacy_rival_surviving_lessons'] += lesson_survives
                counts['five_cell_rival_surviving_lessons'] += five_cell_lesson_survives
        for pair in canonical_pairs(TASK_ID):
            output = bridge.eval_text(rule_application(rule, pair['input']))
            counts['racket_calls'] += 1
            counts['canonical_pairs'] += 1
            counts['canonical_mismatches'] += output != pair['output']
            counts['canonical_validator_rejections'] += bool(GEN.self_check(pair['input']))
            counts['canonical_legacy_rival_mismatches'] += legacy_palette_bbox(pair['input']) != output
            counts['canonical_five_cell_rival_mismatches'] += legacy_palette_bbox(pair['input'], all_colors=True, component_size=5) != output
    finally:
        bridge.close()
    failures = []
    for key in ('original_validator_rejections', 'mirror_mismatches', 'permutation_validator_rejections',
                'racket_equivariance_mismatches', 'legacy_rival_surviving_lessons', 'five_cell_rival_surviving_lessons',
                'distractor_scenes_without_shared_trigger_color', 'canonical_mismatches',
                'canonical_validator_rejections'):
        if counts[key]:
            failures.append(f'{key}={counts[key]}')
    support = set().union(*(set(x['trigger_occurrences']) for x in roles.values()))
    if support != set(range(1, 10)):
        failures.append(f'missing true-plus colors: {sorted(set(range(1, 10)) - support)}')
    counts['unique_original_inputs'] = len(unique)
    report = {
        'schema': 'task-palette-role-audit-v1', 'task_id': TASK_ID, 'phase': args.phase,
        'generator_sha256': hashlib.sha256(Path(GEN.__file__).read_bytes()).hexdigest(),
        'rule_hash': normalized_rule_hash(rule), 'rule_source_sha256': hashlib.sha256(rule.encode()).hexdigest(),
        'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'runtime_cwd': str(Path.cwd()), 'seed_range_inclusive': [0, args.samples - 1],
        'sample_indexes': [0, 1, 2, 3], 'bands': ['easy', 'medium', 'hard'],
        'sampling': 'One disjoint four-demo lesson per (band,seed). Permuted pairs are derived, not independent draws.',
        'counts': dict(sorted(counts.items())), 'per_profile': per_profile, 'color_roles': roles,
        'findings': failures, 'witnesses': witnesses, 'status': 'fail' if failures else 'pass',
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in {'witnesses', 'color_roles'}}, indent=2))
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
