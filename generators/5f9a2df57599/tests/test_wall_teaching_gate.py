"""The cheap gate reads demonstrations, not private answers or execution claims."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/check_wall_teaching.py"


@pytest.fixture(scope="module")
def gate():
    spec = importlib.util.spec_from_file_location("wall_teaching_gate", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lesson(*, large=True, rejected=True, same_shape=True):
    grid = [[5] * 18 for _ in range(12)]
    output = deepcopy(grid)
    if large:
        for row in range(1, 6):
            for col in range(1, 6):
                grid[row][col] = 0
                output[row][col] = 4
    if rejected:
        for row, col in [(8, 10), (8, 11), (9, 10)]:
            grid[row][col] = output[row][col] = 0
        grid[10][11] = 0  # Separate singleton breaks the L's full bottom side.
        output[10][11] = 4
    if same_shape:
        for row, col in [(8, 5), (8, 6), (9, 5)]:
            grid[row][col] = 0
            output[row][col] = 4
    return {"train": [{"input": grid, "output": output}], "test": []}


def test_both_size_counterexamples_are_required(gate):
    result = gate.check_episode(lesson())
    assert result["status"] == "passed"
    assert len(result["large_painted_regions"]) == 1
    assert len(result["small_rejected_wall_regions"]) == 1
    assert gate.check_episode(lesson(large=False))["status"] == "missing_contrast"
    assert gate.check_episode(lesson(rejected=False))["status"] == "missing_contrast"


def test_identical_shape_must_have_opposite_wall_outcomes(gate):
    assert gate.check_episode(lesson(same_shape=False))["status"] == "missing_contrast"
    result = gate.check_episode(lesson())
    assert len(result["matched_shape_wall_contrasts"]) == 1
    assert result["matched_shape_wall_contrasts"][0]["normalized_cells"] == [[0, 0], [0, 1], [1, 0]]


def test_gate_ignores_queries_and_private_metadata_and_does_not_mutate(gate):
    data = lesson()
    expected = gate.check_episode(data)
    data["test"] = [{"input": "invalid", "output": "never inspect"}]
    data["private"] = {"settings": "different", "program": "not executed"}
    before = deepcopy(data)
    assert gate.check_episode(data) == expected
    assert data == before


def test_literal_integer_grids_and_component_labels_are_required(gate):
    data = lesson()
    data["train"][0]["input"][0][0] = False
    with pytest.raises(ValueError, match="integer"):
        gate.check_episode(data)
    data = lesson()
    data["train"][0]["output"][1][1] = 0
    with pytest.raises(ValueError, match="component"):
        gate.check_episode(data)


def test_rejected_canvas_edge_is_not_a_wall_quantification_contrast(gate):
    data = lesson(rejected=False)
    for row in (8, 9):
        for col in (0, 1):
            data["train"][0]["input"][row][col] = 0
            data["train"][0]["output"][row][col] = 0
    result = gate.check_episode(data)
    assert result["small_rejected_wall_regions"] == []
    assert result["status"] == "missing_contrast"


def test_reader_accepts_native_jsonl_wrappers_and_episode_collections(gate, tmp_path):
    path = tmp_path / "native.jsonl"
    path.write_text(json.dumps({"public_id": "opaque", "episode": lesson()}) + "\n")
    assert gate.read_episodes(path) == [lesson()]
    path = tmp_path / "report.json"
    path.write_text(json.dumps({"episodes": [lesson(), lesson()]}))
    assert len(gate.read_episodes(path)) == 2


def test_no_demonstrations_and_gray_mutation_are_rejected(gate):
    with pytest.raises(ValueError, match="demonstration"):
        gate.check_episode({"train": []})
    data = lesson()
    data["train"][0]["output"][0][0] = 4
    with pytest.raises(ValueError, match="gray"):
        gate.check_episode(data)
