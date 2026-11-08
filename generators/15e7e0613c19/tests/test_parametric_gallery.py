"""Prototype-only checks; independent of the production sampler implementation."""
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root
from arc_repl.racket_bridge import RacketBridge

ROOT = find_root(__file__)
SOURCE = ROOT / 'generators/15e7e0613c19/workspace/parametric/prototype.py'
SPEC = importlib.util.spec_from_file_location('packing_parametric_prototype', SOURCE)
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


def test_default_exact_and_only_primary_comparator_changes():
    original = p.canonical_program(ROOT)
    assert p.instantiate(original) == original
    alternate = p.instantiate(original, 'descending')
    assert alternate.replace('(> (obj-size a) (obj-size b))', p.PRIMARY) == original
    with pytest.raises(ValueError):
        p.instantiate(original, 'random')


def test_deterministic_episode_parameter_and_fixture_lawfulness():
    assert {p.parameters(s)['area_order'] for s in (0, 1)} == set(p.AREA_ORDERS)
    for seed in (0, 1):
        assert p.fixture_inputs(seed) == p.fixture_inputs(seed)
        for grid in p.fixture_inputs(seed):
            assert len(grid) == 9 and all(len(row) == 25 for row in grid)
            for color in {c for row in grid for c in row} - {0}:
                cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
                todo = [next(iter(cells))]
                seen = set(todo)
                while todo:
                    r, c = todo.pop()
                    for point in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                        if point in cells and point not in seen:
                            seen.add(point)
                            todo.append(point)
                assert seen == cells


def test_racket_default_matches_all_main_canonical_pairs():
    bridge = RacketBridge()
    try:
        program = p.canonical_program(ROOT)
        pairs = canonical_pairs(p.TASK_ID, root=ROOT, labeled_only=True)
        assert len(pairs) == 3
        for pair in pairs:
            assert p.execute(bridge, p.instantiate(program), pair['input']) == pair['output']
    finally:
        bridge.shutdown()


def test_racket_episode_rivals_ties_and_public_mask():
    bridge = RacketBridge()
    try:
        program = p.canonical_program(ROOT)
        for seed in (0, 1):
            record = p.episode(seed, program, bridge)
            assert len(record['train']) == 3 and len(record['test']) == 1
            assert record['parameters'] == p.parameters(seed)
            assert all(r['demo_differences'] and r['query_differs'] for r in record['rivals'])
            public = p.public_challenge(record)
            assert set(public) == {'train', 'test'}
            assert set(public['test'][0]) == {'input'}
            tie_input = record['train'][1]['input']
            assert p.execute(bridge, p.instantiate(program, 'ascending'), tie_input) == p.execute(
                bridge, p.instantiate(program, 'descending'), tie_input)
    finally:
        bridge.shutdown()
