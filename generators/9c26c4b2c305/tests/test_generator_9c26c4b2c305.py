"""Focused regression and curriculum tests for generator 9c26c4b2c305."""
from __future__ import annotations

import copy
import importlib

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "9c26c4b2c305"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _draw(seed=17, sample_index=0, difficulty="medium", **overrides):
    return GEN.generate(seed, sample_index, difficulty=difficulty, **overrides)


def test_canonical_inputs_and_outputs_match_rule_mirror():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_determinism_fresh_returns_and_no_input_mutation():
    first = _draw(seed=91, sample_index=7, difficulty="hard")
    second = _draw(seed=91, sample_index=7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    frozen = copy.deepcopy(first)
    GEN.rule_mirror(first)
    GEN.observe_overrides(first)
    assert first == frozen


def test_exact_overrides_are_observable_and_unknown_keys_reject():
    for relation in GEN.RELATION_PROFILES:
        for palette in GEN.PALETTE_PROFILES:
            grid = _draw(
                seed=3,
                sample_index=11,
                difficulty="easy",
                grid_w=14,
                relation_profile=relation,
                palette_profile=palette,
            )
            assert GEN.observe_overrides(grid) == {
                "grid_w": 14,
                "relation_profile": relation,
                "palette_profile": palette,
            }
    with pytest.raises(ValueError, match="unknown override"):
        _draw(typo_axis=1)
    with pytest.raises(ValueError):
        _draw(grid_w=3)
    with pytest.raises(ValueError):
        _draw(relation_profile="not_a_profile")


def test_self_check_rejects_structural_impostors():
    valid = _draw(seed=101, sample_index=0)

    ragged = copy.deepcopy(valid)
    ragged[0].pop()
    assert GEN.self_check(ragged)

    mixed_separator = copy.deepcopy(valid)
    mixed_separator[4][0] = 6 if mixed_separator[4][0] != 6 else 7
    assert any("separator row must be uniform" in msg for msg in GEN.self_check(mixed_separator))

    mixed_top_palette = copy.deepcopy(valid)
    for row in range(4):
        for col in range(len(valid[0])):
            if mixed_top_palette[row][col] != 0:
                mixed_top_palette[row][col] = 6
                break
        else:
            continue
        break
    top_colors = {v for row in mixed_top_palette[:4] for v in row if v}
    if len(top_colors) == 1:
        # Mutate a second occupied cell to a different nonzero color.
        changed = False
        for row in range(4):
            for col in range(len(valid[0])):
                if mixed_top_palette[row][col] != 0:
                    mixed_top_palette[row][col] = 5 if mixed_top_palette[row][col] != 5 else 6
                    changed = True
                    break
            if changed:
                break
    assert any("top panel must use exactly one" in msg for msg in GEN.self_check(mixed_top_palette))

    solid_union = copy.deepcopy(valid)
    top_color = next(v for row in solid_union[:4] for v in row if v)
    bottom_color = next(v for row in solid_union[5:] for v in row if v)
    for row in range(4):
        for col in range(len(valid[0])):
            solid_union[row][col] = top_color
            solid_union[5 + row][col] = bottom_color
    assert any("negative cell" in msg for msg in GEN.self_check(solid_union))

    empty_union = copy.deepcopy(valid)
    for row in list(range(4)) + list(range(5, 9)):
        empty_union[row] = [0] * len(valid[0])
    assert GEN.self_check(empty_union)


def test_every_four_example_window_is_identifiable_and_kills_rivals():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for offset in range(GEN.EXAMPLES_NEEDED):
                grid = _draw(
                    seed=10_000 + start + offset,
                    sample_index=start + offset,
                    difficulty=difficulty,
                )
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            query_grid = _draw(
                seed=20_000 + start,
                sample_index=start + GEN.EXAMPLES_NEEDED,
                difficulty=difficulty,
            )
            assert GEN.lesson_identifiable(
                demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            ) == []


def test_each_generated_grid_exposes_all_four_relations():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(16):
            grid = _draw(seed=700 + sample_index, sample_index=sample_index, difficulty=difficulty)
            info, errors = GEN._analyse(grid)
            assert errors == []
            assert all(count > 0 for count in info["relation_counts"].values())


def test_same_color_palette_is_observable_and_refutes_conditional_xor():
    grid = _draw(
        seed=404,
        sample_index=1,
        difficulty="medium",
        grid_w=9,
        relation_profile="balanced",
        palette_profile="same_color_779",
    )
    observed = GEN.observe_overrides(grid)
    assert observed == {
        "grid_w": 9,
        "relation_profile": "balanced",
        "palette_profile": "same_color_779",
    }
    info, errors = GEN._analyse(grid)
    assert errors == []
    assert info["top_colors"] == info["bottom_colors"] == {7}
    assert GEN._rival_same_color_xor_otherwise_or(grid) != GEN.rule_mirror(grid)


def test_each_four_example_schedule_contains_same_color_counterexample():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            same_color_count = 0
            rival_killed = False
            for offset in range(GEN.EXAMPLES_NEEDED):
                grid = _draw(
                    seed=30_000 + start + offset,
                    sample_index=start + offset,
                    difficulty=difficulty,
                )
                info, errors = GEN._analyse(grid)
                assert errors == []
                same_color_count += int(info["top_colors"] == info["bottom_colors"])
                expected = GEN.rule_mirror(grid)
                rival_killed = rival_killed or (
                    GEN._rival_same_color_xor_otherwise_or(grid) != expected
                )
                demos.append({"input": grid, "output": expected})
            assert same_color_count == 1
            assert rival_killed
            query_grid = _draw(
                seed=40_000 + start,
                sample_index=start + GEN.EXAMPLES_NEEDED,
                difficulty=difficulty,
            )
            assert GEN.lesson_identifiable(
                demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            ) == []


def test_same_color_conditional_rival_fits_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID)
    assert all(
        GEN._rival_same_color_xor_otherwise_or(pair["input"]) == pair["output"]
        for pair in pairs
    )
    assert "same_color_xor_otherwise_or" in GEN.CANONICAL_SHORTCUTS
