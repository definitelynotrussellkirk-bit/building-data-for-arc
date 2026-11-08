from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "1409f5f7af2e"
REPO = find_root(__file__)
HERE = REPO / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = HERE / filename
    assert path.is_file(), f"missing parametric artifact: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load("parametric_1409_busiest_column", "prototype.py")


def _canonical_program() -> str:
    for line in canonical_path(REPO).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _decisive_grid() -> list[list[int]]:
    # Column 5 has two activated centers; column 1 has one. Column 0 has more
    # raw green cells than either target column but no green-black-green target.
    return [
        [3, 0, 0, 0, 0, 3, 0, 0],
        [3, 3, 0, 3, 0, 0, 0, 0],
        [3, 0, 0, 0, 0, 3, 0, 4],
        [3, 3, 0, 5, 0, 0, 0, 0],
        [0, 0, 0, 3, 0, 3, 0, 4],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]


def test_default_program_is_exact_canonical_authority(proto):
    assert proto.DEFAULT == {"endpoint_treatment": "preserve"}
    assert proto.program(proto.DEFAULT) == _canonical_program()
    assert proto.program({"endpoint_treatment": "highlight_busiest"}) != _canonical_program()
    assert proto.SETTINGS == [
        {"endpoint_treatment": "preserve"},
        {"endpoint_treatment": "highlight_busiest"},
    ]


def test_transform_has_real_stage_a_intermediate_and_stage_b(proto):
    grid = _decisive_grid()
    before = copy.deepcopy(grid)
    stage_a = proto.stage_a(grid)
    assert proto.busiest_activated_column(stage_a) == 5
    assert sum(value == 2 for row in stage_a for value in row) == 3

    canonical = proto.transform(grid, {"endpoint_treatment": "preserve"})
    highlighted = proto.transform(grid, {"endpoint_treatment": "highlight_busiest"})
    assert canonical == stage_a
    assert highlighted != canonical
    assert [highlighted[row][5] for row in (0, 2, 4)] == [1, 1, 1]
    assert highlighted[2][1] == 2
    assert highlighted[1][5] == 2 and highlighted[3][5] == 2
    assert grid == before


