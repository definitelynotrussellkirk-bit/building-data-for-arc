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
    spec = importlib.util.spec_from_file_location("audit_9000d0ea6484_test", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode():
    return {"seed": 17, "settings": {"start_section": 2, "scan_direction": "forward"},
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
        visible["settings"] = {"start_section": "densest", "scan_direction": "reverse"}
    elif leak == "query_output":
        visible["test"][0]["output"] = [[4]]
    elif leak == "second_query":
        visible["test"].append({"input": [[5]]})
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


def test_serialized_export_checks_projection_order_and_private_label_hash(audit, tmp_path, monkeypatch):
    destination = tmp_path / "export"
    write_bytes = Path.write_bytes
    public_writes = []

    def observe_write(path, payload):
        if path.parent == destination / "public":
            public_writes.append(path.stem)
        return write_bytes(path, payload)

    monkeypatch.setattr(Path, "write_bytes", observe_write)
    audit.export_episodes([episode()], destination, project)
    verified = audit.verify_export(destination)
    assert verified["public_count"] == 4
    files = sorted((destination / "public").glob("*.json"))
    assert public_writes == [path.stem for path in files]
    assert len(files) == 4
    for path in files:
        visible = json.loads(path.read_bytes())
        assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
        assert hashlib.sha256(path.read_bytes()).hexdigest() == path.stem
    private_path = destination / "private.json"
    private = json.loads(private_path.read_bytes())
    assert [row["public_id"] for row in private["public_index"]] == public_writes
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
              "settings": {"start_section": "sparsest", "scan_direction": "forward"}}
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
    assert seen == list(range(8))


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


def test_all_inputs_are_shared_across_settings(audit):
    memo = {}
    repeated = episode()
    audit.check_shared_inputs(repeated, memo)
    for setting in ({"start_section": 0, "scan_direction": "forward"},
                    {"start_section": "densest", "scan_direction": "forward"},
                    {"start_section": "sparsest", "scan_direction": "reverse"}):
        other = deepcopy(repeated)
        other["settings"] = setting
        other["train"][0]["output"] = [[9]]
        audit.check_shared_inputs(other, memo)
    for split, index in (("train", 3), ("test", 3)):
        changed = deepcopy(other)
        changed[split][index]["input"] = [[9]]
        with pytest.raises(ValueError, match="shared|inputs"):
            audit.check_shared_inputs(changed, memo)


def test_all_seven_canonical_pairs_are_retained(audit):
    variants = [{"train": [{"input": [[i]], "output": [[i]]} for i in range(6)],
                 "test": [{"input": [[6]], "output": [[6]]}]}]
    pairs = audit._canonical_pairs(variants)
    assert len(pairs) == 7
    assert [pair["input"][0][0] for pair in pairs] == list(range(7))
    assert [(pair["split"], pair["index"]) for pair in pairs] == [
        *(('train', index) for index in range(6)), ('test', 0)]
    variants[0]["test"].pop()
    with pytest.raises(ValueError, match="7|seven"):
        audit._canonical_pairs(variants)


@pytest.mark.parametrize(("field", "replacement"), [
    ("schema", "unrelated-private-schema"), ("task_id", "another-task")])
def test_rehashed_private_envelope_must_match_task_schema(audit, tmp_path, field, replacement):
    destination = tmp_path / "private-envelope"
    audit.export_episodes([episode()], destination, project)
    private_path = destination / "private.json"
    private = json.loads(private_path.read_bytes())
    private[field] = replacement
    payload = audit.raw(private)
    private_path.write_bytes(payload)
    manifest_path = destination / "export_manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    entry = next(row for row in manifest["files"] if row["path"] == "private.json")
    entry.update(sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))
    manifest_path.write_bytes(audit.raw(manifest))
    with pytest.raises(ValueError, match="private|schema|task"):
        audit.verify_export(destination)


@pytest.mark.parametrize(("field", "replacement"), [
    ("schema", "unrelated-export-schema"), ("episodes", True),
    ("public_count", True), ("training_admitted", True)])
def test_export_envelope_has_typed_counts_and_no_admission(audit, tmp_path, field, replacement):
    destination = tmp_path / "manifest-envelope"
    value = episode()
    value["test"] = value["test"][:1]
    audit.export_episodes([value], destination, project)
    manifest_path = destination / "export_manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest[field] = replacement
    manifest_path.write_bytes(audit.raw(manifest))
    with pytest.raises(ValueError, match="schema|manifest|count|admission"):
        audit.verify_export(destination)


def gap_case(audit):
    value = episode()
    value["settings"] = {"start_section": "densest", "scan_direction": "forward"}
    outputs = [deepcopy(pair["output"]) for pair in value["train"]]
    outputs[-1] = [[9]]
    return value, audit.make_teaching_gap(
        value, "ignore_anchor_candidate_1", "(rule! (lambda (g) '((9))))",
        outputs, episode_index=0)


def test_teaching_gap_retains_executed_prefix_and_novel_repaired_queries(audit):
    value, gap = gap_case(audit)
    assert gap["original_lesson"] == {"train": value["train"][:3], "test": value["train"][3:4]}
    assert gap["rival_query_output"] == [[9]]
    assert gap["differences"] == [{"row": 0, "column": 0, "intended": 3, "rival": 9}]
    assert gap["changed_cells"] == 1
    assert gap["repaired_demo_count"] == 4
    assert gap["repaired_demonstration_refutations"] == [3]
    assert gap["repaired_queries"] == value["test"]
    assert gap["additional_racket_evaluations"] == 0


@pytest.mark.parametrize("invalid", ["prefix_refuted", "query_agrees"])
def test_teaching_gap_requires_demonstration_fit_and_query_difference(audit, invalid):
    value = episode()
    outputs = [deepcopy(pair["output"]) for pair in value["train"]]
    if invalid == "prefix_refuted":
        outputs[0] = [[9]]
        outputs[-1] = [[9]]
    with pytest.raises(ValueError, match="prefix|differ|gap"):
        audit.make_teaching_gap(value, "rival", "(rule! g)", outputs, episode_index=0)


def test_export_manifest_binds_private_teaching_gap(audit, tmp_path):
    value, gap = gap_case(audit)
    artifact = {"schema": "arcpuzzles-task-teaching-gap-v1", "task_id": audit.TASK, "cases": [gap]}
    destination = tmp_path / "gap-export"
    manifest = audit.export_episodes([value], destination, project, teaching_gap=artifact)
    assert manifest["public_count"] == 4
    entry = next(row for row in manifest["files"] if row["path"] == "teaching-gap.json")
    path = destination / entry["path"]
    assert entry["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert json.loads(path.read_bytes()) == artifact
    assert all("teaching" not in p.name for p in (destination / "public").iterdir())
    path.write_bytes(b"{}")
    with pytest.raises(ValueError, match="hash|bytes"):
        audit.verify_export(destination)
