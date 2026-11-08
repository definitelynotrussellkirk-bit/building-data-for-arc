"""Focused authoring tests for the separate gap prototype; no approval claims."""
from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators/dc2c4869445c/workspace/parametric/gap_variant.py"


def test_prototype_entrypoint_exists():
    assert PROTOTYPE.is_file(), "The requested runnable gap prototype is missing"


@pytest.fixture(scope="module")
def proto():
    assert PROTOTYPE.is_file(), "The requested runnable gap prototype is missing"
    spec = importlib.util.spec_from_file_location("dc2c4869445c_gap_test", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def executor(proto):
    with proto.RuleExecutor() as live:
        yield live


def corner_fixture():
    """An asymmetric main whose isolated top-right cell needs 8-connectivity."""
    grid = [[0] * 14 for _ in range(14)]
    for r, c in ((6, 6), (6, 8), (7, 6), (7, 7), (8, 6)):
        grid[r][c] = 7
    for r, c, color in ((5, 5, 2), (5, 6, 3), (6, 5, 4)):
        grid[r][c] = color
    return grid


def rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]


@pytest.mark.parametrize("gap", (0, 1, 2))
@pytest.mark.parametrize("turns", (0, 1, 2, 3))
def test_exact_asymmetric_copies_all_corners_preserve_cues(proto, executor, gap, turns):
    # A wrong diagonal sign, single-axis shift, or 4-connected grouping changes
    # this hand-enumerated target, without consulting the implementation mirror.
    grid = corner_fixture()
    expected = [row[:] for row in grid]
    by_color = {
        2: ((5, 5), (5, 3), (4, 5), (4, 4), (3, 5)),
        3: ((5, 6), (5, 8), (4, 6), (4, 7), (3, 6)),
        4: ((6, 5), (6, 3), (7, 5), (7, 4), (8, 5)),
    }
    for color, cells in by_color.items():
        dr = gap if color in (2, 3) else 0
        dc = gap if color in (2, 4) else 0
        for r, c in cells:
            expected[r - dr][c - dc] = color
    for _ in range(turns):
        grid, expected = rotate(grid), rotate(expected)
    before = [row[:] for row in grid]
    assert proto.input_problems(grid) == []
    assert executor.apply(grid, gap) == expected
    assert proto.python_mirror(grid, gap) == expected
    assert grid == before
    assert all(expected[r][c] == value for r, row in enumerate(grid)
               for c, value in enumerate(row) if value)


@pytest.mark.parametrize("bad", (-1, 3, True, False, 1.0, "1", None))
def test_gap_rejects_outside_and_noninteger_settings(proto, bad):
    with pytest.raises(ValueError, match="gap"):
        proto.program_for_gap(bad)


def test_original_setting_is_exact_canonical_program_and_labels(proto, executor):
    pairs = canonical_pairs("dc2c4869445c", root=ROOT)
    assert len(pairs) == 8
    assert proto.program_for_gap(0) == proto.canonical_program()
    for pair in pairs:
        assert executor.apply(pair["input"], 0) == pair["output"]


def test_clipping_filter_checks_every_setting(proto):
    grid = corner_fixture()
    # Translate two rows upward: gap=0 fits; gap=2 clips.
    grid = grid[2:] + [[0] * 14 for _ in range(2)]
    problems = proto.input_problems(grid)
    assert any("gap=2" in item and "clips" in item for item in problems)


def test_filter_rejects_other_group_in_translation_path(proto):
    grid = [[0] * 20 for _ in range(20)]
    # Each canonical copy fits. At gap=2 the left-facing upper copy hits the
    # second group's input at (8, 7); the two input groups are 8-separated.
    for r, c in ((8, 11), (8, 12), (9, 11), (9, 12)):
        grid[r][c] = 7
    grid[8][10] = 2
    for r, c in ((8, 6), (8, 7), (9, 6), (9, 7)):
        grid[r][c] = 5
    grid[7][6] = 3
    problems = proto.input_problems(grid)
    assert any("gap=2" in item and "input" in item for item in problems)


def test_filter_rejects_two_copies_colliding_in_empty_space(proto):
    grid = [[0] * 20 for _ in range(20)]
    for r, c in ((8, 4), (8, 5), (9, 4), (9, 5)):
        grid[r][c] = 7
    grid[8][6] = 2
    for r, c in ((8, 12), (8, 13), (9, 12), (9, 13)):
        grid[r][c] = 5
    grid[8][11] = 3
    # The original copies occupy columns 6..7 and 10..11 respectively;
    # gap=2 sends both into columns 8..9, which contain no input cells.
    problems = proto.input_problems(grid)
    assert any("gap=2" in item and "targets overlap" in item for item in problems)
    assert not any("paint hits input" in item for item in problems)


