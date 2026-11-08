from __future__ import annotations

import copy
import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


REPO = find_root(__file__)
HERE = REPO / "generators/d00138abe18b/workspace/parametric"


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
    return _load("d001_parametric_prototype", "prototype.py")


def _canonical_program() -> str:
    for line in canonical_path(REPO).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "d00138abe18b":
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _decisive_grid() -> list[list[int]]:
    return [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 4, 4, 3, 0, 0, 0],  # left=2, right=3, mode=4
        [0, 0, 5, 6, 6, 7, 0, 0],  # left=5, right=7, mode=6
        [8, 1, 1, 9, 0, 0, 0, 0],  # left=8, right=9, mode=1
        [0, 2, 5, 5, 3, 0, 0, 0],  # repeated left/right values
        [0, 0, 7, 8, 8, 6, 0, 0],  # deliberately unsorted edge order
    ]


def _edges(grid: list[list[int]]) -> tuple[list[int], list[int], list[int]]:
    left: list[int] = []
    right: list[int] = []
    modes: list[int] = []
    for row in grid:
        values = [value for value in row if value]
        if not values:
            continue
        left.append(values[0])
        right.append(values[-1])
        counts = Counter(values)
        modes.append(max(counts, key=lambda value: (counts[value], -values.index(value))))
    return left, right, modes


def test_default_program_is_exact_canonical_authority(proto):
    assert proto.DEFAULT == {"read_side": "left", "row_order": "top_down"}
    assert proto.program(proto.DEFAULT) == _canonical_program()
    signatures = {(s["read_side"], s["row_order"]) for s in proto.SETTINGS}
    assert signatures == {
        ("left", "top_down"), ("left", "bottom_up"),
        ("right", "top_down"), ("right", "bottom_up"),
    }
    assert len({proto.program(setting) for setting in proto.SETTINGS}) == 4


def test_transform_exposes_all_four_rule_signatures_and_is_input_pure(proto):
    grid = _decisive_grid()
    before = copy.deepcopy(grid)
    expected = {
        ("left", "top_down"): [[2], [5], [8], [2], [7]],
        ("left", "bottom_up"): [[7], [2], [8], [5], [2]],
        ("right", "top_down"): [[3], [7], [9], [3], [6]],
        ("right", "bottom_up"): [[6], [3], [9], [7], [3]],
    }
    for side, order in expected:
        assert proto.transform(grid, {"read_side": side, "row_order": order}) == expected[(side, order)]
    assert grid == before
    assert len({json.dumps(value) for value in expected.values()}) == 4


def test_generated_rows_defeat_mode_dedup_and_sort_shortcuts(proto):
    for setting in proto.SETTINGS:
        episode = proto.generate(19, setting, demos=2, queries=4)
        assert episode["certificate"]["shortcut_survivors"] == []
        for pair in episode["train"]:
            left, right, modes = _edges(pair["input"])
            chosen = left if setting["read_side"] == "left" else right
            if setting["row_order"] == "bottom_up":
                chosen = list(reversed(chosen))
                modes = list(reversed(modes))
            assert chosen != modes
            assert len(set(chosen)) < len(chosen)
            assert chosen != sorted(chosen) and chosen != sorted(chosen, reverse=True)
            assert all(len({v for v in row if v}) == 3 for row in pair["input"] if any(row))


def test_strict_parameters_and_counts(proto):
    bad_settings = (
        {}, {"read_side": "middle", "row_order": "top_down"},
        {"read_side": "left", "row_order": "forward"},
        {"read_side": 1, "row_order": "top_down"},
        {"read_side": "left", "row_order": "top_down", "extra": 0},
    )
    for settings in bad_settings:
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


def test_four_queries_include_substantive_30x30_row_stress(proto):
    episode = proto.generate(31, proto.DEFAULT, demos=3, queries=4)
    grid = episode["test"][-1]["input"]
    output = episode["test"][-1]["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    nonempty = [r for r, row in enumerate(grid) if any(row)]
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(nonempty) >= 20 and len(output) == len(nonempty)
    assert min(r for r, _ in occupied) == 0 and max(r for r, _ in occupied) == 29
    assert min(c for _, c in occupied) == 0 and max(c for _, c in occupied) == 29


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
    changed["settings"] = {"read_side": "right", "row_order": "bottom_up"}
    changed["program_solution"] = "private-change"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[9]]
    assert public_challenge_bytes(proto.public_turn(changed, 0)) == body
    assert public_challenge_id(proto.public_turn(changed, 0)) == identifier
    assert b"program_solution" not in body and b"settings" not in body


def test_adapter_maximum_counts_and_promotion_contract(proto):
    adapter = _load("d001_parametric_adapter", "adapter.py")
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
    decisive = _decisive_grid()
    episode = proto.generate(53, proto.DEFAULT, demos=2, queries=4)
    with proto.RacketRunner() as run:
        for setting in proto.SETTINGS:
            assert run(proto.program(setting), decisive) == proto.transform(decisive, setting)
            grid = episode["test"][-1]["input"]
            assert run(proto.program(setting), grid) == proto.transform(grid, setting)
