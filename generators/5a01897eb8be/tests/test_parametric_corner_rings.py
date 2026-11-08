"""Behavioral tests for the proposed corner-ring parametric prototype only."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "5a01897eb8be"
ROOT = find_root(__file__)
SCRIPT = ROOT / "generators/5a01897eb8be/workspace/parametric/prototype.py"

WITNESS = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 3, 3, 0, 0, 0],
    [0, 0, 2, 0, 0, 0, 3, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

EXPECTED = {
    (2, "all"): [
        [3, 3, 0, 3, 3],
        [3, 2, 0, 2, 3],
        [0, 0, 1, 0, 0],
        [3, 2, 0, 2, 3],
        [3, 3, 0, 3, 3],
    ],
    (2, "diagonal"): [
        [3, 3, 0, 0, 0],
        [3, 2, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 2, 3],
        [0, 0, 0, 3, 3],
    ],
    (4, "all"): [
        [3, 3, 0, 0, 0, 0, 0, 3, 3],
        [3, 0, 0, 0, 0, 0, 0, 0, 3],
        [0, 0, 2, 0, 0, 0, 2, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0, 2, 0, 0],
        [3, 0, 0, 0, 0, 0, 0, 0, 3],
        [3, 3, 0, 0, 0, 0, 0, 3, 3],
    ],
    (4, "diagonal"): [
        [3, 3, 0, 0, 0, 0, 0, 0, 0],
        [3, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 2, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 3],
        [0, 0, 0, 0, 0, 0, 0, 3, 3],
    ],
}


def load_prototype():
    assert SCRIPT.is_file(), "missing runnable task-local parametric prototype"
    spec = importlib.util.spec_from_file_location("parametric_corner_rings_5a01897eb8be", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as instance:
        yield instance


def _canonical_program():
    rows = [
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(programs) == 1
    return programs.pop()


def test_default_program_is_exact_canonical_authority(proto, bridge):
    assert proto.materialize_rule() == _canonical_program()
    parity = proto.canonical_parity(bridge=bridge)
    assert parity["program_exact_match"]
    assert parity["passed"]
    assert parity["cases"]


@pytest.mark.parametrize("setting,expected", EXPECTED.items())
def test_four_settings_have_hand_derived_outputs(proto, bridge, setting, expected):
    source = proto.materialize_rule(*setting)
    assert proto.execute_rule(source, WITNESS, bridge=bridge) == expected
    assert proto.python_transform(WITNESS, *setting) == expected


@pytest.mark.parametrize(
    "setting",
    [(3, "all"), (2, "four"), (True, "all"), (2, True)],
)
def test_undeclared_parameter_values_are_rejected(proto, setting):
    with pytest.raises((TypeError, ValueError)):
        proto.materialize_rule(*setting)


@pytest.mark.parametrize("grid", [[], [[]], [[1], [2, 3]], [[True]], [[10]], [["1"]]])
def test_malformed_grids_do_not_reach_reference_execution(proto, grid):
    with pytest.raises(ValueError):
        proto.execute_rule(proto.materialize_rule(), grid)


def _episode_inputs(episode):
    challenge = episode["challenge"]
    return {
        "train": [pair["input"] for pair in challenge["train"]],
        "test": [pair["input"] for pair in challenge["test"]],
    }


def test_parameter_choice_is_fixed_per_episode_and_strict(proto):
    assert proto.choose_parameters(17) == (2, "all")
    sampled = proto.choose_parameters(17, "sample", "sample")
    assert sampled == proto.choose_parameters(17, "sample", "sample")
    assert sampled in proto.SETTINGS
    assert proto.choose_parameters(17, 4, "sample")[0] == 4
    assert proto.choose_parameters(17, "sample", "diagonal")[1] == "diagonal"
    with pytest.raises(TypeError):
        proto.choose_parameters(True)
    with pytest.raises((TypeError, ValueError)):
        proto.choose_parameters(17, "4", "all")


def test_all_settings_share_inputs_and_queries_ignore_train_count(proto, bridge):
    episodes = {
        setting: proto.generate_episode(
            seed=17,
            ring_step=setting[0],
            corners=setting[1],
            train=3,
            test=4,
            bridge=bridge,
        )
        for setting in proto.SETTINGS
    }
    inputs = [_episode_inputs(episode) for episode in episodes.values()]
    assert all(value == inputs[0] for value in inputs[1:])
    fingerprints = [
        json.dumps(grid, separators=(",", ":"))
        for split in ("train", "test")
        for grid in inputs[0][split]
    ]
    assert len(inputs[0]["train"]) == 3
    assert len(inputs[0]["test"]) == 4
    assert len(set(fingerprints)) == 7
    for setting, episode in episodes.items():
        assert episode["private"]["parameters"] == {
            "ring_step": setting[0],
            "corners": setting[1],
        }

    fewer_demos = proto.generate_episode(seed=17, train=1, test=4, bridge=bridge)
    assert _episode_inputs(fewer_demos)["test"] == inputs[0]["test"]


def test_fourth_query_is_substantive_30x30_boundary_stress(proto, bridge):
    episode = proto.generate_episode(
        seed=43,
        ring_step=4,
        corners="all",
        train=3,
        test=4,
        bridge=bridge,
    )
    grid = episode["challenge"]["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)

    background = grid[0][0]
    foreground = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != background
    ]
    assert len({value for _, _, value in foreground}) == 6
    assert len(foreground) >= 25
    assert any(row == 0 for row, _, _ in foreground)
    assert any(row == 29 for row, _, _ in foreground)
    assert any(col == 0 for _, col, _ in foreground)
    assert any(col == 29 for _, col, _ in foreground)
    assert episode["private"]["answers"][3] == proto.python_transform(
        grid, 4, "all"
    )


@pytest.mark.parametrize("setting", [(2, "all"), (2, "diagonal"), (4, "all"), (4, "diagonal")])
def test_generated_lessons_identify_each_setting_from_demos(proto, bridge, setting):
    episode = proto.generate_episode(
        seed=23,
        ring_step=setting[0],
        corners=setting[1],
        train=3,
        test=4,
        bridge=bridge,
    )
    check = episode["private"]["lesson_check"]
    assert check["identified"]
    assert check["surviving_settings"] == [f"{setting[0]}/{setting[1]}"]
    assert all(row["identifiable_from_demos"] for row in check["queries"])
    assert len(episode["private"]["answers"]) == 4
    assert all("output" not in pair for pair in episode["challenge"]["test"])


def test_demo_only_assessment_reports_real_ambiguity(proto, bridge):
    singleton = [[0, 0], [0, 1]]
    output = proto.execute_rule(proto.materialize_rule(), singleton, bridge=bridge)
    check = proto.assess_lesson(
        [{"input": singleton, "output": output}],
        [WITNESS],
        2,
        "all",
        bridge=bridge,
    )
    assert not check["identified"]
    assert check["surviving_settings"] == [
        "2/all",
        "2/diagonal",
        "4/all",
        "4/diagonal",
    ]
    assert check["queries"][0]["remaining_differing_rivals"]
    assert not check["queries"][0]["identifiable_from_demos"]


def test_surviving_same_answer_rivals_are_not_query_ambiguity(proto, bridge):
    singleton = [[0, 0], [0, 1]]
    output = proto.execute_rule(proto.materialize_rule(), singleton, bridge=bridge)
    check = proto.assess_lesson(
        [{"input": singleton, "output": output}],
        [singleton],
        2,
        "all",
        bridge=bridge,
    )
    assert not check["identified"]
    assert check["queries"][0]["differing_rivals"] == []
    assert check["queries"][0]["remaining_differing_rivals"] == []
    assert check["queries"][0]["identifiable_from_demos"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"train": 0},
        {"test": 0},
        {"max_attempts": 0},
        {"train": True},
        {"test": 33},
    ],
)
def test_invalid_episode_requests_fail_before_sampling(proto, kwargs):
    with pytest.raises((TypeError, ValueError)):
        proto.generate_episode(**kwargs)



def test_public_identifier_and_episode_export_bind_only_visible_bytes(proto, bridge, tmp_path):
    episode = proto.generate_episode(seed=31, bridge=bridge)
    identifier = proto.public_identifier(episode["challenge"])
    assert identifier == "episode-" + public_challenge_id(episode["challenge"])

    out = tmp_path / "episode"
    proto.write_episode(episode, out)
    assert (out / "public/challenge.json").read_bytes() == public_challenge_bytes(
        episode["challenge"]
    )
    visible = json.loads((out / "public/challenge.json").read_text())
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert json.loads((out / "private/episode.json").read_text()) == episode["private"]
    assert (out / "private/program.rkt").read_text() == episode["private"]["program"]


def test_duplicate_public_batch_fails_before_creating_output(proto, bridge, tmp_path):
    episode = proto.generate_episode(seed=37, bridge=bridge)
    out = tmp_path / "duplicates"
    with pytest.raises(ValueError, match="duplicate public challenge"):
        proto.write_episodes([episode, episode], out)
    assert not out.exists()


def test_all_settings_cli_writes_four_opaque_sorted_episodes(proto, tmp_path):
    out = tmp_path / "all-settings"
    assert proto.main(
        [
            "--seed",
            "41",
            "--train",
            "3",
            "--test",
            "4",
            "--all-settings",
            "--out",
            str(out),
        ]
    ) == 0
    episode_dirs = sorted(
        path for path in out.iterdir() if path.is_dir() and path.name.startswith("episode-")
    )
    assert len(episode_dirs) == 4
    assert [path.name for path in episode_dirs] == sorted(path.name for path in episode_dirs)
    assert all(len(path.name) == len("episode-") + 64 for path in episode_dirs)
    for path in episode_dirs:
        public = json.loads((path / "public/challenge.json").read_text())
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert path.name == "episode-" + public_challenge_id(public)
    summary = json.loads((out / "private/summary.json").read_text())
    assert summary["episode_count"] == 4
    assert summary["query_count"] == 16
    assert summary["all_queries_identified_from_demos"]
    assert json.loads((out / "private/canonical-parity.json").read_text())["passed"]
