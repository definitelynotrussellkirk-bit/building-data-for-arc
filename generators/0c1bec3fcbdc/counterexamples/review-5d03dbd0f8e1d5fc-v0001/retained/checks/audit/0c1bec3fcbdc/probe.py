"""Read-only targeted support/rotation audit for the selected baseline source.
Run from WORK/repo with PYTHONPATH=shared/runtime.
"""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

from reviewer_support import canonical_pairs

TASK = '0c1bec3fcbdc'
SOURCE_HASH = '17a8ac658e06089cdbf1fe3837b9de637c47ac4ccb75b9b2e79f74d60c2edbb5'
ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent


def runs(grid, horizontal=False):
    h, w = len(grid), len(grid[0])
    outer, inner = (h, w) if horizontal else (w, h)
    for a in range(outer):
        b = 0
        while b < inner:
            rc = lambda x: (a, x) if horizontal else (x, a)
            r, c = rc(b)
            if grid[r][c] != 6:
                b += 1
                continue
            end = b
            while end + 1 < inner:
                rr, cc = rc(end + 1)
                if grid[rr][cc] != 6:
                    break
                end += 1
            yield end-b+1, rc(b), rc(end)
            b = end+1


def bounded_length_rival(grid):
    out = [row[:] for row in grid]
    for length, first, last in runs(grid):
        if 3 <= length <= 5:
            for r, c in (first, last):
                out[r][c] = 1
    return out


def both_orientations_rival(grid):
    out = [row[:] for row in grid]
    for horizontal in (False, True):
        for length, first, last in runs(grid, horizontal):
            if length >= 3:
                for r, c in (first, last):
                    out[r][c] = 1
    return out


def main():
    source = ROOT / 'generators' / TASK / 'generator.py'
    actual_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual_hash != SOURCE_HASH:
        raise RuntimeError(f'Source changed: {actual_hash}')
    spec = importlib.util.spec_from_file_location('audit_target', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # An accepted profile with the longest validator-supported magenta run.
    witness = [[0] * 10 for _ in range(8)]
    for row in range(6):
        witness[row][1] = 6
    for row in range(4, 7):
        witness[row][4] = 6
    for row in range(1, 3):
        witness[row][8] = 6

    canonical = canonical_pairs(TASK, root=ROOT)
    canonical_fits = {
        name: sum(rival(pair['input']) == pair['output'] for pair in canonical)
        for name, rival in [('bounded_lengths_3_to_5', bounded_length_rival),
                            ('cap_horizontal_too', both_orientations_rival)]
    }
    cases = []
    for seed, size, count, scene in itertools.product(
        (0, 73), module.SIZE_PROFILES, range(2, 5), module.SCENE_PROFILES
    ):
        kwargs = dict(size_profile=size, n_runs=count, scene_profile=scene)
        grid = module.generate(seed, 0, difficulty='medium', **kwargs)
        cases.append({
            'seed': seed, 'sample_index': 0, 'difficulty': 'medium',
            'overrides': kwargs, 'self_check': module.self_check(grid),
            'observed': module.observe_overrides(grid),
            'qualifying_lengths': sorted(length for length, _, _ in runs(grid) if length >= 3),
            'bounded_rival_agrees_with_python_mirror': bounded_length_rival(grid) == module.rule_mirror(grid),
        })
    window = [module.generate(73, index, difficulty='medium') for index in range(5)]
    payload = [witness, *window]
    for filename, data in [
        ('input.json', payload),
        ('prelabel_probe.json', {
            'task_id': TASK, 'generator_sha256': actual_hash,
            'rule_hash': module.RULE_HASH,
            'manual_witness': {
                'payload_index': 0, 'origin': 'hand-authored; no seed or override',
                'seed': None, 'sample_index': None, 'overrides': None,
                'self_check': module.self_check(witness),
                'strict_canonical_like': module.strict_canonical_like(witness),
                'observed': module.observe_overrides(witness),
                'qualifying_lengths': sorted(length for length, _, _ in runs(witness) if length >= 3),
            },
            'canonical_pair_count': len(canonical), 'canonical_rival_fits': canonical_fits,
            'generated_support_probes': cases,
            'rotation_window': [{
                'payload_index': index+1, 'seed': 73, 'sample_index': index,
                'difficulty': 'medium', 'overrides': {},
                'self_check': module.self_check(grid),
                'observed': module.observe_overrides(grid),
            } for index, grid in enumerate(window)],
            'python_labels_are_not_reference_execution': True,
        }),
    ]:
        with (OUT/filename).open('x') as handle:
            json.dump(data, handle, indent=2)
    print(json.dumps({
        'generator_sha256': actual_hash,
        'witness_self_check': module.self_check(witness),
        'witness_observed': module.observe_overrides(witness),
        'canonical_rival_fits': canonical_fits,
        'generated_probe_count': len(cases),
        'generated_invalid_count': sum(bool(case['self_check']) for case in cases),
        'generated_target_lengths': sorted({n for case in cases for n in case['qualifying_lengths']}),
        'bounded_rival_disagreements_with_python_mirror': sum(not case['bounded_rival_agrees_with_python_mirror'] for case in cases),
        'window_profiles': [module.observe_overrides(grid)['scene_profile'] for grid in window],
    }, indent=2))


if __name__ == '__main__':
    main()
