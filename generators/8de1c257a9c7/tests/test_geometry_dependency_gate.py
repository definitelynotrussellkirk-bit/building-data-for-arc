"""Behavior tests for the opt-in count-blind geometry teaching gate."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root

ROOT = find_root(__file__)
PATH = ROOT / "generators/8de1c257a9c7/workspace/parametric/check_geometry_gate.py"


@pytest.fixture(scope="module")
def gate():
    spec = importlib.util.spec_from_file_location("geometry_gate_tests", PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def pair(offsets, *, red=(4, 4)):
    source = [[0] * 7 for _ in range(7)]
    source[1][1] = 3
    source[red[0]][red[1]] = 2
    output = [[0] * 7 for _ in range(7)]
    for dr, dc in offsets:
        source[1 + dr][1 + dc] = 8
        output[red[0] + dr][red[1] + dc] = 8
    return {"input": source, "output": output}


def test_equal_count_geometry_intervention_passes(gate):
    a = pair([(0, 1), (1, 1)])
    b = pair([(1, 0), (1, 1)])
    result = gate.check_episode({"train": [a, b]})
    assert result["status"] == "passed"
    assert result["witnesses"][0]["demo_indices"] == [0, 1]
    assert result["witnesses"][0]["blind_features"]["cyan_count"] == 2


def test_changed_destinations_do_not_establish_geometry_dependency(gate):
    a = pair([(0, 1), (1, 1)])
    b = pair([(1, 0), (1, 1)], red=(5, 4))
    assert gate.check_episode({"train": [a, b]})["status"] == "missing_geometry_contrast"


def test_query_contrast_cannot_rescue_untaught_demonstrations(gate):
    a = pair([(0, 1), (1, 1)])
    b = pair([(1, 0), (1, 1)])
    result = gate.check_episode({"train": [a, deepcopy(a)], "test": [b]})
    assert result["status"] == "missing_geometry_contrast"
    assert result["witnesses"] == []


def test_equal_outputs_do_not_establish_observable_dependency(gate):
    a = pair([(0, 1), (1, 1)])
    b = pair([(1, 0), (1, 1)])
    b["output"] = deepcopy(a["output"])
    assert gate.check_episode({"train": [a, b]})["status"] == "missing_geometry_contrast"


def test_duplicate_input_with_conflicting_labels_is_not_a_witness(gate):
    a = pair([(0, 1), (1, 1)])
    b = deepcopy(a)
    b["output"][0][0] = 8
    assert gate.check_episode({"train": [a, b]})["status"] == "missing_geometry_contrast"


@pytest.mark.parametrize("bad", [True, 3.0, "3"])
def test_coercible_grid_cells_rejected(gate, bad):
    a = pair([(0, 1), (1, 1)])
    a["input"][1][1] = bad
    with pytest.raises((TypeError, ValueError)):
        gate.check_episode({"train": [a]})


def test_private_metadata_does_not_change_result_or_inputs(gate):
    episode = {"train": [pair([(0, 1), (1, 1)]), pair([(1, 0), (1, 1)])]}
    before = deepcopy(episode)
    result = gate.check_episode(episode)
    assert episode == before
    episode.update({"settings": {"stamp_transform": "invented"}, "seed": True})
    assert gate.check_episode(episode) == result


def test_gate_is_explicitly_not_a_reference_verifier(gate):
    result = gate.check_episode({"train": [pair([(0, 1), (1, 1)]), pair([(1, 0), (1, 1)])]})
    assert result["reference_labels_reexecuted"] is False
    assert "finite-bank" in result["possible_false_positive"]
