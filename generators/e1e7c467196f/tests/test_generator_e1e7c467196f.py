"""Focused regression tests for the e1e7c467196f legend-recolor generator."""
from __future__ import annotations

import copy
import itertools
import random

import pytest

from puzzle_generators.per_puzzle.e1e7c467196f import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _pairing_signature(grid: list[list[int]]) -> tuple[int, ...]:
    """Return target ranks indexed by sorted source-color rank."""
    sources = [value for value in grid[0] if value != 0]
    targets = [value for value in grid[1] if value != 0]
    mapping = dict(zip(sources, targets))
    target_rank = {value: index for index, value in enumerate(sorted(targets))}
    return tuple(target_rank[mapping[source]] for source in sorted(sources))


def _pair(seed: int, sample_index: int, difficulty: str = "medium") -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_pairs_are_accepted_and_solved() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_override_boundaries_are_exact_and_unknown_keys_fail() -> None:
    grid = gen.generate(
        41,
        7,
        difficulty="easy",
        grid_h=14,
        grid_w=5,
        K=4,
        n_markers=4,
        n_unmapped=4,
    )
    assert gen.observe_overrides(grid) == {
        "grid_h": 14,
        "grid_w": 5,
        "K": 4,
        "n_markers": 4,
        "n_unmapped": 4,
    }
    assert gen.self_check(grid) == []
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, typo_axis=3)


def test_three_demo_windows_make_every_sliding_lesson_identifiable() -> None:
    for start in range(8):
        demos = [_pair(800 + start, start + offset) for offset in range(3)]
        query = _pair(1800 + start, start + 3)
        assert gen.lesson_identifiable(demos, query) == []
        assert any(
            gen.SEMANTIC_WITNESSES["value_colored_body_cell_stays_unchanged"](
                pair["input"]
            )
            for pair in demos
        )
        assert any(
            gen.SEMANTIC_WITNESSES["neutral_body_color_stays_unchanged"](
                pair["input"]
            )
            for pair in demos
        )


def test_self_check_rejects_targeted_structural_impostors() -> None:
    base = gen.generate(1234, 1, difficulty="medium")
    assert gen.self_check(base) == []

    missing_target = copy.deepcopy(base)
    missing_target[1][1] = 0
    assert any("contiguous aligned" in err for err in gen.self_check(missing_target))

    duplicate_source = copy.deepcopy(base)
    duplicate_source[0][1] = duplicate_source[0][0]
    assert any("source colors must be distinct" in err for err in gen.self_check(duplicate_source))

    source_target_overlap = copy.deepcopy(base)
    source_target_overlap[1][0] = source_target_overlap[0][1]
    assert any("sets must be disjoint" in err for err in gen.self_check(source_target_overlap))

    missing_source_use = copy.deepcopy(base)
    absent = missing_source_use[0][0]
    replacement = missing_source_use[0][1]
    for row in range(2, len(missing_source_use)):
        for col in range(len(missing_source_use[0])):
            if missing_source_use[row][col] == absent:
                missing_source_use[row][col] = replacement
    assert any("omits legend source" in err for err in gen.self_check(missing_source_use))

    excessive_unmapped = copy.deepcopy(base)
    keys = set(excessive_unmapped[0]) - {0}
    neutral = next(color for color in range(1, 10) if color not in keys)
    placed = 0
    for row in range(2, len(excessive_unmapped)):
        for col in range(len(excessive_unmapped[0])):
            if excessive_unmapped[row][col] == 0 and placed < 5:
                excessive_unmapped[row][col] = neutral
                placed += 1
    assert any("unmapped cells" in err for err in gen.self_check(excessive_unmapped))


def test_determinism_fresh_returns_input_purity_and_global_rng() -> None:
    random.seed(20260728)
    state = random.getstate()
    first = gen.generate(91, 2, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(91, 2, difficulty="hard")
    assert first == second
    assert first is not second
    first[2][0] = 99
    third = gen.generate(91, 2, difficulty="hard")
    assert third == second

    before = copy.deepcopy(third)
    _ = gen.rule_mirror(third)
    assert third == before


def test_canonical_k2_profile_emits_rank_aligned_pairing() -> None:
    grid = gen.generate(17, 0, difficulty="medium")
    assert gen.schedule_profile(17, 0, "medium") == "canonical_k2"
    assert _pairing_signature(grid) == (0, 1)


def test_canonical_k3_profile_emits_reverse_rank_pairing() -> None:
    grid = gen.generate(17, 3, difficulty="medium")
    assert gen.schedule_profile(17, 3, "medium") == "canonical_k3_value"
    assert _pairing_signature(grid) == (2, 1, 0)


def test_default_hard_distribution_reaches_every_k4_pairing() -> None:
    signatures: set[tuple[int, ...]] = set()
    for seed in range(1024):
        for sample_index in (1, 2):
            grid = gen.generate(seed, sample_index, difficulty="hard")
            if len([value for value in grid[0] if value != 0]) == 4:
                signatures.add(_pairing_signature(grid))
    assert signatures == set(itertools.permutations(range(4)))


def test_pairing_witnesses_cover_aligned_and_noncyclic_profiles() -> None:
    aligned = gen.generate(23, 0, difficulty="easy")
    reverse = gen.generate(23, 3, difficulty="easy")
    assert gen.SEMANTIC_WITNESSES["rank_aligned_pairing_is_supported"](aligned)
    assert gen.SEMANTIC_WITNESSES["noncyclic_pairing_is_supported"](reverse)


def test_pairing_witnesses_refute_nonzero_cyclic_rank_shortcut() -> None:
    rival_name = "infer_nonzero_cyclic_rank_pairing"
    rival = gen.SEMANTIC_RIVALS[rival_name]
    canonical = canonical_pairs(gen.TASK_ID)
    assert rival(canonical[0]["input"]) == canonical[0]["output"]

    for sample_index in (0, 3):
        grid = gen.generate(31, sample_index, difficulty="medium")
        assert rival(grid) != gen.rule_mirror(grid)

    assert gen.WITNESS_RIVALS["rank_aligned_pairing_is_supported"] == [rival_name]
    assert gen.WITNESS_RIVALS["noncyclic_pairing_is_supported"] == [rival_name]
