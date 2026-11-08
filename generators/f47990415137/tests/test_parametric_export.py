"""Transport tests use synthetic data; they make no reference-label claims."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


EXPORT_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/export.py"
SPEC = importlib.util.spec_from_file_location("f47990415137_parametric_export", EXPORT_PATH)
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)


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
        "settings": {"reference": "axes"},
        "program_solution": "(rule! synthetic-export-fixture)",
        "private": {"reference_execution": "synthetic transport fixture only"},
    }


def files(directory):
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def test_public_turn_has_exact_current_demos_and_only_the_selected_query():
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


def test_first_turn_bytes_ignore_future_queries_and_all_private_metadata():
    full = episode()
    single = deepcopy(full)
    single["test"] = single["test"][:1]
    altered = deepcopy(full)
    altered["test"][0]["output"] = [[9]]
    altered["test"][1:] = [None, {"input": "invalid unrevealed grid"}, {}]
    altered["seed"] = -765
    altered["settings"] = {"reference": "largest"}
    altered["program_solution"] = "another private program"
    bodies = [
        json.dumps(exporter.public_turn(value), sort_keys=True, separators=(",", ":"))
        for value in (full, single, altered)
    ]
    assert bodies[0] == bodies[1] == bodies[2]


@pytest.mark.parametrize("index", [-1, True, 0.0, "0", 4])
def test_public_turn_rejects_invalid_query_selection(index):
    with pytest.raises(ValueError):
        exporter.public_turn(episode(), index)


@pytest.mark.parametrize("grid", [[], [[]], [[True]], [[1.0]], [[-1]], [[10]], [[1], [1, 2]], [[0] * 31]])
def test_public_turn_rejects_invalid_visible_grids(grid):
    source = episode()
    source["test"][0]["input"] = grid
    with pytest.raises(ValueError):
        exporter.public_turn(source)


def test_write_batch_is_sorted_content_addressed_and_keeps_labels_private(tmp_path):
    first = episode()
    second = deepcopy(first)
    second["train"][0]["output"] = [[1, 0]]
    second["settings"] = {"reference": "largest"}
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
    }


def test_write_batch_public_names_ignore_settings_seeds_programs_and_query_answers(tmp_path):
    first = episode()
    changed = deepcopy(first)
    changed.update(seed=56, settings={"reference": "largest"}, program_solution="private variant")
    for pair in changed["test"]:
        pair["output"] = [[9]]
    left, right = tmp_path / "left", tmp_path / "right"
    exporter.write_batch([first], left)
    exporter.write_batch([changed], right)
    assert files(left / "public") == files(right / "public")
    assert files(left / "turns") == files(right / "turns")
    assert files(left / "private") != files(right / "private")


def test_duplicate_controller_payload_is_rejected_before_any_writes(tmp_path):
    first = episode()
    duplicate = deepcopy(first)
    duplicate["seed"] = 42
    duplicate["settings"] = {"reference": "largest"}
    duplicate["test"][0]["output"] = [[9]]
    target = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate"):
        exporter.write_batch([first, duplicate], target)
    assert not target.exists()


def test_duplicate_turn_payload_is_rejected_even_when_controller_payload_differs(tmp_path):
    first = episode()
    duplicate_turn = deepcopy(first)
    duplicate_turn["test"][-1]["input"] = [[8, 0]]
    target = tmp_path / "duplicate-turn"
    with pytest.raises(ValueError, match="duplicate"):
        exporter.write_batch([first, duplicate_turn], target)
    assert not target.exists()


@pytest.mark.parametrize("failure", ["empty", "invalid-visible-grid", "non-json-private"])
def test_batch_preflight_errors_do_not_create_destination(tmp_path, failure):
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


def test_existing_destination_is_preserved(tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    (target / "keep.txt").write_text("existing user content")
    with pytest.raises(FileExistsError):
        exporter.write_batch([episode()], target)
    assert files(target) == {"keep.txt": b"existing user content"}
