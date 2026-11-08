"""Public-byte identities and private/public isolation for the scaling export."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/exporter.py"
SPEC = importlib.util.spec_from_file_location("scaling_export_test", PATH)
E = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E)


@pytest.fixture
def episode():
    # Literal grids test export boundaries, without asserting a puzzle rule.
    return {
        "seed": 17, "task_id": "7fc158ab7b70", "setting": {"count_basis": "cells"},
        "authority": {"rule_text": "PRIVATE PROGRAM", "source_sha256": "PRIVATE HASH"},
        "pairs": {
            "train": [
                {"input": [[1, 0], [0, 1]], "output": [[1, 1], [1, 1]],
                 "annotation": "PRIVATE DEMO NOTE"},
                {"input": [[2, 0], [0, 3]], "output": [[2, 3], [2, 3]]},
            ],
            "test": [
                {"input": [[color, 0], [0, color]], "output": [[9, color]],
                 "future_hint": "PRIVATE QUERY NOTE"}
                for color in (4, 5, 6, 7)
            ],
            "count": 4,
        },
        "future_hint": "PRIVATE FUTURE NOTE",
    }


def read(out, entry):
    return json.loads((out / entry["path"]).read_bytes())


@pytest.mark.parametrize("change", ["setting", "seed", "program", "query_answer", "annotation"])
def test_private_changes_preserve_public_ids_bytes_and_relative_paths(tmp_path, episode, change):
    original = E.export_episode(tmp_path, episode)
    changed = deepcopy(episode)
    if change == "setting":
        changed["setting"] = {"count_basis": "colors", "scale_axes": "columns"}
    elif change == "seed":
        changed["seed"] = 993
    elif change == "program":
        changed["authority"] = {"rule_text": "DIFFERENT PRIVATE PROGRAM"}
    elif change == "query_answer":
        changed["pairs"]["test"][0]["output"] = [[8, 8, 8]]
    else:
        changed["pairs"]["train"][0]["annotation"] = "DIFFERENT PRIVATE NOTE"
    second = E.export_episode(tmp_path, changed)
    for key in ("public_id", "public_archive", "turn_ids", "turns"):
        assert second[key] == original[key]
    assert second["private"] != original["private"]
    assert read(tmp_path, original["private"])["episode"] == episode
    assert read(tmp_path, second["private"])["episode"] == changed
    assert len(list((tmp_path / "public_archive").iterdir())) == 1
    assert len(list((tmp_path / "turns").iterdir())) == 4
    assert len(list((tmp_path / "private").iterdir())) == 2


def test_public_paths_hash_only_exact_visible_serialized_bytes(tmp_path, episode):
    result = E.export_episode(tmp_path, episode)
    for entry in [result["public_archive"], *result["turns"]]:
        raw = (tmp_path / entry["path"]).read_bytes()
        assert re.fullmatch(r"(?:public_archive|turns)/[0-9a-f]{64}\.json", entry["path"])
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
        assert Path(entry["path"]).stem == entry["sha256"]
        assert len(raw) == entry["bytes"]
        assert raw == E.SUPPORT.public_challenge_bytes(json.loads(raw))
    assert result["public_id"] == result["public_archive"]["sha256"]
    assert result["turn_ids"] == [entry["sha256"] for entry in result["turns"]]
    assert E.export_episode(tmp_path, episode) == result


def test_first_turn_is_identical_for_one_or_four_queries(tmp_path, episode):
    one = deepcopy(episode)
    one["pairs"]["test"] = one["pairs"]["test"][:1]
    one["pairs"]["count"] = 1
    full_export = E.export_episode(tmp_path, episode)
    one_export = E.export_episode(tmp_path, one)
    assert E.public_first_turn(one) == E.public_first_turn(episode)
    assert one_export["turns"][0] == full_export["turns"][0]
    assert one_export["turn_ids"][0] == full_export["turn_ids"][0]
    assert one_export["public_id"] != full_export["public_id"]
    assert len(read(tmp_path, full_export["public_archive"])["test"]) == 4
    assert len(read(tmp_path, one_export["public_archive"])["test"]) == 1


def test_turn_schema_strips_all_private_keys_and_future_queries(tmp_path, episode):
    result = E.export_episode(tmp_path, episode)
    for index, entry in enumerate(result["turns"]):
        turn = read(tmp_path, entry)
        assert set(turn) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in turn["train"])
        assert turn["test"] == [{"input": episode["pairs"]["test"][index]["input"]}]
        assert "PRIVATE" not in (tmp_path / entry["path"]).read_text()
    saved = read(tmp_path, result["private"])
    assert saved["episode"] == episode
    assert saved["visibility"] == "controller_only"
    assert saved["turns"] == result["turns"]


def test_projections_and_written_files_are_independent_deep_copies(tmp_path, episode):
    before = deepcopy(episode)
    challenge = E.public_challenge(episode)
    turn = E.public_first_turn(episode)
    result = E.export_episode(tmp_path, episode)
    challenge["train"][0]["input"][0][0] = 8
    turn["test"][0]["input"][0][0] = 9
    assert episode == before
    episode["pairs"]["train"][1]["output"][0][0] = 8
    episode["pairs"]["test"][0]["input"][0][0] = 8
    assert challenge["train"][1]["output"] == before["pairs"]["train"][1]["output"]
    assert turn["train"][1]["output"] == before["pairs"]["train"][1]["output"]
    assert read(tmp_path, result["private"])["episode"] == before
    assert read(tmp_path, result["turns"][0]) == E.public_first_turn(before)


@pytest.mark.parametrize("index", [-1, 4, True, False, 1.0, "0", None])
def test_query_indices_are_strict_and_never_wrap(episode, index):
    with pytest.raises(ValueError):
        E.public_turn(episode, index)


def test_current_turn_does_not_read_future_or_private_answers(episode):
    first = E.public_first_turn(episode)
    episode["pairs"]["test"][0]["output"] = "PRIVATE UNREAD ANSWER"
    episode["pairs"]["test"][1] = "INVALID FUTURE MATERIAL"
    assert E.public_first_turn(episode) == first
    with pytest.raises(ValueError):
        E.public_challenge(episode)


@pytest.mark.parametrize("bad_grid", [[], [[True]], [[0], [1, 2]], [[10]], [[0] * 31], "grid"])
def test_malformed_visible_grids_fail_before_creating_an_export(tmp_path, episode, bad_grid):
    episode["pairs"]["test"][0]["input"] = bad_grid
    out = tmp_path / "new-export"
    with pytest.raises(ValueError):
        E.export_episode(out, episode)
    assert not out.exists()


def test_non_json_private_metadata_fails_before_creating_an_export(tmp_path, episode):
    episode["authority"]["not_json"] = {1, 2}
    out = tmp_path / "new-export"
    with pytest.raises(TypeError):
        E.export_episode(out, episode)
    assert not out.exists()


def test_existing_mismatched_content_is_never_overwritten(tmp_path, episode):
    result = E.export_episode(tmp_path, episode)
    public = tmp_path / result["turns"][0]["path"]
    public.write_bytes(b"retain conflicting file\n")
    with pytest.raises(FileExistsError):
        E.export_episode(tmp_path, episode)
    assert public.read_bytes() == b"retain conflicting file\n"


def test_managed_directory_symlink_cannot_redirect_public_data(tmp_path, episode):
    out = tmp_path / "export"
    out.mkdir()
    outside = tmp_path / "private-elsewhere"
    outside.mkdir()
    (out / "turns").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        E.export_episode(out, episode)
    assert not list(outside.iterdir())
