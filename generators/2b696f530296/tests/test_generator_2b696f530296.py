from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "2b696f530296"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
AUTHORITY_PATHS = (
    ROOT / "data/base/solutions/training/c8cbb738__2b696f530296.json",
    ROOT / "data/base/solutions/augmented/c8cbb738__a1ae67883a2a.json",
)


def _canonical_rows() -> list[dict]:
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert len(rows) == 2
    return rows


def _pair(grid: list[list[int]]) -> dict:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_pin_all_canonical_pairs_and_selected_sources_are_exact() -> None:
    rows = _canonical_rows()
    assert rows[0]["program_solution"] == rows[1]["program_solution"]
    normalized = " ".join(rows[0]["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == "b3149de64a85"
    assert GEN.RULE_HASH == "b3149de64a85"
    assert GEN.VERSION == "2.0.0"

    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 8
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before

    for path in AUTHORITY_PATHS:
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == rows[0]["program_solution"]
        assert target["target_status"] == "selected_canonical_program_solution"
        assert target["raw_code"] != target["target_code"]


def test_every_sliding_four_sample_window_identifies_the_rule() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(12):
            grids = [
                GEN.generate(
                    10_000 + 1_000 * band_index + start,
                    start + offset,
                    difficulty=band,
                )
                for offset in range(5)
            ]
            demos = [_pair(grid) for grid in grids[:4]]
            assert [GEN.observe_overrides(grid)["scene_profile"] for grid in grids[:4]] == [
                GEN.SCENE_PROFILES[(start + offset) % 4] for offset in range(4)
            ]
            assert set(item["scene_profile"] for item in map(GEN.observe_overrides, grids[:4])) == set(
                GEN.SCENE_PROFILES
            )
            assert GEN.lesson_identifiable(demos, _pair(grids[4])) == []


def test_semantic_witnesses_kill_the_two_plausible_rivals() -> None:
    grids = [GEN.generate(22_222, index, difficulty="medium") for index in range(4)]
    for name, witness in GEN.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name

    max_killer = grids[2]
    assert GEN.observe_overrides(max_killer)["scene_profile"] == "mixed_max_killer_r1"
    assert GEN.rival_max_radius(max_killer) != GEN.rule_mirror(max_killer)

    overlap = grids[0]
    assert GEN.observe_overrides(overlap)["scene_profile"] == "uniform_overlap_r1"
    assert GEN.rival_high_color_overwrites(overlap) != GEN.rule_mirror(overlap)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_override_cross_product_is_exact_observable_and_unknown_keys_fail(difficulty: str) -> None:
    case = 0
    for profile in GEN.SCENE_PROFILES:
        for group_count in (2, 3, 4):
            for bg_color in (1, 9):
                requested = {
                    "scene_profile": profile,
                    "group_count": group_count,
                    "bg_color": bg_color,
                }
                grid = GEN.generate(
                    30_000 + case,
                    case,
                    difficulty=difficulty,
                    **requested,
                )
                assert GEN.self_check(grid) == []
                assert GEN.observe_overrides(grid) == requested
                case += 1

    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 2, difficulty=difficulty, inert_axis="accepted")


def test_ordinary_draws_recover_every_keyed_axis() -> None:
    for band in ("easy", "medium", "hard"):
        for index in range(40):
            grid = GEN.generate(40_000 + index, index, difficulty=band)
            observed = GEN.observe_overrides(grid)
            profile = GEN.SCENE_PROFILES[index % 4]
            assert observed["scene_profile"] == profile
            assert observed["group_count"] == GEN._PROFILE_DEFAULT_GROUP_COUNT[profile]
            assert 1 <= observed["bg_color"] <= 9


def test_self_check_rejects_targeted_structural_impostors() -> None:
    valid = GEN.generate(
        51_515,
        1,
        difficulty="medium",
        scene_profile="uniform_disjoint_r2",
        group_count=4,
        bg_color=9,
    )
    facts = GEN._scene_facts(valid)
    first = facts["groups"][0]
    color = first["color"]
    bg = facts["bg_color"]

    wrong_count = copy.deepcopy(valid)
    row, col = first["cells"][0]
    wrong_count[row][col] = bg

    fractional_centroid = copy.deepcopy(valid)
    for row, col in first["cells"]:
        fractional_centroid[row][col] = bg
    cr, cc = first["center"]
    for row, col in ((cr - 1, cc - 1), (cr - 1, cc), (cr, cc - 1), (cr, cc)):
        fractional_centroid[row][col] = color

    one_group = [[9 for _ in range(7)] for _ in range(7)]
    for row, col in ((2, 3), (3, 2), (3, 4), (4, 3)):
        one_group[row][col] = 1

    shared_centroid = [[9 for _ in range(9)] for _ in range(9)]
    for row, col in ((3, 4), (4, 3), (4, 5), (5, 4)):
        shared_centroid[row][col] = 1
    for row, col in ((3, 3), (3, 5), (5, 3), (5, 5)):
        shared_centroid[row][col] = 2

    flat_line = [[9 for _ in range(10)] for _ in range(7)]
    for col in (1, 2, 3, 4):
        flat_line[2][col] = 1
    for row, col in ((3, 7), (4, 6), (4, 8), (5, 7)):
        flat_line[row][col] = 2

    fixtures = {
        "wrong_group_cell_count": wrong_count,
        "fractional_centroid_2x2": fractional_centroid,
        "only_one_foreground_group": one_group,
        "duplicate_group_centroid": shared_centroid,
        "one_dimensional_short_line": flat_line,
    }
    for name, grid in fixtures.items():
        assert GEN.self_check(grid), name


def test_negative_recombination_uses_a_novel_absent_feature_and_is_rejected() -> None:
    grid = GEN.generate(
        61_616,
        1,
        difficulty="hard",
        scene_profile="uniform_disjoint_r2",
        group_count=4,
        bg_color=8,
    )
    facts = GEN._scene_facts(grid)
    group = facts["groups"][0]
    mutation = copy.deepcopy(grid)
    for row, col in group["cells"]:
        mutation[row][col] = facts["bg_color"]
    cr, cc = group["center"]
    replacement_offsets = ((-1, -1), (-1, 0), (0, -1), (0, 0))
    remaining_offsets = {
        tuple(other["offsets"]) for other in facts["groups"][1:]
    }
    assert tuple(sorted(replacement_offsets)) not in remaining_offsets
    for dr, dc in replacement_offsets:
        mutation[cr + dr][cc + dc] = group["color"]
    assert GEN.self_check(mutation)


def test_replay_is_fresh_deterministic_and_global_rng_pure() -> None:
    random.seed(20260727)
    state = random.getstate()
    first = GEN.generate(72_727, 9, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(72_727, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 0 if first[0][0] else 1
    assert first != second
