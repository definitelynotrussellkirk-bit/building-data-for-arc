"""Strict actor masking, publication, and protected native example checks."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parents[1] / "workspace/parametric"


def _load(name):
    path = HERE / (name + ".py")
    assert path.is_file(), f"task-local {name} has not been implemented"
    spec = importlib.util.spec_from_file_location(f"stamp_8de1c257a9c7_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _episode():
    return {
        "train": [
            {"input": [[1, 0]], "output": [[0, 1]], "note": "private demo note"},
            {"input": [[2, 0]], "output": [[0, 2]]},
            {"input": [[3, 0]], "output": [[0, 3]]},
        ],
        "test": [
            {"input": [[4, 0]], "output": [[0, 4]], "note": "private query note"},
            {"input": [[5, 0]], "output": [[0, 5]]},
            {"input": [[6, 0]], "output": [[0, 6]]},
            {"input": [[7, 0]], "output": [[0, 7]]},
        ],
        "seed": 9182,
        "settings": {"stamp_transform": "identity"},
        "program": "synthetic transport fixture; no execution claim",
        "private": {"nested": [None, True, "kept exactly", 0.5]},
    }


def _files(directory):
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def test_public_turn_masks_current_query_and_copies_only_visible_grids():
    exporter = _load("export")
    source = _episode()
    original = deepcopy(source)
    actual = exporter.public_turn(source, 1)
    assert actual == {
        "train": [
            {"input": [[1, 0]], "output": [[0, 1]]},
            {"input": [[2, 0]], "output": [[0, 2]]},
            {"input": [[3, 0]], "output": [[0, 3]]},
        ],
        "test": [{"input": [[5, 0]]}],
    }
    actual["train"][0]["output"][0][0] = 9
    actual["test"][0]["input"][0][0] = 9
    assert source == original


def test_first_turn_neither_reads_future_queries_nor_reveals_total_count():
    exporter = _load("export")
    full = _episode()
    single = deepcopy(full)
    single["test"] = single["test"][:1]
    future_corrupt = deepcopy(full)
    future_corrupt["test"][1:] = [None, {"input": object()}, {}]
    future_corrupt["test"][0]["output"] = object()
    future_corrupt["settings"] = object()
    future_corrupt["seed"] = -32
    future_corrupt["program"] = object()
    future_corrupt["private"] = object()
    payloads = [exporter.public_challenge_bytes(exporter.public_turn(value))
                for value in (full, single, future_corrupt)]
    assert payloads[0] == payloads[1] == payloads[2]
    assert exporter.public_challenge_id(exporter.public_turn(full)) == hashlib.sha256(payloads[0]).hexdigest()


@pytest.mark.parametrize("index", [-1, True, 0.0, "0", 4, None])
def test_turn_selection_requires_an_exact_in_range_integer(index):
    with pytest.raises(ValueError):
        _load("export").public_turn(_episode(), index)


@pytest.mark.parametrize("grid", [
    [], [[]], [[True]], [[1.0]], [["1"]], [[-1]], [[10]],
    [[1], [1, 2]], [[0] * 31], [[0]] * 31, [(0, 1)], ((0, 1),),
])
def test_visible_grid_validation_never_coerces_colors_or_shapes(grid):
    source = _episode()
    source["test"][0]["input"] = grid
    with pytest.raises(ValueError):
        _load("export").public_turn(source)


def test_batch_has_content_only_ids_complete_private_rows_and_hashed_manifest(tmp_path):
    exporter = _load("export")
    first = _episode()
    second = deepcopy(first)
    second["train"][0]["output"] = [[1, 0]]
    second["settings"] = {"stamp_transform": "mirror_horizontal"}
    left, right = tmp_path / "left", tmp_path / "right"
    report = exporter.write_batch([first, second], left)
    exporter.write_batch([second, first], right)
    assert _files(left) == _files(right)
    controllers = sorted((left / "controller").glob("*.json"))
    turns = sorted((left / "onequery").glob("*.json"))
    assert len(controllers) == 2
    assert len(turns) == 8
    assert report["public_ids"] == report["controller_ids"] == [path.stem for path in controllers]
    assert report["turn_ids"] == [path.stem for path in turns]
    for path in controllers + turns:
        raw = path.read_bytes()
        challenge = json.loads(raw)
        assert path.stem == hashlib.sha256(raw).hexdigest()
        assert set(challenge) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        assert len(challenge["test"]) == (4 if path.parent.name == "controller" else 1)
        assert raw == (json.dumps(challenge, sort_keys=True, separators=(",", ":")) + "\n").encode()
    metadata = left / "private/metadata.jsonl"
    assert Path(report["metadata_path"]) == metadata
    rows = [json.loads(line) for line in metadata.read_text().splitlines()]
    assert [row["public_id"] for row in rows] == report["controller_ids"]
    assert {json.dumps(row["episode"], sort_keys=True) for row in rows} == {
        json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True),
    }
    for row in rows:
        assert len(row["turn_ids"]) == 4
        for index, turn_id in enumerate(row["turn_ids"]):
            visible = json.loads((left / "onequery" / f"{turn_id}.json").read_bytes())
            assert visible["test"] == [{"input": row["episode"]["test"][index]["input"]}]
    manifest = json.loads((left / "manifest.json").read_bytes())
    assert manifest["status"] == "complete"
    assert manifest["training_admitted"] is False
    payloads = {name: data for name, data in _files(left).items() if name != "manifest.json"}
    assert set(manifest["files"]) == set(payloads)
    for name, data in payloads.items():
        assert manifest["files"][name] == {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    relative = (HERE / "export.py").relative_to(exporter.REPO).as_posix()
    assert manifest["source_sha256"][relative] == hashlib.sha256((HERE / "export.py").read_bytes()).hexdigest()


def test_public_files_and_ids_ignore_all_private_values(tmp_path):
    exporter = _load("export")
    first = _episode()
    changed = deepcopy(first)
    changed.update(seed=56, settings={"stamp_transform": "mirror_horizontal"}, program="other private source")
    changed["private"] = {"different": True}
    for pair in changed["test"]:
        pair["output"] = [[9]]
    left, right = tmp_path / "left", tmp_path / "right"
    exporter.write_batch([first], left)
    exporter.write_batch([changed], right)
    assert _files(left / "controller") == _files(right / "controller")
    assert _files(left / "onequery") == _files(right / "onequery")
    assert _files(left / "private") != _files(right / "private")


@pytest.mark.parametrize("kind", ["controller", "turn", "demo-input", "query-input", "cross-split-input"])
def test_duplicate_inputs_or_public_payloads_fail_before_publication(tmp_path, kind):
    source = _episode()
    batch = [source]
    if kind in {"controller", "turn"}:
        duplicate = deepcopy(source)
        duplicate["seed"] = 55
        if kind == "turn":
            duplicate["test"][-1]["input"] = [[8, 0]]
        batch.append(duplicate)
    elif kind == "demo-input":
        source["train"][1]["input"] = deepcopy(source["train"][0]["input"])
    elif kind == "query-input":
        source["test"][1]["input"] = deepcopy(source["test"][0]["input"])
    else:
        source["test"][0]["input"] = deepcopy(source["train"][0]["input"])
    target = tmp_path / kind
    with pytest.raises(ValueError, match="duplicate|distinct"):
        _load("export").write_batch(batch, target)
    assert not target.exists()


@pytest.mark.parametrize("kind", ["empty", "query-label", "missing-label", "nan", "object", "tuple", "key"])
def test_full_private_preflight_rejects_invalid_data_before_destination_exists(tmp_path, kind):
    source = _episode()
    batch = [source]
    if kind == "empty":
        batch = []
    elif kind == "query-label":
        source["test"][-1]["output"] = [[True]]
    elif kind == "missing-label":
        del source["test"][-1]["output"]
    elif kind == "nan":
        source["private"]["value"] = float("nan")
    elif kind == "object":
        source["private"]["value"] = object()
    elif kind == "tuple":
        source["private"]["value"] = (1, 2)
    else:
        source["private"][1] = "must not coerce a key"
    target = tmp_path / kind
    with pytest.raises((ValueError, TypeError)):
        _load("export").write_batch(batch, target)
    assert not target.exists()


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (3, 0), (3, 5)])
def test_controller_export_requires_two_to_six_demos_and_one_to_four_queries(tmp_path, demos, queries):
    source = _episode()
    source["train"] = (source["train"] * 3)[:demos]
    source["test"] = (source["test"] * 2)[:queries]
    with pytest.raises(ValueError, match="demo|quer|train|test"):
        _load("export").write_batch([source], tmp_path / "wrong-count")
    assert not (tmp_path / "wrong-count").exists()


@pytest.mark.parametrize("queries", [1, 2, 3, 4])
def test_controller_export_supports_independent_query_counts(tmp_path, queries):
    source = _episode()
    source["test"] = source["test"][:queries]
    target = tmp_path / "counts"
    report = _load("export").write_batch([source], target)
    assert len(report["controller_ids"]) == 1
    assert len(report["turn_ids"]) == queries
    controller = json.loads(next((target / "controller").glob("*.json")).read_bytes())
    assert len(controller["test"]) == queries


def test_existing_destination_is_preserved(tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    (target / "keep.txt").write_text("existing user content")
    with pytest.raises(FileExistsError):
        _load("export").write_batch([_episode()], target)
    assert _files(target) == {"keep.txt": b"existing user content"}


def test_manifest_is_published_last_and_write_failure_leaves_no_complete_batch(tmp_path, monkeypatch):
    exporter = _load("export")
    real_replace = exporter.os.replace
    moves = []

    def observing_replace(source, target):
        moves.append(Path(target).relative_to(tmp_path / "complete").as_posix())
        if Path(target).name == "manifest.json":
            manifest = json.loads(Path(source).read_bytes())
            assert all((tmp_path / "complete" / path).is_file() for path in manifest["files"])
        return real_replace(source, target)

    monkeypatch.setattr(exporter.os, "replace", observing_replace)
    exporter.write_batch([_episode()], tmp_path / "complete")
    assert moves[-1] == "manifest.json"

    def failing_replace(source, target):
        if Path(target).name == "manifest.json":
            raise OSError("injected publication failure")
        return real_replace(source, target)

    monkeypatch.setattr(exporter.os, "replace", failing_replace)
    with pytest.raises(OSError, match="publication failure"):
        exporter.write_batch([_episode()], tmp_path / "failed")
    assert not (tmp_path / "failed").exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == ["complete"]


def test_source_hash_mismatch_stops_before_any_publication(tmp_path):
    exporter = _load("export")
    relative = (HERE / "export.py").relative_to(exporter.REPO).as_posix()
    with pytest.raises(ValueError, match="source"):
        exporter.write_batch([_episode()], tmp_path / "wrong-source", source_sha256={relative: "0" * 64})
    assert not (tmp_path / "wrong-source").exists()


def _contract(tmp_path):
    path = tmp_path / "promotion.json"
    path.write_text(json.dumps({
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/8de1c257a9c7/workspace/parametric/adapter.py",
        "parameters": {"stamp_transform": ["identity", "mirror_horizontal"]},
        "default": {"stamp_transform": "identity"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
    }))
    return path


def test_examples_reject_unprotected_execution_before_export(tmp_path, monkeypatch):
    builder = _load("make_examples")
    monkeypatch.setattr(builder, "PROMOTION_PATH", _contract(tmp_path))
    monkeypatch.setattr(builder, "evaluate_contract", lambda *args, **kwargs: {
        "racket": {"backend": "test", "protected": False},
    })
    with pytest.raises(ValueError, match="protected Racket"):
        builder.build_examples(tmp_path / "unprotected")
    assert not (tmp_path / "unprotected").exists()


@pytest.mark.parametrize("name,value", [
    ("demos", True), ("demos", 3.0), ("demos", "3"), ("demos", 1), ("demos", 7),
    ("queries", False), ("queries", 4.0), ("queries", "4"), ("queries", 0), ("queries", 5),
    ("seed", True), ("seed", 0.0), ("seed", "0"), ("seed", -1), ("seed", 2**63),
])
def test_example_request_is_validated_before_runtime_execution(tmp_path, monkeypatch, name, value):
    builder = _load("make_examples")
    monkeypatch.setattr(builder, "PROMOTION_PATH", _contract(tmp_path))

    def forbidden_execution(*args, **kwargs):
        raise AssertionError("invalid request must not start Racket")

    monkeypatch.setattr(builder, "evaluate_contract", forbidden_execution)
    with pytest.raises(ValueError, match=name):
        builder.build_examples(tmp_path / "invalid-request", **{name: value})
    assert not (tmp_path / "invalid-request").exists()


def test_source_drift_during_native_execution_prevents_export(tmp_path, monkeypatch):
    builder = _load("make_examples")
    monkeypatch.setattr(builder, "PROMOTION_PATH", _contract(tmp_path))
    bindings = iter([{"prototype.py": "before"}, {"prototype.py": "after"}])
    monkeypatch.setattr(builder, "_source_binding", lambda: next(bindings))
    monkeypatch.setattr(builder, "evaluate_contract", lambda *args, **kwargs: {
        "racket": {"backend": "racket", "protected": True},
        "episodes": [], "checks": [], "racket_evaluations": 0,
    })
    with pytest.raises(ValueError, match="source.*changed"):
        builder.build_examples(tmp_path / "source-drift")
    assert not (tmp_path / "source-drift").exists()


def test_cli_saves_the_exact_report_and_refuses_report_overwrite(tmp_path, monkeypatch, capsys):
    builder = _load("make_examples")
    exporter = _load("export")

    def synthetic_build(target, **request):
        return {**exporter.write_batch([_episode()], target), "request": request}

    monkeypatch.setattr(builder, "build_examples", synthetic_build)
    target, report_path = tmp_path / "examples", tmp_path / "report.json"
    assert builder.main(["--out", str(target), "--report", str(report_path), "--seed", "9"]) == 0
    assert report_path.read_text() == capsys.readouterr().out
    report = json.loads(report_path.read_bytes())
    assert report["request"] == {"seed": 9, "demos": 3, "queries": 4}
    before = report_path.read_bytes()
    with pytest.raises(FileExistsError):
        builder.main(["--out", str(tmp_path / "another"), "--report", str(report_path)])
    assert report_path.read_bytes() == before
    assert not (tmp_path / "another").exists()


def test_cli_report_cannot_be_an_unmanifested_file_inside_the_export(tmp_path, monkeypatch):
    builder = _load("make_examples")

    def forbidden_build(*args, **kwargs):
        raise AssertionError("invalid report path must be rejected before generation")

    monkeypatch.setattr(builder, "build_examples", forbidden_build)
    target = tmp_path / "examples"
    with pytest.raises(ValueError, match="report"):
        builder.main(["--out", str(target), "--report", str(target / "report.json")])
    assert not target.exists()


def test_examples_use_each_exact_setting_program_and_protected_labels(tmp_path):
    builder = _load("make_examples")
    adapter = _load("adapter")
    contract = json.loads(builder.PROMOTION_PATH.read_bytes())
    settings = builder.settings_space(contract)
    target = tmp_path / "protected"
    report = builder.build_examples(target, seed=17, demos=3, queries=4)
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert report["native_acceptance"] == "owner_pending"
    assert report["training_admitted"] is False
    rows = [json.loads(line) for line in (target / "private/metadata.jsonl").read_text().splitlines()]
    assert {json.dumps(row["episode"]["settings"], sort_keys=True) for row in rows} == {
        json.dumps(setting, sort_keys=True) for setting in settings
    }
    assert len(report["controller_ids"]) == len(settings)
    assert len(report["turn_ids"]) == 4 * len(settings)
    for row in rows:
        episode = row["episode"]
        assert episode["program"] == adapter.program(episode["settings"])
        assert episode["program_sha256"] == hashlib.sha256(episode["program"].encode()).hexdigest()
        assert episode["private"]["racket"] == report["racket"]
        assert episode["private"]["demo_only_certificate"]["survivors"] == [episode["settings"]]
        assert episode["private"]["native_acceptance"] == "owner_pending"
        assert episode["private"]["training_admitted"] is False
        assert episode["reference"] == "protected_racket_pending_acceptance"
        authored = episode["private"]["adapter_episode"]
        assert authored["program_solution"] == episode["program"]
        assert authored["train"] == episode["train"]
        assert authored["test"] == episode["test"]
        assert "meta" in authored
        binding = episode["private"]["source_sha256"]
        for name in ("prototype.py", "adapter.py", "promotion.json", "export.py", "make_examples.py"):
            source = HERE / name
            assert binding[source.relative_to(builder.REPO).as_posix()] == hashlib.sha256(source.read_bytes()).hexdigest()
        assert len(episode["train"]) == 3 and len(episode["test"]) == 4
