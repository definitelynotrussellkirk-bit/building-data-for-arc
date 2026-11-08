"""A connected same-color group must not masquerade as one distractor cell."""
from copy import deepcopy
import importlib.util
from pathlib import Path


def test_minimum_lesson_distinguishes_cell_count_from_connected_groups():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/native.py"
    spec = importlib.util.spec_from_file_location("_a85_components", path)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    episode = native.generate(24, {"axis_tolerance": "target_panel_count"}, 4, 4)

    def rival(grid):
        facts = native.scene_facts(grid)
        remaining = set(map(tuple, facts["panel_noise_cells"]))
        count = 0
        while remaining:
            frontier = [remaining.pop()]
            count += 1
            while frontier:
                r, c = frontier.pop()
                for nr, nc in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                    if (nr, nc) in remaining and grid[nr][nc] == grid[r][c]:
                        remaining.remove((nr,nc))
                        frontier.append((nr,nc))
        marker, target = facts["marker"], facts["target"]
        delta = [target[i] - marker[i] for i in range(2)]
        step = [0 if abs(d) <= count else (1 if d > 0 else -1) for d in delta]
        result = deepcopy(grid)
        result[marker[0]][marker[1]] = 5
        result[marker[0]+step[0]][marker[1]+step[1]] = 9
        result[target[0]][target[1]] = 9
        return result

    survives = all(rival(p["input"]) == p["output"] for p in episode["train"])
    disagrees = any(rival(p["input"]) != p["output"] for p in episode["test"])
    assert not (survives and disagrees), "connected-group rule fits demos but changes a query"
