"""Focused tests for the task-local, unapproved rectangle-policy prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"
VERIFY_PATH = HOME / "workspace" / "parametric" / "verify.py"
SHARED_RUNTIME = HOME.parents[1] / "shared" / "runtime"


def load_prototype():
    spec = importlib.util.spec_from_file_location(
        "parametric_rectangle_policy_test", PROTOTYPE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load parametric prototype")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_verifier():
    for path in (VERIFY_PATH.parent, SHARED_RUNTIME):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)
    spec = importlib.util.spec_from_file_location(
        "parametric_rectangle_policy_verifier_test", VERIFY_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load parametric verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def test_default_program_is_exact_canonical_authority():
    proto = load_prototype()
    assert proto.PARAMETER_NAME == "rectangle_policy"
    assert proto.ALLOWED_SETTINGS == ("longer", "both")
    assert proto.DEFAULT_SETTING == "longer"
    assert proto.program_for("longer") == proto.canonical_program()


def test_verifier_executes_implicit_grid_rule_wrapper_in_racket():
    proto = load_prototype()
    verifier = load_verifier()
    grid = proto.build_episode(
        20261023, setting="longer", demo_count=5, query_count=4
    )["train"][0]["input"]
    assert verifier.execute(proto.program_for("longer"), [grid]) == [
        proto.apply_python(grid, "longer")
    ]


@pytest.mark.parametrize("setting", ["longer", "both"])
def test_episode_keeps_one_setting_and_four_distinct_identifiable_queries(setting):
    proto = load_prototype()
    episode = proto.build_episode(20261023, setting=setting, demo_count=5, query_count=4)
    assert len(episode["train"]) == 5
    assert len(episode["test"]) == 4
    assert episode["meta"][proto.PARAMETER_NAME] == setting
    all_pairs = episode["train"] + episode["test"]
    assert len({grid_key(pair["input"]) for pair in all_pairs}) == len(all_pairs)
    assert all(
        pair["output"] == proto.apply_python(pair["input"], setting)
        for pair in all_pairs
    )

    other = next(value for value in proto.ALLOWED_SETTINGS if value != setting)
    assert any(
        proto.apply_python(pair["input"], other) != pair["output"]
        for pair in episode["train"]
    )
    assert all(
        proto.is_rectangle(pair["input"])
        and proto.apply_python(pair["input"], other) != pair["output"]
        for pair in episode["test"]
    )


def test_public_projection_redacts_setting_program_seed_and_query_answers():
    proto = load_prototype()
    public = proto.public_challenge(
        proto.build_episode(17, setting="both", demo_count=3, query_count=4)
    )
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    text = json.dumps(public)
    assert "rectangle_policy" not in text
    assert '"both"' not in text
    assert '"program"' not in text
    assert '"seed"' not in text


@pytest.mark.parametrize("bad", [True, False, 1, None, "unknown"])
def test_invalid_settings_fail_closed(bad):
    proto = load_prototype()
    with pytest.raises((TypeError, ValueError)):
        proto.build_episode(0, setting=bad)


@pytest.mark.parametrize("demo_count,query_count", [(0, 4), (1, 0), (1.5, 4), (5, True)])
def test_invalid_episode_counts_fail_closed(demo_count, query_count):
    proto = load_prototype()
    with pytest.raises((TypeError, ValueError)):
        proto.build_episode(0, setting="longer", demo_count=demo_count, query_count=query_count)


def test_public_batch_plan_is_visible_id_sorted_and_enumeration_invariant():
    """Catches writing public files in private setting iteration order."""
    proto = load_prototype()
    verifier = load_verifier()
    items = [
        (
            setting,
            proto.build_episode(
                20261023, setting=setting, demo_count=3, query_count=4
            ),
        )
        for setting in proto.ALLOWED_SETTINGS
    ]

    forward = verifier.plan_public_batch(items)
    reversed_plan = verifier.plan_public_batch(list(reversed(items)))

    assert forward == reversed_plan
    public_ids = [row["public_id"] for row in forward]
    assert public_ids == sorted(public_ids)
    assert all(len(public_id) == 64 for public_id in public_ids)
    assert all(
        row["filename"] == f"episode-{row['public_id']}.json"
        for row in forward
    )
    assert all(
        hashlib.sha256(row["payload"]).hexdigest() == row["public_id"]
        for row in forward
    )


def test_public_batch_identity_ignores_private_data_and_rejects_visible_duplicates():
    """Catches hidden metadata/query labels influencing IDs or bypassing dedupe."""
    proto = load_prototype()
    verifier = load_verifier()
    episode = proto.build_episode(17, setting="both", demo_count=3, query_count=4)
    private_changed = deepcopy(episode)
    private_changed["meta"]["seed"] = 999999
    private_changed["meta"][proto.PARAMETER_NAME] = "longer"
    private_changed["program"] = "private replacement"
    for pair in private_changed["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]

    original_row = verifier.plan_public_batch([("original", episode)])[0]
    changed_row = verifier.plan_public_batch([("changed", private_changed)])[0]
    assert original_row["public_id"] == changed_row["public_id"]
    assert original_row["payload"] == changed_row["payload"]

    with pytest.raises(ValueError, match="duplicate visible public payload"):
        verifier.plan_public_batch(
            [("original", episode), ("private-changed", private_changed)]
        )

    visible_changed = deepcopy(episode)
    old = visible_changed["train"][0]["output"][0][0]
    visible_changed["train"][0]["output"][0][0] = (old + 1) % 10
    visible_row = verifier.plan_public_batch([("visible-changed", visible_changed)])[0]
    assert visible_row["public_id"] != original_row["public_id"]

    query_changed = deepcopy(episode)
    old = query_changed["test"][0]["input"][0][0]
    query_changed["test"][0]["input"][0][0] = (old + 1) % 10
    query_row = verifier.plan_public_batch([("query-changed", query_changed)])[0]
    assert query_row["public_id"] != original_row["public_id"]


def test_public_batch_writer_writes_exact_visible_bytes_in_planned_order(
    tmp_path, monkeypatch
):
    """Catches a writer that plans correctly but writes a private-order batch."""
    proto = load_prototype()
    verifier = load_verifier()
    items = [
        (
            setting,
            proto.build_episode(
                20261023, setting=setting, demo_count=3, query_count=4
            ),
        )
        for setting in reversed(proto.ALLOWED_SETTINGS)
    ]

    real_write_bytes = Path.write_bytes
    write_calls = []

    def recording_write_bytes(path, payload):
        if path.parent == tmp_path:
            write_calls.append(path.name)
        return real_write_bytes(path, payload)

    monkeypatch.setattr(Path, "write_bytes", recording_write_bytes)
    written = verifier.write_public_batch(tmp_path, items)

    assert write_calls == [row["filename"] for row in written]
    assert [row["public_id"] for row in written] == sorted(
        row["public_id"] for row in written
    )
    assert [row["private_key"] for row in written] == [
        row["private_key"]
        for row in verifier.plan_public_batch(list(reversed(items)))
    ]
    assert {path.name for path in tmp_path.iterdir()} == {
        row["filename"] for row in written
    }
    for row in written:
        assert (tmp_path / row["filename"]).read_bytes() == row["payload"]



def test_public_batch_writer_preflights_all_overwrites_before_any_write(tmp_path):
    """Catches a late collision leaving a partially written public batch."""
    proto = load_prototype()
    verifier = load_verifier()
    items = [
        (
            setting,
            proto.build_episode(
                20261023, setting=setting, demo_count=3, query_count=4
            ),
        )
        for setting in proto.ALLOWED_SETTINGS
    ]
    plan = verifier.plan_public_batch(items)
    occupied = tmp_path / plan[-1]["filename"]
    occupied.write_bytes(b"pre-existing")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        verifier.write_public_batch(tmp_path, items)

    assert {path.name for path in tmp_path.iterdir()} == {occupied.name}
    assert occupied.read_bytes() == b"pre-existing"
