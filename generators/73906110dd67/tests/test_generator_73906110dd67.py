from __future__ import annotations

import copy
import importlib
import random

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.73906110dd67.generator")
from reviewer_support import canonical_pairs, find_root


TASK_ID = "73906110dd67"


def _generated_pair(sample_index: int, *, band: str = "medium") -> dict:
    grid = gen.generate(12345, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_inputs_are_accepted() -> None:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    assert all(gen.self_check(pair["input"]) == [] for pair in pairs)


def test_exact_overrides_are_observable() -> None:
    requested = {
        "grid_h": 18,
        "grid_w": 17,
        "n_blobs": 4,
        "size_pattern": "spread",
        "input_size_order": "zigzag",
        "palette_kind": "high",
        "max_bbox_width": 3,
    }
    grid = gen.generate(7, 11, difficulty="easy", **requested)
    assert gen.observe_overrides(grid) == requested


def test_unknown_override_rejected() -> None:
    with pytest.raises(TypeError, match="unknown override axis"):
        gen.generate(0, 0, bogus_axis=1)


def test_self_check_rejects_targeted_impostors() -> None:
    base = gen.generate(41, 0, difficulty="hard")
    facts = gen.semantic_observables(base)
    comps = facts["components"]

    # 1. Recolor a whole component to duplicate another component's color.
    repeated_color = copy.deepcopy(base)
    source_color = comps[0]["color"]
    for r, c in comps[1]["cells"]:
        repeated_color[r][c] = source_color
    assert any("pairwise distinct" in err for err in gen.self_check(repeated_color))

    # 2. Delete cells from the largest component until it ties the next size.
    equal_area = copy.deepcopy(base)
    ordered = sorted(comps, key=lambda comp: comp["size"], reverse=True)
    remove_count = ordered[0]["size"] - ordered[1]["size"]
    for r, c in ordered[0]["cells"][-remove_count:]:
        equal_area[r][c] = 0
    assert gen.self_check(equal_area)

    # 3. Move one cell into the diagonal halo of another component.
    touching = copy.deepcopy(base)
    target = comps[0]["cells"][0]
    donor = comps[-1]["cells"][-1]
    touching[donor[0]][donor[1]] = 0
    touching[target[0] + 1][target[1] + 1] = comps[-1]["color"]
    assert gen.self_check(touching)

    # 4. Remove an entire object so the rule is under-demonstrated.
    too_few = copy.deepcopy(base)
    for r, c in comps[-1]["cells"]:
        too_few[r][c] = 0
    assert any("expected 3-4" in err for err in gen.self_check(too_few))


def test_every_four_demo_window_refutes_all_named_rivals() -> None:
    for start in range(8):
        demos = [_generated_pair(start + offset) for offset in range(4)]
        query = _generated_pair(start + 4)
        assert gen.lesson_identifiable(demos, query) == []


def test_generation_is_deterministic_fresh_and_rng_pure() -> None:
    random.seed(9981)
    before = random.getstate()
    first = gen.generate(99, 17, difficulty="hard")
    after = random.getstate()
    second = gen.generate(99, 17, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == gen.generate(99, 17, difficulty="hard")
    assert before == after


def test_schedule_covers_every_canonical_canvas_size() -> None:
    expected = {
        (len(pair["input"]), len(pair["input"][0]))
        for pair in canonical_pairs(TASK_ID, root=find_root(__file__))
    }
    generated = {
        (len(grid), len(grid[0]))
        for sample_index in range(24)
        if gen.schedule_profile(0, sample_index).startswith("canonical_")
        for grid in [gen.generate(0, sample_index, difficulty="medium")]
    }
    assert expected <= generated


def test_height_eight_is_an_exact_observable_override() -> None:
    requested = {
        "grid_h": 8,
        "grid_w": 11,
        "n_blobs": 3,
        "size_pattern": "spread",
        "input_size_order": "zigzag",
        "palette_kind": "mixed",
        "max_bbox_width": 3,
    }
    grid = gen.generate(17, 5, difficulty="hard", **requested)
    assert gen.observe_overrides(grid) == requested


def test_canonical_profiles_are_not_confined_to_two_origin_rows() -> None:
    row_counts = []
    for sample_index in range(24):
        if not gen.schedule_profile(73, sample_index).startswith("canonical_"):
            continue
        grid = gen.generate(73, sample_index, difficulty="medium")
        origins = [component["bbox"][:2] for component in gen.semantic_observables(grid)["components"]]
        row_counts.append(len({row for row, _ in origins}))
    assert row_counts
    assert min(row_counts) >= 3


def test_generated_palette_support_covers_all_foreground_colors() -> None:
    seen: set[int] = set()
    for seed in range(8):
        for sample_index in range(16):
            grid = gen.generate(seed, sample_index, difficulty="medium")
            seen.update(value for row in grid for value in row if value != 0)
    assert seen == set(range(1, 10))


def test_every_five_pair_window_is_identifiable_under_any_query_rotation() -> None:
    for start in range(8):
        pairs = [_generated_pair(start + offset) for offset in range(5)]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (
                start,
                query_index,
                gen.lesson_identifiable(demos, query),
            )


def test_distribution_probe_is_reusable_and_checks_rotated_lessons() -> None:
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path
    import sys

    tool_path = (
        find_root(__file__)
        / "generators"
        / TASK_ID
        / "workspace"
        / "distribution_probe.py"
    )
    spec = spec_from_file_location("distribution_probe_73906110dd67", tool_path)
    assert spec is not None and spec.loader is not None
    tool = module_from_spec(spec)
    sys.modules[spec.name] = tool
    spec.loader.exec_module(tool)

    report = tool.probe_generator(
        gen,
        heights=(8,),
        widths=(10,),
        bands=("easy",),
        rotation_starts=range(4),
    )
    assert report["override_probe"]["cases"] == 72
    assert report["override_probe"]["errors"] == []
    assert report["rotation_probe"]["ambiguous"] == []
