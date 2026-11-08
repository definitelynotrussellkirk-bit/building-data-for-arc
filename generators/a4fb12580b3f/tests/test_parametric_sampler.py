"""Focused tests for the separate parametric sampler and Python oracle."""
import importlib.util
import json
from pathlib import Path
import random

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("anchor_parametric_prototype", ROOT / "workspace/parametric/prototype.py")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


def roles(grid):
    objects = p.components(grid)
    anchor = next(cells for color, cells in objects if color == 1)
    direct = [(color, cells) for color, cells in objects if color != 1 and p.touches(cells, anchor)]
    relay = max(direct, key=lambda obj: len(obj[1]))
    targets = [(color, cells) for color, cells in objects if color != 1 and not p.touches(cells, anchor) and p.touches(cells, relay[1])]
    return objects, anchor, direct, relay, targets


@pytest.mark.parametrize("height,width", [(14, 14), (14, 30), (30, 14), (30, 30), (19, 23)])
def test_constructive_grammar_and_actual_transform(height, width):
    for seed in range(12):
        g = p.sample_input(seed, seed % 7, height=height, width=width)
        objects, anchor, direct, relay, targets = roles(g)
        assert (len(g), len(g[0])) == (height, width)
        assert len([1 for color, _ in objects if color == 1]) == 1
        assert 2 <= len(direct) <= 4
        assert sum(len(cells) == len(relay[1]) for _, cells in direct) == 1
        assert targets and any(color != 4 for color, _ in targets)
        assert sum(v == 0 for row in g for v in row) > height * width / 2
        assert any(len(cells) > len(relay[1]) for _, cells in objects if not p.touches(cells, anchor) and cells != anchor)
        assert any(p.touches(cells, anchor, diagonal=True) and not p.touches(cells, anchor) and not p.touches(cells, relay[1]) and color != 4 for color, cells in objects if color != 1)
        assert any(not p.touches(cells, anchor) and not p.touches(cells, relay[1]) and any(p.touches(cells, small) for _, small in direct if small != relay[1]) and color != 4 for color, cells in objects if color != 1)
        direct_colors = {color for color, _ in direct if color != 4}
        assert any(color in direct_colors and not p.touches(cells, anchor) and not p.touches(cells, relay[1]) for color, cells in objects)
        assert any(color == relay[0] and cells != relay[1] and p.touches(cells, relay[1], diagonal=True) and not p.touches(cells, relay[1]) and not p.touches(cells, anchor) for color, cells in objects)
        expected_direct = {cell for _, cells in direct for cell in cells}
        expected_relay = expected_direct | {cell for _, cells in targets for cell in cells}
        for mode, changed in [("direct", expected_direct), ("largest_relay", expected_relay)]:
            out = p.solve(g, mode)
            assert out == [[4 if (r, c) in changed else v for c, v in enumerate(row)] for r, row in enumerate(g)]
        assert p.solve(g, "direct") != p.solve(g, "largest_relay")
        json.dumps(p.analyze(g))


def test_episode_counts_uniqueness_determinism_and_private_rng():
    random.seed(188)
    before = random.getstate()
    for demos in range(2, 7):
        for queries in range(1, 5):
            episode = p.episode_inputs(73, demos, queries)
            assert episode == p.episode_inputs(73, demos, queries)
            assert len(episode["train"]) == demos and len(episode["test"]) == queries
            grids = episode["train"] + episode["test"]
            assert len({json.dumps(g) for g in grids}) == len(grids)
            assert roles(grids[0])[3][0] != 4
            assert roles(grids[1])[3][0] == 4
            assert roles(grids[0])[2][-1] == roles(grids[0])[3]
            assert roles(grids[1])[2][0] == roles(grids[1])[3]
    assert random.getstate() == before
    episode = p.episode_inputs(9)
    assert (30, 30) in {(len(g), len(g[0])) for g in episode["test"]}


def test_large_canvas_contains_additional_reasoning_content():
    for seed in range(8):
        small = p.sample_input(seed, 0, height=14, width=14)
        large = p.sample_input(seed, 0, height=30, width=30)
        assert len(roles(large)[3][1]) > len(roles(small)[3][1])
        assert sum(v != 0 for row in large for v in row) > 2 * sum(v != 0 for row in small for v in row)
        cells = {(r, c) for r, row in enumerate(large) for c, v in enumerate(row) if v}
        assert max(r for r, c in cells) - min(r for r, c in cells) >= 26
        assert max(c for r, c in cells) - min(c for r, c in cells) >= 26


@pytest.mark.parametrize("kwargs", [{"height":13}, {"width":31}, {"height":True}, {"width":15.2}])
def test_clear_dimension_rejections(kwargs):
    with pytest.raises(ValueError, match="14.*30"):
        p.sample_input(0, 0, **kwargs)


@pytest.mark.parametrize("demos,queries", [(1,4), (7,4), (3,0), (3,5), (True,4)])
def test_clear_count_rejections(demos, queries):
    with pytest.raises(ValueError):
        p.episode_inputs(0, demos, queries)


def test_oracle_snapshots_components_and_rejects_bad_requests():
    g = [[1,2,2,3,5], [6,0,0,0,0], [7,0,0,0,0]]
    assert p.solve(g, "largest_relay") == [[1,4,4,4,5], [4,0,0,0,0], [7,0,0,0,0]]
    assert g[0] == [1,2,2,3,5]
    with pytest.raises(ValueError, match="mode"):
        p.solve(g, "unknown")
    with pytest.raises(ValueError, match="anchor"):
        p.solve([[0,2]])
    with pytest.raises(ValueError, match="largest"):
        p.solve([[2,1,3]], "largest_relay")
