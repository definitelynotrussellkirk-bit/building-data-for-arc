"""Public transport must expose exactly one query and only known labels."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1] / "workspace/parametric"


def _load(name):
    path = BASE / name
    assert path.is_file(), f"missing reusable export verifier: {path}"
    spec = importlib.util.spec_from_file_location("_a85_export_" + path.stem, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_projection_masks_answers_future_inputs_and_private_metadata():
    native = _load("native.py")
    verifier = _load("verify_native.py")
    episode = native.generate(17, {"axis_tolerance": "target_panel_count"}, 4, 4)
    first = native.public_turn(episode)
    verifier.validate_turn(first, episode, 0)
    truncated = deepcopy(episode)
    truncated["test"] = truncated["test"][:1]
    assert native.public_turn(truncated) == first
    changed = deepcopy(episode)
    changed["settings"] = {"axis_tolerance": 999}
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[0]]
    changed["test"][1:] = [{"input": [[0]], "output": [[1]]}]
    assert native.public_turn(changed) == first
    for index in range(4):
        turn = native.public_turn(episode, index)
        assert set(turn) == {"train", "test"}
        assert len(turn["test"]) == 1
        assert turn["test"][0] == {"input": episode["test"][index]["input"]}
        verifier.validate_turn(turn, episode, index)


@pytest.mark.parametrize("mutation", ("answer", "future", "settings", "demo_program", "wrong_query", "bool_cell"))
def test_export_verifier_rejects_leaks_and_wrong_projection(mutation):
    native = _load("native.py")
    verifier = _load("verify_native.py")
    episode = native.generate(0, {"axis_tolerance": 1}, 4, 4)
    public = native.public_turn(episode)
    if mutation == "answer":
        public["test"][0]["output"] = episode["test"][0]["output"]
    elif mutation == "future":
        public["test"].append({"input": episode["test"][1]["input"]})
    elif mutation == "settings":
        public["settings"] = {"axis_tolerance": 1}
    elif mutation == "demo_program":
        public["train"][0]["program"] = episode["program_solution"]
    elif mutation == "wrong_query":
        public["test"][0]["input"] = episode["test"][1]["input"]
    else:
        public["test"][0]["input"][0][0] = True
    with pytest.raises(ValueError):
        verifier.validate_turn(public, episode, 0)
