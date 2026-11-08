"""Behavioral checks for the opt-in marker-size family, not production admission."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_path, find_root


HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "marker_size_prototype_test", HOME / "workspace/parametric/prototype.py"
)
proto = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proto)
SETTINGS = ({"length_rule": "fixed_five"}, {"length_rule": "marker_size"})


def tiny_scene():
    grid = [[0] * 15 for _ in range(10)]
    for length, column in ((3, 2), (5, 5), (7, 8)):
        for row in range(1, length + 1):
            grid[row][column] = 1
    for row, column in ((7, 11), (8, 11), (8, 12)):
        grid[row][column] = 6
    return grid


def test_default_is_exact_canonical_string():
    root = find_root(__file__)
    rows = (json.loads(line) for line in canonical_path(root).read_text().splitlines())
    row = next(r for r in rows if r.get("task_id") == "7bba59d92716")
    assert proto.program(SETTINGS[0]) == row["program_solution"]
    assert proto.program(SETTINGS[1]).startswith("(rule!")


def test_marker_count_changes_selected_objects_and_keeps_other_cells():
    source = tiny_scene()
    expected = deepcopy(source)
    expected[2][2] = 2
    assert proto.mirror(source, SETTINGS[1]) == expected
    expected = deepcopy(source)
    expected[3][5] = 2
    assert proto.mirror(source, SETTINGS[0]) == expected
    assert source == tiny_scene()


def test_four_connectivity_and_branch_exclusion():
    source = tiny_scene()
    source[0][6] = 1  # Diagonal to the five-line's endpoint, no 4-contact.
    expected = deepcopy(source)
    expected[3][5] = 2
    assert proto.mirror(source, SETTINGS[0]) == expected
    source[1][6] = 1  # Now orthogonally connected: the five-line is not a target.
    assert proto.mirror(source, SETTINGS[0]) == source


@pytest.mark.parametrize("settings", SETTINGS)
def test_independent_counts_prefixes_novelty_and_determinism(settings):
    state = random.getstate()
    big = proto.generate(17, settings, demos=6, queries=4)
    for demos in (2, 3, 6):
        for queries in (1, 4):
            episode = proto.generate(17, settings, demos=demos, queries=queries)
            assert episode["train"] == big["train"][:demos]
            assert episode["test"] == big["test"][:queries]
    assert random.getstate() == state
    pairs = big["train"] + big["test"]
    assert len({json.dumps(p["input"]) for p in pairs}) == len(pairs)
    assert all(proto.mirror(p["input"], settings) == p["output"] for p in pairs)
    assert proto.generate(17, settings, 6, 4) == big


def test_input_sampling_has_no_private_setting_dependency():
    a, b = (proto.generate(0, setting, 3, 4) for setting in SETTINGS)
    for split in ("train", "test"):
        assert [p["input"] for p in a[split]] == [p["input"] for p in b[split]]
    assert a["train"][0]["output"] != b["train"][0]["output"]
    assert a["train"][1]["output"] != b["train"][1]["output"]


def test_generated_source_satisfies_native_worker_contract():
    for settings in SETTINGS:
        episode = proto.generate(0, settings, 2, 4)
        assert episode.get("program_solution") == proto.program(settings)


def test_demo_markers_have_distinct_sizes_and_nonrectangular_geometry():
    episode = proto.generate(0, SETTINGS[1], 2, 4)
    for pair, size in zip(episode["train"], (3, 7)):
        cells = [(r, c) for r, row in enumerate(pair["input"])
                 for c, value in enumerate(row) if value == 6]
        assert len(cells) == size
        height = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
        width = max(c for _, c in cells) - min(c for _, c in cells) + 1
        assert height * width != size
        assert height != size


def test_two_demos_reject_boundary_cell_count_before_cross_query():
    episode = proto.generate(0, SETTINGS[1], 2, 4)

    def boundary_prediction(grid):
        marker = set(proto.components(grid, 6)[0])
        count = sum(any((r + dr, c + dc) not in marker
                        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    for r, c in marker)
        output = deepcopy(grid)
        for cells in proto.components(grid, 1):
            if len(cells) == count and len({c for _, c in cells}) == 1:
                output[(cells[0][0] + cells[-1][0]) // 2][cells[0][1]] = 2
        return output

    assert any(boundary_prediction(p["input"]) != p["output"] for p in episode["train"])


def test_thirty_by_thirty_is_substantive_and_contacts_boundaries():
    episode = proto.generate(0, SETTINGS[1], 3, 4)
    pair = episode["test"][2]
    grid = pair["input"]
    assert len(grid) == len(grid[0]) == 30
    assert sum(v != 0 for row in grid for v in row) >= 120
    assert all(any(grid[r][c] for r in range(r0, r0 + 15)
                   for c in range(c0, c0 + 15))
               for r0 in (0, 15) for c0 in (0, 15))
    assert any(grid[r][c] == 1 for r in range(30) for c in range(30)
               if r in (0, 29) or c in (0, 29))
    assert sum(v == 2 for row in pair["output"] for v in row) >= 2


@pytest.mark.parametrize("settings", [{}, {"length_rule": "unknown"},
    {"length_rule": True}, {"length_rule": "marker_size", "extra": 1}, None])
def test_settings_rejected(settings):
    with pytest.raises((TypeError, ValueError)):
        proto.generate(0, settings)
    with pytest.raises((TypeError, ValueError)):
        proto.program(settings)


@pytest.mark.parametrize("kwargs", [{"demos": 1}, {"demos": 7},
    {"demos": True}, {"demos": 2.0}, {"queries": 0}, {"queries": 5},
    {"queries": True}, {"seed": -1}, {"seed": True}, {"seed": 1.0}])
def test_request_boundaries_rejected(kwargs):
    args = dict(seed=0, settings=SETTINGS[0], demos=3, queries=4)
    args.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        proto.generate(**args)


@pytest.mark.parametrize("grid", [[], [[]], [[True]], [[1.0]], [[10]], [[-1]],
    [[0], [0, 0]], [[0] * 31], [[0]] * 31])
def test_invalid_grids_rejected(grid):
    with pytest.raises((TypeError, ValueError)):
        proto.mirror(grid, SETTINGS[0])


def test_marker_mode_rejects_missing_or_ambiguous_marker():
    with pytest.raises(ValueError):
        proto.mirror([[0, 1], [0, 1]], SETTINGS[1])
    with pytest.raises(ValueError):
        proto.mirror([[6, 0, 6]], SETTINGS[1])
