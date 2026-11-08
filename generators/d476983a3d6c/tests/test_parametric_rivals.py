"""Independent route semantics and protected Racket rival parity."""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]
PATH = HOME / 'workspace/parametric/rivals.py'
_spec = importlib.util.spec_from_file_location('d476983a3d6c_independent_rivals', PATH)
rivals = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = rivals
_spec.loader.exec_module(rivals)


def test_sequential_canvas_changes_route():
    g = rivals.fixtures()['sequential_cmd1']
    actual = rivals.intended(g, 'avoid_painted')
    assert actual[4][1:5] == [4, 4, 4, 4]
    assert actual[2][2] == 0
    assert actual != rivals.bank('avoid_painted')['original_canvas_costs'](g)
    assert g[2][2] == 0


def test_command_not_encoded_by_object_count():
    g = rivals.fixtures()['sequential_cmd1']
    assert rivals.intended(g, 'command') != rivals.bank('command')['color_count_parity_command'](g)


def test_nonpairs_preserved_and_original_markers_drive_later_pairs():
    g = rivals.fixtures()['marker_overwrite']
    out = rivals.intended(g, 'command')
    assert out != rivals.bank('command')['current_canvas_markers'](g)
    h = rivals.fixtures()['clutter']
    assert rivals.intended(h, 'command') != rivals.bank('command')['drop_nonpairs'](h)


@pytest.mark.parametrize('grid', [[], [[]], [[True]], [[1.0]], [[10]], [[1],[0,0]], [[0]], [[1,1]], [[1] for _ in range(31)]])
def test_declared_strict_domain(grid):
    with pytest.raises(ValueError):
        rivals.intended(grid, 'command')


def test_bank_modes_and_aliases_are_explicit():
    assert len(rivals.bank('command')) >= 15
    assert len(rivals.bank('avoid_painted')) >= 25
    assert 'reverse_endpoints' not in rivals.bank('command')
    assert 'reverse_endpoints' not in rivals.bank('avoid_painted')
    with pytest.raises(ValueError):
        rivals.bank('unknown')


@pytest.fixture(scope='module')
def protected():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    from reviewer_support import find_root
    root = find_root(__file__).resolve()
    nested = root / 'shared/runtime'
    runtime = nested if (nested/'arc_repl/racket_bridge.py').is_file() else root
    assert runtime.is_relative_to(root)
    assert (runtime/'arc_repl/racket_bridge.py').is_file()
    assert (runtime/'puzzle_generators/rule_wrap.py').is_file()
    with _local_imports(runtime, HOME/'workspace/parametric'):
        apply, identity, bridge = _real_evaluator(runtime)
        assert identity['backend'] == 'racket' and identity['protected']
        try:
            yield apply
        finally:
            bridge.close()


@pytest.mark.parametrize('name', ['single', 'sequential_cmd1', 'sequential_cmd2', 'marker_overwrite', 'clutter', 'counts_and_order', 'edge_alignment'])
def test_protected_racket_parity(protected, name):
    grid = rivals.fixtures()[name]
    for mode in ['command', 'avoid_painted']:
        assert protected(rivals.racket(mode, None), grid) == rivals.intended(grid, mode)
        for rival_name, predict in rivals.bank(mode).items():
            assert protected(rivals.racket(mode, rival_name), grid) == predict(grid), (mode, rival_name, name)


# Protected before-repair controls retained from the independent reviewer.
_CONFIRMED_REVIEW_CONTROLS = [{'mode': 'command', 'rival': 'restore_command', 'input': [[1, 6], [6, 0]], 'output': [[6, 6], [6, 0]], 'rival_output': [[1, 6], [6, 0]]}, {'mode': 'avoid_painted', 'rival': 'restore_command', 'input': [[2, 9], [0, 3], [0, 3], [9, 0]], 'output': [[9, 9], [9, 3], [9, 3], [9, 0]], 'rival_output': [[2, 9], [9, 3], [9, 3], [9, 0]]}, {'mode': 'avoid_painted', 'rival': 'ignore_nonpairs', 'input': [[2, 0, 9], [0, 0, 3], [0, 3, 0], [9, 0, 0]], 'output': [[2, 0, 9], [0, 3, 3], [0, 3, 9], [9, 9, 9]], 'rival_output': [[9, 9, 9], [9, 0, 3], [9, 3, 3], [9, 0, 0]]}, {'mode': 'avoid_painted', 'rival': 'first_pair_command', 'input': [[2, 9], [0, 3], [0, 3], [9, 0]], 'output': [[9, 9], [9, 3], [9, 3], [9, 0]], 'rival_output': [[2, 9], [0, 3], [0, 3], [9, 9]]}, {'mode': 'avoid_painted', 'rival': 'positive_tie_hv', 'input': [[2, 9], [0, 3], [9, 0]], 'output': [[2, 9], [0, 9], [9, 9]], 'rival_output': [[9, 9], [9, 3], [9, 0]]}, {'mode': 'avoid_painted', 'rival': 'positive_tie_vh', 'input': [[1, 4, 0, 0, 6], [6, 0, 3, 5, 0]], 'output': [[6, 6, 6, 6, 6], [6, 0, 3, 5, 0]], 'rival_output': [[1, 4, 0, 0, 6], [6, 6, 6, 6, 6]]}, {'mode': 'avoid_painted', 'rival': 'cap_two_cost', 'input': [[1, 0, 0, 0, 0, 0], [0, 9, 5, 0, 0, 0], [0, 0, 7, 0, 9, 0], [0, 0, 0, 0, 0, 5]], 'output': [[1, 0, 0, 0, 0, 0], [0, 9, 5, 9, 9, 0], [0, 0, 5, 0, 9, 0], [0, 0, 5, 5, 5, 5]], 'rival_output': [[1, 0, 0, 0, 0, 0], [0, 9, 5, 5, 5, 5], [0, 0, 7, 0, 9, 5], [0, 0, 0, 0, 0, 5]]}]

@pytest.mark.parametrize('case', _CONFIRMED_REVIEW_CONTROLS, ids=lambda x: x['mode']+'-'+x['rival'])
def test_confirmed_contextual_rival_controls(protected, case):
    mode, name, grid = case['mode'], case['rival'], case['input']
    assert rivals.intended(grid, mode) == case['output']
    assert rivals.bank(mode)[name](grid) == case['rival_output']
    assert case['output'] != case['rival_output']
    assert protected(rivals.racket(mode, None), grid) == case['output']
    assert protected(rivals.racket(mode, name), grid) == case['rival_output']
