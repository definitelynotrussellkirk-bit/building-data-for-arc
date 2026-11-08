"""Sequential public writer regressions; fixtures are synthetic, not Racket proof.

The real receipt parser and execution validator run here. Only live source
inventory lookup is replaced by a tiny source-hashed fixture. Native protected
qualification of the actual adapter is separate round evidence.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import parametric_promotion as native


HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "arc0b6b3a286ad0_projection", HOME / "workspace/parametric/export_qualified.py")
EXPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTER)


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


@pytest.fixture
def qualified(tmp_path, monkeypatch):
    root = tmp_path / "library"
    (root / "catalog").mkdir(parents=True)
    (root / "catalog/puzzles.jsonl").write_text("")
    source = root / "source.py"
    source.write_text("# bounded fixture source\n")
    contract = {"schema": native.CONTRACT, "parameters": {"closure_rounds": [1, 2]},
                "default": {"closure_rounds": 1},
                "limits": {"demos": [2, 6], "queries": [1, 4]}}

    def ready(catalog, task_id):
        assert catalog.root == root and task_id == EXPORTER.TASK_ID
        return deepcopy(contract), {"task_id": task_id,
            "canonical_program_sha256": sha(b"(rule! g)"),
            "files": [{"path": "source.py", "sha256": sha(source.read_bytes())}]}

    monkeypatch.setattr(native, "_ready", ready)
    jobs, episodes, checks = [], [], []
    for rounds in (1, 2):
        for seed in (0, 17):
            settings = {"closure_rounds": rounds}
            job = {"settings": settings, "seed": seed, "demos": 3, "queries": 4}
            program = "(rule! g)" if rounds == 1 else "(rule! (flip-lr g))"
            pairs = [{"input": [[seed // 10, seed % 10, index, 9]],
                      "output": [[seed // 10, seed % 10, index, 9]] if rounds == 1
                      else [[9, index, seed % 10, seed // 10]]} for index in range(7)]
            jobs.append(job)
            episodes.append({"task_id": EXPORTER.TASK_ID, "settings": settings,
                             "seed": seed, "program": program, "program_sha256": sha(program.encode()),
                             "train": pairs[:3], "test": pairs[3:]})
            checks.append({"survivors": [settings], "label_count": 7})
    execution = {"episodes": episodes, "checks": checks,
                 "racket": {"backend": "racket", "protected": True}, "racket_evaluations": 28}
    binding = ready(type("FixtureCatalog", (), {"root": root})(), EXPORTER.TASK_ID)[1]
    programs = native._check_execution(execution, jobs, binding, contract)
    directory = tmp_path / "qualification"
    directory.mkdir()
    (directory / "execution.json").write_bytes(raw(execution))
    qualification = {"schema": native.QUALIFICATION, "status": "qualified", "task_id": EXPORTER.TASK_ID,
                     "source_binding": binding, "contract": contract, "jobs": jobs, "programs": programs,
                     "execution": {"path": "execution.json", "sha256": sha(raw(execution))},
                     "training_admitted": False}
    path = directory / "qualification.json"
    path.write_bytes(raw(qualification))
    return root, source, path, qualification, execution


def rewrite_receipts(fixture):
    _, _, path, qualification, execution = fixture
    encoded = raw(execution)
    path.with_name("execution.json").write_bytes(encoded)
    qualification["execution"]["sha256"] = sha(encoded)
    path.write_bytes(raw(qualification))


def test_first_view_matches_single_query_and_ignores_all_private_fields(qualified):
    episode = qualified[4]["episodes"][0]
    expected = EXPORTER.public_view_bytes(episode)
    single = deepcopy(episode)
    single["test"] = single["test"][:1]
    assert EXPORTER.public_view_bytes(single) == expected
    assert EXPORTER._public_bytes(single) == expected
    changed = deepcopy(episode)
    changed.update(seed=999, settings={"unrelated": "private"}, program="private program",
                   program_solution="private adapter program", program_sha256="private hash")
    changed["test"][0]["output"] = [[8]]
    changed["test"][1:] = [{"input": [[8, 8]], "output": [[7]]}]
    assert EXPORTER.public_view_bytes(changed) == expected
    visible = json.loads(expected)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])


@pytest.mark.parametrize("index", [True, False, -1, 4, 1.0])
def test_query_index_is_an_exact_bounded_integer(qualified, index):
    with pytest.raises(ValueError, match="query_index"):
        EXPORTER.public_view_bytes(qualified[4]["episodes"][0], index)


def test_export_has_sorted_visible_hash_names_and_private_query_order(qualified, tmp_path, monkeypatch):
    root, _, path, _, execution = qualified
    written = []
    write_bytes = Path.write_bytes

    def observe(path, value):
        if path.parent.name == "public":
            written.append(path.stem)
        return write_bytes(path, value)

    monkeypatch.setattr(Path, "write_bytes", observe)
    output = tmp_path / "export"
    result = EXPORTER.export_qualified(path, output, library=root)
    assert result["views"] == 16 and result["episodes"] == 4
    assert written == sorted(set(written))
    assert {child.name for child in output.iterdir()} == {"public", "private"}
    assert (output / "private/qualification.json").read_bytes() == path.read_bytes()
    assert (output / "private/execution.json").read_bytes() == path.with_name("execution.json").read_bytes()
    assert json.loads((output / "private/execution.json").read_bytes())["episodes"] == execution["episodes"]
    manifest = json.loads((output / "private/manifest.json").read_bytes())
    assert [row["path"] for row in manifest["public_files"]] == sorted(row["path"] for row in manifest["public_files"])
    for mapping, episode in zip(manifest["episodes"], execution["episodes"]):
        assert mapping["view_ids"] == [sha(EXPORTER.public_view_bytes(episode, index)) for index in range(4)]
    for file in (output / "public").iterdir():
        payload = file.read_bytes()
        assert file.name == sha(payload) + ".json"
        visible = json.loads(payload)
        assert set(visible) == {"train", "test"}
        assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    assert EXPORTER.verify_export(output, library=root)["status"] == "verified_projection"
    assert manifest["training_admitted"] is False and manifest["racket_replayed"] is False


@pytest.mark.parametrize("change", ["source", "execution_bytes", "status", "program_map", "unprotected"])
def test_native_receipt_failures_publish_nothing(qualified, tmp_path, change):
    root, source, path, qualification, execution = qualified
    if change == "source":
        source.write_text("# changed after qualification\n")
    elif change == "execution_bytes":
        file = path.with_name("execution.json")
        file.write_bytes(file.read_bytes() + b" ")
    else:
        if change == "status":
            qualification["status"] = "accepted"
        elif change == "program_map":
            qualification["programs"] = {}
        else:
            execution["racket"]["protected"] = False
        rewrite_receipts(qualified)
    output = tmp_path / "rejected"
    with pytest.raises(ValueError):
        EXPORTER.export_qualified(path, output, library=root)
    assert not output.exists()


@pytest.mark.parametrize("change", ["boolean_input", "boolean_label", "ragged", "duplicate_input", "duplicate_view", "shortened_queries"])
def test_invalid_projection_data_publish_nothing(qualified, tmp_path, change):
    root, _, path, _, execution = qualified
    episode = execution["episodes"][0]
    if change == "boolean_input":
        episode["test"][0]["input"][0][0] = True
    elif change == "boolean_label":
        episode["test"][0]["output"][0][0] = False
    elif change == "ragged":
        episode["train"][0]["input"].append([1])
    elif change == "duplicate_input":
        episode["test"][0]["input"] = deepcopy(episode["train"][0]["input"])
    elif change == "duplicate_view":
        execution["episodes"][1]["train"] = deepcopy(episode["train"])
        execution["episodes"][1]["test"] = deepcopy(episode["test"])
    else:
        episode["test"].pop()
        qualified[3]["jobs"][0]["queries"] = 3
        execution["checks"][0]["label_count"] = 6
    rewrite_receipts(qualified)
    output = tmp_path / "rejected"
    with pytest.raises(ValueError):
        EXPORTER.export_qualified(path, output, library=root)
    assert not output.exists()


def test_source_edit_during_serialization_prevents_publication(qualified, tmp_path, monkeypatch):
    root, source, path, _, _ = qualified
    original = EXPORTER.public_view_bytes

    def changed(episode, query_index=0):
        result = original(episode, query_index)
        source.write_text("# changed during serialization\n")
        return result

    monkeypatch.setattr(EXPORTER, "public_view_bytes", changed)
    output = tmp_path / "rejected"
    with pytest.raises(ValueError, match="source|contract"):
        EXPORTER.export_qualified(path, output, library=root)
    assert not output.exists()


def test_existing_output_is_preserved(qualified, tmp_path):
    root, _, path, _, _ = qualified
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_bytes(b"unchanged")
    with pytest.raises(FileExistsError):
        EXPORTER.export_qualified(path, output, library=root)
    assert sentinel.read_bytes() == b"unchanged"


@pytest.mark.parametrize("change", ["public_bytes", "public_extra", "public_directory", "manifest_order", "source"])
def test_saved_bundle_verifier_rejects_tampering(qualified, tmp_path, change):
    root, source, path, _, _ = qualified
    output = tmp_path / "export"
    EXPORTER.export_qualified(path, output, library=root)
    if change == "public_bytes":
        first = next((output / "public").glob("*.json"))
        first.write_bytes(first.read_bytes() + b" ")
    elif change == "public_extra":
        (output / "public/leak.json").write_bytes(b'{"seed": 17}')
    elif change == "public_directory":
        (output / "public/seed-17").mkdir()
    elif change == "manifest_order":
        manifest = output / "private/manifest.json"
        value = json.loads(manifest.read_bytes())
        value["episodes"][0]["view_ids"].reverse()
        manifest.write_bytes(raw(value))
    else:
        source.write_text("# source changed after export\n")
    with pytest.raises(ValueError):
        EXPORTER.verify_export(output, library=root)
