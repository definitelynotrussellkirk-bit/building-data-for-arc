"""Public projection is independent of all controller-only state."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def tool():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/check.py"
    assert path.is_file(), "the runnable parametric check/export tool is missing"
    spec = importlib.util.spec_from_file_location("ef03216cf2fa_public_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode():
    return {
        "train": [{"input": [[1, 0]], "output": [[1]]}],
        "test": [{"input": [[2, 0]], "output": [[2]]},
                 {"input": [[3, 0]], "output": [[3]]}],
        "settings": {"ranking": "perimeter"},
        "seed": 17,
        "program_solution": "PRIVATE",
    }


def test_private_changes_cannot_change_first_public_turn():
    check = tool()
    before = episode()
    after = copy.deepcopy(before)
    after.update(seed=999, settings={"ranking": "normalized_top_edge"},
                 program_solution="OTHER PRIVATE")
    after["test"][0]["output"] = [[9]]
    after["test"][1] = {"input": [[8, 8]], "output": [[7]]}
    assert check.public_view_bytes(before, 0) == check.public_view_bytes(after, 0)
    visible = json.loads(check.public_view_bytes(before, 0))
    assert visible == {"train": before["train"], "test": [{"input": [[2, 0]]}]}
    single = {**before, "test": before["test"][:1]}
    assert check.public_view_bytes(single, 0) == check.public_view_bytes(before, 0)


def test_public_view_rejects_bool_or_invalid_query_index():
    check = tool()
    for index in (True, -1, 2, "0", 0.0):
        with pytest.raises((TypeError, ValueError)):
            check.public_view_bytes(episode(), index)


def test_writer_hashes_exact_visible_bytes_and_masks_all_answers(tmp_path):
    check = tool()
    destination = tmp_path / "public"
    paths = check.write_public_views([episode()], destination)
    assert len(paths) == 2
    assert sorted(p.name for p in destination.iterdir()) == sorted(paths)
    for filename in paths:
        raw = (destination / filename).read_bytes()
        assert filename == hashlib.sha256(raw).hexdigest() + ".json"
        value = json.loads(raw)
        assert set(value) == {"train", "test"}
        assert len(value["test"]) == 1
        assert set(value["test"][0]) == {"input"}


def test_duplicate_public_payload_fails_before_publication(tmp_path):
    check = tool()
    destination = tmp_path / "public"
    with pytest.raises(ValueError, match="duplicate"):
        check.write_public_views([episode(), episode()], destination)
    assert not destination.exists()


def test_existing_public_destination_is_preserved(tmp_path):
    check = tool()
    destination = tmp_path / "public"
    destination.mkdir()
    (destination / "keep.txt").write_text("keep")
    with pytest.raises(FileExistsError):
        check.write_public_views([episode()], destination)
    assert (destination / "keep.txt").read_text() == "keep"
