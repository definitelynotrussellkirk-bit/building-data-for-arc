from __future__ import annotations

import copy
from collections import Counter
import importlib
import random

from reviewer_support import canonical_pairs, find_root

TASK_ID = "7a37505e7bd0"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.7a37505e7bd0.generator"
)


def test_canonical_inputs_are_accepted_and_mirror_outputs() -> None:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 8
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_every_five_sample_window_covers_scale_factors_and_zero_witness() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(10):
            grids = [GEN.generate(12345, start + offset, difficulty=band) for offset in range(5)]
            counts = [GEN.observe_overrides(grid)["color_count"] for grid in grids]
            assert set(counts) == {1, 2, 3, 4, 5}
            assert any(0 in {value for row in grid for value in row} for grid in grids)
            demos = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
            query_grid = GEN.generate(54321, start + 5, difficulty=band)
            query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []


def test_override_is_exact_observable_and_unknown_keys_reject() -> None:
    for count in range(1, 6):
        grid = GEN.generate(7, 11, difficulty="hard", color_count=count)
        assert GEN.observe_overrides(grid)["color_count"] == count
        assert GEN.self_check(grid) == []
    try:
        GEN.generate(7, 0, typo_axis=3)
    except ValueError as exc:
        assert "unknown override" in str(exc)
    else:
        raise AssertionError("unknown override was accepted")


def test_self_check_rejects_targeted_impostors() -> None:
    impostors = {
        "all_zero": [[0] * 3 for _ in range(3)],
        "singleton": [[7]],
        "short_line": [[1, 2, 1]],
        "solid_2x2": [[4, 4], [4, 4]],
        "eight_plus_one": [[1, 1, 1], [1, 1, 1], [1, 1, 2]],
        "row_only_variation": [[1, 1, 1], [2, 2, 2], [1, 1, 1]],
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(9917)
    before = random.getstate()
    first = GEN.generate(2026, 19, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(2026, 19, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    mutated = copy.deepcopy(first)
    mutated[0][0] = (mutated[0][0] + 1) % 10
    assert second != mutated


def _identity_palette_shortcut(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rival: treat canonical identity colors 3/8 as an identity cue."""
    colors = {value for row in grid for value in row}
    if colors & {3, 8}:
        return copy.deepcopy(grid)
    return GEN.rule_mirror(grid)


def test_every_five_demo_lesson_refutes_identity_palette_shortcut() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            for start in range(5):
                grids = [
                    GEN.generate(seed, start + offset, difficulty=band)
                    for offset in range(5)
                ]
                assert any(
                    _identity_palette_shortcut(grid) != GEN.rule_mirror(grid)
                    for grid in grids
                ), (band, seed, start, grids)


def test_identity_palette_witness_pairs_rotate_across_counts_three_to_five() -> None:
    witnessed_pairs: set[tuple[int, int]] = set()
    for seed in range(8):
        grids = [GEN.generate(seed, offset, difficulty="medium") for offset in range(5)]
        lesson_witnesses = []
        for grid in grids:
            colors = {value for row in grid for value in row}
            if len(colors) > 1 and colors & {3, 8}:
                lesson_witnesses.append(len(colors))
        assert len(lesson_witnesses) == 2, (seed, lesson_witnesses, grids)
        witnessed_pairs.add(tuple(sorted(lesson_witnesses)))
    assert witnessed_pairs == {(3, 4), (4, 5), (3, 5)}


def test_multicolor_identity_witness_is_never_modal_background() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(16):
            for sample_index in range(10):
                grid = GEN.generate(seed, sample_index, difficulty=band)
                counts = Counter(value for row in grid for value in row)
                special = set(counts) & {3, 8}
                if len(counts) > 1 and special:
                    modal = max(counts.values())
                    assert all(counts[color] < modal for color in special), (
                        band, seed, sample_index, counts, grid
                    )


def test_identity_witnesses_do_not_make_lawful_minimal_collapses() -> None:
    """Mirror defect-lint's two monochrome probes on every 3/8 witness."""
    for band in ("easy", "medium", "hard"):
        for seed in range(16):
            for sample_index in range(10):
                grid = GEN.generate(seed, sample_index, difficulty=band)
                counts = Counter(value for row in grid for value in row)
                if len(counts) <= 1 or not (set(counts) & {3, 8}):
                    continue
                modal = counts.most_common(1)[0][0]
                foreground = min(color for color in counts if color != modal)
                all_background = [[modal] * 3 for _ in range(3)]
                full_foreground = [[foreground] * 3 for _ in range(3)]
                assert GEN.self_check(all_background), (
                    "all_background", band, seed, sample_index, counts, grid
                )
                assert GEN.self_check(full_foreground), (
                    "full_one_color", band, seed, sample_index, counts, grid
                )


def test_six_pair_lesson_is_identifiable_under_every_query_rotation() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            pairs = []
            for sample_index in range(6):
                grid = GEN.generate(seed, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == [], (
                    band,
                    seed,
                    query_index,
                    GEN.lesson_identifiable(demos, query),
                )
