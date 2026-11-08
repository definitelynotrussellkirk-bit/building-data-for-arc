"""Projection tests with hand grids; these do not certify Racket label semantics."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "workspace/parametric/export_examples.py"


def _exporter():
    assert SOURCE.is_file(), "The task-local example writer must exist"
    spec = importlib.util.spec_from_file_location("frame_export_projection_tests", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _episode(queries=4):
    """Small literal serialization fixture, deliberately not an ARC rule oracle."""
    return {
        "seed": 17,
        "settings": {"axis": "vertical"},
        "program_solution": "private reference text",
        "train": [
            {"input": [[1, 0]], "output": [[1, 1]], "hidden": "demo metadata"},
            {"input": [[0, 2]], "output": [[2, 2]]},
        ],
        "test": [
            {"input": [[3, 0]], "output": [[3, 3]]},
            {"input": [[0, 4]], "output": [[4, 4]]},
            {"input": [[5, 0]], "output": [[5, 5]]},
            {"input": [[0, 6]], "output": [[6, 6]]},
        ][:queries],
    }


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _visible_train():
    return [
        {"input": [[1, 0]], "output": [[1, 1]]},
        {"input": [[0, 2]], "output": [[2, 2]]},
    ]


def test_public_files_have_exact_visible_bytes_and_private_order(tmp_path):
    exporter = _exporter()
    episode = _episode()
    before = deepcopy(episode)
    output = tmp_path / "examples"
    exporter.write_examples(output, [episode])

    index = json.loads((output / "private.json").read_bytes())
    record = index["episodes"][0]
    assert record["episode"] == episode
    assert episode == before
    expected = _raw({"train": _visible_train(), "test": [
        {"input": [[3, 0]]}, {"input": [[0, 4]]},
        {"input": [[5, 0]]}, {"input": [[0, 6]]},
    ]})
    assert record["public"] == "public/" + hashlib.sha256(expected).hexdigest() + ".json"
    assert (output / record["public"]).read_bytes() == expected
    assert len(record["turns"]) == 4
    for path, query in zip(record["turns"], episode["test"]):
        expected_turn = _raw({"train": _visible_train(), "test": [{"input": query["input"]}]})
        assert path == "turns/public/" + hashlib.sha256(expected_turn).hexdigest() + ".json"
        assert (output / path).read_bytes() == expected_turn
    assert exporter.verify_examples(output)["status"] == "verified_projection"


def test_first_turn_has_identical_name_and_bytes_for_one_or_four_queries(tmp_path):
    exporter = _exporter()
    paths = []
    for count in (1, 4):
        output = tmp_path / str(count)
        exporter.write_examples(output, [_episode(count)])
        record = json.loads((output / "private.json").read_bytes())["episodes"][0]
        paths.append((record["turns"][0], (output / record["turns"][0]).read_bytes()))
    assert paths[0] == paths[1]


def test_private_settings_seed_program_and_query_labels_do_not_change_public_ids(tmp_path):
    exporter = _exporter()
    first = _episode()
    second = deepcopy(first)
    second.update(seed=999, settings={"axis": "long_axis"}, program_solution="different private text")
    second["test"][0]["output"] = [[9, 9]]
    records = []
    for name, episode in (("a", first), ("b", second)):
        output = tmp_path / name
        exporter.write_examples(output, [episode])
        records.append(json.loads((output / "private.json").read_bytes())["episodes"][0])
    assert records[0]["public"] == records[1]["public"]
    assert records[0]["turns"] == records[1]["turns"]


def test_existing_directory_is_refused_without_overwriting(tmp_path):
    exporter = _exporter()
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("unchanged")
    with pytest.raises(FileExistsError):
        exporter.write_examples(output, [_episode()])
    assert sentinel.read_text() == "unchanged"
    assert not (output / "private.json").exists()


@pytest.mark.parametrize("bad_case", ["boolean_input", "ragged_input", "missing_query_label", "boolean_query_label", "duplicate_input", "duplicate_public"])
def test_invalid_payloads_fail_before_creating_destination(tmp_path, bad_case):
    exporter = _exporter()
    episode = _episode()
    episodes = [episode]
    if bad_case == "boolean_input":
        episode["test"][0]["input"] = [[True, 0]]
    elif bad_case == "ragged_input":
        episode["test"][0]["input"] = [[3, 0], [3]]
    elif bad_case == "missing_query_label":
        del episode["test"][0]["output"]
    elif bad_case == "boolean_query_label":
        episode["test"][0]["output"] = [[True, 3]]
    elif bad_case == "duplicate_input":
        episode["test"][0]["input"] = deepcopy(episode["train"][0]["input"])
    elif bad_case == "duplicate_public":
        episodes.append(deepcopy(episode))
        episodes[1]["test"][0]["output"] = [[9, 9]]
    output = tmp_path / "invalid"
    with pytest.raises(ValueError):
        exporter.write_examples(output, episodes)
    assert not output.exists()


@pytest.mark.parametrize("corruption", ["leaked_answer", "changed_demo", "wrong_turn_order", "unlisted_public_file", "private_boolean_label"])
def test_verifier_rejects_projection_and_inventory_corruption(tmp_path, corruption):
    exporter = _exporter()
    output = tmp_path / "examples"
    exporter.write_examples(output, [_episode()])
    index_path = output / "private.json"
    index = json.loads(index_path.read_bytes())
    record = index["episodes"][0]
    if corruption in {"leaked_answer", "changed_demo"}:
        path = output / record["turns"][0]
        value = json.loads(path.read_bytes())
        if corruption == "leaked_answer":
            value["test"][0]["output"] = [[3, 3]]
        else:
            value["train"][0]["output"] = [[9, 9]]
        path.write_bytes(_raw(value))
    elif corruption == "wrong_turn_order":
        record["turns"].reverse()
        index_path.write_bytes(_raw(index))
    elif corruption == "unlisted_public_file":
        (output / "turns/public/extra.json").write_text("{}\n")
    else:
        record["episode"]["test"][0]["output"] = [[True, 3]]
        index_path.write_bytes(_raw(index))
    with pytest.raises(ValueError):
        exporter.verify_examples(output)
