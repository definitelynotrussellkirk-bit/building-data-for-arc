"""Prototype-only tests for an episode-wide target-color rule parameter."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)


TASK_ID = "2f7883fbd26f"
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "target_color.py"
)


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "the task-local target_color prototype is missing"
    spec = importlib.util.spec_from_file_location("task_target_color_prototype", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as instance:
        yield instance


def run_direct(bridge, program, grid):
    body = strip_rule_wrapper(program) if program.lstrip().startswith("(rule!") else program
    bridge.eval_text(f"(define parametric-target-color-rule {body})")
    bridge.define_grid("parametric-target-color-input", grid)
    return bridge.eval_text("(parametric-target-color-rule parametric-target-color-input)")


def canonical_program():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        rows = [
            row
            for line in handle
            if line.strip()
            if (row := json.loads(line)).get("task_id") == TASK_ID
        ]
    assert len(rows) == 1
    return rows[0]["program_solution"]


def test_default_program_preserves_all_canonical_pairs(prototype, bridge):
    assert prototype.DEFAULT_TARGET_COLOR == 1
    assert prototype.emit_racket() == prototype.emit_racket(1)
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        expected = run_direct(bridge, canonical_program(), pair["input"])
        assert expected == pair["output"]
        assert run_direct(bridge, prototype.emit_racket(), pair["input"]) == expected


def test_episode_setting_is_fixed_replayable_and_only_changes_rule(prototype, bridge):
    color_one = prototype.make_episode(46371, target_color=1, bridge=bridge, root=ROOT)
    color_two = prototype.make_episode(46371, target_color=2, bridge=bridge, root=ROOT)
    replay = prototype.make_episode(46371, target_color=2, bridge=bridge, root=ROOT)
    assert color_two == replay
    assert color_two is not replay
    assert color_one["parameters"] == {"target_color": 1}
    assert color_two["parameters"] == {"target_color": 2}
    assert len(color_two["train"]) == 3 and len(color_two["test"]) == 1
    assert [pair["input"] for pair in color_one["train"] + color_one["test"]] == [
        pair["input"] for pair in color_two["train"] + color_two["test"]
    ]
    for episode in (color_one, color_two):
        assert episode["program"] == prototype.emit_racket(
            episode["parameters"]["target_color"]
        )
        assert episode["program_sha256"] == hashlib.sha256(
            episode["program"].encode()
        ).hexdigest()
        for pair in episode["train"] + episode["test"]:
            assert GEN.self_check(pair["input"]) == []
            assert pair["output"] == run_direct(bridge, episode["program"], pair["input"])
    assert all(
        left["output"] != right["output"]
        for left, right in zip(
            color_one["train"] + color_one["test"],
            color_two["train"] + color_two["test"],
        )
    )


def test_seeded_selection_occurs_once_per_episode(prototype, bridge):
    observed = set()
    for seed in range(4):
        short = prototype.make_episode(
            seed, target_color=None, n_train=1, bridge=bridge, root=ROOT
        )
        long = prototype.make_episode(
            seed, target_color=None, n_train=3, bridge=bridge, root=ROOT
        )
        observed.add(short["parameters"]["target_color"])
        assert short["parameters"] == long["parameters"]
        assert short["program"] == long["program"]
        assert short["train"][0] == long["train"][0]
    assert observed == {1, 2}


@pytest.mark.parametrize("target_color", [1, 2])
def test_demonstrations_identify_setting_before_query(prototype, bridge, target_color):
    episode = prototype.make_episode(
        911, target_color=target_color, bridge=bridge, root=ROOT
    )
    report = prototype.analyze_settings(
        episode["train"],
        [pair["input"] for pair in episode["test"]],
        bridge=bridge,
    )
    assert report["declared_settings"] == [1, 2]
    assert report["compatible_settings"] == [target_color]
    assert report["identified"] is True
    assert report["query_relevant_ambiguities"] == []
    for candidate, detail in report["settings"].items():
        candidate = int(candidate)
        assert detail["demo_matches"] == [candidate == target_color] * 3


def test_public_challenge_redacts_parameter_program_and_query_answers(prototype, bridge):
    episode = prototype.make_episode(772, target_color=2, bridge=bridge, root=ROOT)
    before = copy.deepcopy(episode)
    challenge = prototype.public_challenge(episode)
    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    assert challenge["train"] == episode["train"]
    challenge["train"][0]["input"][0][0] = 9
    assert episode == before


def test_invalid_parameters_and_episode_bounds_fail_closed(prototype):
    for value in (0, 3, True, False, "1", 1.0, 1.75):
        with pytest.raises(ValueError, match="target_color"):
            prototype.emit_racket(value)
    for kwargs in (
        {"seed": True},
        {"seed": "12"},
        {"seed": 2, "n_train": 0},
        {"seed": 2, "n_train": 5},
        {"seed": 2, "n_test": 0},
        {"seed": 2, "n_test": 3},
    ):
        with pytest.raises(ValueError):
            prototype.make_episode(root=ROOT, **kwargs)


def test_cli_evidence_is_executed_source_bound_and_public_safe(prototype, tmp_path):
    seed = 9173
    out = tmp_path / "parametric"
    command = [sys.executable, str(PROTOTYPE_PATH), "--seed", str(seed), "--out", str(out)]
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert {path.name for path in out.iterdir()} == {
        "episodes.private.json",
        "challenges.public.json",
        "verification.json",
    }
    private = json.loads((out / "episodes.private.json").read_text())
    public = json.loads((out / "challenges.public.json").read_text())
    verification = json.loads((out / "verification.json").read_text())
    assert private["status"] == "prototype"
    assert private["seed"] == seed
    assert {episode["parameters"]["target_color"] for episode in private["episodes"]} == {1, 2}
    assert private["sources"]["selected_generator"]["sha256"] == GENERATOR_SHA256
    assert public == [prototype.public_challenge(episode) for episode in private["episodes"]]
    assert verification["status"] == "passed"
    assert verification["canonical_default_parity"] == {
        "all_match": True,
        "pair_count": 4,
    }
    assert verification["all_episode_labels_reexecuted"] is True
    assert verification["all_settings_identified"] is True
    assert verification["distinguishing_witness"]["outputs_differ"] is True
    for name, digest in verification["artifact_sha256"].items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest
