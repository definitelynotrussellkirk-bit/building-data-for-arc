"""Focused tests for the proposed episode-fixed panel-threshold prototype.

These tests exercise a task-local authoring tool.  They do not change or approve
this task's selected canonical generator or its fixed threshold-2 rule.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_id


TASK_ID = "a9c4475d7cda"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
CANONICAL_SHA256 = "4e6231455ecb950b5c408077976da1f2ee06d3b29707dbbd2717e6cdbbeb6668"
THRESHOLD_FRAGMENT = {
    value: f"\n                                 {value})\n                             1\n                             0)"
    for value in (1, 2, 3)
}


@pytest.fixture(scope="module")
def prototype():
    assert SOURCE.is_file(), "the proposed task-local parametric prototype must exist"
    spec = importlib.util.spec_from_file_location(
        "parametric_a9c4475d7cda_panel_threshold", SOURCE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def _threshold_witness_grid():
    """A 9x9 lawful panel grid with hand-picked counts 0,1,2,3."""
    grid = [[0] * 9 for _ in range(9)]
    for row in (2, 5):
        grid[row] = [8] * 9
    for row in range(9):
        for col in (2, 5):
            grid[row][col] = 8

    # Panel bands are rows/cols [0:2], [3:5], [6:9].  The counts below are
    # intentionally literal so expected masks do not reuse prototype logic.
    counts = (
        (0, 1, 2),
        (3, 0, 1),
        (2, 3, 0),
    )
    row_bands = ((0, 2), (3, 5), (6, 9))
    col_bands = ((0, 2), (3, 5), (6, 9))
    for panel_row, (row_start, row_end) in enumerate(row_bands):
        for panel_col, (col_start, col_end) in enumerate(col_bands):
            cells = [
                (row, col)
                for row in range(row_start, row_end)
                for col in range(col_start, col_end)
            ]
            for row, col in cells[: counts[panel_row][panel_col]]:
                grid[row][col] = 6
    return grid


def test_default_materialization_is_exact_and_alternates_only_threshold(prototype):
    """Catches default drift or an alternate rewriting more than the threshold."""
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert prototype.materialize_rule(2, root=ROOT) == canonical
    for threshold in (1, 3):
        alternate = prototype.materialize_rule(threshold, root=ROOT)
        assert alternate != canonical
        assert alternate.count(THRESHOLD_FRAGMENT[threshold]) == 1
        assert alternate.replace(
            THRESHOLD_FRAGMENT[threshold], THRESHOLD_FRAGMENT[2], 1
        ) == canonical


@pytest.mark.parametrize("value", [True, False, 0, 4, 2.0, "2", None])
def test_invalid_threshold_values_fail_closed(prototype, value):
    """Catches bool coercion and settings outside the declared finite family."""
    with pytest.raises(ValueError, match="panel_threshold"):
        prototype.materialize_rule(value, root=ROOT)


def test_real_racket_matches_hand_derived_threshold_boundaries(prototype, bridge):
    """Catches Python-only labels or a wrong comparison operator/boundary."""
    grid = _threshold_witness_grid()
    before = copy.deepcopy(grid)
    expected = {
        1: [[0, 1, 1], [1, 0, 1], [1, 1, 0]],
        2: [[0, 0, 1], [1, 0, 0], [1, 1, 0]],
        3: [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
    }
    for threshold in (1, 2, 3):
        actual = prototype.execute_rule(
            prototype.materialize_rule(threshold, root=ROOT),
            grid,
            bridge=bridge,
        )
        assert actual == expected[threshold]
    assert grid == before


def test_episode_has_one_setting_three_demos_and_four_distinct_queries(
    prototype, bridge
):
    """Catches per-pair resampling, cloned inputs, or query-dependent teaching."""
    episode = prototype.make_episode(
        11,
        panel_threshold=2,
        demo_count=3,
        query_count=4,
        difficulty="medium",
        root=ROOT,
        bridge=bridge,
    )
    assert episode["status"] == "proposed_unapproved"
    assert episode["approved"] is False
    assert episode["parameters"] == {"panel_threshold": 2}
    assert episode["selection_scope"] == "once_per_episode"
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    assert len({pair["input_sha256"] for pair in pairs}) == 7
    assert all(pair["panel_threshold"] == 2 for pair in pairs)
    assert all({1, 2, 3} <= set(pair["panel_counts"]) for pair in pairs)

    selected, = [
        row for row in episode["parameter_rivals"] if row["panel_threshold"] == 2
    ]
    assert selected["status"] == "matches_episode"
    for rival in [
        row for row in episode["parameter_rivals"] if row["panel_threshold"] != 2
    ]:
        assert rival["status"] == "refuted_by_demonstrations"
        assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
        assert rival["query_mismatch_indices"] == [0, 1, 2, 3]
    assert episode["ambiguities"] == []


def test_episode_is_deterministic_and_does_not_touch_global_rng(prototype, bridge):
    """Catches hidden global randomness and coupled demo/query count handling."""
    assert {
        prototype.parameters_for_seed(seed)["panel_threshold"] for seed in (0, 1, 2)
    } == {1, 2, 3}
    random.seed(1947)
    before = random.getstate()
    first = prototype.make_episode(
        2, demo_count=2, query_count=4, root=ROOT, bridge=bridge
    )
    second = prototype.make_episode(
        2, demo_count=2, query_count=4, root=ROOT, bridge=bridge
    )
    assert first == second
    assert random.getstate() == before

    for kwargs in (
        {"demo_count": 0},
        {"demo_count": True},
        {"demo_count": 17},
        {"query_count": 0},
        {"query_count": False},
        {"query_count": 17},
        {"difficulty": "extreme"},
    ):
        with pytest.raises(ValueError):
            prototype.make_episode(0, root=ROOT, bridge=bridge, **kwargs)


def test_public_projection_masks_answers_and_uses_visible_content_only(
    prototype, bridge
):
    """Catches private setting/program/query-answer leakage into public identity."""
    episode = prototype.make_episode(
        0, demo_count=3, query_count=4, root=ROOT, bridge=bridge
    )
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    public_id = public_challenge_id(public)

    private_only_mutation = copy.deepcopy(episode)
    private_only_mutation["seed"] = 999999
    private_only_mutation["parameters"]["panel_threshold"] = 3
    private_only_mutation["racket_source"] = "private mutation"
    private_only_mutation["test"][0]["output"][0][0] ^= 1
    assert prototype.public_challenge(private_only_mutation) == public
    assert public_challenge_id(prototype.public_challenge(private_only_mutation)) == public_id

    before = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_write_evidence_covers_all_settings_and_hashes_retained_files(
    prototype, tmp_path
):
    """Catches incomplete setting coverage, unsafe names, and unbound evidence."""
    out = tmp_path / "evidence"
    report = prototype.write_evidence(
        (0, 1, 2),
        out=out,
        root=ROOT,
        demo_count=3,
        query_count=4,
        difficulty="medium",
    )
    assert report["status"] == "proposed_unapproved"
    assert report["counts"] == {
        "episodes": 3,
        "train_pairs": 9,
        "query_pairs": 12,
        "distinct_input_grids": 21,
        "settings_exercised": 3,
        "canonical_pairs_checked": 5,
        "ambiguous_parameter_rivals": 0,
    }
    public_ids = [row["public_id"] for row in report["episodes"]]
    assert public_ids == sorted(public_ids)

    for row in report["episodes"]:
        public_path = out / row["public_path"]
        private_path = out / row["private_path"]
        public = json.loads(public_path.read_text())
        private = json.loads(private_path.read_text())
        visible_id = public_challenge_id(public)
        assert public_path.name == f"challenge-{visible_id}.json"
        assert row["public_id"] == visible_id
        assert prototype.public_challenge(private) == public
        assert "threshold" not in public_path.name
        assert "seed" not in public_path.name

    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0,), out=out, root=ROOT)


def _load_module(path: Path, name: str):
    assert path.is_file(), f"required module is missing: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_promotion_adapter_reuses_prototype_and_preserves_independent_counts(
    prototype,
):
    """Catches adapter rule forks, wrong settings, or coupled demos/queries."""
    adapter_path = ROOT / f"generators/{TASK_ID}/workspace/parametric/adapter.py"
    adapter = _load_module(adapter_path, "parametric_a9c4475d7cda_adapter")

    assert adapter.program({"panel_threshold": 2}) == prototype.canonical_source(
        root=ROOT
    )
    alternate = adapter.program({"panel_threshold": 3})
    assert alternate == prototype.materialize_rule(3, root=ROOT)

    generated = adapter.generate(
        17, {"panel_threshold": 3}, demos=2, queries=4
    )
    assert set(generated) == {"train", "test", "program_solution"}
    assert len(generated["train"]) == 2
    assert len(generated["test"]) == 4
    assert generated["program_solution"] == alternate
    pairs = generated["train"] + generated["test"]
    assert all(set(pair) == {"input", "output"} for pair in pairs)
    assert len(
        {
            hashlib.sha256(
                json.dumps(pair["input"], separators=(",", ":")).encode()
            ).hexdigest()
            for pair in pairs
        }
    ) == 6

    for bad_settings in (
        {},
        {"panel_threshold": 2, "extra": 1},
        {"panel_threshold": True},
        {"panel_threshold": 4},
    ):
        with pytest.raises(ValueError):
            adapter.program(bad_settings)


def test_promotion_contract_declares_exact_bounded_family():
    """Catches a promotion contract that exposes unreviewed settings or counts."""
    path = ROOT / f"generators/{TASK_ID}/workspace/parametric/promotion.json"
    contract = json.loads(path.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/a9c4475d7cda/workspace/parametric/adapter.py",
        "parameters": {"panel_threshold": [1, 2, 3]},
        "default": {"panel_threshold": 2},
        "limits": {"demos": [1, 16], "queries": [1, 16]},
    }
