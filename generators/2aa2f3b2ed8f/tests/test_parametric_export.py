"""Task-local sequential projection and checked-export boundary regressions."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil

import pytest


EXPORT = Path(__file__).resolve().parents[1] / "workspace/parametric/export.py"


def _module():
    assert EXPORT.is_file(), "Missing task-local public_turn/export_episodes API"
    spec = importlib.util.spec_from_file_location("_slide_parametric_export_test", EXPORT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _episode():
    return {
        "train": [
            {"input": [[1, 0]], "output": [[0, 1]]},
            {"input": [[2, 0]], "output": [[0, 2]]},
        ],
        "test": [
            {"input": [[3, 0]], "output": [[0, 3]]},
            {"input": [[4, 0]], "output": [[0, 4]]},
        ],
        "settings": {"mover": "body"},
        "seed": 9,
        "program": "private reference",
    }


def test_public_turn_has_only_demonstrations_and_one_query():
    export = _module()
    expected = {
        "train": [
            {"input": [[1, 0]], "output": [[0, 1]]},
            {"input": [[2, 0]], "output": [[0, 2]]},
        ],
        "test": [{"input": [[3, 0]]}],
    }
    assert export.public_turn(_episode(), 0) == expected
    changed = _episode()
    changed.update(seed=100, settings={"mover": "target"}, program="another private program")
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[8, 8]]
    assert _raw(export.public_turn(changed, 0)) == _raw(expected)


@pytest.mark.parametrize("bad_grid", [[[True]], [[1.0]], [[1], [2, 3]], [[0]] * 31])
def test_public_turn_rejects_malformed_visible_grids(bad_grid):
    export = _module()
    episode = _episode()
    episode["test"][0]["input"] = bad_grid
    with pytest.raises(ValueError):
        export.public_turn(episode, 0)


@pytest.mark.parametrize("index", [True, -1, 2, 0.0])
def test_public_turn_rejects_invalid_query_index(index):
    with pytest.raises(ValueError):
        _module().public_turn(_episode(), index)


@pytest.mark.parametrize("options", [
    {"seed": True}, {"seed": -1}, {"seed": 2**63},
    {"demos": True}, {"demos": 1}, {"demos": 7},
    {"queries": True}, {"queries": 0}, {"queries": 5},
])
def test_invalid_request_leaves_no_destination(tmp_path, options):
    export = _module()
    output = tmp_path / "new"
    request = {"seed": 17, "demos": 3, "queries": 4, **options}
    with pytest.raises(ValueError):
        export.export_episodes(output, **request)
    assert not output.exists()


def test_existing_output_is_refused(tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("keep")
    with pytest.raises((FileExistsError, ValueError)):
        _module().export_episodes(output, seed=17)
    assert marker.read_text() == "keep"


@pytest.fixture(scope="module")
def checked_export(tmp_path_factory):
    export = _module()
    output = tmp_path_factory.mktemp("checked") / "bundle"
    summary = export.export_episodes(output, seed=17, demos=3, queries=4)
    return export, output, summary


def test_real_racket_export_is_private_and_sequential(checked_export):
    export, output, summary = checked_export
    assert summary["episodes"] == 2
    assert summary["public_files"] == 8
    controller = json.loads((output / "private/controller.json").read_bytes())
    assert controller["racket"]["backend"] == "racket"
    assert controller["racket"]["protected"] is True
    assert controller["racket_evaluations"] == 20
    assert [row["settings"] for row in controller["episodes"]] == [
        {"mover": "body"}, {"mover": "target"}]
    assert all(row["reference"] == "proposed_parametric" for row in controller["episodes"])
    assert b"accepted_parametric" not in (output / "private/controller.json").read_bytes()
    assert sorted(p.name for p in output.iterdir()) == ["private", "public"]
    public_paths = list((output / "public").iterdir())
    manifest = json.loads((output / "private/manifest.json").read_bytes())
    indexed_public = [row["path"] for row in manifest["files"] if row["path"].startswith("public/")]
    assert indexed_public == sorted("public/" + path.name for path in public_paths)
    assert len(public_paths) == 8
    for episode, check in zip(controller["episodes"], controller["checks"]):
        assert len(episode["train"]) == 3 and len(episode["test"]) == 4
        assert len(episode["reveal_ids"]) == 4
        assert check["survivors"] == [episode["settings"]]
        for index, visible_id in enumerate(episode["reveal_ids"]):
            assert re.fullmatch(r"[0-9a-f]{64}", visible_id)
            data = (output / "public" / f"{visible_id}.json").read_bytes()
            visible = json.loads(data)
            assert set(visible) == {"train", "test"}
            assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
            assert data == _raw({"train": episode["train"], "test": [
                {"input": episode["test"][index]["input"]}]})
            assert hashlib.sha256(data).hexdigest() == visible_id
    result = export.verify_export(output)
    assert result["episodes"] == 2 and result["public_files"] == 8
    assert result["racket_reexecuted"] is False


def test_first_turn_is_identical_for_single_and_four_query_exports(checked_export, tmp_path):
    export, multi, _ = checked_export
    single = tmp_path / "single"
    export.export_episodes(single, seed=17, demos=3, queries=1)
    multi_data = json.loads((multi / "private/controller.json").read_bytes())
    single_data = json.loads((single / "private/controller.json").read_bytes())
    for many, one in zip(multi_data["episodes"], single_data["episodes"]):
        assert many["reveal_ids"][0] == one["reveal_ids"][0]
        name = many["reveal_ids"][0] + ".json"
        assert (multi / "public" / name).read_bytes() == (single / "public" / name).read_bytes()


def test_duplicate_visible_batch_is_rejected_before_output(checked_export, monkeypatch, tmp_path):
    export, source, _ = checked_export
    controller = json.loads((source / "private/controller.json").read_bytes())
    result = {key: deepcopy(controller[key]) for key in
              ("episodes", "checks", "racket", "racket_evaluations")}
    for row in result["episodes"]:
        row.pop("reveal_ids")
        row["reference"] = "accepted_parametric"
    result["episodes"][1]["train"] = deepcopy(result["episodes"][0]["train"])
    monkeypatch.setattr(export, "evaluate_contract", lambda *args, **kwargs: result)
    output = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="[Dd]uplicate"):
        export.export_episodes(output, seed=17)
    assert not output.exists()


def test_failed_native_execution_leaves_no_destination(monkeypatch, tmp_path):
    export = _module()
    def fail(*args, **kwargs):
        raise ValueError("Racket query labels failed")
    monkeypatch.setattr(export, "evaluate_contract", fail)
    output = tmp_path / "failed"
    with pytest.raises(ValueError, match="Racket"):
        export.export_episodes(output, seed=17)
    assert not output.exists()


def _refresh_manifest(output, relative):
    manifest_path = output / "private/manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    data = (output / relative).read_bytes()
    for row in manifest["files"]:
        if row["path"] == relative:
            row.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    manifest_path.write_bytes(_raw(manifest))


def test_verifier_refuses_symlinked_manifest_before_reading(tmp_path):
    output = tmp_path / "export"
    (output / "private").mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text("This outside file must not be parsed.")
    (output / "private/manifest.json").symlink_to(outside)
    with pytest.raises(ValueError, match="symlinks"):
        _module().verify_export(output)


@pytest.mark.parametrize("mutation", [
    "label_hash", "private_bool", "private_float", "query_count", "demo_count",
    "public_answer", "manifest_path", "program_hash", "certificate", "unindexed_file",
])
def test_serialized_verifier_rejects_corrupted_exports(checked_export, tmp_path, mutation):
    export, source, _ = checked_export
    output = tmp_path / mutation
    shutil.copytree(source, output)
    controller_path = output / "private/controller.json"
    controller = json.loads(controller_path.read_bytes())
    if mutation == "manifest_path":
        path = output / "private/manifest.json"
        manifest = json.loads(path.read_bytes())
        manifest["files"][0]["path"] = "../../outside.json"
        path.write_bytes(_raw(manifest))
    elif mutation == "unindexed_file":
        (output / "public/extra.json").write_text("{}\n")
    elif mutation == "public_answer":
        relative = "public/" + controller["episodes"][0]["reveal_ids"][0] + ".json"
        visible = json.loads((output / relative).read_bytes())
        visible["test"][0]["output"] = [[7]]
        (output / relative).write_bytes(_raw(visible))
        _refresh_manifest(output, relative)
    else:
        if mutation == "label_hash":
            grid = controller["episodes"][0]["test"][0]["output"]
            grid[0][0] = (grid[0][0] + 1) % 10
        elif mutation in {"private_bool", "private_float"}:
            controller["episodes"][0]["test"][0]["output"][0][0] = (
                True if mutation == "private_bool" else 1.0)
        elif mutation == "query_count":
            controller["request"]["queries"] = 1
        elif mutation == "demo_count":
            controller["request"]["demos"] = True
        elif mutation == "program_hash":
            controller["episodes"][0]["program_sha256"] = "0" * 64
        elif mutation == "certificate":
            controller["checks"][0]["survivors"] = [{"mover": "target"}]
        controller_path.write_bytes(_raw(controller))
        if mutation != "label_hash":
            _refresh_manifest(output, "private/controller.json")
    with pytest.raises(ValueError):
        export.verify_export(output)
