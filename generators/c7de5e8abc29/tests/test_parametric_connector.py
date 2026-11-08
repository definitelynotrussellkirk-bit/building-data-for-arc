from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


REPO = find_root(__file__)
HERE = REPO / "generators/c7de5e8abc29/workspace/parametric"


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
    return _load("c7de_parametric_prototype", "prototype.py")


def _canonical_program() -> str:
    for line in canonical_path(REPO).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "c7de5e8abc29":
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def _decisive_grid() -> list[list[int]]:
    grid = [[0] * 8 for _ in range(8)]
    grid[1][1] = grid[3][3] = 2       # NW-SE diagonal
    grid[1][6] = grid[3][4] = 3       # NE-SW diagonal
    grid[5][1] = grid[5][5] = 4       # horizontal
    grid[2][7] = grid[6][7] = 6       # vertical
    return grid


def test_default_program_is_exact_canonical_authority(proto):
    assert proto.DEFAULT == {"alignment": "diagonal"}
    assert proto.program(proto.DEFAULT) == _canonical_program()
    assert len({proto.program(setting) for setting in proto.SETTINGS}) == 2


def test_alignment_transform_is_decisive_and_input_pure(proto):
    grid = _decisive_grid()
    before = copy.deepcopy(grid)
    diagonal = proto.transform(grid, {"alignment": "diagonal"})
    orthogonal = proto.transform(grid, {"alignment": "orthogonal"})

    assert grid == before
    assert diagonal[2][2] == 2 and diagonal[2][5] == 3
    assert diagonal[5][3] == 0 and diagonal[4][7] == 0
    assert orthogonal[5][3] == 4 and orthogonal[4][7] == 6
    assert orthogonal[2][2] == 0 and orthogonal[2][5] == 0
    assert diagonal != orthogonal


def test_strict_parameters_and_counts(proto):
    for settings in ({}, {"alignment": "both"}, {"alignment": 1},
                     {"alignment": "diagonal", "extra": 0}):
        with pytest.raises(ValueError):
            proto.program(settings)
    for key, value in (("seed", True), ("seed", 1.0), ("demos", 1),
                       ("demos", 7), ("demos", True), ("queries", 1),
                       ("queries", 5), ("queries", True)):
        kwargs = dict(seed=9, settings=proto.DEFAULT, demos=3, queries=4)
        kwargs[key] = value
        with pytest.raises(ValueError):
            proto.generate(**kwargs)


def test_generation_is_deterministic_identifiable_and_count_independent(proto):
    for setting in proto.SETTINGS:
        short = proto.generate(17, setting, demos=2, queries=4)
        long = proto.generate(17, setting, demos=6, queries=4)
        assert short == proto.generate(17, setting, demos=2, queries=4)
        assert short["train"] == long["train"][:2]
        assert short["test"] == long["test"]
        assert len(short["train"]) == 2 and len(short["test"]) == 4
        all_inputs = short["train"] + short["test"]
        assert len({proto.digest(pair["input"]) for pair in all_inputs}) == 6
        assert short["certificate"]["survivors"] == [setting]
        assert len(short["certificate"]["queries"]) == 4

        tampered = copy.deepcopy(short)
        tampered["train"][0]["output"] = [[9]]
        with pytest.raises(ValueError):
            proto.certify(tampered)


def test_four_queries_include_substantive_30x30_boundary_stress(proto):
    episode = proto.generate(31, proto.DEFAULT, demos=3, queries=4)
    grid = episode["test"][-1]["input"]
    output = episode["test"][-1]["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    painted = [(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value]
    assert len(painted) >= 70
    assert min(r for r, _ in painted) == 0 and max(r for r, _ in painted) == 29
    assert min(c for _, c in painted) == 0 and max(c for _, c in painted) == 29


def test_first_turn_projection_hides_answers_future_queries_and_count(proto):
    from reviewer_support import public_challenge_bytes, public_challenge_id

    episode = proto.generate(41, proto.DEFAULT, demos=3, queries=4)
    visible = proto.public_turn(episode, 0)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    body = public_challenge_bytes(visible)
    identifier = public_challenge_id(visible)

    changed = copy.deepcopy(episode)
    changed["settings"] = {"alignment": "orthogonal"}
    changed["program_solution"] = "private-change"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[9]]
    assert public_challenge_bytes(proto.public_turn(changed, 0)) == body
    assert public_challenge_id(proto.public_turn(changed, 0)) == identifier
    assert b"program_solution" not in body and b"settings" not in body


def test_adapter_maximum_counts_and_promotion_contract(proto):
    adapter = _load("c7de_parametric_adapter", "adapter.py")
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
