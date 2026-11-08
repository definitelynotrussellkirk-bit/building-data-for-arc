from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


PROBE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "audit_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("fa55_audit_probe_test", PROBE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_components_distinguish_the_disconnected_template():
    probe = _load_probe()
    grid = [
        [0, 0, 0, 0],
        [0, 2, 0, 2],
        [0, 0, 2, 0],
    ]
    components = probe.same_color_components(grid, color=2)
    assert sorted(len(component) for component in components) == [1, 1, 1]


def test_documented_whole_template_stamps_all_cells_inside_each_frame():
    probe = _load_probe()
    grid = [[0] * 10 for _ in range(8)]
    for r, c in ((0, 0), (0, 2), (1, 1)):
        grid[r][c] = 2
    # 5x5 frame at rows 3..7, cols 5..9.
    for c in range(5, 10):
        grid[3][c] = 6
        grid[7][c] = 6
    for r in range(3, 8):
        grid[r][5] = 6
        grid[r][9] = 6

    out = probe.documented_whole_template_output(grid)
    interior_six = {
        (r, c)
        for r, row in enumerate(out)
        for c, value in enumerate(row)
        if value == 6 and 3 < r < 7 and 5 < c < 9
    }
    assert interior_six == {(4, 6), (4, 8), (5, 7)}
