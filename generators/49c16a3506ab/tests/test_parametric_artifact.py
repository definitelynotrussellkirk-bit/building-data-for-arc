"""Actual writer/Racket and adversarial serialized-artifact checks."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import types

import pytest
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

HOME = find_root(__file__) / "generators/49c16a3506ab/workspace/parametric"


@pytest.fixture(scope="module")
def tool():
    path = HOME / "artifact.py"
    assert path.is_file(), "The Racket-backed artifact tool is not yet implemented"
    sys.path.insert(0, str(HOME))
    try:
        spec = importlib.util.spec_from_file_location("stop_short_artifact_tests", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


@pytest.fixture(scope="module")
def examples(tool):
    return [tool.adapter.generate(17, {"stop_short": stop}, 3, 4) for stop in range(3)]


def test_actual_writer_racket_and_sequential_projection(tool, examples, tmp_path):
    output = tmp_path / "export"
    manifest = tool.write_export(examples, output)
    result = tool.verify_export(output)
    assert result["episodes"] == 3
    assert result["turns"] == 12
    assert result["racket_replayed"] is False
    assert manifest["racket_evaluations"] == 39
    assert manifest["training_admitted"] is False
    public = sorted((output / "public").glob("*.json"))
    assert [p.stem for p in public] == sorted(public_challenge_id(e) for e in examples)
    for ep in examples:
        turn = tool.adapter.visible_turn(ep, 0)
        assert (output / "turns" / (public_challenge_id(turn) + ".json")).read_bytes() == public_challenge_bytes(turn)
    with pytest.raises(FileExistsError):
        tool.write_export(examples, output)


@pytest.mark.parametrize("corruption", ["duplicate", "bool_output", "wrong_answer", "invalid_grammar"])
def test_writer_rejects_before_publication(tool, examples, tmp_path, corruption):
    bad = copy.deepcopy(examples[:1])
    if corruption == "duplicate":
        bad *= 2
    elif corruption == "bool_output":
        bad[0]["train"][0]["output"][0][0] = True
    elif corruption == "wrong_answer":
        bad[0]["test"][0]["output"][0][0] = 6
    else:
        grid = bad[0]["test"][0]["input"]
        color = grid[0][0]
        grid[0][3] = color  # nonmoving scatter adjacent to the top-left block
        bad[0]["test"][0]["output"] = tool.adapter.transform(grid, 0)
    output = tmp_path / "bad"
    with pytest.raises(ValueError):
        tool.write_export(bad, output)
    assert not output.exists()


@pytest.mark.parametrize("corruption", ["public_byte", "extra_file", "forged_certificate", "private_bool"])
def test_verifier_rejects_tampered_serialized_artifacts(tool, examples, tmp_path, corruption):
    output = tmp_path / "export"
    tool.write_export(examples[:1], output)
    if corruption == "public_byte":
        path = next((output / "public").glob("*.json"))
        path.write_bytes(path.read_bytes() + b" ")
    elif corruption == "extra_file":
        (output / "turns" / "unexpected.json").write_text("{}")
    else:
        path = output / "private.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if corruption == "forged_certificate":
            rows[0]["episode"]["certificate"]["surviving_settings"] = []
        else:
            rows[0]["episode"]["test"][0]["output"][0][0] = True
        path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows))
        manifest_path = output / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["files"]["private.jsonl"] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        tool.verify_export(output)


def test_certificate_boolean_cannot_impersonate_integer(tool, examples):
    bad = copy.deepcopy(examples[1])
    bad["certificate"]["surviving_settings"][0]["stop_short"] = True
    with pytest.raises(ValueError, match="certificate"):
        tool._validate(bad)


def test_artifact_loads_its_adjacent_adapter_despite_cached_name(monkeypatch):
    monkeypatch.setitem(sys.modules, "adapter", types.SimpleNamespace(TASK_ID="unrelated-family"))
    spec = importlib.util.spec_from_file_location("stop_short_polluted_import", HOME / "artifact.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.adapter.TASK_ID == "49c16a3506ab"
