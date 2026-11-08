"""Focused semantic and contract regressions for task cae2f5a8b903."""
from __future__ import annotations

import copy
import importlib
import json
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

gen = importlib.import_module(
    "puzzle_generators.per_puzzle.cae2f5a8b903.generator"
)
from scripts.canonical_profile_gate import (  # noqa: E402
    canonical_pairs,
    canonical_rule_hash,
    canonical_rule_source,
)


def test_rule_hash_source_sync_and_all_canonical_pairs() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID)
    selected = canonical_rule_source(gen.TASK_ID)
    base = json.loads(
        (
            REPO_ROOT
            / "data/base/solutions/training/39a8645d__cae2f5a8b903.json"
        ).read_text(encoding="utf-8")
    )
    target = base["racket_target"]
    assert target["target_code"] == selected
    assert target["target_code_role"] == "selected_task_rule"
    assert target["raw_code_role"] == "archival_executable_source"
    assert selected in (
        REPO_ROOT / "solvers/grounded_rules.py"
    ).read_text(encoding="utf-8")

    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        snapshot = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == snapshot


def test_canonical_shape_frequency_shortcut_is_real_and_declared() -> None:
    shortcut = gen.CANONICAL_SHORTCUTS["most_repeated_motif_ignoring_color"]
    for pair in canonical_pairs(gen.TASK_ID):
        assert shortcut(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_profiles_are_exact_and_witnessed(band: str) -> None:
    expected = (
        {
            "grid_h": 14,
            "grid_w": 14,
            "n_colors": 3,
            "winner_count": 4,
            "winner_color_rank": "lowest",
            "area_relation": "loser_more_cells",
            "winner_position": "later",
            "loser_motif_relation": "distinct",
            "winner_linkage": "diagonal",
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "n_colors": 2,
            "winner_count": 2,
            "winner_color_rank": "highest",
            "area_relation": "winner_most_cells",
            "winner_position": "first",
            "loser_motif_relation": "distinct",
            "winner_linkage": "orthogonal",
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "n_colors": 3,
            "winner_count": 4,
            "winner_color_rank": "highest",
            "area_relation": "winner_most_cells",
            "winner_position": "later",
            "loser_motif_relation": "shared",
            "winner_linkage": "orthogonal",
        },
        {
            "grid_h": {"easy": 12, "medium": 14, "hard": 16}[band],
            "grid_w": {"easy": 12, "medium": 14, "hard": 16}[band],
            "n_colors": 3,
            "winner_count": 3,
            "winner_color_rank": "lowest",
            "area_relation": "winner_most_cells",
            "winner_position": "first",
            "loser_motif_relation": "distinct",
            "winner_linkage": "diagonal",
        },
    )
    assert tuple(gen.schedule_profile(8, i, band) for i in range(4)) == (
        gen.SCHEDULE_PROFILES
    )
    for index, wanted in enumerate(expected):
        grid = gen.generate(719, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == wanted
        assert gen.rule_mirror(grid)

    profile0 = gen.generate(719, 0, difficulty=band)
    assert gen.SEMANTIC_WITNESSES["object_count_beats_cell_mass"](profile0)
    assert gen.SEMANTIC_WITNESSES["winner_occurs_after_a_loser"](profile0)
    assert gen.SEMANTIC_WITNESSES["lowest_rank_wins"](profile0)
    assert gen.SEMANTIC_WITNESSES[
        "diagonal_eight_connectivity_matters"
    ](profile0)

    profile1 = gen.generate(719, 1, difficulty=band)
    assert gen.SEMANTIC_WITNESSES["highest_rank_wins"](profile1)

    profile2 = gen.generate(719, 2, difficulty=band)
    assert gen.SEMANTIC_WITNESSES[
        "losing_colors_share_the_modal_motif"
    ](profile2)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_sliding_four_demo_window_kills_all_rivals(band: str) -> None:
    for start in range(20):
        demos = []
        for offset in range(gen.EXAMPLES_NEEDED):
            grid = gen.generate(4401, start + offset, difficulty=band)
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(
            4401, start + gen.EXAMPLES_NEEDED, difficulty=band
        )
        assert gen.lesson_identifiable(demos, {"input": query_grid}) == []
        for name, competitor in gen.LESSON_COMPETITORS.items():
            assert any(
                competitor(pair["input"]) != pair["output"] for pair in demos
            ), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "axis,value",
    [
        ("grid_h", 12),
        ("grid_h", 16),
        ("grid_w", 12),
        ("grid_w", 16),
        ("n_colors", 2),
        ("n_colors", 3),
        ("winner_count", 2),
        ("winner_count", 4),
        ("winner_color_rank", "lowest"),
        ("winner_color_rank", "highest"),
        ("area_relation", "winner_most_cells"),
        ("area_relation", "loser_more_cells"),
        ("winner_position", "first"),
        ("winner_position", "later"),
        ("loser_motif_relation", "distinct"),
        ("loser_motif_relation", "shared"),
        ("winner_linkage", "orthogonal"),
        ("winner_linkage", "diagonal"),
    ],
)
def test_every_single_override_is_exact_and_observable(
    band: str, axis: str, value: object
) -> None:
    grid = gen.generate(751, 0, difficulty=band, **{axis: value})
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid)[axis] == value


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 12,
            "grid_w": 16,
            "n_colors": 2,
            "winner_count": 4,
            "winner_color_rank": "lowest",
            "area_relation": "winner_most_cells",
            "winner_position": "later",
            "loser_motif_relation": "distinct",
            "winner_linkage": "diagonal",
        },
        {
            "grid_h": 16,
            "grid_w": 12,
            "n_colors": 3,
            "winner_count": 4,
            "winner_color_rank": "highest",
            "area_relation": "loser_more_cells",
            "winner_position": "first",
            "loser_motif_relation": "shared",
            "winner_linkage": "diagonal",
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "n_colors": 3,
            "winner_count": 3,
            "winner_color_rank": "lowest",
            "area_relation": "winner_most_cells",
            "winner_position": "later",
            "loser_motif_relation": "distinct",
            "winner_linkage": "orthogonal",
        },
    ],
)
def test_compatible_full_override_tuples_round_trip(overrides: dict) -> None:
    grid = gen.generate(811, 2, difficulty="hard", **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides


def test_unknown_invalid_and_declared_incompatible_calls_reject_loudly() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")
    with pytest.raises(ValueError, match="grid_h"):
        gen.generate(1, 0, grid_h=13)
    with pytest.raises(ValueError, match="winner_color_rank"):
        gen.generate(1, 0, winner_color_rank="middle")

    cases = [
        {"n_colors": 3, "winner_count": 2},
        {"n_colors": 2, "loser_motif_relation": "shared"},
        {"winner_count": 2, "loser_motif_relation": "shared"},
        {"winner_count": 3, "area_relation": "loser_more_cells"},
        {"area_relation": "loser_more_cells", "winner_linkage": "orthogonal"},
    ]
    for overrides in cases:
        with pytest.raises(ValueError) as raised:
            gen.generate(1, 0, **overrides)
        assert set(raised.value.incompatible_axes) == set(overrides)


def test_determinism_fresh_returns_seed_index_variation_and_global_rng_purity() -> None:
    random.seed(92831)
    state = random.getstate()
    first = gen.generate(71, 9, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(71, 9, difficulty="medium")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
    assert second != gen.generate(72, 9, difficulty="medium")
    assert second != gen.generate(71, 10, difficulty="medium")


def test_self_check_rejects_targeted_impostors_and_generic_mutations() -> None:
    fixtures = dict(gen.mutation_fixtures())
    assert len(fixtures) >= 4
    for name, grid in fixtures.items():
        assert gen.self_check(grid), name

    valid = gen.generate(51, 2)
    blank = [[0] * len(valid[0]) for _ in valid]
    assert gen.self_check(blank)

    two_color = gen.generate(51, 1)
    info, _ = gen._analysis(two_color)
    minority = min(info["counts"], key=info["counts"].get)
    dropped_color = [
        [0 if value == minority else value for value in row]
        for row in two_color
    ]
    assert gen.self_check(dropped_color)

    absent_color = copy.deepcopy(valid)
    present = {value for row in valid for value in row}
    new_color = next(color for color in range(1, 10) if color not in present)
    components = gen._components(absent_color)
    row, col = components[len(components) // 2]["cells"][0]
    absent_color[row][col] = new_color
    assert gen.self_check(absent_color)


def test_negative_recombination_uses_a_novel_replacement_motif_and_is_rejected() -> None:
    grid = gen.generate(1337, 0, difficulty="medium")
    mutated = copy.deepcopy(grid)
    info, _ = gen._analysis(mutated)
    winner = info["winner"]
    target = info["by_color"][winner][-1]
    existing = {
        obj["motif"] for obj in info["components"] if obj is not target
    }
    replacement = next(
        shape
        for shape in gen._DIAGONAL_SHAPES[4]
        if shape not in existing and shape != target["motif"]
    )
    for row, col in target["cells"]:
        mutated[row][col] = 0
    r1, c1, _r2, _c2 = target["bbox"]
    for dr, dc in replacement:
        mutated[r1 + dr][c1 + dc] = winner

    remaining_motifs = {
        obj["motif"]
        for obj in gen._components(mutated)
        if obj["bbox"] != target["bbox"]
    }
    assert replacement not in remaining_motifs
    assert gen.self_check(mutated)
    # Distribution rejection and oracle executability are separate claims.
    output = gen.rule_mirror(mutated)
    assert len(output) == 3 and all(len(row) == 3 for row in output)
