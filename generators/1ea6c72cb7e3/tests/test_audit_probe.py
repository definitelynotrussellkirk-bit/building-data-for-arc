from pathlib import Path
import importlib.util


def load():
    path = Path(__file__).resolve().parents[1] / 'workspace/audit_targets.py'
    assert path.exists(), 'missing reusable audit reproducer'
    spec = importlib.util.spec_from_file_location('audit_targets', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_first_run_rival_restarts_only_for_first_run():
    audit = load()
    assert audit.first_run_only([[0,2,2,2,0,3,3,3]]) == [[0,2,0,2,0,0,0,0]]


def test_echo_overwrite_rival_changes_occupied_target_without_mutating_input():
    audit = load()
    grid = [[0,9,0], [3,0,0], [0,0,0]]
    assert audit.echo_overwrite(grid) == [[0,9,0], [5,0,0], [0,0,0]]
    assert grid[1][0] == 3


def test_echo_wrap_rival_wraps_boundary_only():
    audit = load()
    assert audit.echo_wrap([[0,0], [9,0]]) == [[0,5], [9,0]]
