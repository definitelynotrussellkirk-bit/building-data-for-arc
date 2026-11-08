"""Task-local public export and demonstration-only ambiguity regressions."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import public_challenge_bytes, public_challenge_id


PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"


@pytest.fixture(scope="module")
def prototype():
    spec = importlib.util.spec_from_file_location("cfadc43e5098_export_revision", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=64) as instance:
        yield instance


@pytest.fixture(scope="module")
def evidence(prototype, bridge):
    return prototype.build_evidence(bridge, seed=17, demo_count=2, query_count=4)


@pytest.fixture(scope="module")
def agreement_inputs(prototype):
    generator, _, _ = prototype._generator()
    inputs = [generator.generate(991, index, scene_profile=profile)
              for index, profile in enumerate(("public_1", "public_2"))]
    assert all(not generator.self_check(grid) for grid in inputs)
    return inputs


def make_episode(prototype, bridge, demos, queries, policy="same_color"):
    def pair(grid):
        return {"input": deepcopy(grid), "output": prototype.run_racket(bridge, policy, grid)}

    return {
        "parameter": {"blocker_policy": policy},
        "train": [pair(grid) for grid in demos],
        "test": [pair(grid) for grid in queries],
    }


def public_files(out):
    return {path.name: path.read_bytes() for path in (out / "public").glob("*.json")}


def test_public_writer_hashes_exact_written_visible_bytes(prototype, evidence, tmp_path):
    out = tmp_path / "batch"
    prototype.materialize(out, evidence)
    expected = {}
    for record in evidence["settings"].values():
        raw = public_challenge_bytes(record["episode"])
        digest = hashlib.sha256(raw).hexdigest()
        assert digest == public_challenge_id(record["episode"])
        assert prototype.public_episode_id(record["episode"]) == "episode-" + digest
        expected["episode-" + digest + ".json"] = raw
    assert public_files(out) == expected
    assert all(set(json.loads(raw)) == {"train", "test"} for raw in expected.values())
    manifest = json.loads((out / "manifest.json").read_text())
    for row in manifest["files"]:
        raw = (out / row["path"]).read_bytes()
        assert row["sha256"] == hashlib.sha256(raw).hexdigest()
        assert row["bytes"] == len(raw)


def test_private_metadata_and_query_answers_do_not_change_export(prototype, evidence, tmp_path):
    changed = deepcopy(evidence)
    changed["seed"] = -193
    for record in changed["settings"].values():
        episode = record["episode"]
        episode["seed"] = -193
        episode["parameter"]["blocker_policy"] = "private-value-changed"
        episode["racket_sha256"] = "private-reference-changed"
        episode["private_note"] = "do not publish"
        for pair in episode["train"]:
            pair["private_note"] = "do not publish"
        for pair in episode["test"]:
            pair["output"] = [[9]]
        # Cached metadata is not an authority for the public filename or content.
        record["public_challenge"]["episode_id"] = "hidden-setting-and-seed"
        record["public_challenge"]["train"] = [{"input": [[1]], "output": [[2]]}]
    first, second = tmp_path / "original", tmp_path / "changed"
    prototype.materialize(first, evidence)
    prototype.materialize(second, changed)
    assert public_files(first) == public_files(second)
    for policy, record in evidence["settings"].items():
        assert prototype.public_challenge(record["episode"]) == prototype.public_challenge(
            changed["settings"][policy]["episode"]
        )
    report = json.loads((second / "report.json").read_text())
    for record in report["settings"].values():
        assert record["public_challenge"] == prototype.public_challenge(record["episode"])


def test_duplicate_visible_payloads_fail_before_any_output(prototype, evidence, tmp_path):
    duplicated = deepcopy(evidence)
    original = duplicated["settings"]["same_color"]
    other = deepcopy(original)
    other["episode"]["parameter"]["blocker_policy"] = "any_color"
    other["episode"]["seed"] = 999
    other["episode"]["test"][0]["output"] = [[9]]
    duplicated["settings"]["any_color"] = other
    out = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="duplicate|collision"):
        prototype.materialize(out, duplicated)
    assert not out.exists()


def test_public_write_sequence_is_sorted_and_setting_order_independent(
    prototype, evidence, tmp_path, monkeypatch
):
    first, second = tmp_path / "forward", tmp_path / "reverse"
    orders = {first: [], second: []}
    original_open = Path.open

    def recording_open(path, mode="r", *args, **kwargs):
        if mode[0] in "wxa" and path.parent.name == "public" and path.parent.parent in orders:
            orders[path.parent.parent].append(path.name)
        return original_open(path, mode, *args, **kwargs)

    reversed_evidence = deepcopy(evidence)
    reversed_evidence["settings"] = dict(reversed(list(reversed_evidence["settings"].items())))
    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", recording_open)
        prototype.materialize(first, evidence)
        prototype.materialize(second, reversed_evidence)
    assert len(orders[first]) == 2
    assert orders[first] == orders[second] == sorted(public_files(first))
    assert public_files(first) == public_files(second)


@pytest.mark.parametrize("kind", ["empty_directory", "stale_directory", "file", "symlink"])
def test_existing_output_target_is_preserved(prototype, evidence, tmp_path, kind):
    out = tmp_path / "occupied"
    if kind == "file":
        out.write_bytes(b"keep this file")
    elif kind == "symlink":
        destination = tmp_path / "destination"
        destination.mkdir()
        (destination / "keep.txt").write_bytes(b"keep this file")
        out.symlink_to(destination, target_is_directory=True)
    else:
        out.mkdir()
        if kind == "stale_directory":
            (out / "stale.json").write_bytes(b"keep this file")
    before = {str(path.relative_to(tmp_path)): path.read_bytes()
              for path in tmp_path.rglob("*") if path.is_file()}
    with pytest.raises(FileExistsError):
        prototype.materialize(out, evidence)
    after = {str(path.relative_to(tmp_path)): path.read_bytes()
             for path in tmp_path.rglob("*") if path.is_file()}
    assert after == before


@pytest.mark.parametrize("policy,demo_count,query_count", [
    ("same_color", 1, 1),
    ("any_color", 1, 4),
    ("same_color", 4, 1),
    ("any_color", 3, 5),
])
def test_independent_counts_have_valid_racket_backed_analysis(
    prototype, bridge, policy, demo_count, query_count
):
    episode = prototype.build_episode(bridge, seed=23, blocker_policy=policy,
                                      demo_count=demo_count, query_count=query_count)
    analysis = prototype.analyze_episode(bridge, episode)
    assert analysis["production"]["status"] == "no_ambiguity_found"
    assert analysis["production"]["actual_demo_count"] == demo_count
    assert analysis["production"]["actual_query_count"] == query_count
    assert analysis["production"].get("reference_labels_valid") is True
    assert analysis["production"].get("surviving_settings") == [policy]
    assert all(row["query_input_distinct"] for row in analysis["queries"])
    assert all(row.get("surviving_settings_disagree") is False for row in analysis["queries"])
    assert len({tuple(map(tuple, pair["input"]))
                for pair in episode["train"] + episode["test"]}) == demo_count + query_count


def test_surviving_settings_with_equal_query_answers_are_not_ambiguous(
    prototype, bridge, agreement_inputs
):
    episode = make_episode(prototype, bridge, agreement_inputs[:1], agreement_inputs[1:])
    analysis = prototype.analyze_episode(bridge, episode)
    assert analysis["production"]["status"] == "no_ambiguity_found"
    assert set(analysis["production"].get("surviving_settings", [])) == {"same_color", "any_color"}
    assert analysis["production"]["alternative_fits_demonstrations"] is True
    assert analysis["queries"][0]["query_differs_under_alternative"] is False
    assert analysis["queries"][0].get("surviving_settings_disagree") is False
    assert all(row["status"] == "no_ambiguity_found" for row in analysis["rotations"])


def test_unidentified_setting_is_ambiguous_only_when_query_predictions_disagree(
    prototype, bridge, agreement_inputs, evidence
):
    witness = evidence["settings"]["same_color"]["episode"]["train"][0]["input"]
    episode = make_episode(prototype, bridge, agreement_inputs[:1], [witness])
    analysis = prototype.analyze_episode(bridge, episode)
    assert analysis["production"]["status"] == "ambiguous"
    assert set(analysis["production"].get("surviving_settings", [])) == {"same_color", "any_color"}
    assert analysis["queries"][0].get("surviving_settings_disagree") is True
    assert analysis["rotations"][0]["status"] == "no_ambiguity_found"
    assert analysis["rotations"][1]["status"] == "ambiguous"


def test_true_setting_demonstration_labels_are_checked(prototype, bridge, evidence):
    witness = evidence["settings"]["same_color"]["episode"]["train"][0]["input"]
    query = evidence["settings"]["same_color"]["episode"]["test"][0]["input"]
    episode = make_episode(prototype, bridge, [witness], [query])
    episode["train"][0]["output"] = prototype.run_racket(bridge, "any_color", witness)
    analysis = prototype.analyze_episode(bridge, episode)
    assert analysis["production"]["status"] == "invalid_labels"
    assert analysis["production"].get("reference_labels_valid") is False
    assert analysis["production"].get("surviving_settings") == ["any_color"]
    assert analysis["production"].get("demonstration_label_mismatch_indices") == [0]


def test_query_answers_cannot_select_surviving_settings(prototype, bridge, agreement_inputs, evidence):
    witness = evidence["settings"]["same_color"]["episode"]["train"][0]["input"]
    episode = make_episode(prototype, bridge, agreement_inputs[:1], [witness])
    original = prototype.analyze_episode(bridge, episode)
    episode["test"][0]["output"] = prototype.run_racket(bridge, "any_color", witness)
    changed = prototype.analyze_episode(bridge, episode)
    assert changed["production"]["status"] == "invalid_labels"
    assert set(changed["production"].get("surviving_settings", [])) == {"same_color", "any_color"}
    assert changed["production"]["surviving_settings"] == original["production"]["surviving_settings"]
    assert changed["queries"][0].get("surviving_settings_disagree") is True
    assert changed["production"].get("query_label_mismatch_indices") == [0]
