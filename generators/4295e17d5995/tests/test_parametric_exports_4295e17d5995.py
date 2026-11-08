"""Public projection regressions for the task-local parametric audit writer."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def writer():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/audit.py"
    if not path.exists():
        pytest.fail("The task-local public example writer is not implemented")
    spec = importlib.util.spec_from_file_location("wall_audit_exports", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture():
    return {
        "train": [
            {"input": [[2, 7, 4]], "output": [[2, 7, 4]]},
            {"input": [[3, 7, 6]], "output": [[3, 7, 6]]},
        ],
        "test": [
            {"input": [[1, 7, 8]], "output": [[1, 8, 8]]},
            {"input": [[9, 7, 0]], "output": [[9, 9, 0]]},
        ],
        "settings": {"wall_relation": "matching"},
        "seed": 29,
        "program": "private reference",
    }


def test_first_view_contains_only_demonstrations_and_selected_input():
    value = writer().public_bytes(fixture(), query_index=0)
    expected = (b'{"test":[{"input":[[1,7,8]]}],"train":'
                b'[{"input":[[2,7,4]],"output":[[2,7,4]]},'
                b'{"input":[[3,7,6]],"output":[[3,7,6]]}]}\n')
    assert value == expected


def test_first_view_and_id_ignore_private_labels_and_unrevealed_queries():
    module = writer()
    first = fixture()
    changed = deepcopy(first)
    changed.update(settings={"wall_relation": "opposite"}, seed=999, program="another private rule")
    changed["test"][0]["output"] = [[9, 9, 9]]
    changed["test"][1]["input"] = [[8, 8, 8]]
    changed["test"].append({"input": [[5, 5, 5]], "output": [[6, 6, 6]]})
    assert module.public_bytes(first, query_index=0) == module.public_bytes(changed, query_index=0)


def test_writer_publishes_exact_content_hashes_and_separate_private_data(tmp_path):
    module = writer()
    out = tmp_path / "examples"
    module.write_examples([fixture()], out)
    public = list((out / "public").glob("*.json"))
    initial = list((out / "first_turn").glob("*.json"))
    assert len(public) == len(initial) == 1
    for path in public + initial:
        assert path.stem == hashlib.sha256(path.read_bytes()).hexdigest()
        payload = json.loads(path.read_bytes())
        assert set(payload) == {"train", "test"}
        assert all(set(pair) == {"input"} for pair in payload["test"])
    assert len(json.loads(initial[0].read_bytes())["test"]) == 1
    private = json.loads((out / "episodes.private.json").read_text())
    assert private[0]["settings"] == {"wall_relation": "matching"}
    assert private[0]["test"][1]["output"] == [[9, 9, 0]]


def test_duplicate_public_episodes_reject_before_creating_destination(tmp_path):
    module = writer()
    first = fixture()
    changed = deepcopy(first)
    changed["settings"] = {"wall_relation": "opposite"}
    changed["test"][0]["output"] = [[0, 0, 0]]
    out = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate"):
        module.write_examples([first, changed], out)
    assert not out.exists()


def test_same_first_turn_with_different_future_query_is_also_duplicate(tmp_path):
    module = writer()
    first = fixture()
    changed = deepcopy(first)
    changed["test"][1]["input"] = [[6, 7, 8]]
    out = tmp_path / "duplicate-first"
    with pytest.raises(ValueError, match="duplicate first-turn"):
        module.write_examples([first, changed], out)
    assert not out.exists()


def test_proposal_writer_does_not_repeat_native_worker_acceptance_label(tmp_path):
    module = writer()
    episode = fixture()
    episode["reference"] = "accepted_parametric"
    out = tmp_path / "proposal"
    module.write_examples([episode], out)
    private = json.loads((out / "episodes.private.json").read_text())
    assert private[0]["reference"] == "proposed_parametric"
    assert private[0]["native_worker_reference"] == "accepted_parametric"
    assert private[0]["training_admitted"] is False
