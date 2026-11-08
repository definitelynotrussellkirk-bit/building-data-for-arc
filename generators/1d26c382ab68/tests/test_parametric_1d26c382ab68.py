"""Observable native-adapter, geometry, teaching and public-view regressions."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
DEFAULT = {"target": "rotation_match"}
COMPOSED = {"target": "turn_guided_reflection"}


def test_main_has_native_adapter():
    assert (HOME / "workspace/parametric/adapter.py").is_file(), "MAIN lacks a native parametric adapter"


@pytest.fixture(scope="module")
def adapter():
    path = HOME / "workspace/parametric/adapter.py"
    assert path.is_file(), "MAIN lacks a native parametric adapter"
    spec = importlib.util.spec_from_file_location("tested_rotation_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_scene():
    # Hand-written P/F pentominoes: first lower P is a clockwise quarter turn.
    template = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)]
    shapes = [
        [(0, 0), (0, 1), (0, 2), (1, 1), (1, 2)],  # R(P)
        [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],  # R(F(P))
        [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)],  # F(R(P))
        [(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)],  # F-pentomino
        [(0, 0), (0, 1), (1, 1), (1, 2), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (2, 1), (2, 2)],
    ]
    grid = [[0] * 13 for _ in range(12)]
    grid[3] = [9] * 13
    for row, col in template:
        grid[row][col + 4] = 1
    cells = []
    for slot, shape in enumerate(shapes):
        top, left = 4 + 4 * (slot // 3), 4 * (slot % 3)
        positions = [(top + row, left + col) for row, col in shape]
        cells.append(positions)
        for row, col in positions:
            grid[row][col] = 8
    return grid, cells


def paint(grid, cells):
    output = deepcopy(grid)
    for row, col in cells:
        output[row][col] = 2
    return output


def test_default_is_exact_selected_canonical_program(adapter):
    rows = [json.loads(line) for line in
            (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()]
    selected = [row["program_solution"] for row in rows
                if row["task_id"] == "1d26c382ab68"]
    assert selected and set(selected) == {adapter.program(DEFAULT)}


def test_hand_checked_order_sensitive_selection(adapter):
    grid, cells = fixture_scene()
    assert adapter.expected_output(grid, DEFAULT) == paint(grid, cells[0])
    assert adapter.expected_output(grid, COMPOSED) == paint(grid, cells[1])
    # Reflecting the already rotated match chooses another real candidate.
    assert adapter.rival_outputs(grid)["reflect_match"] == paint(grid, cells[2])


def test_protected_racket_on_literal_fixture(adapter):
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        grid, cells = fixture_scene()
        assert identity["protected"] is True
        assert apply(adapter.program(DEFAULT), grid) == paint(grid, cells[0])
        assert apply(adapter.program(COMPOSED), grid) == paint(grid, cells[1])
        assert apply(adapter.counterfactual_program("wrong_order"), grid) == paint(grid, cells[2])
    finally:
        bridge.close()


@pytest.mark.parametrize("seed", [0, 17, 934])
@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_counts_distinctness_matched_inputs_and_teaching(adapter, seed, demos):
    episodes = [adapter.generate(seed, setting, demos, 4)
                for setting in (DEFAULT, COMPOSED)]
    for episode in episodes:
        assert len(episode["train"]) == demos and len(episode["test"]) == 4
        pairs = episode["train"] + episode["test"]
        keys = [json.dumps(pair["input"]) for pair in pairs]
        assert len(keys) == len(set(keys))
        assert adapter.teaching_check(episode)["ambiguities"] == []
        assert [len(pair["input"]) for pair in episode["test"]] == [11, 20, 24, 30]
        first, second = episode["train"][:2]
        sep = next(i for i, row in enumerate(first["input"]) if set(row) == {9})
        assert first["input"][sep:] == second["input"][sep:]
        assert first["output"][sep:] != second["output"][sep:]
        stress = episode["test"][-1]["input"]
        assert len(stress) == len(stress[0]) == 30
        assert sum(value not in (0, 9) for row in stress for value in row) >= 300
    assert [p["input"] for p in episodes[0]["train"] + episodes[0]["test"]] == [
        p["input"] for p in episodes[1]["train"] + episodes[1]["test"]]


def test_determinism_and_query_count_does_not_change_first_turn(adapter):
    for setting in (DEFAULT, COMPOSED):
        one = adapter.generate(17, setting, 3, 1)
        four = adapter.generate(17, setting, 3, 4)
        assert four == adapter.generate(17, setting, 3, 4)
        assert public_challenge_bytes(adapter.model_view(one, 0)) == public_challenge_bytes(
            adapter.model_view(four, 0))
        assert one["train"] == four["train"] and one["test"][0] == four["test"][0]


def test_public_projection_is_private_invariant_and_one_query_only(adapter):
    episode = adapter.generate(19, COMPOSED, 3, 4)
    visible = adapter.model_view(episode, 0)
    altered = deepcopy(episode)
    altered.update(settings={"secret": "changed"}, seed=789, program_solution="private")
    altered["train"][0]["private_program"] = "must not enter a model turn"
    for pair in altered["test"]:
        pair["output"] = [[7]]
    altered["test"][1:]=[{"input": [[6]], "output": [[5]]}]
    assert adapter.model_view(altered, 0) == visible
    assert public_challenge_bytes(visible) == public_challenge_bytes(adapter.model_view(altered, 0))
    assert public_challenge_id(visible) == public_challenge_id(adapter.model_view(altered, 0))
    assert set(visible) == {"train", "test"} and len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}
    visible["train"][0]["input"][0][0] = 7
    assert episode["train"][0]["input"] != visible["train"][0]["input"]


@pytest.mark.parametrize("demos,queries", [(1,4),(7,4),(True,4),(3,0),(3,5),(3,False)])
def test_bad_counts_fail_loudly(adapter, demos, queries):
    with pytest.raises(ValueError):
        adapter.generate(0, DEFAULT, demos, queries)


@pytest.mark.parametrize("settings", [{}, {"target": True}, {"target":"unknown"},
                                      {"target":"rotation_match", "extra": 1}])
def test_bad_settings_fail_loudly(adapter, settings):
    with pytest.raises(ValueError):
        adapter.program(settings)


def test_bad_seed_and_non_integer_grid_fail_loudly(adapter):
    for seed in (True, -1, 2**63, 1.5):
        with pytest.raises(ValueError):
            adapter.generate(seed, DEFAULT, 3, 4)
    grid, _ = fixture_scene()
    for value in (False, 0.0, 10):
        bad = deepcopy(grid)
        bad[0][0] = value
        with pytest.raises(ValueError):
            adapter.expected_output(bad, DEFAULT)
