from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


REPO = find_root(__file__)
HERE = REPO / "generators/c7f337af82e5/workspace/parametric"


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
    return _load("c7f_parametric_prototype", "prototype.py")


def _canonical_program() -> str:
    for line in canonical_path(REPO).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "c7f337af82e5":
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _decisive_grid(control: int) -> list[list[int]]:
    grid = [[0] * 10 for _ in range(8)]
    grid[0][0] = control
    # 3x3 hollow frame.
    for r in range(0, 3):
        for c in range(2, 5):
            if r in (0, 2) or c in (2, 4):
                grid[r][c] = 7
    # 3x3 filled rectangle.
    for r in range(4, 7):
        for c in range(6, 9):
            grid[r][c] = 7
    return grid


def _positions(grid: list[list[int]], value: int) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(grid) for c, cell in enumerate(row) if cell == value}


def test_default_program_is_exact_canonical_authority(proto):
    assert proto.DEFAULT == {"mapping": "standard"}
    assert proto.program(proto.DEFAULT) == _canonical_program()
    assert proto.SETTINGS == [{"mapping": "standard"}, {"mapping": "reversed"}]
    assert len({proto.program(setting) for setting in proto.SETTINGS}) == 2


def test_mapping_transform_switches_selected_shape_and_is_input_pure(proto):
    for control in (1, 2):
        grid = _decisive_grid(control)
        before = copy.deepcopy(grid)
        standard = proto.transform(grid, {"mapping": "standard"})
        reversed_result = proto.transform(grid, {"mapping": "reversed"})
        assert grid == before
        assert standard[0][0] == 0 and reversed_result[0][0] == 0
        standard_eights = _positions(standard, 8)
        reversed_eights = _positions(reversed_result, 8)
        assert standard_eights and reversed_eights and standard_eights.isdisjoint(reversed_eights)
        if control == 1:
            assert (1, 2) in standard_eights and (5, 7) in reversed_eights
        else:
            assert (5, 7) in standard_eights and (1, 2) in reversed_eights


def test_minimum_lesson_teaches_both_control_branches_and_mapping(proto):
    for setting in proto.SETTINGS:
        episode = proto.generate(19, setting, demos=2, queries=4)
        assert [pair["input"][0][0] for pair in episode["train"]] == [1, 2]
        assert episode["certificate"]["survivors"] == [setting]
        assert episode["certificate"]["shortcut_survivors"] == []
        for pair in episode["train"]:
            components = proto.describe_components(pair["input"])
            assert any(component["hollow"] for component in components)
            assert any(not component["hollow"] for component in components)
            assert {component["color"] for component in components} == {7}


def test_strict_parameters_and_counts(proto):
    for settings in ({}, {"mapping": "other"}, {"mapping": 1},
                     {"mapping": "standard", "extra": 0}):
        with pytest.raises(ValueError):
            proto.program(settings)
    for key, value in (
        ("seed", True), ("seed", 1.0), ("demos", 1), ("demos", 7),
        ("demos", True), ("queries", 1), ("queries", 5), ("queries", True),
    ):
        kwargs = dict(seed=9, settings=proto.DEFAULT, demos=3, queries=4)
        kwargs[key] = value
        with pytest.raises(ValueError):
            proto.generate(**kwargs)


def test_generation_is_deterministic_count_independent_and_identifiable(proto):
    for setting in proto.SETTINGS:
        short = proto.generate(17, setting, demos=2, queries=4)
        long = proto.generate(17, setting, demos=6, queries=4)
        assert short == proto.generate(17, setting, demos=2, queries=4)
        assert short["train"] == long["train"][:2]
        assert short["test"] == long["test"]
        assert len(short["train"]) == 2 and len(short["test"]) == 4
        all_pairs = short["train"] + short["test"]
        assert len({proto.digest(pair["input"]) for pair in all_pairs}) == 6
        assert short["certificate"]["survivors"] == [setting]
        assert len(short["certificate"]["queries"]) == 4

        tampered = copy.deepcopy(short)
        tampered["train"][0]["output"] = [[9]]
        with pytest.raises(ValueError):
            proto.certify(tampered)


def test_four_queries_include_substantive_30x30_slot_stress(proto):
    for setting in proto.SETTINGS:
        episode = proto.generate(31, setting, demos=3, queries=4)
        grid = episode["test"][-1]["input"]
        output = episode["test"][-1]["output"]
        assert (len(grid), len(grid[0])) == (30, 30)
        orange = _positions(grid, 7)
        cyan = _positions(output, 8)
        assert len(proto.describe_components(grid)) >= 5
        assert len(orange) >= 250 and len(cyan) >= 80
        assert {r for r, _ in orange} >= {0, 29}
        assert {c for _, c in orange} >= {0, 29}
        assert {r for r, _ in cyan} >= {0, 29}
        assert {c for _, c in cyan} >= {0, 29}


def test_first_turn_projection_hides_answers_future_queries_and_count(proto):
    from reviewer_support import public_challenge_bytes, public_challenge_id

    episode = proto.generate(41, proto.DEFAULT, demos=3, queries=4)
    visible = proto.public_turn(episode, 0)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    body = public_challenge_bytes(visible)
    identifier = public_challenge_id(visible)

    changed = copy.deepcopy(episode)
    changed["settings"] = {"mapping": "reversed"}
    changed["program_solution"] = "private-change"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[9]]
    assert public_challenge_bytes(proto.public_turn(changed, 0)) == body
    assert public_challenge_id(proto.public_turn(changed, 0)) == identifier
    assert b"program_solution" not in body and b"settings" not in body


def test_adapter_maximum_counts_and_promotion_contract(proto):
    adapter = _load("c7f_parametric_adapter", "adapter.py")
    episode = adapter.generate(5, proto.DEFAULT, 6, 4)
    assert (len(episode["train"]), len(episode["test"])) == (6, 4)
    assert episode["program_solution"] == adapter.program(proto.DEFAULT)
    promotion = json.loads((HERE / "promotion.json").read_text())
    assert promotion["default"] == proto.DEFAULT
    assert promotion["limits"] == {"demos": [2, 6], "queries": [4, 4]}



def test_batch_rejects_duplicate_public_challenges_without_partial_output(proto, tmp_path):
    episode = proto.generate(67, proto.DEFAULT, demos=2, queries=4)
    same_public_different_private = copy.deepcopy(episode)
    same_public_different_private["review_marker"] = "different private record"
    assert proto.public_turn(episode, 0) == proto.public_turn(same_public_different_private, 0)
    destination = tmp_path / "duplicate-batch"
    with pytest.raises(ValueError, match="distinct first-turn challenges"):
        proto.write_batch([episode, same_public_different_private], destination)
    assert not destination.exists()

def test_protected_racket_matches_mirror(proto):
    episode = proto.generate(53, proto.DEFAULT, demos=2, queries=4)
    with proto.RacketRunner() as run:
        for setting in proto.SETTINGS:
            for control in (1, 2):
                decisive = _decisive_grid(control)
                assert run(proto.program(setting), decisive) == proto.transform(decisive, setting)
            grid = episode["test"][-1]["input"]
            assert run(proto.program(setting), grid) == proto.transform(grid, setting)
