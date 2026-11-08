"""Behavioral contract for the unselected, two-mode parametric adapter."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
ADAPTER = Path(__file__).resolve().parents[1] / "workspace/parametric/adapter.py"
MODES = ("fixed", "relative_to_largest")


@pytest.fixture(scope="module")
def adapter():
    assert ADAPTER.is_file(), f"Parametric adapter is not implemented: {ADAPTER}"
    spec = importlib.util.spec_from_file_location("b28619e32f6f_parametric_tests", ADAPTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def enclosed_regions(grid):
    """Independent four-neighbor flood fill; exterior components are discarded."""
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 0}
    regions = []
    while unseen:
        start = unseen.pop()
        component = {start}
        pending = [start]
        touches_edge = False
        while pending:
            r, c = pending.pop()
            touches_edge |= r in (0, height - 1) or c in (0, width - 1)
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        if not touches_edge:
            regions.append(component)
    return regions


def expected_labels(grid, mode):
    regions = enclosed_regions(grid)
    largest = max(map(len, regions), default=0)
    result = deepcopy(grid)
    for region in regions:
        area = len(region)
        if mode == "fixed":
            color = 8 if area <= 8 else 4 if area <= 24 else 3
        else:
            color = 8 if area * 4 <= largest else 4 if area * 2 <= largest else 3
        for r, c in region:
            result[r][c] = color
    return result


def inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def assert_curriculum(first_two):
    areas_by_grid = [{len(region) for region in enclosed_regions(pair["input"])} for pair in first_two]
    assert {7, 8, 9, 23, 24, 25} <= set().union(*areas_by_grid)
    # Each witness is relative to its own grid's largest enclosed region.
    for denominator in (4, 2):
        for offset in (-1, 0, 1):
            assert any(
                max(areas) % denominator == 0
                and max(areas) // denominator + offset in areas
                for areas in areas_by_grid
            ), (denominator, offset, areas_by_grid)


def test_fixed_program_preserves_exact_canonical_racket(adapter):
    from arcpuzzles.catalog import Catalog

    canonical = Catalog(ROOT)._variants()["b28619e32f6f"][0]["program_solution"]
    assert adapter.program({"threshold_mode": "fixed"}) == canonical
    relative = adapter.program({"threshold_mode": "relative_to_largest"})
    assert isinstance(relative, str) and relative.strip()
    assert relative != canonical


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_episodes_have_correct_labels_curriculum_and_query_extremes(adapter, seed, demos):
    episodes = {}
    for mode in MODES:
        settings = {"threshold_mode": mode}
        episode = adapter.generate(seed, settings, demos=demos, queries=4)
        assert settings == {"threshold_mode": mode}
        assert set(episode) == {"train", "test", "program_solution"}
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program(settings)
        pairs = episode["train"] + episode["test"]
        seen = set()
        for pair in pairs:
            assert set(pair) == {"input", "output"}
            grid = pair["input"]
            assert isinstance(grid, list) and 7 <= len(grid) <= 30
            assert isinstance(grid[0], list) and 7 <= len(grid[0]) <= 30
            assert all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
            assert all(type(cell) is int and cell in (0, 2) for row in grid for cell in row)
            assert enclosed_regions(grid), "A scene must contain an enclosed region"
            assert pair["output"] == expected_labels(grid, mode)
            key = tuple(map(tuple, grid))
            assert key not in seen, "Demo and query inputs must all be distinct"
            seen.add(key)
        assert_curriculum(episode["train"][:2])
        query_grids = inputs(episode, "test")
        assert any(len(grid) == len(grid[0]) == 7 for grid in query_grids)
        dense = [grid for grid in query_grids if len(grid) == len(grid[0]) == 30]
        assert dense, "Four queries must include a 30 by 30 stress case"
        red_cells = [(r, c) for r, row in enumerate(dense[0]) for c, cell in enumerate(row) if cell == 2]
        assert len(red_cells) > 150
        assert max(r for r, _ in red_cells) - min(r for r, _ in red_cells) + 1 >= 26
        assert max(c for _, c in red_cells) - min(c for _, c in red_cells) + 1 >= 26
        episodes[mode] = episode
    for split in ("train", "test"):
        assert inputs(episodes["fixed"], split) == inputs(episodes["relative_to_largest"], split)
    assert any(
        fixed["output"] != relative["output"]
        for fixed, relative in zip(episodes["fixed"]["train"], episodes["relative_to_largest"]["train"])
    ), "The demonstrations must distinguish the two threshold policies"


@pytest.mark.parametrize("mode", MODES)
def test_counts_preserve_input_streams_and_defaults(adapter, mode):
    settings = {"threshold_mode": mode}
    default = adapter.generate(17, settings)
    one_query = adapter.generate(17, settings, demos=3, queries=1)
    extra_demos = adapter.generate(17, settings, demos=6, queries=4)
    assert len(default["train"]) == 3 and len(default["test"]) == 4
    assert one_query["train"] == default["train"]
    assert one_query["test"] == default["test"][:1]
    assert extra_demos["train"][:3] == default["train"]
    assert extra_demos["test"] == default["test"]


def test_maximum_seed_is_deterministic_and_results_are_fresh(adapter):
    settings = {"threshold_mode": "relative_to_largest"}
    before_settings = deepcopy(settings)
    first = adapter.generate(2**63 - 1, settings, demos=2, queries=1)
    snapshot = deepcopy(first)
    second = adapter.generate(2**63 - 1, settings, demos=2, queries=1)
    assert first == second
    assert settings == before_settings
    first["train"][0]["input"][0][0] = 9
    assert first["train"][0]["output"] == snapshot["train"][0]["output"]
    assert first["train"][1:] == snapshot["train"][1:]
    assert first["test"] == snapshot["test"]
    assert second == snapshot
    assert adapter.generate(2**63 - 1, settings, demos=2, queries=1) == snapshot


@pytest.mark.parametrize("settings", [
    None, True, [], {}, {"threshold_mode": "unknown"},
    {"threshold_mode": []}, {"threshold_mode": "fixed", "extra": 1},
])
def test_invalid_settings_fail_at_both_public_entry_points(adapter, settings):
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(17, settings)


@pytest.mark.parametrize(("argument", "invalid"), [
    ("seed", -1), ("seed", 2**63), ("seed", True), ("seed", 1.0), ("seed", "17"), ("seed", None),
    ("demos", 1), ("demos", 7), ("demos", True), ("demos", 3.0), ("demos", "3"),
    ("queries", 0), ("queries", 5), ("queries", False), ("queries", 1.0), ("queries", "1"),
])
def test_invalid_numeric_arguments_are_not_coerced(adapter, argument, invalid):
    arguments = {"seed": 17, "settings": {"threshold_mode": "fixed"}, "demos": 2, "queries": 1}
    arguments[argument] = invalid
    with pytest.raises(ValueError):
        adapter.generate(**arguments)


def test_turn_projection_hides_future_queries_and_private_metadata(adapter):
    path = ADAPTER.with_name("verify.py")
    assert path.is_file(), "Missing runnable verification/export helper"
    spec = importlib.util.spec_from_file_location("b28619e32f6f_verify_tests", path)
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    episode = adapter.generate(17, {"threshold_mode": "fixed"})
    first = verifier.turn_bytes(episode, 0)
    import json
    challenge = json.loads(first)
    assert set(challenge) == {"train", "test"}
    assert challenge["train"] == episode["train"]
    assert challenge["test"] == [{"input": episode["test"][0]["input"]}]
    private_change = deepcopy(episode)
    private_change.update(seed=999, settings={"threshold_mode": "other"}, program_solution="private")
    private_change["test"][0]["output"] = [[9]]
    private_change["test"][1:]=[{"input": [[9]], "output": [[9]]}]
    assert verifier.turn_bytes(private_change, 0) == first
    single = adapter.generate(17, {"threshold_mode": "fixed"}, queries=1)
    assert verifier.turn_bytes(single, 0) == first
    with pytest.raises(ValueError):
        verifier.turn_bytes(episode, True)
    with pytest.raises(ValueError):
        verifier.turn_bytes(episode, 4)


def test_room_carving_cannot_create_a_nested_red_frame(adapter):
    from reviewer_support import load_selected_generator
    canonical, _, _ = load_selected_generator("b28619e32f6f", root=ROOT)

    class PrioritizeInteriorBlock:
        def shuffle(self, cells):
            cells.sort(key=lambda cell: (not (2 <= cell[0] <= 4 and 2 <= cell[1] <= 4), cell))

    h, w, cells = adapter._impl._room(101, PrioritizeInteriorBlock())
    assert len(cells) == 101
    grid = [[0] * (w + 4) for _ in range(h + 4)]
    for r in range(h + 2):
        for c in range(w + 2):
            grid[r + 1][c + 1] = 2
    for r, c in cells:
        grid[r + 2][c + 2] = 0
    assert canonical.self_check(grid) == []
