from __future__ import annotations

import importlib.util
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GEN_PATH = ROOT / "puzzle_generators/per_puzzle/3025c0637069/generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generator_3025c0637069", GEN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



def test_all_canonical_pairs_are_accepted_and_reproduced():
    gen = load_generator()
    from scripts.canonical_profile_gate import canonical_pairs

    for pair in canonical_pairs("3025c0637069"):
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._solve_grid(pair["input"]) == pair["output"]


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    gen = load_generator()
    random.seed(99173)
    state = random.getstate()
    first = gen.generate(8142, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(8142, 7, difficulty="hard")
    assert first == second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(8142, 7, difficulty="hard") == second


def test_exact_overrides_are_observable_and_unknown_keys_fail():
    gen = load_generator()
    cases = [
        dict(canvas_kind="canonical", shape_height=8, shape_width=8,
             rect_height=3, rect_width=3, occluder_side="left",
             position_bias="left", palette_pair="p12"),
        dict(canvas_kind="expanded", shape_height=10, shape_width=9,
             rect_height=5, rect_width=4, occluder_side="right",
             position_bias="right", palette_pair="p91"),
        dict(canvas_kind="canonical", shape_height=9, shape_width=10,
             rect_height=4, rect_width=4, occluder_side="right",
             position_bias="center", palette_pair="p56"),
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(1200 + index, 17 + index, difficulty="medium", **overrides)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        assert observed == overrides
    try:
        gen.generate(1, 1, misspelled_axis="left")
    except ValueError as exc:
        assert "unknown override" in str(exc)
    else:
        raise AssertionError("unknown override key was accepted")


def test_structural_mutations_are_rejected():
    gen = load_generator()
    grid = gen.generate(771, 0, difficulty="medium")
    analysis, errors = gen._analyze(grid)
    assert errors == [] and analysis is not None
    rr0, rc0, rr1, rc1 = analysis["rect_bbox"]
    shape = analysis["shape_color"]
    rect = analysis["rect_color"]
    axis2 = analysis["axis2"]

    asymmetric = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            mc = axis2 - c
            if value == shape and not (rr0 <= r <= rr1 and rc0 <= mc <= rc1):
                asymmetric[r][c] = 0
                break
        else:
            continue
        break
    assert gen.self_check(asymmetric)

    broken_rectangle = [row[:] for row in grid]
    broken_rectangle[rr0][rc0] = 0
    assert gen.self_check(broken_rectangle)

    one_color = [[rect if value == shape else value for value in row] for row in grid]
    assert gen.self_check(one_color)

    non_rectangular_occluder = [row[:] for row in grid]
    add_c = rc1 + 1 if rc1 + 1 < len(grid[0]) else rc0 - 1
    non_rectangular_occluder[rr0][add_c] = rect
    assert gen.self_check(non_rectangular_occluder)


def test_two_demo_schedule_refutes_declared_shortcuts():
    gen = load_generator()
    pairs = []
    for sample_index in range(3):
        grid = gen.generate(9090, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": gen._solve_grid(grid)})
    assert gen.lesson_identifiable(pairs[:2], pairs[2]) == []
    for rival_name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:2]), rival_name
