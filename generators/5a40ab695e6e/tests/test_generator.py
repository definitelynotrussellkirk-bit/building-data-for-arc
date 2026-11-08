"""Focused regressions for symmetry-signature generator 5a40ab695e6e."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

import pytest

TASK_ID = "5a40ab695e6e"
GENERATOR_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = GENERATOR_DIR / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(
        f"generator_{TASK_ID}", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    with (REPO_ROOT / "shared/data/canonical/puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [*row["train"], *tests]
    raise AssertionError(f"canonical task {TASK_ID} is missing")


def signature(grid):
    return tuple(tuple(row) for row in grid)


def independent_symmetry_rule(grid):
    """Small test oracle, intentionally independent of production helpers."""
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    seen = set()
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0 = min(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            mask = {(rr - r0, cc - c0) for rr, cc in cells}
            mh = max(rr for rr, _ in mask)
            mw = max(cc for _, cc in mask)
            lr = {(rr, mw - cc) for rr, cc in mask} == mask
            ud = {(mh - rr, cc) for rr, cc in mask} == mask
            new_color = 2 if lr and ud else 3 if lr else 4 if ud else 6
            for rr, cc in cells:
                out[rr][cc] = new_color
    return out


def test_rule_pin_axes_and_every_canonical_pair():
    gen = load_generator()
    assert gen.RULE_HASH == "5e6364f401b5"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_objects"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert independent_symmetry_rule(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_controls_are_total_observable_and_unknown_controls_fail(difficulty):
    gen = load_generator()
    cases = [
        {"grid_h": 9, "grid_w": 10, "n_objects": 3},
        {"grid_h": 11, "grid_w": 13, "n_objects": 4},
        {"grid_h": 14, "grid_w": 16, "n_objects": 3},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(20261003, index, difficulty=difficulty, **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, difficulty=difficulty, meta={"overrides": overrides}) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, mystery_axis=7)
    for bad in (True, 9.0, "9"):
        with pytest.raises(ValueError, match="grid_h"):
            gen.generate(1, 0, grid_h=bad)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="impossible")


def test_default_distribution_is_valid_diverse_and_replays_cleanly():
    gen = load_generator()
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        grids = [
            gen.generate(700_000 + band_index, index, difficulty=difficulty)
            for index in range(120)
        ]
        assert all(gen.self_check(grid, difficulty=difficulty) == [] for grid in grids)
        assert len({signature(grid) for grid in grids}) >= 115
        strict_hits = sum(gen.strict_canonical_like(grid) == [] for grid in grids)
        assert strict_hits >= 35, (difficulty, strict_hits)
        canonical_profile_hits = sum(
            (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            in {(9, 10, 4), (10, 10, 4), (9, 11, 4), (10, 11, 4)}
            for grid in grids
        )
        assert canonical_profile_hits >= 20, (difficulty, canonical_profile_hits)

    random.seed(20261003)
    before = random.getstate()
    first = gen.generate(777, 19, difficulty="hard")
    after = random.getstate()
    second = gen.generate(777, 19, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(777, 19, difficulty="hard") == second


def test_shape_banks_match_their_declared_symmetry_classes():
    gen = load_generator()
    for class_name, bank in gen.SHAPE_BANKS.items():
        assert bank, class_name
        assert {gen._symmetry_class(shape) for shape in bank} == {class_name}


def test_canonical_size_area_shortcut_is_real_and_generated_counterexamples_exist():
    gen = load_generator()
    assert set(gen.CANONICAL_SHORTCUTS) == {"bbox_area_lookup"}
    shortcut = gen.CANONICAL_SHORTCUTS["bbox_area_lookup"]
    for pair in canonical_pairs():
        assert shortcut(pair["input"]) == pair["output"]

    counterexamples = []
    for sample_index in range(18):
        grid = gen.generate(424242, sample_index, difficulty="medium")
        if shortcut(grid) != gen.rule_mirror(grid):
            counterexamples.append(grid)
    assert counterexamples
    assert all(
        gen.SEMANTIC_WITNESSES["bbox_area_shortcut_counterexample"](grid)
        for grid in counterexamples
    )


def test_every_consecutive_three_demo_window_refutes_every_named_competitor():
    gen = load_generator()
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.SCHEDULE_PROFILES) == {
        "canonical_lr",
        "bbox_trap",
        "canonical_ud",
    }
    for difficulty in ("easy", "medium", "hard"):
        pairs = []
        for sample_index in range(18):
            grid = gen.generate(998877, sample_index, difficulty=difficulty)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for start in range(15):
            demos = pairs[start : start + gen.EXAMPLES_NEEDED]
            query = pairs[start + gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == [], (difficulty, start)
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert not all(
                    competitor(pair["input"]) == pair["output"] for pair in demos
                ), (difficulty, start, name)


def test_each_witness_names_a_real_rival_disagreement():
    gen = load_generator()
    assert set(gen.WITNESS_RIVALS) == set(gen.SEMANTIC_WITNESSES)
    grids = [gen.generate(123456, index) for index in range(18)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        firing = [grid for grid in grids if gen.SEMANTIC_WITNESSES[witness_name](grid)]
        assert firing, witness_name
        for grid in firing:
            authority = gen.rule_mirror(grid)
            assert any(
                gen.SEMANTIC_RIVALS[name](grid) != authority
                for name in rival_names
            )


def test_self_check_rejects_malformed_and_targeted_impostors():
    gen = load_generator()
    for malformed in (None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(9)]):
        assert gen.self_check(malformed)

    valid = gen.generate(314159, 4, grid_h=9, grid_w=10, n_objects=3)

    touching = copy.deepcopy(valid)
    comps = gen._components_nonzero(touching)
    victim_color, victim_cells = comps[0]
    other_color, other_cells = comps[1]
    vr, vc = victim_cells[0]
    injected = None
    for rr, cc in other_cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = rr + dr, cc + dc
                if (
                    0 <= nr < len(touching)
                    and 0 <= nc < len(touching[0])
                    and touching[nr][nc] == 0
                    and abs(nr - vr) + abs(nc - vc) > 1
                ):
                    touching[nr][nc] = victim_color
                    injected = (nr, nc)
                    break
            if injected:
                break
        if injected:
            break
    assert injected is not None

    repeated_color = copy.deepcopy(valid)
    color_a, cells_a = gen._components_nonzero(repeated_color)[0]
    color_b, cells_b = gen._components_nonzero(repeated_color)[1]
    for r, c in cells_b:
        repeated_color[r][c] = color_a

    too_small = [[0 for _ in range(10)] for _ in range(9)]
    too_small[0][0] = 1
    too_small[0][5] = 2
    too_small[8][9] = 3

    assert gen.self_check(touching)
    assert gen.self_check(repeated_color)
    assert gen.self_check(too_small)


def test_four_pair_lessons_refute_competitors_under_every_query_rotation():
    """A counterexample must not disappear merely because it becomes the query."""
    gen = load_generator()
    for difficulty in ("easy", "medium", "hard"):
        for block in range(8):
            pairs = []
            start = block * 4
            for sample_index in range(start, start + 4):
                grid = gen.generate(606060 + block, sample_index, difficulty=difficulty)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == [], (
                    difficulty,
                    block,
                    query_index,
                    [gen.schedule_profile(606060 + block, start + i, difficulty) for i in range(4)],
                )


def test_task_local_semantic_probe_covers_rotations_and_joint_override_domain():
    probe_path = GENERATOR_DIR / "workspace" / "semantic_probe.py"
    spec = importlib.util.spec_from_file_location("semantic_probe_5a40", probe_path)
    probe = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(probe)
    report = probe.run_probe(lessons_per_band=3)
    assert report["status"] == "PASS"
    assert report["canonical_shortcut"]["canonical_pairs_fit"] == 4
    assert report["exact_overrides"]["accepted"] == 6 * 7 * 2 * 3
    assert report["exact_overrides"]["failures"] == []
    for band in ("easy", "medium", "hard"):
        cell = report["per_band"][band]
        assert cell["production_lessons"] == 3
        assert cell["production_unidentifiable"] == []
        assert cell["cyclic_rotations"] == 12
        assert cell["cyclic_unidentifiable"] == []


def test_generated_source_palette_keeps_rule_result_colors_reserved():
    gen = load_generator()
    result_colors = {2, 3, 4, 6}
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(24):
            grid = gen.generate(515151, sample_index, difficulty=difficulty)
            source_colors = {value for row in grid for value in row if value != 0}
            assert source_colors.isdisjoint(result_colors), (
                difficulty,
                sample_index,
                source_colors & result_colors,
            )
