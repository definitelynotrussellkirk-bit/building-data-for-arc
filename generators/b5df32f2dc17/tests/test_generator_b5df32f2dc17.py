from __future__ import annotations

import importlib

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.b5df32f2dc17.generator")


def test_rule_hash_and_canonical_inputs():
    assert gen.RULE_HASH == "5afe989c75c5"
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_overrides_are_observable_and_unknown_rejected():
    for n_runs in (2, 3):
        grid = gen.generate(17, 2, difficulty="hard", grid_h=5, grid_w=14, n_runs=n_runs, palette_size=6)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {
            "grid_h": 5,
            "grid_w": 14,
            "palette_size": 6,
            "n_runs": n_runs,
        }
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, not_an_axis=3)


def test_structural_impostors_are_rejected():
    good = gen.generate(5, 1, grid_h=4, grid_w=12, n_runs=3, palette_size=4)
    assert gen.self_check(good) == []

    all_background = [[0] * 12 for _ in range(4)]
    singleton = [[0] * 12 for _ in range(4)]
    singleton[0][0] = 3
    tied = [[0] * 12 for _ in range(4)]
    tied[0][0:2] = [2, 2]
    tied[0][4:6] = [4, 4]
    touching = [row[:] for row in good]
    first = gen._row_runs(touching[0])
    start2 = first[1][0]
    touching[0][start2 - 1] = first[0][2]
    already_sorted = [[0] * 12 for _ in range(4)]
    already_sorted[0][0:4] = [2] * 4
    already_sorted[0][5:7] = [5] * 2

    for bad in (all_background, singleton, tied, touching, already_sorted):
        assert gen.self_check(bad), bad


def test_three_slot_sliding_windows_kill_named_rivals():
    seed = 909
    pairs = []
    for sample_index in range(9):
        grid = gen.generate(seed, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    for start in range(6):
        demos = pairs[start:start + gen.EXAMPLES_NEEDED]
        query = pairs[start + gen.EXAMPLES_NEEDED]
        assert gen.lesson_identifiable(demos, query) == []
        assert {gen.observe_overrides(pair["input"])["n_runs"] for pair in demos} == {2, 3}
        for rival in gen.LESSON_COMPETITORS.values():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def _row_role(row):
    runs = gen._row_runs(row)
    lengths = [length for _, length, _ in runs]
    if not runs:
        return "blank"
    if len(runs) == 1:
        return "single"
    if lengths == sorted(lengths, reverse=True):
        return "multi_already_sorted"
    return "multi_needs_reorder"


def test_default_distribution_includes_rowwise_control_cases():
    """A learner must see that sorting/repacking is applied independently per row."""
    seen_roles = set()
    seen_color_orders = set()
    blank_scenes = 0

    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        for index in range(40):
            seed = 710_000 + 10_000 * band_index + index
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []

            roles = [_row_role(row) for row in grid]
            seen_roles.update(roles)
            assert "multi_needs_reorder" in roles
            assert "multi_already_sorted" in roles
            assert "single" in roles
            blank_scenes += "blank" in roles

            run_counts = [len(gen._row_runs(row)) for row in grid]
            observed = gen.observe_overrides(grid)
            assert observed["n_runs"] == max(run_counts)

            for row in grid:
                colors = [color for _, _, color in gen._row_runs(row)]
                if len(colors) >= 2:
                    if colors == sorted(colors):
                        seen_color_orders.add("ascending")
                    elif colors == sorted(colors, reverse=True):
                        seen_color_orders.add("descending")
                    else:
                        seen_color_orders.add("mixed")

    assert seen_roles == {
        "blank",
        "single",
        "multi_already_sorted",
        "multi_needs_reorder",
    }
    assert blank_scenes > 0
    assert "ascending" in seen_color_orders
    assert seen_color_orders & {"descending", "mixed"}


def test_single_and_sorted_row_shortcuts_are_executable_and_refuted():
    """The generated curriculum must kill two row-homogeneity shortcuts."""
    assert "multi_run_rows_only" in gen.LESSON_COMPETITORS
    assert "leave_already_sorted_rows" in gen.LESSON_COMPETITORS

    for sample_index in range(12):
        grid = gen.generate(991, sample_index, difficulty="medium")
        expected = gen.rule_mirror(grid)
        assert gen.LESSON_COMPETITORS["multi_run_rows_only"](grid) != expected
        assert gen.LESSON_COMPETITORS["leave_already_sorted_rows"](grid) != expected


def test_override_corner_still_realizes_all_exact_axes():
    grid = gen.generate(
        81,
        5,
        difficulty="hard",
        grid_h=3,
        grid_w=11,
        n_runs=2,
        palette_size=6,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 3,
        "grid_w": 11,
        "palette_size": 6,
        "n_runs": 2,
    }


def test_lesson_hook_accepts_all_three_run_rotation_when_rivals_are_refuted():
    """Query rotation may leave only 3-run demos; identifiability is rival-based."""
    seed = 4242
    demo_indices = (1, 2, 4)  # all scheduled with max n_runs == 3
    demos = []
    for sample_index in demo_indices:
        grid = gen.generate(seed, sample_index, difficulty="medium")
        assert gen.observe_overrides(grid)["n_runs"] == 3
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed, 5, difficulty="medium")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}

    for rival in gen.LESSON_COMPETITORS.values():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos)
    assert gen.lesson_identifiable(demos, query) == []
