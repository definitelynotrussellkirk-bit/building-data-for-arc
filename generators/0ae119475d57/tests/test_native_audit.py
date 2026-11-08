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
    spec = importlib.util.spec_from_file_location("audit_0ae119475d57_test", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode():
    return {"seed": 17, "settings": {"overlap_precedence": "lower_wins"},
            "program_solution": "(rule! g)",
            "train": [{"input": [[i]], "output": [[i]]} for i in range(4)],
            "test": [{"input": [[i]], "output": [[i]]} for i in range(4, 8)]}


def execute_identity(_program, grid):
    return deepcopy(grid)


def project(value, index):
    return {"train": deepcopy(value["train"]),
            "test": [{"input": deepcopy(value["test"][index]["input"])}]}


def test_replayed_labels_are_required(audit):
    original = episode()
    checked = audit.verify_episode(original, "(rule! g)", execute_identity, demos=4, queries=4)
    assert checked["test"][-1]["output"] == [[7]]
    original["test"][0]["output"] = [[9]]
    with pytest.raises(ValueError, match="label"):
        audit.verify_episode(original, "(rule! g)", execute_identity, demos=4, queries=4)


def test_bool_grid_and_duplicate_input_are_rejected(audit):
    value = episode()
    value["train"][0]["input"] = [[True]]
    with pytest.raises(ValueError, match="grid"):
        audit.verify_episode(value, "(rule! g)", execute_identity, demos=4, queries=4)
    value = episode()
    value["test"][0]["input"] = value["train"][0]["input"]
    with pytest.raises(ValueError, match="distinct|duplicate"):
        audit.verify_episode(value, "(rule! g)", execute_identity, demos=4, queries=4)


@pytest.mark.parametrize("leak", ["settings", "query_output", "second_query", "demo_metadata"])
def test_public_projection_rejects_private_or_future_fields(audit, leak):
    visible = project(episode(), 0)
    if leak == "settings":
        visible["settings"] = {"overlap_precedence": "secret"}
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
    expected = b'{"test":[{"input":[[4]]}],"train":[{"input":[[0]],"output":[[0]]},{"input":[[1]],"output":[[1]]},{"input":[[2]],"output":[[2]]},{"input":[[3]],"output":[[3]]}]}\n'
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
              "settings": {"overlap_precedence": "private"}}
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


def test_rivals_use_only_first_four_demonstrations(audit):
    value = episode()
    value["train"].append({"input": [[8]], "output": [[8]]})
    seen = []

    def candidate(_program, grid):
        seen.append(grid[0][0])
        return [[9]] if grid[0][0] in (8, 4) else deepcopy(grid)

    result = audit.screen_candidate(value, "(rule! g)", candidate)
    assert result["screened_demo_count"] == 4
    assert result["demonstration_refutations"] == []
    assert result["query_mismatches"] == [0]
    assert result["status"] == "ambiguous_queries"
    assert seen == [0, 1, 2, 3, 4, 5, 6, 7]


def test_rival_execution_error_is_not_teaching_evidence(audit):
    seen = []

    def broken(_program, grid):
        seen.append(grid[0][0])
        if grid == [[3]]:
            raise RuntimeError("deliberate evaluator failure")
        return [[9]]

    with pytest.raises(RuntimeError, match="deliberate evaluator failure"):
        audit.screen_candidate(episode(), "(rule! g)", broken)
    assert seen == [0, 1, 2, 3]


def test_shared_input_prefix_and_geometry_groups(audit):
    memo = {}
    fixed = episode()
    fixed["settings"] = {"overlap_precedence": "lower_wins"}
    audit.check_shared_inputs(fixed, memo)
    upper = deepcopy(fixed)
    upper["settings"] = {"overlap_precedence": "upper_wins"}
    audit.check_shared_inputs(upper, memo)
    dynamic = deepcopy(fixed)
    dynamic["settings"] = {"overlap_precedence": "denser_wins"}
    dynamic["test"][2]["input"] = [[7]]
    dynamic["test"][3]["input"] = [[8]]
    audit.check_shared_inputs(dynamic, memo)
    sparse = deepcopy(dynamic)
    sparse["settings"] = {"overlap_precedence": "sparser_wins"}
    audit.check_shared_inputs(sparse, memo)
    wrong_prefix = deepcopy(dynamic)
    wrong_prefix["test"][0]["input"] = [[9]]
    with pytest.raises(ValueError, match="shared|prefix"):
        audit.check_shared_inputs(wrong_prefix, memo)
    wrong_group = deepcopy(sparse)
    wrong_group["test"][3]["input"] = [[9]]
    with pytest.raises(ValueError, match="shared|group"):
        audit.check_shared_inputs(wrong_group, memo)
