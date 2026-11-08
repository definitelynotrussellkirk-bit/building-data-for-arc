"""Behavioral regression checks for the rotation-only jigsaw family."""
from pathlib import Path
from collections import Counter
import copy
import importlib.util
import pytest

HOME = Path(__file__).resolve().parents[1]


def load(name, path):
    assert path.is_file(), f"Missing authored source: {path.name}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def adapter():
    return load('_7b_test_adapter', HOME / 'workspace/parametric/adapter.py')


def turn(grid):
    return [list(row) for row in zip(*grid[::-1])]


def literal_case():
    # The singleton 7 at (2,2) touches the main 7 piece only diagonally.
    answer = [[int(c) for c in row] for row in
              ['577999', '779999', '747939', '444333', '444443', '444333']]
    canvas = [[0] * 21 for _ in range(20)]
    for index, color in enumerate([3, 7, 9, 4]):
        cells = [(r, c, x) for r, row in enumerate(answer) for c, x in enumerate(row)
                 if x == color or (color == 7 and x == 5)]
        for _ in range(index):
            cells = [(c, -r, x) for r, c, x in cells]
        top, left = min(r for r, c, x in cells), min(c for r, c, x in cells)
        dr, dc = [(1, 1), (2, 12), (12, 2), (11, 12)][index]
        for r, c, x in cells:
            canvas[r-top+dr][c-left+dc] = x
    return canvas, answer


def test_literal_preserves_diagonal_fragment_and_all_colors(adapter):
    grid, expected = literal_case()
    before = copy.deepcopy(grid)
    assert adapter.kernel.solve(grid) == expected
    assert adapter.kernel.solve(grid, 'northeast') == turn(expected)
    assert grid == before
    for _ in range(3):
        grid = turn(grid)
        assert adapter.kernel.solve(grid) == expected


def test_ambiguous_pieces_are_rejected(adapter):
    grid = [[0]*9 for _ in range(9)]
    for color, (dr, dc) in zip([7, 1, 2, 3], [(0,0),(0,6),(6,0),(6,6)]):
        for r in range(2):
            for c in range(2):
                grid[dr+r][dc+c] = color
    grid[0][0] = 5
    with pytest.raises(ValueError, match='ambiguous'):
        adapter.kernel.solve(grid)


def test_default_bytes_and_native_closure(adapter):
    assert adapter.program({'anchor_corner':'northwest'}) == (HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes() == (HOME/'workspace/parametric/canonical.rkt').read_bytes()
    assert (HOME/'generator.py').read_bytes() == (HOME/'workspace/parametric/kernel.py').read_bytes()


@pytest.mark.parametrize('seed', [0, 17, 43, 101])
def test_matched_inputs_unique_outputs_and_substantive_boundary(adapter, seed):
    nw = adapter.generate(seed, {'anchor_corner':'northwest'}, 2, 4)
    ne = adapter.generate(seed, {'anchor_corner':'northeast'}, 2, 4)
    bank = [p['input'] for split in ('train','test') for p in nw[split]]
    assert bank == [p['input'] for split in ('train','test') for p in ne[split]]
    assert len({repr(g) for g in bank}) == len(bank)
    for split in ('train', 'test'):
        for a, b in zip(nw[split], ne[split]):
            assert b['output'] == turn(a['output'])
            assert a['output'] != b['output']
            assert Counter(x for row in a['input'] for x in row if x) == Counter(x for row in a['output'] for x in row)
    stress = nw['test'][-1]
    assert (len(stress['input']), len(stress['input'][0])) == (30,30)
    assert (len(stress['output']), len(stress['output'][0])) == (24,24)
    assert sum(x != 0 for row in stress['input'] for x in row) == 576
    for r0, r1, c0, c1 in [(0,15,0,15),(0,15,15,30),(15,30,0,15),(15,30,15,30)]:
        assert sum(bool(stress['input'][r][c]) for r in range(r0,r1) for c in range(c0,c1)) > 100


def test_counts_prefix_invalid_values_and_no_aliasing(adapter):
    settings = {'anchor_corner':'northwest'}
    full = adapter.generate(9, settings, 2, 4)
    assert adapter.generate(9, settings, 6, 4)['test'] == full['test']
    assert adapter.generate(9, settings, 2, 1)['test'] == full['test'][:1]
    full['test'][0]['output'][0][0] = 0
    assert adapter.generate(9, settings, 2, 1)['test'][0]['output'][0][0] == 5
    for args in [(True,settings,2,4),(0,{},2,4),(0,{'anchor_corner':'south'},2,4),
                 (0,{'anchor_corner':'northwest','extra':1},2,4),
                 (0,settings,1,4),(0,settings,7,4),(0,settings,2,0),(0,settings,2,5)]:
        with pytest.raises(ValueError):
            adapter.generate(*args)


def test_base_api_strict_grids_and_input_preservation(adapter):
    base = load('_7b_test_base', HOME/'generator.py')
    assert base.RULE_TASK_ID == 'ee_7b3084d4'
    grid = base.generate(seed=17, sample_index=0, difficulty='medium')
    original = copy.deepcopy(grid)
    assert base.self_check(grid, difficulty='medium') == []
    assert grid == original
    for invalid in [[], [[True]], [[0],[0,1]], [[10]], [[0]]]:
        with pytest.raises(ValueError):
            adapter.kernel.solve(invalid)


def test_live_protected_racket_literal_and_large_case(adapter):
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
    from arcpuzzles.review_programs import strict_programs
    root = HOME.parent.parent
    programs = [adapter.program({'anchor_corner':x}) for x in adapter.CORNERS]
    strict_programs(root, programs)
    literal, _ = literal_case()
    large = adapter.generate(71, {'anchor_corner':'northwest'}, 2, 4)['test'][-1]['input']
    with _local_imports(root/'shared/runtime', HOME/'workspace/parametric'):
        apply, identity, bridge = _real_evaluator(root/'shared/runtime')
        try:
            assert identity['backend'] == 'racket' and identity['protected'] is True
            for corner, program in zip(adapter.CORNERS, programs):
                for grid in [literal,large]:
                    assert _grid(apply(program,_grid(grid))) == adapter.kernel.solve(grid,corner)
        finally:
            bridge.close()
