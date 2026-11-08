from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random

import pytest

from puzzle_generators import base
gen = importlib.import_module("puzzle_generators.per_puzzle.3a0af56db83e.generator")
from reviewer_support import canonical_pairs as _canonical_pairs, canonical_path, find_root


ROOT = find_root(__file__)


def canonical_pairs(task_id):
    return _canonical_pairs(task_id, root=ROOT)


def canonical_rule_hash(task_id):
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == task_id and row.get("program_solution"):
                source = " ".join(str(row["program_solution"]).split())
                return hashlib.sha256(source.encode()).hexdigest()[:12]
    raise FileNotFoundError(f"{task_id}: no canonical program_solution")


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_canonical_acceptance_and_rule_mirror():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID)
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 7
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]


def _projected_multiplicity_counts(grid):
    counts = {arity: 0 for arity in range(5)}
    for row in range(3):
        for col in range(len(grid[0])):
            arity = sum(grid[band * 3 + row][col] != 0 for band in range(4))
            counts[arity] += 1
    return counts


def test_every_generated_scene_covers_all_projected_overlap_arities():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = gen.generate(90_000 + sample_index, sample_index, difficulty=difficulty)
            counts = _projected_multiplicity_counts(grid)
            assert all(counts[arity] > 0 for arity in range(5)), (
                difficulty,
                sample_index,
                counts,
            )


@pytest.mark.parametrize("mask_profile", gen.MASK_PROFILES)
def test_wide_profiles_mix_overlap_arities_without_losing_axis_observability(mask_profile):
    grid = gen.generate(95_000, 5, grid_w=12, mask_profile=mask_profile)
    counts = _projected_multiplicity_counts(grid)
    substantial_bins = sum(count >= len(grid[0]) for count in counts.values())
    assert substantial_bins >= 2, (mask_profile, counts)
    assert gen.observe_overrides(grid)["mask_profile"] == mask_profile


def test_every_generated_scene_contains_complete_priority_witnesses():
    expected_pairs = {tuple(sorted(pair)) for pair in gen._PAIR_ROLES}
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = gen.generate(100_000 + sample_index, sample_index, difficulty=difficulty)
            sig = gen.semantic_signature(grid)
            assert all(sig["pair_counts"].get(pair, 0) > 0 for pair in expected_pairs)
            assert all(sig["winner_counts"][band] > 0 for band in range(4))
            assert sig["zero_projected"] > 0
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                if name == "varied_band_color_mapping" and sample_index % 4 == 0:
                    assert not witness(grid)
                else:
                    assert witness(grid), (difficulty, sample_index, name)


def test_two_step_schedule_is_identifiable_and_breaks_color_shortcut():
    canonical = canonical_pairs(gen.TASK_ID)
    assert all(
        gen._canonical_color_priority(pair["input"]) == pair["output"]
        for pair in canonical
    )
    for difficulty_index, difficulty in enumerate(("easy", "medium", "hard")):
        for start in range(0, 16):
            lesson_seed = 210_000 + difficulty_index * 10_000 + start
            demos = [
                _pair(gen.generate(lesson_seed, start + offset, difficulty=difficulty))
                for offset in range(2)
            ]
            query = _pair(gen.generate(lesson_seed, start + 2, difficulty=difficulty))
            assert gen.lesson_identifiable(demos, query) == []
            assert any(
                gen._canonical_color_priority(pair["input"]) != pair["output"]
                for pair in demos
            )


def test_same_seed_lesson_remains_identifiable_under_every_query_rotation():
    # Regression from the source-bound 100-per-band census: with this lesson
    # seed, samples 61 and 63 once shared the max-aligned varied palette
    # (8,5,2,4), so max_color_overlay survived when sample 62 was held out.
    seed = 1_911_857_371
    pairs = [
        _pair(gen.generate(seed, sample_index, difficulty="hard"))
        for sample_index in range(61, 64)
    ]
    for query_index in range(3):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == [], query_index


def test_two_step_schedule_refutes_overlap_arity_shortcuts():
    rival_names = {"reverse_on_three_way", "reverse_on_four_way"}
    assert rival_names <= set(gen.LESSON_COMPETITORS)
    for difficulty_index, difficulty in enumerate(("easy", "medium", "hard")):
        for start in range(16):
            lesson_seed = 320_000 + difficulty_index * 10_000 + start
            demos = [
                _pair(gen.generate(lesson_seed, start + offset, difficulty=difficulty))
                for offset in range(2)
            ]
            for name in rival_names:
                rival = gen.LESSON_COMPETITORS[name]
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    difficulty,
                    start,
                    name,
                )


def test_boundary_overrides_are_exact_observable_and_unknown_keys_reject():
    case = 0
    for width in (4, 12):
        for mask_profile in gen.MASK_PROFILES:
            for palette_mode in gen.PALETTE_MODES:
                grid = gen.generate(
                    400_000 + case,
                    case,
                    difficulty="hard",
                    grid_w=width,
                    mask_profile=mask_profile,
                    palette_mode=palette_mode,
                )
                assert gen.observe_overrides(grid) == {
                    "grid_w": width,
                    "mask_profile": mask_profile,
                    "palette_mode": palette_mode,
                }
                assert gen.self_check(grid) == []
                case += 1
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 1, projected_overlap_kind="full")
    with pytest.raises(ValueError, match="grid_w"):
        gen.generate(1, 1, grid_w=3)


def test_self_check_rejects_baseline_impostors():
    source = copy.deepcopy(canonical_pairs(gen.TASK_ID)[0]["input"])

    wrong_height = copy.deepcopy(source[:-1])
    assert gen.self_check(wrong_height)

    empty_band = copy.deepcopy(source)
    for row in range(3):
        empty_band[row] = [0] * len(empty_band[row])
    assert any("band 0 is empty" in error for error in gen.self_check(empty_band))

    mixed_band = copy.deepcopy(source)
    # Canonical band 0 is color 5; inject a second nonzero color into a zero cell.
    for row in range(3):
        for col, value in enumerate(mixed_band[row]):
            if value == 0:
                mixed_band[row][col] = 9
                break
        else:
            continue
        break
    assert any("monochrome" in error for error in gen.self_check(mixed_band))

    duplicate_band_color = copy.deepcopy(source)
    for row in range(3, 6):
        duplicate_band_color[row] = [5 if value == 4 else value for value in duplicate_band_color[row]]
    assert any("distinct" in error for error in gen.self_check(duplicate_band_color))


def test_replay_fresh_returns_global_rng_purity_and_provenance():
    random.seed(991)
    before = random.getstate()
    captured = []
    base.set_ctx_observer(captured.append)
    try:
        first = gen.generate(42, 7, difficulty="hard")
    finally:
        base.set_ctx_observer(None)
    after = random.getstate()
    second = gen.generate(42, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert len(captured) == 1
    assert captured[0].recorded_draws() == gen.observe_overrides(first)
    assert captured[0].overrides_used() == {}
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert first != second
