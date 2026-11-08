"""Prototype-only regressions; these do not approve a new canonical rule."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
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


TASK_ID = "4ecf2a93671f"
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "mask_role.py"
LAWFUL_GRID = [[0, 0, 7], [7, 0, 7], [7, 7, 0]]


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "the task-local mask_role prototype is missing"
    spec = importlib.util.spec_from_file_location("task_mask_role_prototype", PROTOTYPE_PATH)
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
    """Execute a self-contained lambda independently of the authoring helper."""
    body = strip_rule_wrapper(program) if program.lstrip().startswith("(rule!") else program
    bridge.eval_text(f"(define parametric-test-rule {body})")
    bridge.define_grid("parametric-test-input", grid)
    return bridge.eval_text("(parametric-test-rule parametric-test-input)")


def canonical_program():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        selected = [row for line in handle if line.strip()
                    if (row := json.loads(line)).get("task_id") == TASK_ID]
    assert len(selected) == 1
    return selected[0]["program_solution"]


@pytest.mark.parametrize("role", ["background", "foreground"])
def test_racket_selects_same_mask_for_block_and_subcell(bridge, role):
    # Replacing AND by OR, or changing only one coordinate's predicate, fails.
    prototype = load_prototype()
    assert GEN.self_check(LAWFUL_GRID) == []
    actual = run_direct(bridge, prototype.emit_racket(role), LAWFUL_GRID)
    n = len(LAWFUL_GRID)
    mask = [[int((value == 0) == (role == "background")) for value in row]
            for row in LAWFUL_GRID]
    assert len(actual) == n * n
    assert all(len(row) == n * n for row in actual)
    for block_r in range(n):
        for block_c in range(n):
            block = [row[block_c * n:(block_c + 1) * n]
                     for row in actual[block_r * n:(block_r + 1) * n]]
            expected = [[7 * value for value in row] for row in mask]
            if not mask[block_r][block_c]:
                expected = [[0] * n for _ in range(n)]
            assert block == expected
    support = sum(sum(row) for row in mask)
    assert sum(value != 0 for row in actual for value in row) == support * support


def test_default_program_preserves_all_canonical_pairs(prototype, bridge):
    assert prototype.DEFAULT_MASK_ROLE == "background"
    assert prototype.emit_racket() == prototype.emit_racket("background")
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        expected = run_direct(bridge, canonical_program(), pair["input"])
        assert expected == pair["output"]
        assert run_direct(bridge, prototype.emit_racket(), pair["input"]) == expected


def test_episode_setting_is_fixed_replayable_and_only_changes_the_rule(prototype, bridge):
    random.seed(614)
    before = random.getstate()
    background = prototype.make_episode(46371, mask_role="background", bridge=bridge, root=ROOT)
    foreground = prototype.make_episode(46371, mask_role="foreground", bridge=bridge, root=ROOT)
    replay = prototype.make_episode(46371, mask_role="foreground", bridge=bridge, root=ROOT)
    assert random.getstate() == before
    assert foreground == replay
    assert foreground is not replay
    assert foreground["parameters"] == {"mask_role": "foreground"}
    assert len(foreground["train"]) == 3 and len(foreground["test"]) == 1
    assert [p["input"] for p in foreground["train"] + foreground["test"]] == [
        p["input"] for p in background["train"] + background["test"]]
    for episode in (background, foreground):
        assert episode["program"] == prototype.emit_racket(episode["parameters"]["mask_role"])
        assert episode["program_sha256"] == hashlib.sha256(episode["program"].encode()).hexdigest()
        for pair in episode["train"] + episode["test"]:
            assert GEN.self_check(pair["input"]) == []
            assert pair["output"] == run_direct(bridge, episode["program"], pair["input"])
    assert all(a["output"] != b["output"] for a, b in zip(
        background["train"] + background["test"], foreground["train"] + foreground["test"]))


def test_seeded_selection_is_once_per_episode_and_default_is_canonical(prototype, bridge):
    default = prototype.make_episode(67, bridge=bridge, root=ROOT)
    assert default["parameters"] == {"mask_role": "background"}
    observed_roles = set()
    for seed in range(4):
        short = prototype.make_episode(seed, mask_role=None, n_train=1, bridge=bridge, root=ROOT)
        longer = prototype.make_episode(seed, mask_role=None, n_train=3, bridge=bridge, root=ROOT)
        observed_roles.add(short["parameters"]["mask_role"])
        assert short["parameters"] == longer["parameters"]
        assert short["program"] == longer["program"]
        assert short["train"][0] == longer["train"][0]
        for pair in longer["train"] + longer["test"]:
            assert pair["output"] == run_direct(bridge, longer["program"], pair["input"])
    assert observed_roles == {"background", "foreground"}


@pytest.mark.parametrize("role", ["background", "foreground"])
def test_finite_rivals_are_eliminated_by_demos_before_query(prototype, bridge, role):
    episode = prototype.make_episode(911, mask_role=role, bridge=bridge, root=ROOT)
    query_inputs = [pair["input"] for pair in episode["test"]]
    report = prototype.analyze_settings(episode["train"], query_inputs, bridge=bridge, root=ROOT)
    assert report["declared_settings"] == ["background", "foreground"]
    assert report["compatible_settings"] == [role]
    assert report["identified"] is True
    assert report["query_relevant_ambiguities"] == []
    for candidate, detail in report["settings"].items():
        assert detail["demo_matches"] == [candidate == role] * 3
        assert detail["query_predictions"] == [
            run_direct(bridge, prototype.emit_racket(candidate), grid) for grid in query_inputs]


def test_missing_demos_retain_honest_query_relevant_ambiguity(prototype, bridge):
    report = prototype.analyze_settings([], [LAWFUL_GRID], bridge=bridge, root=ROOT)
    assert report["compatible_settings"] == ["background", "foreground"]
    assert report["identified"] is False
    assert report["query_relevant_ambiguities"] == [
        {"settings": ["background", "foreground"], "query_indices": [0]}]


def test_public_challenge_contains_only_demos_and_query_inputs(prototype, bridge):
    episode = prototype.make_episode(772, mask_role="foreground", bridge=bridge, root=ROOT)
    before = copy.deepcopy(episode)
    challenge = prototype.public_challenge(episode)
    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    assert challenge["train"] == episode["train"]
    assert [pair["input"] for pair in challenge["test"]] == [pair["input"] for pair in episode["test"]]
    challenge["train"][0]["input"][0][0] = -1
    assert episode == before


def test_invalid_parameter_and_episode_bounds_fail_closed(prototype):
    for role in ("blue", "BACKGROUND", 0, True):
        with pytest.raises(ValueError, match="mask_role"):
            prototype.emit_racket(role)
    for kwargs in ({"seed": True}, {"seed": "12"}, {"seed": 2, "n_train": 0},
                   {"seed": 2, "n_train": 9}, {"seed": 2, "n_test": 0},
                   {"seed": 2, "n_test": 5}):
        with pytest.raises(ValueError):
            prototype.make_episode(root=ROOT, **kwargs)


def test_cli_evidence_is_source_bound_executed_and_public_safe(prototype, tmp_path):
    # Exercise the real authoring command; no mocked oracle or solver feedback.
    seed = 9173
    out = tmp_path / "parametric"
    command = [sys.executable, str(PROTOTYPE_PATH), "--seed", str(seed), "--out", str(out)]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    assert {p.name for p in out.iterdir()} == {
        "episodes.private.json", "challenges.public.json", "verification.json"}
    private = json.loads((out / "episodes.private.json").read_text())
    public = json.loads((out / "challenges.public.json").read_text())
    check = json.loads((out / "verification.json").read_text())
    assert private["status"] == "prototype"
    assert private["seed"] == seed
    assert {e["parameters"]["mask_role"] for e in private["episodes"]} == {"background", "foreground"}
    assert private["sources"]["selected_generator"]["sha256"] == GENERATOR_SHA256
    for entry in private["sources"]["prototype_files"]:
        assert hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    assert public == [prototype.public_challenge(episode) for episode in private["episodes"]]
    assert check["status"] == "passed"
    assert check["canonical_default_parity"]["pair_count"] == 4
    assert check["canonical_default_parity"]["all_match"] is True
    assert check["all_episode_labels_reexecuted"] is True
    assert check["all_settings_identified"] is True
    assert check["distinguishing_witness"]["outputs_differ"] is True
    assert check["invocation"]["argv"] == command[1:]
    assert f"--seed {seed}" in check["invocation"]["replay_from_packet_root"]
    for name, digest in check["artifact_sha256"].items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest
