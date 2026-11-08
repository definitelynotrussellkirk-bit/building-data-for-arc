"""Independent, bounded topology checks for the opt-in scene grammar."""
import importlib.util
from pathlib import Path

import unittest


PATH = Path(__file__).parents[1] / "workspace" / "parametric" / "scenes.py"
spec = importlib.util.spec_from_file_location("frame_parametric_scenes", PATH)
scenes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scenes)


def inspect(g):
    assert g and all(len(row) == len(g[0]) for row in g)
    assert all(type(x) is int and 0 <= x <= 9 for row in g for x in row)
    cells = {(r, c) for r, row in enumerate(g) for c, x in enumerate(row) if x}
    top, left = min(r for r, c in cells), min(c for r, c in cells)
    bottom, right = max(r for r, c in cells), max(c for r, c in cells)
    color = g[top][left]
    assert color in (1, 4, 5, 6, 8, 9)
    assert all(g[r][c] == color for r, c in ((top, left), (top, right), (bottom, left), (bottom, right)))
    assert all(g[top][c] in (color, 3) and g[bottom][c] in (color, 2) for c in range(left + 1, right))
    assert all(g[r][left] in (color, 2) and g[r][right] in (color, 3) for r in range(top + 1, bottom))
    assert all(g[r][c] in (0, 7) for r in range(top + 1, bottom) for c in range(left + 1, right))
    assert any(g[bottom][c] == 2 for c in range(left + 1, right))
    assert any(g[r][right] == 3 for r in range(top + 1, bottom))
    rows = {r for r in range(top + 1, bottom) if g[r][left] == 2}
    cols = {c for c in range(left + 1, right) if g[top][c] == 3}
    assert rows and cols
    old = {(r, c) for r, row in enumerate(g) for c, value in enumerate(row) if value == 7}
    crossings = {(r, c) for r in rows for c in cols}
    return old, crossings


def components(cells):
    remaining = set(cells)
    groups = []
    while remaining:
        todo = [remaining.pop()]
        group = set(todo)
        while todo:
            r, c = todo.pop()
            for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if p in remaining:
                    remaining.remove(p)
                    group.add(p)
                    todo.append(p)
        groups.append(group)
    return groups


def check_scene_contract_and_reproducibility(profile, seed):
    g = scenes.sample_scene(seed, profile)
    assert g == scenes.sample_scene(seed, profile)
    old, crosses = inspect(g)
    assert old and crosses - old
    assert 5 <= len(g) <= 30 and 6 <= len(g[0]) <= 30
    groups = components(old | crosses)
    if profile == "bridge":
        assert max(map(len, components(old))) == 5
        assert sorted(map(len, groups)) == [1, 1, 1, 1, 1, 1, 5, 8]
        winner = max(groups, key=len)
        assert len(winner & crosses) == 4
        assert sum(bool(winner & x) for x in components(old)) == 4
        assert not winner & max(components(old), key=len)
    elif profile == "tie":
        assert sorted(map(len, groups)) == [1, 1, 1, 1, 1, 1, 9, 12, 12]
        assert max(map(len, components(old))) == 12
    elif profile == "small":
        assert (len(g), len(g[0])) == (5, 6)
        assert sorted(map(len, groups)) == [1, 1, 1, 3]
    elif profile == "dense":
        assert (len(g), len(g[0])) == (30, 30)
        assert len(old | crosses) >= 100
        assert len(groups) >= 4
        assert max(r for r, c in old | crosses) - min(r for r, c in old | crosses) >= 23
        assert max(c for r, c in old | crosses) - min(c for r, c in old | crosses) >= 23


def check_seed_diversity():
    for profile in ("bridge", "tie", "small", "transfer", "dense"):
        grids = {tuple(map(tuple, scenes.sample_scene(seed, profile))) for seed in range(4)}
        assert len(grids) >= 3


class SceneTests(unittest.TestCase):
    def test_bounded_topology_matrix(self):
        for profile in ("bridge", "tie", "small", "transfer", "dense"):
            for seed in (0, 1, 7, 19):
                with self.subTest(profile=profile, seed=seed):
                    check_scene_contract_and_reproducibility(profile, seed)

    def test_seed_diversity(self):
        check_seed_diversity()

    def test_lesson_requires_relative_ranking(self):
        for seed in (0, 1, 7, 19):
            with self.subTest(seed=seed):
                bridge_old, bridge_cross = inspect(scenes.sample_scene(seed, "bridge"))
                tie_old, tie_cross = inspect(scenes.sample_scene(seed, "tie"))
                bridge_sizes = sorted(map(len, components(bridge_old | bridge_cross)))
                tie_sizes = sorted(map(len, components(tie_old | tie_cross)))
                # An absolute cutoff retaining the demo's eight-cell winner
                # would also retain the other demo's nine-cell loser.
                assert bridge_sizes[-1] == 8
                assert tie_sizes[-3:] == [9, 12, 12]
                assert bridge_sizes[-1] < tie_sizes[-3] < tie_sizes[-1]

    def test_unknown_profile(self):
        with self.assertRaises(ValueError):
            scenes.sample_scene(0, "unknown")


if __name__ == "__main__":
    unittest.main()
