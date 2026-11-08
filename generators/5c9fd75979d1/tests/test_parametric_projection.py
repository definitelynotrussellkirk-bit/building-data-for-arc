"""Projection/file-boundary tests; synthetic receipts do not claim Racket replay."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


TASK = "5c9fd75979d1"
HOME = Path(__file__).resolve().parents[1]


@pytest.fixture
def projector():
    path = HOME / "workspace/parametric/export_qualified.py"
    assert path.is_file(), "The qualified-evidence projector must exist"
    spec = importlib.util.spec_from_file_location("qualified_projection_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write_receipt(folder, qualification, execution):
    folder.mkdir(parents=True, exist_ok=True)
    payload = encoded(execution)
    (folder / "execution.json").write_bytes(payload)
    qualification["execution"] = {
        "path": "execution.json", "sha256": hashlib.sha256(payload).hexdigest()
    }
    path = folder / "qualification.json"
    path.write_bytes(encoded(qualification))
    return path


@pytest.fixture
def qualified(tmp_path, projector, monkeypatch):
    # The source-ready boundary is the sole substitute: the parent is still
    # authoring the real prototype. Native receipt validation remains real.
    contract = {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK}/workspace/parametric/adapter.py",
        "parameters": {"min_bbox_area": [2, 4, 8]},
        "default": {"min_bbox_area": 2},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
    }
    programs = {
        2: "(rule! (lambda (g) g))",
        4: "(rule! (lambda (g) (flip-lr g)))",
        8: "(rule! (lambda (g) (flip-ud g)))",
    }
    binding = {
        "task_id": TASK, "rule_task_id": TASK,
        "generator_sha256": "a" * 64, "rule_hash": "b" * 12,
        "canonical_program_sha256": hashlib.sha256(programs[2].encode()).hexdigest(),
        "files": [{"path": contract["adapter"], "sha256": "c" * 64}],
        "executor": {"parametric_promotion.py": "d" * 64},
    }
    jobs, episodes, checks = [], [], []
    for cutoff in (2, 4, 8):
        for seed in (0, 17):
            index = len(episodes)
            setting = {"min_bbox_area": cutoff}
            pairs = []
            for offset in range(7):
                number = index * 7 + offset
                grid = [[number // 10, number % 10], [0, 1]]
                pairs.append({"input": grid, "output": copy.deepcopy(grid)})
            jobs.append({"seed": seed, "settings": setting, "demos": 3, "queries": 4})
            episodes.append({
                "task_id": TASK, "seed": seed, "settings": setting,
                "train": pairs[:3], "test": pairs[3:], "program": programs[cutoff],
                "program_sha256": hashlib.sha256(programs[cutoff].encode()).hexdigest(),
                "reference": "accepted_parametric",
            })
            checks.append({"seed": seed, "settings": setting,
                           "counts": {"demos": 3, "queries": 4},
                           "survivors": [setting], "label_count": 7})
    execution = {"episodes": episodes, "checks": checks,
                 "racket": {"backend": "racket", "protected": True},
                 "racket_evaluations": 78}
    qualification = {
        "schema": "arcpuzzles-parametric-qualification-v1", "status": "qualified",
        "task_id": TASK, "source_binding": copy.deepcopy(binding),
        "contract": copy.deepcopy(contract), "jobs": jobs,
        "programs": {json.dumps({"min_bbox_area": value}, separators=(",", ":")):
                     hashlib.sha256(program.encode()).hexdigest()
                     for value, program in programs.items()},
        "limits": "Synthetic serialization fixture only; no Racket execution.",
        "training_admitted": False,
    }
    monkeypatch.setattr(projector.native, "_ready", lambda catalog, tid:
                        (copy.deepcopy(contract), copy.deepcopy(binding)))
    path = write_receipt(tmp_path / "qualification", qualification, execution)
    return path, qualification, execution, binding


def test_first_turn_has_only_visible_demo_and_one_query(projector):
    episode = {"train": [{"input": [[1]], "output": [[2]]}],
               "test": [{"input": [[3]], "output": [[4]]},
                        {"input": [[5]], "output": [[6]]}],
               "settings": {"secret": 8}, "program": "PRIVATE", "seed": 42}
    identifier, payload = projector.project_query(episode, 0)
    expected = b'{"test":[{"input":[[3]]}],"train":[{"input":[[1]],"output":[[2]]}]}\n'
    assert payload == expected
    assert identifier == hashlib.sha256(expected).hexdigest()
    single = copy.deepcopy(episode)
    single["test"] = single["test"][:1]
    assert projector.project_query(single, 0) == (identifier, payload)


def test_private_changes_cannot_change_public_bytes_or_id(projector):
    episode = {"train": [{"input": [[1]], "output": [[2]]}],
               "test": [{"input": [[3]], "output": [[4]]},
                        {"input": [[5]], "output": [[6]]}]}
    changed = copy.deepcopy(episode)
    changed.update(seed=999, settings={"min_bbox_area": 8}, program="SECRET",
                   episode_index=123, query_count=4)
    changed["test"][0]["output"] = [[9]]
    changed["test"][1] = {"input": [[8, 8]], "output": [[7]]}
    assert projector.project_query(changed, 0) == projector.project_query(episode, 0)


def test_exports_every_query_with_private_order_and_source_receipt(projector, qualified, tmp_path):
    path, _, execution, _ = qualified
    out = tmp_path / "export"
    result = projector.export_qualification(path, out)
    assert result["episodes"] == 6
    assert result["public_queries"] == 24
    public_files = sorted((out / "public").iterdir())
    assert len(public_files) == 24
    assert {p.name for p in out.iterdir()} == {"public", "private"}
    private = json.loads((out / "private/manifest.json").read_bytes())
    assert private["owner_acceptance"] == "not_performed"
    assert private["training_admitted"] is False
    assert private["qualification_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert [row["path"] for row in private["public_files"]] == sorted(
        row["path"] for row in private["public_files"])
    for source, hidden in zip(execution["episodes"], private["episodes"]):
        assert hidden["seed"] == source["seed"]
        assert hidden["settings"] == source["settings"]
        assert hidden["program"] == source["program"]
        assert hidden["test"] == source["test"]
        assert len(hidden["public_ids"]) == 4
        for query, identifier in zip(source["test"], hidden["public_ids"]):
            payload = (out / "public" / f"{identifier}.json").read_bytes()
            assert hashlib.sha256(payload).hexdigest() == identifier
            assert json.loads(payload) == {"train": source["train"], "test": [{"input": query["input"]}]}
    assert all(len(json.loads(path.read_bytes())["test"]) == 1 for path in public_files)


@pytest.mark.parametrize("damage", ["status", "task", "digest", "unprotected", "source", "programs", "coverage", "bad_grid"])
def test_rejects_invalid_receipts_before_publication(projector, qualified, tmp_path, damage):
    path, q, execution, binding = qualified
    if damage == "status":
        q["status"] = "proposed"
    elif damage == "task":
        q["task_id"] = "another_task"
    elif damage == "unprotected":
        execution["racket"]["protected"] = False
    elif damage == "source":
        binding["generator_sha256"] = "f" * 64
    elif damage == "programs":
        q["programs"] = {}
    elif damage == "coverage":
        q["jobs"] = q["jobs"][:-1]
        execution["episodes"] = execution["episodes"][:-1]
        execution["checks"] = execution["checks"][:-1]
    elif damage == "bad_grid":
        execution["episodes"][0]["test"][0]["output"] = [[True]]
    write_receipt(path.parent, q, execution)
    if damage == "digest":
        (path.parent / "execution.json").write_bytes(b"{}\n")
    out = tmp_path / "rejected"
    with pytest.raises(ValueError):
        projector.export_qualification(path, out)
    assert not out.exists()


def test_rejects_duplicate_visible_queries_even_with_different_private_labels(projector, qualified, tmp_path):
    path, q, execution, _ = qualified
    first, second = execution["episodes"][:2]
    second["train"] = copy.deepcopy(first["train"])
    second["test"][0]["input"] = copy.deepcopy(first["test"][0]["input"])
    second["test"][0]["output"] = [[9]]
    write_receipt(path.parent, q, execution)
    out = tmp_path / "duplicates"
    with pytest.raises(ValueError, match="[Dd]uplicate"):
        projector.export_qualification(path, out)
    assert not out.exists()


def test_refuses_existing_destination_without_modifying_it(projector, qualified, tmp_path):
    path, *_ = qualified
    out = tmp_path / "existing"
    out.mkdir()
    marker = out / "keep.txt"
    marker.write_text("untouched")
    with pytest.raises(FileExistsError):
        projector.export_qualification(path, out)
    assert marker.read_text() == "untouched"
    assert list(out.iterdir()) == [marker]


def test_cli_exports_without_acceptance(projector, qualified, tmp_path, capsys):
    path, *_ = qualified
    out = tmp_path / "cli-export"
    assert projector.main(["--qualification", str(path), "--out", str(out)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["public_queries"] == 24
    assert summary["owner_acceptance"] == "not_performed"
