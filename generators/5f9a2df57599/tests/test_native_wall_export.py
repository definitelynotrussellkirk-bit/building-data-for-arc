"""Strict transport boundaries; these tests do not certify Racket labels."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1] / "workspace/parametric"


@lru_cache(maxsize=1)
def exporter():
    path = HOME / "export.py"
    assert path.is_file(), "strict native exporter is not implemented"
    spec = importlib.util.spec_from_file_location("_walls_export_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode():
    return {
        "train": [
            {"input": [[0]], "output": [[9]]},
            {"input": [[1]], "output": [[9]]},
            {"input": [[2]], "output": [[9]]},
        ],
        "test": [
            {"input": [[3]], "output": [[9]]},
            {"input": [[4]], "output": [[9]]},
            {"input": [[5]], "output": [[9]]},
            {"input": [[6]], "output": [[9]]},
        ],
        "seed": 0,
        "settings": {"side_boundary_policy": "canvas_edges"},
        "program_solution": "private program bytes\n",
        "meta": {"private_count": 4, "profile": "private profile"},
        "native_wrapper": {"reference": "accepted_parametric", "seed": 0},
    }


def test_visible_identifiers_ignore_private_changes_and_preserve_full_episode(tmp_path):
    export = exporter()
    first = episode()
    changed = deepcopy(first)
    changed.update(seed=81, settings={"side_boundary_policy": "gray_walls"})
    changed["program_solution"] = "different private program"
    changed["meta"] = {"private_count": 19, "profile": "different profile"}
    changed["native_wrapper"] = {"reference": "native wrapper", "seed": 81}
    for pair in changed["test"]:
        pair["output"] = [[8]]
    originals = deepcopy([first, changed])

    reports = [export.write_batch([value], tmp_path / name)
               for value, name in ((first, "first"), (changed, "changed"))]
    assert reports[0]["controller_ids"] == reports[1]["controller_ids"]
    assert reports[0]["turn_ids"] == reports[1]["turn_ids"]
    assert len(reports[0]["controller_ids"]) == 1
    assert len(reports[0]["turn_ids"]) == 4
    for value, report, name in zip((first, changed), reports, ("first", "changed"), strict=True):
        destination = tmp_path / name
        private_rows = [json.loads(line) for line in Path(report["metadata_path"]).read_text().splitlines()]
        assert len(private_rows) == 1
        assert private_rows[0]["episode"] == value
        for identifier, pair in zip(private_rows[0]["turn_ids"], value["test"], strict=True):
            turn = json.loads((destination / "turns" / f"{identifier}.json").read_bytes())
            assert turn["test"] == [{"input": pair["input"]}]
        controller = destination / "private/controllers" / (report["controller_ids"][0] + ".json")
        assert len(json.loads(controller.read_bytes())["test"]) == 4
        for path in [controller, *sorted((destination / "turns").glob("*.json"))]:
            raw = path.read_bytes()
            assert path.stem == hashlib.sha256(raw).hexdigest()
            public = json.loads(raw)
            assert set(public) == {"train", "test"}
            assert all(set(pair) == {"input", "output"} for pair in public["train"])
            assert all(set(pair) == {"input"} for pair in public["test"])
            assert b"side_boundary_policy" not in raw
            assert b"private" not in raw
            if path.parent.name == "turns":
                assert len(public["test"]) == 1
        manifest = json.loads(Path(report["manifest_path"]).read_bytes())
        actual_files = {path.relative_to(destination).as_posix()
                        for path in destination.rglob("*") if path.is_file()}
        assert actual_files == set(manifest["files"]) | {"manifest.json"}
        assert manifest["complete"] is True
        assert manifest["training_admitted"] is False
        for relative, digest in manifest["files"].items():
            assert hashlib.sha256((destination / relative).read_bytes()).hexdigest() == digest
    assert [first, changed] == originals


def test_one_query_projection_ignores_hidden_labels_future_queries_and_counts():
    export = exporter()
    full = episode()
    single = deepcopy(full)
    single["test"] = single["test"][:1]
    expected = {
        "train": [
            {"input": [[0]], "output": [[9]]},
            {"input": [[1]], "output": [[9]]},
            {"input": [[2]], "output": [[9]]},
        ],
        "test": [{"input": [[3]]}],
    }
    assert export.public_turn(full) == export.public_turn(single) == expected
    poisoned = deepcopy(full)
    poisoned["meta"] = object()
    poisoned["test"][0]["output"] = [[True]]
    poisoned["test"][1:] = [object(), {"input": "future input must remain unread"}]
    assert export.public_turn(poisoned) == expected
    original = deepcopy(full)
    visible = export.public_turn(full)
    visible["train"][0]["input"][0][0] = 7
    visible["test"][0]["input"][0][0] = 7
    assert full == original
    for bad in (True, False, -1, 0.0, "0", 4):
        with pytest.raises(ValueError):
            export.public_turn(full, bad)


def test_invalid_visible_or_private_grids_fail_before_destination(tmp_path):
    export = exporter()
    malformed = (
        ("train", "input", [[True]]),
        ("train", "output", [[1.0]]),
        ("test", "input", [["1"]]),
        ("test", "output", [[False]]),
        ("test", "output", [[-1]]),
        ("test", "output", [[10]]),
        ("test", "output", [[0], [1, 2]]),
        ("test", "output", []),
        ("test", "output", ((1,),)),
        ("test", "output", [[0] * 31]),
    )
    for index, (split, key, grid) in enumerate(malformed):
        value = episode()
        value[split][0][key] = grid
        destination = tmp_path / f"invalid-{index}"
        with pytest.raises(ValueError):
            export.write_batch([value], destination)
        assert not destination.exists()
    for index, (split, count) in enumerate((("train", 1), ("train", 7), ("test", 0), ("test", 5))):
        value = episode()
        value[split] = (value[split] * 3)[:count]
        destination = tmp_path / f"invalid-count-{index}"
        with pytest.raises(ValueError):
            export.write_batch([value], destination)
        assert not destination.exists()


def test_duplicate_inputs_and_duplicate_visible_payloads_fail_before_destination(tmp_path):
    export = exporter()
    for index, (split, position) in enumerate((("train", 1), ("test", 0), ("test", 1))):
        value = episode()
        source = value["test"][0] if position == 1 and split == "test" else value["train"][0]
        value[split][position]["input"] = deepcopy(source["input"])
        destination = tmp_path / f"input-{index}"
        with pytest.raises(ValueError, match="distinct"):
            export.write_batch([value], destination)
        assert not destination.exists()
    first = episode()
    second = deepcopy(first)
    second["seed"] = 99
    with pytest.raises(ValueError, match="duplicate"):
        export.write_batch([first, second], tmp_path / "duplicate-controller")
    assert not (tmp_path / "duplicate-controller").exists()
    second["test"][-1]["input"] = [[7]]
    with pytest.raises(ValueError, match="duplicate"):
        export.write_batch([first, second], tmp_path / "duplicate-turn")
    assert not (tmp_path / "duplicate-turn").exists()


def test_non_json_private_data_and_empty_batch_fail_before_destination(tmp_path):
    export = exporter()
    for index, invalid in enumerate((object(), float("nan"), {1: "non-string key"}, (1, 2))):
        value = episode()
        value["meta"] = invalid
        destination = tmp_path / f"private-{index}"
        with pytest.raises(ValueError):
            export.write_batch([value], destination)
        assert not destination.exists()
    with pytest.raises(ValueError):
        export.write_batch([], tmp_path / "empty")
    assert not (tmp_path / "empty").exists()


def test_existing_destinations_are_never_overwritten(tmp_path):
    export = exporter()
    partial = tmp_path / "partial"
    partial.mkdir()
    (partial / "sentinel").write_bytes(b"retain partial data")
    ordinary_file = tmp_path / "ordinary-file"
    ordinary_file.write_bytes(b"retain file")
    dangling = tmp_path / "dangling"
    dangling.symlink_to(tmp_path / "missing")
    empty = tmp_path / "empty-directory"
    empty.mkdir()
    for destination in (partial, ordinary_file, dangling, empty):
        with pytest.raises(FileExistsError):
            export.write_batch([episode()], destination)
    assert (partial / "sentinel").read_bytes() == b"retain partial data"
    assert ordinary_file.read_bytes() == b"retain file"
    assert dangling.is_symlink()
    assert list(empty.iterdir()) == []


def test_write_failure_leaves_no_complete_manifest_and_cannot_be_reused(tmp_path, monkeypatch):
    export = exporter()
    destination = tmp_path / "interrupted"
    original_write = Path.write_bytes

    def failing_write(path, content):
        if path.name == "manifest.pending":
            raise OSError("injected full disk")
        return original_write(path, content)

    monkeypatch.setattr(Path, "write_bytes", failing_write)
    with pytest.raises(OSError, match="injected full disk"):
        export.write_batch([episode()], destination)
    assert destination.is_dir()
    assert list((destination / "turns").glob("*.json"))
    assert not (destination / "manifest.json").exists()
    with pytest.raises(FileExistsError):
        export.write_batch([episode()], destination)


def test_example_builder_rejects_invalid_requests_and_existing_report_before_export(tmp_path):
    path = HOME / "make_examples.py"
    assert path.is_file(), "native example builder is not implemented"
    spec = importlib.util.spec_from_file_location("_walls_examples_test", path)
    assert spec and spec.loader
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    for index, request in enumerate((
        {"seed": True}, {"seed": -1}, {"seed": 2**63},
        {"demos": False}, {"demos": 1}, {"queries": 4.0}, {"queries": 5},
    )):
        destination = tmp_path / f"bad-request-{index}"
        with pytest.raises(ValueError):
            builder.build_examples(destination, **request)
        assert not destination.exists()
    existing_report = tmp_path / "report.json"
    existing_report.write_bytes(b"retain report")
    destination = tmp_path / "report-collision"
    with pytest.raises(FileExistsError):
        builder.build_examples(destination, report_path=existing_report)
    assert not destination.exists()
    assert existing_report.read_bytes() == b"retain report"
    with pytest.raises(ValueError):
        builder.build_examples(destination, report_path=destination / "report.json")
    assert not destination.exists()
