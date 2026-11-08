"""Behavioral tests for the proposed reflection/precedence prototype only."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
SCRIPT = ROOT / "generators/576426a573af/workspace/parametric/prototype.py"
WITNESS = [[1, 3], [2, 0]]
EXPECTED = {
    ("vertical", "original"): [[1, 3], [2, 3]],
    ("vertical", "mirror"): [[2, 3], [1, 3]],
    ("horizontal", "original"): [[1, 3], [2, 2]],
    ("horizontal", "mirror"): [[3, 1], [2, 2]],
}


def load_prototype():
    assert SCRIPT.is_file(), "missing runnable task-local parametric prototype"
    spec = importlib.util.spec_from_file_location("parametric_overlay_576426a573af", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as live:
        yield live


def test_cli_writes_two_demos_and_four_distinct_unlabeled_queries(tmp_path):
    out = tmp_path / "episode"
    run = subprocess.run(
        [sys.executable, str(SCRIPT), "--seed", "17", "--train", "2", "--test", "4", "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True, timeout=90,
    )
    assert run.returncode == 0, run.stderr
    challenge = json.loads((out / "public/challenge.json").read_text())
    private = json.loads((out / "private/episode.json").read_text())
    assert set(challenge) == {"train", "test"}
    assert len(challenge["train"]) == 2
    assert len(challenge["test"]) == len(private["answers"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    inputs = [json.dumps(pair["input"]) for split in ("train", "test") for pair in challenge[split]]
    assert len(set(inputs)) == 6
    assert private["parameters"] == {"axis": "vertical", "precedence": "original"}
    assert private["lesson_check"]["identified"]
    assert all(row["identifiable_from_demos"] for row in private["lesson_check"]["queries"])


@pytest.mark.parametrize("setting,expected", EXPECTED.items())
def test_four_rules_have_hand_checked_distinct_outputs(proto, bridge, setting, expected):
    before = copy.deepcopy(WITNESS)
    program = proto.materialize_rule(*setting)
    assert proto.execute_rule(program, WITNESS, bridge=bridge) == expected
    assert proto.python_transform(WITNESS, *setting) == expected
    assert WITNESS == before


def test_default_program_matches_canonical_authority_and_all_canonical_pairs(proto, bridge):
    report = proto.canonical_parity(root=ROOT, bridge=bridge)
    assert report["program_exact_match"]
    assert report["cases"] and len(report["cases"]) == 3
    assert all(case["matches"] for case in report["cases"])
    for pair in canonical_pairs("576426a573af", root=ROOT):
        assert proto.execute_rule(proto.materialize_rule(), pair["input"], bridge=bridge) == pair["output"]


@pytest.mark.parametrize("axis,precedence", EXPECTED)
def test_episode_settings_are_fixed_and_identified_by_demos_alone(proto, bridge, axis, precedence):
    episode = proto.generate_episode(seed=23, axis=axis, precedence=precedence, train=2, test=4, bridge=bridge)
    challenge, private = episode["challenge"], episode["private"]
    program = proto.materialize_rule(axis, precedence)
    assert private["program"] == program
    assert private["program_sha256"] == hashlib.sha256(program.encode()).hexdigest()
    assert private["lesson_check"]["surviving_settings"] == [f"{axis}/{precedence}"]
    for pair in challenge["train"]:
        assert pair["output"] == proto.execute_rule(program, pair["input"], bridge=bridge)
    for pair, answer, check in zip(challenge["test"], private["answers"], private["lesson_check"]["queries"], strict=True):
        assert answer == proto.execute_rule(program, pair["input"], bridge=bridge)
        assert check["identifiable_from_demos"]
        assert len(check["refuting_demo_indices"]) == 3
        assert all(indices and max(indices) < 2 for indices in check["refuting_demo_indices"].values())
        assert check["remaining_differing_rivals"] == []
    sizes = [(len(pair["input"]), len(pair["input"][0])) for pair in challenge["test"]]
    assert (30, 30) in sizes
    assert all(len(pair["input"]) <= 14 and len(pair["input"][0]) <= 14 for pair in challenge["train"])


def test_seed_replay_and_input_sampling_do_not_leak_the_setting(proto, bridge):
    first = proto.generate_episode(seed=31, train=1, test=4, bridge=bridge)
    replay = proto.generate_episode(seed=31, train=1, test=4, bridge=bridge)
    assert first == replay
    alternative = proto.generate_episode(seed=31, axis="horizontal", precedence="mirror", train=1, test=4, bridge=bridge)
    for split in ("train", "test"):
        assert [pair["input"] for pair in first["challenge"][split]] == [pair["input"] for pair in alternative["challenge"][split]]
    assert first["private"]["answers"] != alternative["private"]["answers"]
    changed = proto.generate_episode(seed=32, train=1, test=4, bridge=bridge)
    assert first["challenge"] != changed["challenge"]


def test_ambiguous_demos_remain_ambiguous_despite_distinct_query_predictions(proto, bridge):
    blank = [[0, 0], [0, 0]]
    check = proto.assess_lesson([{"input": blank, "output": blank}], [WITNESS], bridge=bridge)
    assert not check["identified"]
    assert len(check["surviving_settings"]) == 4
    assert not check["queries"][0]["identifiable_from_demos"]
    assert check["queries"][0]["remaining_differing_rivals"]


def test_corrupt_demo_labels_cannot_identify_a_rule(proto, bridge):
    check = proto.assess_lesson([{"input": WITNESS, "output": [[9, 9], [9, 9]]}], [WITNESS], bridge=bridge)
    assert not check["identified"]
    assert check["surviving_settings"] == []
    assert not check["queries"][0]["identifiable_from_demos"]


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": "3"}, {"train": 0}, {"train": True}, {"test": 0}, {"test": 33}, {"max_attempts": 0}])
def test_invalid_episode_requests_fail_explicitly(proto, kwargs):
    with pytest.raises((TypeError, ValueError)):
        proto.generate_episode(**kwargs)


@pytest.mark.parametrize("setting", [("diagonal", "original"), ("vertical", "highest"), (True, "original")])
def test_undeclared_parameter_values_are_rejected(proto, setting):
    with pytest.raises(ValueError):
        proto.materialize_rule(*setting)


@pytest.mark.parametrize("grid", [[], [[]], [[1], [2, 3]], [[True]], [[10]], [["1"]]])
def test_malformed_grids_do_not_reach_reference_execution(proto, grid):
    with pytest.raises(ValueError):
        proto.execute_rule(proto.materialize_rule(), grid)


def test_existing_output_is_preserved(proto, bridge, tmp_path):
    out = tmp_path / "already-there"
    out.mkdir()
    marker = out / "keep.txt"
    marker.write_text("original")
    episode = proto.generate_episode(seed=7, train=1, test=1, bridge=bridge)
    with pytest.raises(FileExistsError):
        proto.write_episode(episode, out)
    assert marker.read_text() == "original"


@pytest.fixture(scope="module")
def all_settings_cli_export(tmp_path_factory):
    """Exercise the real Racket-backed CLI once for the public writer checks."""
    out = tmp_path_factory.mktemp("parametric-public") / "all-settings"
    run = subprocess.run(
        [sys.executable, str(SCRIPT), "--seed", "17", "--train", "2", "--test", "4",
         "--all-settings", "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True, timeout=90,
    )
    assert run.returncode == 0, run.stderr
    public_files = sorted(out.glob("*/public/challenge.json"))
    assert len(public_files) == 4
    episodes = [{"challenge": json.loads(path.read_text()),
                 "private": json.loads((path.parent.parent / "private/episode.json").read_text())}
                for path in public_files]
    return out, episodes


def _public_batch_files(out):
    return {str(path.relative_to(out)): path.read_bytes()
            for path in out.glob("*/public/challenge.json")}


def _private_only_changes(episode):
    changed = copy.deepcopy(episode)
    changed["private"]["seed"] = -999
    parameters = changed["private"]["parameters"]
    parameters["axis"] = "horizontal" if parameters["axis"] == "vertical" else "vertical"
    parameters["precedence"] = "mirror" if parameters["precedence"] == "original" else "original"
    changed["private"]["answers"] = [[[9]] for _ in changed["challenge"]["test"]]
    changed["private"]["program"] = "private reference replacement"
    changed["private"]["extra_metadata"] = {"setting_ordinal": 999}
    # Extra fields must never enter the public projection, even if an authoring
    # caller carries them alongside the allowed visible fields.
    changed["challenge"]["seed"] = -999
    changed["challenge"]["train"][0]["private_note"] = "hidden"
    changed["challenge"]["test"][0]["output"] = [[9]]
    changed["challenge"]["test"][0]["private_note"] = "hidden"
    return changed


def test_cli_all_settings_public_names_are_content_bound(all_settings_cli_export):
    out, episodes = all_settings_cli_export
    summary = json.loads((out / "private/summary.json").read_text())
    setting_by_identifier = {}
    for path in out.glob("*/public/challenge.json"):
        # The digest binds the actual canonical public bytes, including their
        # final newline, rather than any setting, seed, label, or export index.
        expected_identifier = "episode-" + hashlib.sha256(path.read_bytes()).hexdigest()
        assert path.parent.parent.name == expected_identifier
        challenge = json.loads(path.read_text())
        private = json.loads((path.parent.parent / "private/episode.json").read_text())
        assert set(challenge) == {"train", "test"}
        assert len(challenge["train"]) == 2 and len(challenge["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        assert len(private["answers"]) == 4
        assert private["lesson_check"]["identified"]
        assert all(row["identifiable_from_demos"] for row in private["lesson_check"]["queries"])
        assert (path.parent.parent / "private/program.rkt").read_text() == private["program"]
        setting_by_identifier[expected_identifier] = private["parameters"]
    assert {tuple(episode["private"]["parameters"][key] for key in ("axis", "precedence"))
            for episode in episodes} == set(EXPECTED)
    assert summary["episode_count"] == 4 and summary["query_count"] == 16
    assert {record["public_identifier"]: record["parameters"] for record in summary["episodes"]} == setting_by_identifier


def test_batch_public_export_ignores_private_metadata_and_query_answers(proto, all_settings_cli_export, tmp_path):
    _, episodes = all_settings_cli_export
    original, changed = tmp_path / "original", tmp_path / "changed"
    proto.write_episodes([episodes[0]], original)
    proto.write_episodes([_private_only_changes(episodes[0])], changed)
    assert _public_batch_files(original) == _public_batch_files(changed)


def test_single_public_export_keeps_neutral_path_and_visible_schema(proto, all_settings_cli_export, tmp_path):
    _, episodes = all_settings_cli_export
    original, changed = tmp_path / "original", tmp_path / "changed"
    proto.write_episode(episodes[0], original)
    proto.write_episode(_private_only_changes(episodes[0]), changed)
    original_public = original / "public/challenge.json"
    changed_public = changed / "public/challenge.json"
    assert original_public.read_bytes() == changed_public.read_bytes()
    assert sorted(path.name for path in (changed / "public").iterdir()) == ["challenge.json"]
    challenge = json.loads(changed_public.read_text())
    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])


def test_public_batch_names_change_with_each_visible_component(proto, all_settings_cli_export, tmp_path):
    _, episodes = all_settings_cli_export
    base = tmp_path / "base"
    proto.write_episodes([episodes[0]], base)
    identifiers = set(_public_batch_files(base))
    for split, key in (("train", "input"), ("train", "output"), ("test", "input")):
        changed = copy.deepcopy(episodes[0])
        grid = changed["challenge"][split][0][key]
        grid[0][0] = (grid[0][0] + 1) % 10
        out = tmp_path / (split + "-" + key)
        proto.write_episodes([changed], out)
        paths = set(_public_batch_files(out))
        assert identifiers.isdisjoint(paths)
        identifiers.update(paths)
    assert len(identifiers) == 4


def test_public_batch_names_ignore_setting_enumeration_order(proto, all_settings_cli_export, tmp_path, monkeypatch):
    _, episodes = all_settings_cli_export
    forward, reverse = tmp_path / "forward", tmp_path / "reverse"
    creation_order = []
    original_writer = proto.write_episode

    def record_creation(episode, out):
        creation_order.append(Path(out).name)
        return original_writer(episode, out)

    monkeypatch.setattr(proto, "write_episode", record_creation)
    proto.write_episodes(episodes, forward)
    forward_order = creation_order[:]
    creation_order.clear()
    proto.write_episodes(list(reversed(episodes)), reverse)
    assert _public_batch_files(forward) == _public_batch_files(reverse)
    assert creation_order == forward_order == sorted(forward_order)


def test_duplicate_visible_batch_payloads_fail_before_creating_output(proto, all_settings_cli_export, tmp_path):
    _, episodes = all_settings_cli_export
    out = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate public"):
        proto.write_episodes([episodes[0], _private_only_changes(episodes[0])], out)
    assert not out.exists()
