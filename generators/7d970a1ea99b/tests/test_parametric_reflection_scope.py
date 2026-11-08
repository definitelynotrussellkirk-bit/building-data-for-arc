from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "7d970a1ea99b"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(filename: str, name: str):
    path = HOME / filename
    assert path.is_file(), f"missing parametric artifact: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load("prototype.py", "_parametric_7d970a1ea99b_test")


def _canonical_program():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError(TASK_ID)


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _decisive_grid():
    grid = [[0] * 8 for _ in range(8)]
    grid[3][3] = 2  # unique diagonal cue
    grid[0][5] = 2
    grid[6][1] = 2
    grid[1][7] = 4
    grid[5][2] = 6
    return grid


def test_default_program_is_exact_canonical_and_alternate_is_distinct(proto):
    assert proto.DEFAULT == {"reflection_scope": "all"}
    assert proto.program(proto.DEFAULT) == _canonical_program()
    assert len({proto.program(setting) for setting in proto.SETTINGS}) == 2


def test_cue_color_transform_uses_input_derived_intermediate(proto):
    grid = _decisive_grid()
    before = copy.deepcopy(grid)
    all_out = proto.transform(grid, {"reflection_scope": "all"})
    cue_out = proto.transform(grid, {"reflection_scope": "diagonal_cued"})
    assert grid == before
    assert proto.diagonal_cue_color(grid) == 2
    assert all_out[7][1] == 4 and all_out[2][5] == 6
    assert cue_out[5][0] == 2 and cue_out[1][6] == 2
    assert cue_out[7][1] == 0 and cue_out[2][5] == 0
    assert cue_out[1][7] == 4 and cue_out[5][2] == 6
    assert cue_out != all_out


def test_matched_inputs_count_independence_and_demo_identification(proto):
    all_short = proto.generate(17, {"reflection_scope": "all"}, demos=2, queries=4)
    cue_short = proto.generate(17, {"reflection_scope": "diagonal_cued"}, demos=2, queries=4)
    all_long = proto.generate(17, {"reflection_scope": "all"}, demos=6, queries=4)
    assert _inputs(all_short) == _inputs(cue_short)
    assert all_short["train"] == all_long["train"][:2]
    assert all_short["test"] == all_long["test"]
    assert len({proto.digest(grid) for grid in _inputs(all_short)}) == 6
    assert all_short["certificate"]["survivors"] == [{"reflection_scope": "all"}]
    assert cue_short["certificate"]["survivors"] == [{"reflection_scope": "diagonal_cued"}]
    assert all(result == "refuted" for result in cue_short["certificate"]["rivals"].values())


def test_two_demo_minimum_crosses_cue_color_and_frequency_rank(proto):
    episode = proto.generate(29, {"reflection_scope": "diagonal_cued"}, demos=2, queries=4)
    profiles = [proto.profile(pair["input"]) for pair in episode["train"]]
    assert profiles[0]["cue_color"] != profiles[1]["cue_color"]
    assert {row["cue_frequency_rank"] for row in profiles} >= {"least", "most"}
    assert profiles[0]["shape"] == profiles[1]["shape"]


def test_query_bank_has_substantive_boundary_spanning_30x30(proto):
    episode = proto.generate(41, proto.DEFAULT, demos=3, queries=4)
    stress = episode["test"][-1]["input"]
    output = episode["test"][-1]["output"]
    assert (len(stress), len(stress[0])) == (30, 30)
    occupied = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    painted = [(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value]
    assert len(occupied) >= 40 and len(painted) >= 70
    assert {min(r for r, _ in painted), max(r for r, _ in painted)} == {0, 29}
    assert {min(c for _, c in painted), max(c for _, c in painted)} == {0, 29}
    assert len({value for row in stress for value in row if value}) >= 4


def test_strict_settings_counts_and_grid_validation(proto):
    for settings in ({}, {"reflection_scope": "other"}, {"reflection_scope": 1},
                     {"reflection_scope": "all", "extra": 0}):
        with pytest.raises(ValueError):
            proto.program(settings)
    for key, value in (("seed", True), ("seed", 1.0), ("demos", 1), ("demos", 7),
                       ("queries", 0), ("queries", 5), ("queries", True)):
        kwargs = dict(seed=7, settings=proto.DEFAULT, demos=3, queries=4)
        kwargs[key] = value
        with pytest.raises(ValueError):
            proto.generate(**kwargs)
    bad = _decisive_grid()
    bad[4][4] = 3
    with pytest.raises(ValueError, match="exactly one nonzero diagonal cue"):
        proto.transform(bad, {"reflection_scope": "diagonal_cued"})


def test_first_turn_projection_hides_private_and_future_fields(proto):
    episode = proto.generate(53, {"reflection_scope": "diagonal_cued"}, demos=3, queries=4)
    visible = proto.public_turn(episode, 0)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    body = public_challenge_bytes(visible)
    identifier = public_challenge_id(visible)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"reflection_scope": "all"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[9]]
    assert public_challenge_bytes(proto.public_turn(changed, 0)) == body
    assert public_challenge_id(proto.public_turn(changed, 0)) == identifier


def test_adapter_contract_and_protected_racket_labels(proto):
    adapter = _load("adapter.py", "_parametric_7d970a1ea99b_adapter_test")
    promotion = json.loads((HOME / "promotion.json").read_text())
    assert promotion["default"] == proto.DEFAULT
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    episode = adapter.generate(61, {"reflection_scope": "diagonal_cued"}, 6, 4)
    assert len(episode["train"]) == 6 and len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program({"reflection_scope": "diagonal_cued"})

    with proto.RacketRunner() as run:
        for setting in proto.SETTINGS:
            assert run(proto.program(setting), _decisive_grid()) == proto.transform(_decisive_grid(), setting)
            grid = episode["test"][-1]["input"]
            assert run(proto.program(setting), grid) == proto.transform(grid, setting)
