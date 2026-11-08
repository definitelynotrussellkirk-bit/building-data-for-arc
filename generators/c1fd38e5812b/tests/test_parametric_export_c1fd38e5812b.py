"""Synthetic transport regressions and one protected native integration check."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


EXPORT_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/export.py"
@pytest.fixture(scope="module")
def exporter(tmp_path_factory):
    assert EXPORT_PATH.is_file(), "task-local native exporter is not implemented"
    spec = importlib.util.spec_from_file_location("c1fd38e5812b_native_export", EXPORT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    contract = tmp_path_factory.mktemp("transport-contract") / "promotion.json"
    contract.write_text(json.dumps({"limits": {"demos": [3, 6], "queries": [1, 4]}}))
    module.PROMOTION_PATH = contract
    return module


def episode():
    return {
        "train": [
            {"input": [[1, 0]], "output": [[0, 1]], "private_note": "demo"},
            {"input": [[2, 0]], "output": [[0, 2]]},
            {"input": [[3, 0]], "output": [[0, 3]]},
        ],
        "test": [
            {"input": [[4, 0]], "output": [[0, 4]], "private_note": "query"},
            {"input": [[5, 0]], "output": [[0, 5]]},
            {"input": [[6, 0]], "output": [[0, 6]]},
            {"input": [[7, 0]], "output": [[0, 7]]},
        ],
        "seed": 9182,
        "settings": {"fixture_policy": "first"},
        "program_solution": "(rule! synthetic-export-fixture)",
        "private": {"reference_execution": "synthetic transport fixture only"},
    }


def files(directory):
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def test_public_turn_has_exact_current_demos_and_only_the_selected_query(exporter):
    source = episode()
    original = deepcopy(source)
    result = exporter.public_turn(source, 1)
    assert result == {
        "train": [
            {"input": [[1, 0]], "output": [[0, 1]]},
            {"input": [[2, 0]], "output": [[0, 2]]},
            {"input": [[3, 0]], "output": [[0, 3]]},
        ],
        "test": [{"input": [[5, 0]]}],
    }
    result["train"][0]["output"][0][0] = 9
    result["test"][0]["input"][0][0] = 9
    assert source == original


def test_first_turn_bytes_ignore_future_queries_and_all_private_metadata(exporter):
    full = episode()
    single = deepcopy(full)
    single["test"] = single["test"][:1]
    altered = deepcopy(full)
    altered["test"][0]["output"] = [[9]]
    altered["test"][1:] = [None, {"input": "invalid unrevealed grid"}, {}]
    altered["seed"] = -765
    altered["settings"] = {"fixture_policy": "second"}
    altered["program_solution"] = "another private program"
    bodies = [
        json.dumps(exporter.public_turn(value), sort_keys=True, separators=(",", ":"))
        for value in (full, single, altered)
    ]
    assert bodies[0] == bodies[1] == bodies[2]


@pytest.mark.parametrize("index", [-1, True, 0.0, "0", 4])
def test_public_turn_rejects_invalid_query_selection(exporter, index):
    with pytest.raises(ValueError):
        exporter.public_turn(episode(), index)


@pytest.mark.parametrize("grid", [[], [[]], [[True]], [[1.0]], [[-1]], [[10]], [[1], [1, 2]], [[0] * 31]])
def test_public_turn_rejects_invalid_visible_grids(exporter, grid):
    source = episode()
    source["test"][0]["input"] = grid
    with pytest.raises(ValueError):
        exporter.public_turn(source)


def test_write_batch_is_sorted_content_addressed_and_keeps_labels_private(exporter, tmp_path):
    first = episode()
    second = deepcopy(first)
    second["train"][0]["output"] = [[1, 0]]
    second["settings"] = {"fixture_policy": "second"}
    left, right = tmp_path / "left", tmp_path / "right"
    report = exporter.write_batch([first, second], left)
    exporter.write_batch([second, first], right)
    assert files(left) == files(right)
    public_files = sorted((left / "public").glob("*.json"))
    turn_files = sorted((left / "turns").glob("*.json"))
    assert len(public_files) == 2
    assert len(turn_files) == 8
    assert report["public_ids"] == [path.stem for path in public_files]
    assert report["turn_ids"] == [path.stem for path in turn_files]
    for path in public_files + turn_files:
        raw = path.read_bytes()
        challenge = json.loads(raw)
        assert path.stem == hashlib.sha256(raw).hexdigest()
        assert set(challenge) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        assert len(challenge["test"]) == (4 if path.parent.name == "public" else 1)
    metadata = left / "private/metadata.jsonl"
    assert Path(report["metadata_path"]) == metadata
    rows = [json.loads(line) for line in metadata.read_text().splitlines()]
    assert [row["public_id"] for row in rows] == report["public_ids"]
    assert {json.dumps(row["episode"], sort_keys=True) for row in rows} == {
        json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True)
    }
    for row in rows:
        assert len(row["turn_ids"]) == 4
        for index, turn_id in enumerate(row["turn_ids"]):
            visible = json.loads((left / "turns" / f"{turn_id}.json").read_bytes())
            assert visible["test"] == [{"input": row["episode"]["test"][index]["input"]}]
    assert set(files(left)) == {
        *(f"public/{identifier}.json" for identifier in report["public_ids"]),
        *(f"turns/{identifier}.json" for identifier in report["turn_ids"]),
        "private/metadata.jsonl",
        "manifest.json",
    }
    manifest = json.loads((left / "manifest.json").read_bytes())
    assert manifest["complete"] is True
    assert manifest["training_admitted"] is False
    assert manifest["native_acceptance"] == "owner_pending"
    assert manifest["files"] == {name: hashlib.sha256(body).hexdigest()
                                 for name, body in files(left).items()
                                 if name != "manifest.json"}


def test_write_batch_public_names_ignore_settings_seeds_programs_and_query_answers(exporter, tmp_path):
    first = episode()
    changed = deepcopy(first)
    changed.update(seed=56, settings={"fixture_policy": "second"}, program_solution="private variant")
    for pair in changed["test"]:
        pair["output"] = [[9]]
    left, right = tmp_path / "left", tmp_path / "right"
    exporter.write_batch([first], left)
    exporter.write_batch([changed], right)
    assert files(left / "public") == files(right / "public")
    assert files(left / "turns") == files(right / "turns")
    assert files(left / "private") != files(right / "private")


def test_duplicate_controller_payload_is_rejected_before_any_writes(exporter, tmp_path):
    first = episode()
    duplicate = deepcopy(first)
    duplicate["seed"] = 42
    duplicate["settings"] = {"fixture_policy": "second"}
    duplicate["test"][0]["output"] = [[9]]
    target = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate"):
        exporter.write_batch([first, duplicate], target)
    assert not target.exists()


def test_duplicate_turn_payload_is_rejected_even_when_controller_payload_differs(exporter, tmp_path):
    first = episode()
    duplicate_turn = deepcopy(first)
    duplicate_turn["test"][-1]["input"] = [[8, 0]]
    target = tmp_path / "duplicate-turn"
    with pytest.raises(ValueError, match="duplicate"):
        exporter.write_batch([first, duplicate_turn], target)
    assert not target.exists()


@pytest.mark.parametrize("failure", ["empty", "invalid-visible-grid", "non-json-private"])
def test_batch_preflight_errors_do_not_create_destination(exporter, tmp_path, failure):
    source = episode()
    batch = [source]
    if failure == "empty":
        batch = []
    elif failure == "invalid-visible-grid":
        second = deepcopy(source)
        second["test"][-1]["input"] = [[True]]
        batch.append(second)
    else:
        source["private"]["unsupported"] = object()
    target = tmp_path / failure
    with pytest.raises((ValueError, TypeError)):
        exporter.write_batch(batch, target)
    assert not target.exists()


def test_existing_destination_is_preserved(exporter, tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    (target / "keep.txt").write_text("existing user content")
    with pytest.raises(FileExistsError):
        exporter.write_batch([episode()], target)
    assert files(target) == {"keep.txt": b"existing user content"}


@pytest.fixture(scope="module")
def example_builder():
    path = EXPORT_PATH.with_name("make_examples.py")
    assert path.is_file(), "protected native example builder is not implemented"
    spec = importlib.util.spec_from_file_location("c1fd38e5812b_make_examples", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_example_builder_rejects_unprotected_execution_before_export(example_builder, tmp_path, monkeypatch):
    contract_path = tmp_path / "promotion.json"
    contract_path.write_text(json.dumps({
        "parameters": {"fixture_policy": ["first", "second"]},
        "default": {"fixture_policy": "first"},
        "limits": {"demos": [3, 6], "queries": [1, 4]},
    }))
    monkeypatch.setattr(example_builder, "PROMOTION_PATH", contract_path)
    monkeypatch.setattr(
        example_builder,
        "evaluate_contract",
        lambda *args, **kwargs: {"racket": {"backend": "test", "protected": False}},
    )
    target = tmp_path / "unprotected"
    with pytest.raises(ValueError, match="protected Racket"):
        example_builder.build_examples(target)
    assert not target.exists()


def test_example_builder_materializes_declared_settings_with_protected_labels(example_builder, tmp_path):
    contract = json.loads(example_builder.PROMOTION_PATH.read_text())
    settings = example_builder.settings_space(contract)
    target = tmp_path / "protected"
    result = example_builder.build_examples(target, seed=17)
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert result["native_acceptance"] == "owner_pending"
    assert result["training_admitted"] is False
    rows = [json.loads(line) for line in (target / "private/metadata.jsonl").read_text().splitlines()]
    assert {json.dumps(row["episode"]["settings"], sort_keys=True) for row in rows} == {
        json.dumps(setting, sort_keys=True) for setting in settings
    }
    assert result["settings"] == settings
    assert len(rows) == len(settings)
    for row in rows:
        record = row["episode"]
        assert len(record["train"]) == 3
        assert len(record["test"]) == 4
        assert record["private"]["racket"] == result["racket"]
        assert record["private"]["native_acceptance"] == "owner_pending"
        assert record["private"]["training_admitted"] is False
        binding = record["private"]["source_sha256"]
        for name in ("prototype.py", "adapter.py", "promotion.json", "export.py", "make_examples.py"):
            source = EXPORT_PATH.with_name(name)
            relative = source.relative_to(example_builder.REPO).as_posix()
            assert binding[relative] == hashlib.sha256(source.read_bytes()).hexdigest()
        assert record["program_sha256"] == hashlib.sha256(record["program"].encode()).hexdigest()
        assert "authoring_focus" not in record["private"]
        assert record["private"]["demo_only_certificate"]["survivors"] == [record["settings"]]
        assert record["reference"] == "protected_racket_pending_acceptance"
        assert record["program"].startswith("(rule!")
        for index, turn_id in enumerate(row["turn_ids"]):
            turn = json.loads((target / "turns" / f"{turn_id}.json").read_bytes())
            assert set(turn) == {"train", "test"}
            assert turn["test"] == [{"input": record["test"][index]["input"]}]
    assert len(result["public_ids"]) == len(settings)
    assert len(result["turn_ids"]) == 4 * len(settings)


@pytest.mark.parametrize("name,value", [
    ("demos", True), ("demos", 3.0), ("demos", "3"), ("demos", 1), ("demos", 2), ("demos", 7),
    ("queries", False), ("queries", 4.0), ("queries", "4"), ("queries", 0), ("queries", 5),
    ("seed", True), ("seed", 0.0), ("seed", "0"), ("seed", -1), ("seed", 2**63),
])
def test_builder_rejects_invalid_request_before_execution(example_builder, tmp_path, monkeypatch, name, value):
    contract_path = tmp_path / "promotion.json"
    contract_path.write_text(json.dumps({
        "parameters": {"view": ["compressed", "largest_component_crop"]}, "default": {"view": "compressed"},
        "limits": {"demos": [3, 6], "queries": [1, 4]},
    }))
    monkeypatch.setattr(example_builder, "PROMOTION_PATH", contract_path)
    executed = []
    monkeypatch.setattr(example_builder, "evaluate_contract", lambda *args, **kwargs: executed.append(True))
    target = tmp_path / "invalid-request"
    with pytest.raises(ValueError, match=name):
        example_builder.build_examples(target, **{name: value})
    assert executed == []
    assert not target.exists()


def test_builder_refuses_source_drift_before_export(example_builder, tmp_path, monkeypatch):
    contract_path = tmp_path / "promotion.json"
    contract_path.write_text(json.dumps({
        "parameters": {"view": ["compressed", "largest_component_crop"]}, "default": {"view": "compressed"},
        "limits": {"demos": [3, 6], "queries": [1, 4]},
    }))
    monkeypatch.setattr(example_builder, "PROMOTION_PATH", contract_path)
    snapshots = iter([{"prototype.py": "before"}, {"prototype.py": "after"}])
    monkeypatch.setattr(example_builder, "_source_binding", lambda: next(snapshots))
    monkeypatch.setattr(example_builder, "evaluate_contract", lambda *args, **kwargs: {
        "racket": {"backend": "racket", "protected": True},
        "episodes": [], "checks": [], "racket_evaluations": 0,
    })
    target = tmp_path / "changed-source"
    with pytest.raises(ValueError, match="source.*changed"):
        example_builder.build_examples(target)
    assert not target.exists()


@pytest.mark.parametrize("failure", ["one-demo", "two-demos", "seven-demos", "five-queries", "repeated-demo", "demo-query-overlap", "invalid-private-answer", "missing-private-answer", "non-finite-private"])
def test_writer_rejects_invalid_episode_contract_before_writes(exporter, tmp_path, failure):
    source = episode()
    if failure == "one-demo":
        source["train"] = source["train"][:1]
    elif failure == "two-demos":
        source["train"] = source["train"][:2]
    elif failure == "seven-demos":
        source["train"] = [{"input": [[i, 1]], "output": [[1, i]]} for i in range(7)]
    elif failure == "five-queries":
        source["test"].append({"input": [[8, 0]], "output": [[0, 8]]})
    elif failure == "repeated-demo":
        source["train"][1]["input"] = deepcopy(source["train"][0]["input"])
    elif failure == "demo-query-overlap":
        source["test"][0]["input"] = deepcopy(source["train"][0]["input"])
    elif failure == "invalid-private-answer":
        source["test"][0]["output"] = [[True]]
    elif failure == "missing-private-answer":
        del source["test"][0]["output"]
    else:
        source["private"]["score"] = float("nan")
    target = tmp_path / failure
    with pytest.raises((ValueError, TypeError)):
        exporter.write_batch([source], target)
    assert not target.exists()


def test_writer_does_not_publish_manifest_after_io_failure(exporter, tmp_path, monkeypatch):
    target = tmp_path / "io-failure"
    original = Path.write_bytes
    count = 0
    def fail_after_first(path, body):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("injected write failure")
        return original(path, body)
    monkeypatch.setattr(Path, "write_bytes", fail_after_first)
    with pytest.raises(OSError, match="injected"):
        exporter.write_batch([episode()], target)
    assert not (target / "manifest.json").exists()