def test_sampling_episode_identifiability_replay_and_public_boundary(proto, executor):
    pool = proto.sample_pool(1729, n_pairs=4, max_attempts=128, executor=executor)
    replay = proto.sample_pool(1729, n_pairs=4, max_attempts=128, executor=executor)
    assert pool == replay
    assert len(pool["pairs"]) == 4
    assert len({pair["input_sha256"] for pair in pool["pairs"]}) == 4
    for gap in (0, 1, 2):
        episode = proto.episode_from_pool(pool, gap=gap)
        public, private = episode["public"], episode["private"]
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3 and len(public["test"]) == 1
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert private["parameters"] == {"gap": gap}
        assert all(row["status"] == "eliminated_by_demonstrations"
                   for row in private["rival_checks"])
        for accepted, labeled in zip(pool["pairs"], private["train"] + private["test"]):
            assert labeled["output"] == executor.apply(accepted["input"], gap)
            assert labeled["pair_sha256"] == proto.json_sha256(
                {"input": labeled["input"], "output": labeled["output"]})
            assert proto.input_problems(labeled["input"]) == []
    automatic = proto.episode_from_pool(pool, gap=None, episode_index=4)["private"]
    chosen = proto.gap_from_seed(pool["seed"], episode_index=4)
    assert automatic["parameters"] == {"gap": chosen}
    assert automatic["parameter_selection"] == "seed_sha256_once_per_episode"
    assert all(labeled["output"] == pair["outputs"][str(chosen)]
               for pair, labeled in zip(pool["pairs"], automatic["train"] + automatic["test"]))


def test_seed_choice_is_once_per_episode_deterministic_and_bounded(proto):
    values = [proto.gap_from_seed(1729, episode_index=i) for i in range(30)]
    assert set(values) == {0, 1, 2}
    assert values == [proto.gap_from_seed(1729, episode_index=i) for i in range(30)]


def test_incomplete_sampling_is_loud_and_bounded(proto, executor):
    with pytest.raises(proto.SamplingError, match="incomplete") as caught:
        proto.sample_pool(1729, n_pairs=4, max_attempts=1, executor=executor)
    assert caught.value.details["attempts"] == 1
    assert caught.value.details["accepted"] < 4


def test_episode_refuses_unidentifiable_demonstrations(proto, executor):
    pool = proto.sample_pool(1729, n_pairs=4, max_attempts=128, executor=executor)
    # This corrupts stored labels deliberately: an ambiguous dataset must fail,
    # rather than accepting hidden parameters as proof of learnability.
    for pair in pool["pairs"][:3]:
        pair["outputs"]["1"] = [row[:] for row in pair["outputs"]["0"]]
    with pytest.raises(ValueError, match="identifiable"):
        proto.episode_from_pool(pool, gap=0)


def test_write_evidence_exercises_runtime_receipt_and_public_boundary(proto, tmp_path):
    # A real writer regression: treating runtime_identity as a method failed
    # after labels were computed. This also detects missing staged helper paths.
    out = tmp_path / "gap-evidence"
    report = proto.write_evidence(out, gap="all", seed=1729)
    assert json.loads((out / "report.json").read_text()) == report
    assert report["status"] == "complete_prototype"
    assert report["runtime_identity"]["backend"] == "racket"
    assert report["canonical_pairs_checked"] == 8
    assert report["actual_racket_rule_calls"] == 20
    assert len(report["episodes"]) == 3
    for relative, digest in report["source_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
    for symbol in (proto.RacketBridge, proto.canonical_path, proto.strip_rule_wrapper):
        imported_path = Path(sys.modules[symbol.__module__].__file__).resolve()
        assert str(imported_path.relative_to(ROOT)) in report["source_sha256"]
    for relative, digest in report["artifacts"].items():
        assert hashlib.sha256((out / relative).read_bytes()).hexdigest() == digest
    for value, program in report["programs"].items():
        assert "callable_path" in program
        assert "bridge_definition_path" in program
        assert (out / program["callable_path"]).read_text() == proto.callable_for_gap(int(value))
        assert (out / program["bridge_definition_path"]).read_text() == proto.bridge_definition_for_gap(int(value))
        assert hashlib.sha256((out / program["callable_path"]).read_bytes()).hexdigest() == program["callable_sha256"]
        assert hashlib.sha256((out / program["bridge_definition_path"]).read_bytes()).hexdigest() == program["bridge_definition_sha256"]
    for row in report["episodes"]:
        public = json.loads((out / row["public"]).read_text())
        private = json.loads((out / row["private"]).read_text())
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert private["parameters"] == {"gap": row["gap"]}
        assert len(private["train"]) == 3 and len(private["test"]) == 1
        assert private["public_sha256"] == proto.json_sha256(public)
        assert private["query_holdouts"]["all_identifiable"] is True
        assert len(private["query_holdouts"]["rotations"]) == 4
        assert all(len(rotation["rival_checks"]) == 2
                   and all(rival["status"] == "eliminated_by_demonstrations"
                           for rival in rotation["rival_checks"])
                   for rotation in private["query_holdouts"]["rotations"])


def test_writer_failure_retains_request_and_source_bindings(proto, tmp_path):
    out = tmp_path / "incomplete-gap-evidence"
    with pytest.raises(proto.SamplingError):
        proto.write_evidence(out, gap="all", seed=1729, max_attempts=1)
    failure = json.loads((out / "failure.json").read_text())
    assert failure["status"] == "failed_incomplete_prototype"
    assert "source_sha256" in failure
    assert failure["source_sha256"][str(PROTOTYPE.relative_to(ROOT))] == hashlib.sha256(PROTOTYPE.read_bytes()).hexdigest()
    assert failure["request"]["seed"] == 1729
    assert failure["request"]["max_attempts"] == 1
    assert failure["details"]["generator_sha256"]
    assert len(failure["programs"]) == 3
    assert not (out / "report.json").exists()
