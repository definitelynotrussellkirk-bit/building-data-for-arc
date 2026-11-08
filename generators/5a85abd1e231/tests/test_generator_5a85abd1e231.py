from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "5a85abd1e231"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_rule_hash_and_all_canonical_pairs_match_python_mirror() -> None:
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "2b7620b38386"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    observed = []
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        frozen = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == frozen
        observed.append(GEN.observe_overrides(source))
    assert {item["scene_profile"] for item in observed} == set(GEN.SCENE_PROFILES)
    assert {item["contact_mode"] for item in observed} == set(GEN.CONTACT_MODES)


def test_regression_old_seed_now_has_the_full_nine_tile_compass_grammar() -> None:
    # Baseline VERSION 3.1.0 produced an 8x10 grid with only two solid tiles for
    # this exact witness. That taught a partial synthetic problem while passing
    # its own self_check. The repaired generator must express the whole task.
    grid = GEN.generate(0, 0, difficulty="easy")
    analysis = GEN._analysis(grid)
    assert analysis["errors"] == []
    assert len(analysis["origins"]) == 9
    assert analysis["blank_count"] == 1
    assert set(analysis["directions"]) == set(GEN._DIRECTION_ORDER)
    assert analysis["profile"] in GEN.SCENE_PROFILES
    assert analysis["palette_size"] in (9, 10)


@pytest.mark.parametrize("profile", GEN.SCENE_PROFILES)
@pytest.mark.parametrize("contact_mode", GEN.CONTACT_MODES)
def test_exact_override_axes_are_realized_and_observable(profile: str, contact_mode: str) -> None:
    grid = GEN.generate(
        918273,
        17,
        difficulty="hard",
        scene_profile=profile,
        contact_mode=contact_mode,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "scene_profile": profile,
        "contact_mode": contact_mode,
    }


def test_unknown_axis_profile_contact_and_difficulty_fail_closed() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, typo_axis="x")
    with pytest.raises(ValueError, match="unknown scene_profile"):
        GEN.generate(1, 2, scene_profile="not_real")
    with pytest.raises(ValueError, match="unknown contact_mode"):
        GEN.generate(1, 2, contact_mode="not_real")
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 2, difficulty="extreme")


def test_schedule_covers_every_profile_and_contact_branch_in_every_band() -> None:
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(1000 + i, i, difficulty=band) for i in range(12)]
        observed = [GEN.observe_overrides(grid) for grid in grids]
        assert {item["scene_profile"] for item in observed} == set(GEN.SCENE_PROFILES)
        assert {item["contact_mode"] for item in observed} == set(GEN.CONTACT_MODES)
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)


def test_semantic_witnesses_fire_and_declared_rivals_are_actually_wrong() -> None:
    for band in ("easy", "medium", "hard"):
        hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        for sample_index in range(30):
            grid = GEN.generate(70000 + sample_index, sample_index, difficulty=band)
            official = GEN.rule_mirror(grid)
            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                hits[name] += int(predicate(grid))
            for rival in GEN.SEMANTIC_RIVALS.values():
                # The scheduled random assignment almost always refutes each
                # rival per grid; the dedicated witness contract below is the
                # actual semantic-gate obligation.
                assert isinstance(rival(grid), list)
            for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
                if GEN.SEMANTIC_WITNESSES[witness_name](grid):
                    assert any(GEN.SEMANTIC_RIVALS[name](grid) != official for name in rival_names)
        assert all(count > 0 for count in hits.values()), (band, hits)


def test_three_demo_lesson_covers_profiles_contacts_and_kills_rivals() -> None:
    for band in ("easy", "medium", "hard"):
        pairs = []
        for sample_index in range(4):
            grid = GEN.generate(8080 + sample_index, sample_index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_self_check_rejects_structural_shortcuts_and_mutations() -> None:
    base = GEN.generate(314159, 5, difficulty="medium", contact_mode="separated")
    analysis = GEN._analysis(base)

    missing_tile = copy.deepcopy(base)
    top, left = analysis["origins"][0]
    for dr in range(3):
        for dc in range(3):
            missing_tile[top + dr][left + dc] = 0
    assert GEN.self_check(missing_tile)

    wrong_glyph = copy.deepcopy(base)
    tile = next(tile for tile in analysis["tiles"] if tile["direction"] is not None)
    top, left = tile["origin"]
    signal = [(dr, dc) for dr in range(3) for dc in range(3) if wrong_glyph[top + dr][left + dc] != 5]
    dr, dc = signal[0]
    wrong_glyph[top + dr][left + dc] = 5
    assert GEN.self_check(wrong_glyph)

    extra_noise = copy.deepcopy(base)
    occupied = set().union(*(GEN._tile_cells(origin) for origin in analysis["origins"]))
    row, col = next((r, c) for r in range(len(base)) for c in range(len(base[0])) if (r, c) not in occupied)
    extra_noise[row][col] = 1
    assert GEN.self_check(extra_noise)

    wrong_palette = copy.deepcopy(base)
    source_color = next(tile["color"] for tile in analysis["tiles"] if tile["color"] is not None)
    for tile in analysis["tiles"]:
        if tile["color"] is not None and tile["color"] != source_color:
            top, left = tile["origin"]
            for dr in range(3):
                for dc in range(3):
                    if wrong_palette[top + dr][left + dc] == tile["color"]:
                        wrong_palette[top + dr][left + dc] = source_color
            break
    assert GEN.self_check(wrong_palette)


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(24681357)
    before = random.getstate()
    first = GEN.generate(12345, 17, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(12345, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_self_check_rejects_two_cell_tile_contact_outside_canonical_grammar() -> None:
    # The canonical touching layout joins exactly one pair through one cardinal
    # edge cell. Offsetting the lower tile by only one column creates a two-cell
    # seam; the old analyzer classified it as the lawful touching_pair branch.
    origins = [
        (0, 0),
        (3, 1),
        (9, 6),
        (12, 1),
        (7, 10),
        (2, 6),
        (11, 12),
        (3, 12),
        (13, 8),
    ]
    colors = [1, 2, 3, 4, 6, 7, 8, 1]
    grid = [[0 for _ in range(15)] for _ in range(16)]
    for origin, direction, color in zip(origins[:8], GEN._DIRECTION_ORDER, colors):
        GEN._stamp_tile(grid, origin[0], origin[1], direction, color)
    GEN._stamp_tile(grid, origins[8][0], origins[8][1], None, None)

    analysis = GEN._analysis(grid)
    assert analysis["components"] == 8
    assert any("exactly one cardinal edge cell" in error for error in GEN.self_check(grid))
