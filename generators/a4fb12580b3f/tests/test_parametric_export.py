"""Authoring export boundaries; native source readiness is isolated, never accepted."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]


def load_exporter():
    path = HOME / "workspace/parametric/export_qualified.py"
    assert path.is_file(), "The authoring-only qualified exporter has not been implemented"
    spec = importlib.util.spec_from_file_location("a4fb_export_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode():
    return {"task_id": "a4fb12580b3f", "seed": 19,
            "settings": {"mode": "largest_relay"}, "program": "(lambda (g) g)",
            "train": [{"input": [[1, 2]], "output": [[1, 4]]}],
            "test": [{"input": [[1, color]], "output": [[1, 4]]}
                     for color in (3, 5, 6, 7)]}


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


@pytest.fixture
def qualified(tmp_path, monkeypatch):
    """Use the real native receipt checker, isolating only live catalog readiness.

    These synthetic labels are serialization fixtures, never reference evidence.
    The complete current native qualification is exercised by the caller's run.
    """
    from arcpuzzles import parametric_promotion as native
    contract = {"default": {"mode": "direct"}}
    binding = {"task_id": "a4fb12580b3f", "source_sha256": "source-fixture"}
    monkeypatch.setattr(native, "_ready", lambda catalog, task_id: (contract, binding))
    value = episode()
    value["program_sha256"] = hashlib.sha256(value["program"].encode()).hexdigest()
    # The worker's accepted_parametric field predates actual acceptance; this
    # exporter must replace it with an explicit authoring-only designation.
    value["reference"] = "accepted_parametric"
    job = {"seed": 19, "settings": value["settings"], "demos": 1, "queries": 4}
    execution = {"episodes": [value], "checks": [{"survivors": [value["settings"]],
                 "label_count": 5}], "racket": {"backend": "racket", "protected": True},
                 "racket_evaluations": 5}
    path = tmp_path / "qualification.json"

    def write():
        encoded = raw(execution)
        path.with_name("execution.json").write_bytes(encoded)
        receipt = {"schema": native.QUALIFICATION, "status": "qualified",
                   "task_id": value["task_id"], "contract": contract,
                   "source_binding": binding, "jobs": [job],
                   "programs": native._check_execution(execution, [job], binding, contract),
                   "execution": {"path": "execution.json", "sha256": hashlib.sha256(encoded).hexdigest()}}
        path.write_bytes(raw(receipt))
        return path

    write()
    return path, execution, binding, write


def test_first_turn_is_exactly_single_query_projection_and_does_not_mutate():
    exporter = load_exporter()
    from reviewer_support import public_challenge_bytes, public_challenge_id
    full = episode()
    before = deepcopy(full)
    visible = exporter.reveal(full, 0)
    single = deepcopy(full)
    single["test"] = single["test"][:1]
    assert visible == {"train": before["train"], "test": [{"input": [[1, 3]]}]}
    assert public_challenge_bytes(visible) == public_challenge_bytes(single)
    assert public_challenge_id(visible) == public_challenge_id(single)
    visible["train"][0]["input"][0][0] = 9
    assert full == before


def test_private_changes_cannot_change_first_turn_bytes_or_identifier():
    exporter = load_exporter()
    from reviewer_support import public_challenge_bytes, public_challenge_id
    initial = episode()
    changed = deepcopy(initial)
    changed.update(seed=999, settings={"mode": "direct"}, program="private alternative")
    changed["test"][0]["output"] = [[9]]
    changed["test"][1:] = [{"input": [[8]], "output": [[2]]}]
    first, second = exporter.reveal(initial, 0), exporter.reveal(changed, 0)
    assert public_challenge_bytes(first) == public_challenge_bytes(second)
    assert public_challenge_id(first) == public_challenge_id(second)
    assert set(first) == {"train", "test"} and len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}


@pytest.mark.parametrize("index", [True, False, -1, 4, 1.0, "0", None])
def test_reveal_rejects_invalid_index(index):
    with pytest.raises(ValueError, match="index"):
        load_exporter().reveal(episode(), index)


@pytest.mark.parametrize("split,field", [("train", "input"), ("train", "output"),
                                          ("test", "input"), ("test", "output")])
@pytest.mark.parametrize("grid", [[[True]], [[1], [2, 3]], [], [[10]], [[1.0]]])
def test_reveal_rejects_invalid_grids(split, field, grid):
    value = episode()
    value[split][0][field] = grid
    with pytest.raises(ValueError):
        load_exporter().reveal(value, 0)


def test_each_query_can_be_revealed_without_future_metadata():
    exporter = load_exporter()
    for index, query in enumerate(episode()["test"]):
        assert exporter.reveal(episode(), index) == {
            "train": episode()["train"], "test": [{"input": query["input"]}]}


def test_export_uses_exact_visible_hash_names_and_private_receipts(qualified, tmp_path):
    path, execution, _, _ = qualified
    exporter = load_exporter()
    out = tmp_path / "new-export"
    before = deepcopy(execution)
    result = exporter.export_qualified(ROOT, path, out)
    public = (out / "public.jsonl").read_bytes()
    digest = hashlib.sha256(public).hexdigest()
    assert sorted(p.name for p in (out / "public").iterdir()) == [digest + ".json"]
    assert (out / "public" / (digest + ".json")).read_bytes() == public
    challenge = json.loads(public)
    assert challenge == exporter.reveal(execution["episodes"][0], 0)
    private = json.loads((out / "private.jsonl").read_bytes())
    assert private["episode"]["test"] == execution["episodes"][0]["test"]
    assert private["episode"]["seed"] == 19
    assert private["episode"]["settings"] == {"mode": "largest_relay"}
    assert private["episode"]["program"] == "(lambda (g) g)"
    assert private["episode"]["reference"] == "qualified_authoring_only"
    manifest = json.loads((out / "manifest.private.json").read_bytes())
    assert result == manifest
    assert manifest["training_admitted"] is False
    assert manifest["status"] == "authoring_only"
    assert manifest["owner_acceptance"] == "not_performed"
    assert manifest["qualification"]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert manifest["execution"]["sha256"] == hashlib.sha256(path.with_name("execution.json").read_bytes()).hexdigest()
    assert "source_binding" in manifest
    assert execution == before
    with pytest.raises(FileExistsError):
        exporter.export_qualified(ROOT, path, out)


def test_corrupt_execution_is_refused_before_publication(qualified, tmp_path):
    path, _, _, _ = qualified
    path.with_name("execution.json").write_bytes(b"{}\n")
    out = tmp_path / "invalid"
    with pytest.raises(ValueError, match="execution hash"):
        load_exporter().export_qualified(ROOT, path, out)
    assert not out.exists()


def test_current_source_drift_is_refused_before_publication(qualified, tmp_path):
    path, _, binding, _ = qualified
    binding["source_sha256"] = "changed-current-source"
    out = tmp_path / "drift"
    with pytest.raises(ValueError, match="current source/contract"):
        load_exporter().export_qualified(ROOT, path, out)
    assert not out.exists()


def test_private_invalid_label_is_refused_before_publication(qualified, tmp_path):
    path, execution, _, write = qualified
    execution["episodes"][0]["test"][3]["output"] = [[False]]
    write()
    out = tmp_path / "bad-private"
    with pytest.raises(ValueError):
        load_exporter().export_qualified(ROOT, path, out)
    assert not out.exists()
