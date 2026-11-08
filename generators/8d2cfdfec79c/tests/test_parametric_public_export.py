"""Task-local public export regressions; fixtures need no reference runtime."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import public_challenge_bytes, public_challenge_id


@pytest.fixture(scope="module")
def exporter():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/public_export.py"
    assert path.is_file(), "task-local public projection/export helper is missing"
    spec = importlib.util.spec_from_file_location("rectangle_public_export", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def episode():
    return {
        "train": [
            {"input": [[0, 1]], "output": [[1, 1]], "private": "demo note"},
            {"input": [[2], [0]], "output": [[2], [2]]},
        ],
        "test": [
            {"input": [[3, 0]], "output": [[3, 3]]},
            {"input": [[4, 0, 4]], "output": [[4, 4, 4]]},
            {"input": [[5], [0], [5]], "output": [[5], [5], [5]]},
            {"input": [[6, 0], [0, 6]], "output": [[6, 6], [6, 6]]},
        ],
        "settings": {"secret": "parameter"},
        "program": "private reference code",
        "seed": 8123,
        "query_count": 4,
    }


def test_selected_turn_contains_only_demos_and_one_query(exporter, episode):
    visible = exporter.public_turn(episode, query_index=1)
    expected = {
        "train": [
            {"input": [[0, 1]], "output": [[1, 1]]},
            {"input": [[2], [0]], "output": [[2], [2]]},
        ],
        "test": [{"input": [[4, 0, 4]]}],
    }
    assert visible == expected
    assert public_challenge_bytes(visible) == (
        b'{"test":[{"input":[[4,0,4]]}],"train":[{"input":[[0,1]],'
        b'"output":[[1,1]]},{"input":[[2],[0]],"output":[[2],[2]]}]}\n'
    )


def test_first_turn_equals_single_query_episode_without_future_inputs(exporter, episode):
    single = deepcopy(episode)
    single["test"] = single["test"][:1]
    single.pop("query_count")
    first = exporter.public_turn(episode)
    assert first == exporter.public_turn(single)
    assert first["test"] == [{"input": [[3, 0]]}]
    # Neither malformed future pairs nor private answers are consulted.
    episode["test"][0]["output"] = object()
    episode["test"][1:] = [None, {"input": "unrevealed future input"}]
    assert exporter.public_turn(episode) == first


def test_private_metadata_and_query_answers_do_not_change_bytes_or_ids(exporter, episode):
    original = exporter.public_turn(episode)
    altered = deepcopy(episode)
    altered.update(settings={"different": True}, seed=-999, program="other program", final=True)
    altered["train"][0]["private"] = "changed"
    for pair in altered["test"]:
        pair["output"] = [[9]]
        pair["turn_number"] = 99
    projected = exporter.public_turn(altered)
    assert projected == original
    assert public_challenge_bytes(projected) == public_challenge_bytes(original)
    assert public_challenge_id(projected) == public_challenge_id(original)


def test_projection_copies_grids_and_breaks_source_aliases(exporter, episode):
    shared_row = [7, 0]
    episode["train"][0] = {"input": [shared_row], "output": [shared_row]}
    episode["test"][0]["input"] = [shared_row, shared_row]
    visible = exporter.public_turn(episode)
    visible["train"][0]["input"][0][0] = 8
    visible["test"][0]["input"][0][0] = 9
    assert shared_row == [7, 0]
    assert visible["train"][0]["output"] == [[7, 0]]
    assert visible["test"][0]["input"][1] == [7, 0]
    shared_row[1] = 6
    assert visible["train"][0]["output"] == [[7, 0]]


@pytest.mark.parametrize("query_index", [True, False, 1.0, "0", None, -1, 4])
def test_bad_query_indices_fail_closed(exporter, episode, query_index):
    with pytest.raises(ValueError):
        exporter.public_turn(episode, query_index=query_index)


@pytest.mark.parametrize("bad", [None, {}, {"train": [], "test": []},
    {"train": [{"input": [[0]], "output": [[True]]}], "test": [{"input": [[1]]}]},
    {"train": [{"input": [[0]], "output": [[1]]}], "test": [{"input": [[1], [1, 2]]}]},
])
def test_malformed_visible_content_is_rejected(exporter, bad):
    with pytest.raises(ValueError):
        exporter.public_turn(bad)


def test_writer_emits_exact_canonical_bytes_sorted_content_ids(exporter, episode, tmp_path):
    other = deepcopy(episode)
    other["test"][2]["input"] = [[8, 0, 8]]
    expected = [
        {"train": [{"input": [[0, 1]], "output": [[1, 1]]},
                   {"input": [[2], [0]], "output": [[2], [2]]}],
         "test": [{"input": [[5], [0], [5]]}]},
        {"train": [{"input": [[0, 1]], "output": [[1, 1]]},
                   {"input": [[2], [0]], "output": [[2], [2]]}],
         "test": [{"input": [[8, 0, 8]]}]},
    ]
    out = tmp_path / "public"
    ids = exporter.write_public_turns([other, episode], out, query_index=2)
    expected_bytes = {hashlib.sha256(public_challenge_bytes(p)).hexdigest():
                      public_challenge_bytes(p) for p in expected}
    assert ids == sorted(expected_bytes)
    assert sorted(p.name for p in out.iterdir()) == [f"{key}.json" for key in ids]
    for key in ids:
        raw = (out / f"{key}.json").read_bytes()
        assert raw == expected_bytes[key]
        assert key == public_challenge_id(json.loads(raw))


def test_duplicate_visible_payload_rejected_before_creating_directory(exporter, episode, tmp_path):
    other = deepcopy(episode)
    other.update(seed=999, settings={"other": "private"}, program="different")
    other["test"][0]["output"] = [[9]]
    out = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate"):
        exporter.write_public_turns([episode, other], out)
    assert not out.exists()


def test_invalid_later_episode_does_not_leave_partial_export(exporter, episode, tmp_path):
    bad = deepcopy(episode)
    bad["train"][1]["output"] = [[10]]
    out = tmp_path / "invalid"
    with pytest.raises(ValueError):
        exporter.write_public_turns([episode, bad], out)
    assert not out.exists()


def test_writer_requires_fresh_directory(exporter, episode, tmp_path):
    out = tmp_path / "existing"
    out.mkdir()
    marker = out / "keep.txt"
    marker.write_text("preserve me")
    with pytest.raises(FileExistsError):
        exporter.write_public_turns([episode], out)
    assert list(out.iterdir()) == [marker]
    assert marker.read_text() == "preserve me"


@pytest.mark.parametrize("query_index", [True, -1, 4])
def test_writer_rejects_bad_index_without_output(exporter, episode, tmp_path, query_index):
    out = tmp_path / "bad-index"
    with pytest.raises(ValueError):
        exporter.write_public_turns([episode], out, query_index=query_index)
    assert not out.exists()


def test_empty_batch_is_rejected_without_output(exporter, tmp_path):
    out = tmp_path / "empty"
    with pytest.raises(ValueError):
        exporter.write_public_turns([], out)
    assert not out.exists()
