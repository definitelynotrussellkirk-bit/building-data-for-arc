from pathlib import Path
import importlib.util
import pytest

TOOL = Path(__file__).parents[1] / 'workspace/audit_targets.py'


def load():
    assert TOOL.is_file(), 'audit replay tool not implemented'
    spec = importlib.util.spec_from_file_location('audit_targets', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_first_and_last_are_distinct_on_later_decoys():
    tool = load()
    grid = [[0]*5 for _ in range(5)]
    grid[1][1], grid[3][2] = 6, 2
    first, last = tool.parity_pattern(grid), tool.parity_pattern(grid,last=True)
    assert first[2][1] == 6 and first[0] == [0,4,0,4,0]
    assert last[4][2] == 2 and last[0] == [4,0,4,0,4]
    assert first != last
    grid[3][2] = 0
    assert tool.parity_pattern(grid) == tool.parity_pattern(grid,last=True)


def test_one_way_mirror_preserves_decoy_without_copying_it_back():
    tool = load()
    grid = [[0]*8 for _ in range(3)]
    grid[0][0], grid[1][2], grid[2][4] = 3, 5, 6
    output = tool.copy_left(grid)
    assert output[0] == [3,0,0,0,0,0,0,3]
    assert output[1] == [0,0,5,0,0,5,0,0]
    assert output[2] == grid[2]
