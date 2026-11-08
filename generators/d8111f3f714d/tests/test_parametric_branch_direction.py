from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import random

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, load_selected_generator


TASK_ID = "d8111f3f714d"
ROOT = find_root(__file__)
GEN, _SOURCE_PATH, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), f"missing prototype: {PROTOTYPE_PATH}"
    spec = importlib.util.spec_from_file_location(
        "test_parametric_d8111f3f714d", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _vertical_scene(*branches: tuple[int, int]) -> list[list[int]]:
    grid = [[0 for _ in range(12)] for _ in range(12)]
    for row, col in ((1, 5), (10, 5), *branches):
        grid[row][col] = 2
    assert GEN.self_check(grid) == []
    return grid


def _horizontal_scene(*branches: tuple[int, int]) -> list[list[int]]:
    grid = [[0 for _ in range(12)] for _ in range(12)]
    for row, col in ((5, 1), (5, 10), *branches):
        grid[row][col] = 2
    assert GEN.self_check(grid) == []
    return grid


def test_default_program_is_exact_canonical_source() -> None:
    proto = _load_prototype()

    assert proto.DEFAULT_SETTING == "toward_trunk"
    assert proto.SETTINGS == ("toward_trunk", "away_to_edge")
    assert proto.program_for() == proto.canonical_record()["program_solution"]
    assert proto.program_for("toward_trunk") == proto.canonical_record()[
        "program_solution"
    ]
    assert proto.program_for("away_to_edge") != proto.program_for("toward_trunk")
    with pytest.raises(ValueError, match="branch_direction"):
        proto.program_for("sideways")


def test_python_mirror_draws_hand_derived_vertical_rays() -> None:
    proto = _load_prototype()
    grid = _vertical_scene((3, 2), (7, 8))

    toward = proto.python_mirror(grid, "toward_trunk")
    away = proto.python_mirror(grid, "away_to_edge")

    assert toward == GEN.rule_mirror(grid)
    assert [toward[3][col] for col in range(12)] == [0, 0, 2, 3, 3, 3, 0, 0, 0, 0, 0, 0]
    assert [toward[7][col] for col in range(12)] == [0, 0, 0, 0, 0, 3, 3, 3, 2, 0, 0, 0]
    assert [away[3][col] for col in range(12)] == [3, 3, 2, 0, 0, 3, 0, 0, 0, 0, 0, 0]
    assert [away[7][col] for col in range(12)] == [0, 0, 0, 0, 0, 3, 0, 0, 2, 3, 3, 3]
    assert [away[row][5] for row in range(12)] == [0, 2, 3, 3, 3, 3, 3, 3, 3, 3, 2, 0]


def test_python_mirror_draws_hand_derived_horizontal_rays() -> None:
    proto = _load_prototype()
    grid = _horizontal_scene((2, 3), (8, 7))

    toward = proto.python_mirror(grid, "toward_trunk")
    away = proto.python_mirror(grid, "away_to_edge")

    assert toward == GEN.rule_mirror(grid)
    assert [toward[row][3] for row in range(12)] == [0, 0, 2, 3, 3, 3, 0, 0, 0, 0, 0, 0]
    assert [toward[row][7] for row in range(12)] == [0, 0, 0, 0, 0, 3, 3, 3, 2, 0, 0, 0]
    assert [away[row][3] for row in range(12)] == [3, 3, 2, 0, 0, 3, 0, 0, 0, 0, 0, 0]
    assert [away[row][7] for row in range(12)] == [0, 0, 0, 0, 0, 3, 0, 0, 2, 3, 3, 3]
    assert away[5][1:11] == [2, 3, 3, 3, 3, 3, 3, 3, 3, 2]


def test_edge_branch_may_have_zero_length_away_ray_but_still_changes_rule() -> None:
    proto = _load_prototype()
    grid = _vertical_scene((3, 0), (7, 8))

    away = proto.python_mirror(grid, "away_to_edge")
    toward = proto.python_mirror(grid, "toward_trunk")

    assert away[3][0] == 2
    assert all(away[3][col] == 0 for col in range(1, 5))
    assert all(toward[3][col] == 3 for col in range(1, 5))
    assert away != toward


def test_episode_uses_one_setting_and_retains_three_demos_four_unique_queries() -> None:
    proto = _load_prototype()
    before = random.getstate()
    with RacketBridge(max_calls_before_restart=128) as bridge:
        episode = proto.sample_episode(
            20261023,
            setting="away_to_edge",
            demonstration_count=3,
            query_count=4,
            bridge=bridge,
        )
    after = random.getstate()

    assert before == after
    assert episode["parameters"] == {"branch_direction": "away_to_edge"}
    assert episode["meta"]["selection_scope"] == "once_per_episode"
    assert episode["meta"]["demonstration_count"] == 3
    assert episode["meta"]["query_count"] == 4
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4

    all_pairs = episode["train"] + episode["test"]
    input_hashes = [proto.grid_hash(pair["input"]) for pair in all_pairs]
    assert len(input_hashes) == len(set(input_hashes)) == 7
    assert {GEN._analyze(pair["input"])["orientation"] for pair in all_pairs} == {
        "v",
        "h",
    }

    rival = "toward_trunk"
    check = episode["meta"]["rival_checks"][rival]
    assert check["demonstration_disagreements"] == [0, 1, 2]
    assert check["query_disagreements"] == [0, 1, 2, 3]
    assert episode["meta"]["surviving_settings_from_demonstrations"] == [
        "away_to_edge"
    ]


def test_counts_and_seed_reject_bools_nonpositive_and_oversized_requests() -> None:
    proto = _load_prototype()

    for value in (True, False, 0, -1, 1.5):
        with pytest.raises(ValueError, match="positive exact integer"):
            proto.sample_episode(0, demonstration_count=value, query_count=4)
        with pytest.raises(ValueError, match="positive exact integer"):
            proto.sample_episode(0, demonstration_count=3, query_count=value)
    with pytest.raises(ValueError, match="maximum"):
        proto.sample_episode(
            0,
            demonstration_count=proto.MAX_EPISODE_PAIR_COUNT,
            query_count=1,
        )
    for seed in (True, -1, 1.5):
        with pytest.raises(ValueError, match="nonnegative exact integer"):
            proto.select_setting(seed)


def test_public_export_redacts_private_fields_and_query_answers() -> None:
    proto = _load_prototype()
    with RacketBridge(max_calls_before_restart=128) as bridge:
        episode = proto.sample_episode(
            9,
            setting="toward_trunk",
            demonstration_count=3,
            query_count=4,
            bridge=bridge,
        )
    public = proto.public_challenge(episode)

    assert set(public) == {"train", "test"}
    assert public["train"] == episode["train"]
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "parameters" not in public
    assert "program" not in public
    assert "meta" not in public

    public["train"][0]["input"][0][0] = 9
    public["test"][0]["input"][0][0] = 9
    assert episode["train"][0]["input"][0][0] != 9
    assert episode["test"][0]["input"][0][0] != 9


def test_public_filename_depends_only_on_visible_challenge_bytes() -> None:
    proto = _load_prototype()
    with RacketBridge(max_calls_before_restart=128) as bridge:
        episode = proto.sample_episode(
            17,
            setting="toward_trunk",
            demonstration_count=3,
            query_count=4,
            bridge=bridge,
        )

    baseline = proto.public_filename(episode)
    hidden = deepcopy(episode)
    hidden["parameters"]["branch_direction"] = "away_to_edge"
    hidden["program"] = "private replacement"
    hidden["meta"]["seed"] = 999999
    hidden["test"][0]["output"][0][0] = 9
    assert proto.public_filename(hidden) == baseline

    visible = deepcopy(episode)
    visible["train"][0]["output"][0][0] = 9
    assert proto.public_filename(visible) != baseline


def test_racket_programs_match_python_mirror_on_both_orientations_and_edge() -> None:
    proto = _load_prototype()
    grids = [
        _vertical_scene((3, 2), (7, 8)),
        _horizontal_scene((2, 3), (8, 7)),
        _vertical_scene((3, 0), (7, 8)),
    ]

    with RacketBridge(max_calls_before_restart=128) as bridge:
        for setting in proto.SETTINGS:
            actual = proto.execute_rule_many(
                proto.program_for(setting), grids, bridge=bridge
            )
            expected = [proto.python_mirror(grid, setting) for grid in grids]
            assert actual == expected


def test_evidence_manifest_sorts_episode_rows_by_public_id(tmp_path: Path) -> None:
    """Catch setting-order output that violates deterministic public-ID ordering."""
    proto = _load_prototype()
    manifest = proto.write_evidence(
        tmp_path / "evidence",
        base_seed=20261023,
        demonstration_count=3,
        query_count=4,
    )

    public_ids = [row["public_id"] for row in manifest["episodes"]]
    assert public_ids == sorted(public_ids)