def test_counts_are_strict_prefix_stable_and_inputs_match_across_settings(proto):
    for bad in (
        {},
        {"endpoint_treatment": "other"},
        {"endpoint_treatment": 1},
        {"endpoint_treatment": "preserve", "extra": 0},
    ):
        with pytest.raises(ValueError):
            proto.program(bad)
    for key, value in (("seed", True), ("demos", 1), ("demos", 7), ("queries", 3), ("queries", 5)):
        kwargs = dict(seed=9, settings=proto.DEFAULT, demos=3, queries=4)
        kwargs[key] = value
        with pytest.raises(ValueError):
            proto.generate(**kwargs)

    short = proto.generate(17, proto.DEFAULT, demos=2, queries=4)
    long = proto.generate(17, proto.DEFAULT, demos=6, queries=4)
    alternate = proto.generate(17, {"endpoint_treatment": "highlight_busiest"}, demos=2, queries=4)
    assert short == proto.generate(17, proto.DEFAULT, demos=2, queries=4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"]
    assert [p["input"] for p in short["train"] + short["test"]] == [
        p["input"] for p in alternate["train"] + alternate["test"]
    ]
    all_inputs = [p["input"] for p in short["train"] + short["test"]]
    assert len({proto.digest(grid) for grid in all_inputs}) == len(all_inputs)


def test_two_demos_identify_each_setting_and_refute_named_shortcuts(proto):
    for setting in proto.SETTINGS:
        episode = proto.generate(31, setting, demos=2, queries=4)
        certificate = proto.certify(episode)
        assert certificate["survivors"] == [setting]
        assert certificate["shortcut_survivors"] == []
        assert len(certificate["queries"]) == 4


def test_minimum_lesson_refutes_nonlocal_and_diagonal_connectivity(proto):
    setting = {"endpoint_treatment": "highlight_busiest"}

    def finish(stage):
        winner = proto.busiest_activated_column(stage)
        output = copy.deepcopy(stage)
        for row in range(len(output)):
            if output[row][winner] == 3:
                output[row][winner] = 1
        return output

    def nonlocal_vertical(grid):
        stage = copy.deepcopy(grid)
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if (
                    grid[row][col] == 0
                    and any(grid[above][col] == 3 for above in range(row))
                    and any(grid[below][col] == 3 for below in range(row + 1, len(grid)))
                ):
                    stage[row][col] = 2
        return finish(stage)

    def vertical_or_diagonal(grid):
        stage = copy.deepcopy(grid)
        width = len(grid[0])
        for row in range(1, len(grid) - 1):
            for col in range(width):
                if grid[row][col] != 0:
                    continue
                matched = grid[row - 1][col] == 3 and grid[row + 1][col] == 3
                if 0 < col < width - 1:
                    matched = matched or (
                        grid[row - 1][col - 1] == 3
                        and grid[row + 1][col + 1] == 3
                    ) or (
                        grid[row - 1][col + 1] == 3
                        and grid[row + 1][col - 1] == 3
                    )
                if matched:
                    stage[row][col] = 2
        return finish(stage)

    rivals = (nonlocal_vertical, vertical_or_diagonal)
    for seed in range(300):
        episode = proto.generate(seed, setting, demos=2, queries=4)
        for rival in rivals:
            assert any(
                rival(pair["input"]) != pair["output"]
                for pair in episode["train"]
            ), (seed, rival.__name__)


def test_minimum_lesson_requires_highlighting_off_chain_greens(proto):
    setting = {"endpoint_treatment": "highlight_busiest"}

    def endpoints_only(grid):
        stage = proto.stage_a(grid)
        winner = proto.busiest_activated_column(stage)
        endpoints = {
            endpoint
            for row, col in proto._targets(grid)
            if col == winner
            for endpoint in ((row - 1, col), (row + 1, col))
        }
        output = copy.deepcopy(stage)
        for row, col in endpoints:
            if output[row][col] == 3:
                output[row][col] = 1
        return output

    for seed in range(100):
        episode = proto.generate(seed, setting, demos=2, queries=4)
        assert any(
            endpoints_only(pair["input"]) != pair["output"]
            for pair in episode["train"]
        ), seed


def test_minimum_lesson_refutes_target_rank_and_scan_order_shortcuts(proto):
    setting = {"endpoint_treatment": "highlight_busiest"}

    def rival(grid, mode):
        stage = proto.stage_a(grid)
        targets = proto._targets(grid)
        if mode == "leftmost_target_column":
            column = min(col for _, col in targets)
        elif mode == "rightmost_target_column":
            column = max(col for _, col in targets)
        elif mode == "first_scan_target_column":
            column = targets[0][1]
        elif mode == "last_scan_target_column":
            column = targets[-1][1]
        else:
            raise AssertionError(mode)
        output = copy.deepcopy(stage)
        for row in range(len(output)):
            if output[row][column] == 3:
                output[row][column] = 1
        return output

    modes = (
        "leftmost_target_column",
        "rightmost_target_column",
        "first_scan_target_column",
        "last_scan_target_column",
    )
    for seed in range(100):
        episode = proto.generate(seed, setting, demos=2, queries=4)
        for mode in modes:
            assert any(
                rival(pair["input"], mode) != pair["output"]
                for pair in episode["train"]
            ), (seed, mode)


def test_same_profile_moves_winner_and_refutes_dimension_lookup(proto):
    # The profile dimensions/order are public. The stage-B selector must come
    # from the stage-A activations, not a hard-coded size -> column table.
    legacy_columns = {
        (9, 9): 5,
        (10, 12): 1,
        (12, 10): 8,
        (15, 16): 7,
        (18, 20): 2,
        (24, 24): 21,
        (8, 11): 1,
        (14, 17): 8,
        (21, 25): 23,
        (30, 30): 0,
    }
    winners = set()
    lookup_disagreements = 0
    setting = {"endpoint_treatment": "highlight_busiest"}
    for seed in range(24):
        episode = proto.generate(seed, setting, demos=2, queries=4)
        pair = episode["test"][0]
        grid = pair["input"]
        stage = proto.stage_a(grid)
        winner = proto.busiest_activated_column(stage)
        winners.add(winner)

        hard_coded = copy.deepcopy(stage)
        legacy = legacy_columns[(len(grid), len(grid[0]))]
        for row in range(len(hard_coded)):
            if hard_coded[row][legacy] == 3:
                hard_coded[row][legacy] = 1
        if hard_coded != pair["output"]:
            lookup_disagreements += 1

    assert len(winners) >= 4
    assert lookup_disagreements == 24


def test_queries_cover_boundaries_crossed_controls_and_substantive_30x30(proto):
    episode = proto.generate(43, {"endpoint_treatment": "highlight_busiest"}, demos=3, queries=4)
    winners = []
    most_green_columns = []
    for pair in episode["test"]:
        grid = pair["input"]
        stage_a = proto.stage_a(grid)
        winner = proto.busiest_activated_column(stage_a)
        winners.append(winner)
        green_counts = [sum(row[col] == 3 for row in grid) for col in range(len(grid[0]))]
        most_green_columns.append(max(range(len(green_counts)), key=lambda col: green_counts[col]))
        assert winner != most_green_columns[-1]
        assert proto.transform(grid, episode["settings"]) == pair["output"]
    assert len(set(winners)) >= 3

    grid = episode["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(occupied) >= 35
    assert min(r for r, _ in occupied) == 0 and max(r for r, _ in occupied) == 29
    assert min(c for _, c in occupied) == 0 and max(c for _, c in occupied) == 29


def test_first_turn_projection_hides_private_fields_future_queries_and_count(proto):
    episode = proto.generate(59, proto.DEFAULT, demos=3, queries=4)
    visible = proto.public_turn(episode, 0)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    body = public_challenge_bytes(visible)
    identifier = public_challenge_id(visible)

    changed = copy.deepcopy(episode)
    changed["settings"] = {"endpoint_treatment": "highlight_busiest"}
    changed["program_solution"] = "private-change"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[9]]
    assert public_challenge_bytes(proto.public_turn(changed, 0)) == body
    assert public_challenge_id(proto.public_turn(changed, 0)) == identifier
    assert b"settings" not in body and b"program_solution" not in body


def test_adapter_and_promotion_contract(proto):
    adapter = _load("parametric_1409_adapter", "adapter.py")
    episode = adapter.generate(5, proto.DEFAULT, 6, 4)
    assert len(episode["train"]) == 6 and len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program(proto.DEFAULT)
    promotion = json.loads((HERE / "promotion.json").read_text())
    assert promotion["default"] == proto.DEFAULT
    assert promotion["limits"] == {"demos": [2, 6], "queries": [4, 4]}


def test_protected_racket_matches_python_claims(proto):
    grids = [_decisive_grid()]
    episode = proto.generate(71, proto.DEFAULT, demos=2, queries=4)
    grids.extend(pair["input"] for pair in episode["test"])
    with proto.RacketRunner() as execute:
        for setting in proto.SETTINGS:
            for grid in grids:
                assert execute(proto.program(setting), grid) == proto.transform(grid, setting)
