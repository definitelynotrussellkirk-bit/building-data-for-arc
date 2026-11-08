"""Strict authoring-export regressions; these tests do not claim Racket replay."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/audit.py"
SPEC = importlib.util.spec_from_file_location("_row_export_audit_test", PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def episode(marker=1):
    return {"train": [{"input": [[marker, 2]], "output": [[2]]}],
            "test": [{"input": [[marker, 3]], "output": [[3]]}],
            "settings": {"selection": "rows"}, "seed": 0, "program_solution": "private"}


def rewrite_hash(out, name):
    manifest = json.loads((out / "manifest.json").read_text())
    manifest["files"][name] = AUDIT.digest((out / name).read_bytes())
    (out / "manifest.json").write_bytes(AUDIT.json_bytes(manifest))


def test_writer_exact_public_bytes_names_sorted_batch_and_private_invariance(tmp_path):
    source = [episode(4), episode(1)]
    out = tmp_path / "export"
    assert AUDIT.write_export(out, source, {"status": "test-only"})["status"] == "passed"
    rows = AUDIT.prepare_public(source)
    assert sorted(p.name for p in (out / "public").iterdir()) == [r[0] + ".json" for r in rows]
    assert (out / "public.jsonl").read_bytes() == b"".join(r[1] for r in rows)
    for identifier, raw, original in rows:
        assert (out / "public" / f"{identifier}.json").read_bytes() == raw
        visible = json.loads(raw)
        assert set(visible) == {"train", "test"} and set(visible["test"][0]) == {"input"}
        changed = copy.deepcopy(original)
        changed.update(seed=17, settings={"selection": "secret"}, program_solution="new secret")
        changed["test"][0]["output"] = [[9]]
        assert AUDIT.prepare_public([changed])[0][:2] == (identifier, raw)


def test_duplicate_visible_bytes_rejected_before_destination_creation(tmp_path):
    first, second = episode(), episode()
    second.update(seed=17, settings={"selection": "another"})
    second["test"][0]["output"] = [[9]]
    out = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate visible"):
        AUDIT.write_export(out, [first, second], {})
    assert not out.exists()


def test_existing_destination_refused_without_modification(tmp_path):
    sentinel = tmp_path / "keep.txt"
    sentinel.write_text("unchanged")
    with pytest.raises(FileExistsError):
        AUDIT.write_export(tmp_path, [episode()], {})
    assert sentinel.read_text() == "unchanged" and sorted(p.name for p in tmp_path.iterdir()) == ["keep.txt"]


@pytest.mark.parametrize("split,field", [("train", "input"), ("train", "output"),
                                        ("test", "input"), ("test", "output")])
def test_bool_cells_fail_closed_in_visible_and_private_grids(tmp_path, split, field):
    bad = episode()
    bad[split][0][field][0][0] = True
    out = tmp_path / "bad"
    with pytest.raises(ValueError, match="exact integer"):
        AUDIT.write_export(out, [bad], {})
    assert not out.exists()


def test_verifier_rejects_public_projection_tampering(tmp_path):
    out = tmp_path / "export"
    AUDIT.write_export(out, [episode()], {})
    public = next((out / "public").iterdir())
    value = json.loads(public.read_text())
    value["test"][0]["output"] = [[3]]
    public.write_bytes(AUDIT.json_bytes(value))
    rewrite_hash(out, "public/" + public.name)
    with pytest.raises(ValueError, match="projection differs"):
        AUDIT.verify_export(out)


def test_verifier_rejects_private_bool_even_with_updated_manifest(tmp_path):
    out = tmp_path / "export"
    AUDIT.write_export(out, [episode()], {})
    private = json.loads((out / "private.json").read_text())
    private["episodes"][0]["test"][0]["output"] = [[True]]
    (out / "private.json").write_bytes(AUDIT.json_bytes(private))
    rewrite_hash(out, "private.json")
    with pytest.raises(ValueError, match="exact integer"):
        AUDIT.verify_export(out)


def test_first_turn_uses_only_demos_and_current_query():
    one = episode()
    many = copy.deepcopy(one)
    many["test"] += [{"input": [[9]], "output": [[8]]}] * 3
    many.update(seed=17, settings={"selection": "hidden"}, final_turn=False, total_queries=4)
    many["test"][0]["output"] = [[7]]
    assert AUDIT.current_query_bytes(one) == AUDIT.current_query_bytes(many)
    assert json.loads(AUDIT.current_query_bytes(many)) == {
        "train": one["train"], "test": [{"input": one["test"][0]["input"]}]}


def test_verifier_rejects_noncanonical_batch_order(tmp_path):
    out = tmp_path / "export"
    AUDIT.write_export(out, [episode(4), episode(1)], {})
    lines = (out / "public.jsonl").read_bytes().splitlines(keepends=True)
    (out / "public.jsonl").write_bytes(b"".join(reversed(lines)))
    rewrite_hash(out, "public.jsonl")
    with pytest.raises(ValueError, match="sorted hash order"):
        AUDIT.verify_export(out)


def test_verifier_rejects_private_public_id_mismatch(tmp_path):
    out = tmp_path / "export"
    AUDIT.write_export(out, [episode()], {})
    private = json.loads((out / "private.json").read_text())
    private["episodes"][0]["public_id"] = "0" * 64
    (out / "private.json").write_bytes(AUDIT.json_bytes(private))
    rewrite_hash(out, "private.json")
    with pytest.raises(ValueError, match="public identifier differs"):
        AUDIT.verify_export(out)


def test_strict_json_rejects_duplicate_keys(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"train":[],"train":[],"test":[]}')
    with pytest.raises(ValueError, match="duplicate JSON"):
        AUDIT.read_json(path)
