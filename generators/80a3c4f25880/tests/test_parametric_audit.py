"""Integrity boundaries of the task-local audit; no Racket needed here."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/audit.py"


@pytest.fixture
def audit():
    assert PATH.is_file(), "Task-local executable audit is required"
    spec = importlib.util.spec_from_file_location("audit_80a3c4f25880_test", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode():
    return {"seed": 17, "settings": {"selection": "canonical"},
            "program_solution": "(rule! g)",
            "train": [{"input": [[i]], "output": [[i]]} for i in range(3)],
            "test": [{"input": [[i]], "output": [[i]]} for i in range(3, 7)]}


def execute_identity(_program, grid):
    return deepcopy(grid)


def project(value, index):
    return {"train": deepcopy(value["train"]),
            "test": [{"input": deepcopy(value["test"][index]["input"])}]}


def test_replayed_labels_are_required(audit):
    original = episode()
    checked = audit.verify_episode(original, "(rule! g)", execute_identity, demos=3, queries=4)
    assert checked["test"][-1]["output"] == [[6]]
    original["test"][0]["output"] = [[9]]
    with pytest.raises(ValueError, match="label"):
        audit.verify_episode(original, "(rule! g)", execute_identity, demos=3, queries=4)


def test_bool_grid_and_duplicate_input_are_rejected(audit):
    value = episode()
    value["train"][0]["input"] = [[True]]
    with pytest.raises(ValueError, match="grid"):
        audit.verify_episode(value, "(rule! g)", execute_identity, demos=3, queries=4)
    value = episode()
    value["test"][0]["input"] = value["train"][0]["input"]
    with pytest.raises(ValueError, match="distinct|duplicate"):
        audit.verify_episode(value, "(rule! g)", execute_identity, demos=3, queries=4)


@pytest.mark.parametrize("leak", ["settings", "query_output", "second_query", "demo_metadata"])
def test_public_projection_rejects_private_or_future_fields(audit, leak):
    visible = project(episode(), 0)
    if leak == "settings":
        visible["settings"] = {"selection": "secret"}
    elif leak == "query_output":
        visible["test"][0]["output"] = [[3]]
    elif leak == "second_query":
        visible["test"].append({"input": [[4]]})
    else:
        visible["train"][0]["seed"] = 17
    with pytest.raises(ValueError, match="public|query|visible"):
        audit.public_bytes(visible)


def test_exact_public_bytes_and_forged_id(audit):
    visible = project(episode(), 0)
    raw = audit.public_bytes(visible)
    expected = b'{"test":[{"input":[[3]]}],"train":[{"input":[[0]],"output":[[0]]},{"input":[[1]],"output":[[1]]},{"input":[[2]],"output":[[2]]}]}\n'
    assert raw == expected
    identifier = hashlib.sha256(expected).hexdigest()
    assert audit.verify_public_bytes(raw, identifier) == visible
    with pytest.raises(ValueError, match="identity|ID|hash"):
        audit.verify_public_bytes(raw, "f" * 64)
    visible["test"][0]["input"] = [[False]]
    with pytest.raises(ValueError, match="grid"):
        audit.public_bytes(visible)


def test_serialized_export_checks_projection_and_private_label_hash(audit, tmp_path):
    destination = tmp_path / "export"
    audit.export_episodes([episode()], destination, project)
    verified = audit.verify_export(destination)
    assert verified["public_count"] == 4
    files = sorted((destination / "public").glob("*.json"))
    assert len(files) == 4
    for path in files:
        visible = json.loads(path.read_bytes())
        assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
        assert hashlib.sha256(path.read_bytes()).hexdigest() == path.stem
    private_path = destination / "private.json"
    private = json.loads(private_path.read_bytes())
    private["episodes"][0]["test"][0]["output"] = [[9]]
    private_path.write_text(json.dumps(private))
    with pytest.raises(ValueError, match="hash|bytes"):
        audit.verify_export(destination)


def test_serialized_export_rejects_manifest_listed_unindexed_public_leak(audit, tmp_path):
    destination = tmp_path / "orphan"
    value = episode()
    value["test"] = value["test"][:1]
    audit.export_episodes([value], destination, project)
    leaked = {"train": deepcopy(value["train"]),
              "test": [{"input": [[9]], "output": [[9]]}],
              "settings": {"selection": "private"}}
    payload = (json.dumps(leaked, sort_keys=True, separators=(",", ":")) + "\n").encode()
    identifier = hashlib.sha256(payload).hexdigest()
    path = f"public/{identifier}.json"
    (destination / path).write_bytes(payload)
    manifest_path = destination / "export_manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"].append({"path": path, "sha256": identifier, "bytes": len(payload)})
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="public|inventory|index"):
        audit.verify_export(destination)


def test_export_refuses_duplicate_visible_inputs_and_nonempty_destination(audit, tmp_path):
    with pytest.raises(ValueError, match="duplicate|Duplicate"):
        audit.export_episodes([episode(), episode()], tmp_path / "duplicates", project)
    destination = tmp_path / "occupied"
    destination.mkdir()
    marker = destination / "keep.txt"
    marker.write_text("user data")
    with pytest.raises(FileExistsError):
        audit.export_episodes([episode()], destination, project)
    assert marker.read_text() == "user data"
