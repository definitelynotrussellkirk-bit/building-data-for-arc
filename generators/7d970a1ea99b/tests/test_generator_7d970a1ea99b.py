from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "7d970a1ea99b"
ROOT = find_root(__file__)
GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load(GENERATOR, "_generator_7d970a1ea99b_test")


def _transpose_conflicts(grid):
    conflicts = []
    for r in range(len(grid)):
        for c in range(r + 1, len(grid)):
            a, b = grid[r][c], grid[c][r]
            if a and b:
                conflicts.append((r, c, a, b))
    return conflicts


def test_canonical_program_identity_and_all_original_pairs(gen):
    assert gen.RULE_HASH == "2b970065d6a3"
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_generation_removes_transpose_collisions_and_exercises_both_triangles(gen):
    seen_diagonal = False
    seen_upper = False
    seen_lower = False
    for difficulty in ("easy", "medium", "hard", None):
        for seed in range(12):
            for index in range(8):
                grid = gen.generate(seed, index, difficulty=difficulty)
                assert gen.self_check(grid, difficulty=difficulty) == []
                assert _transpose_conflicts(grid) == []
                assert gen.rule_mirror(grid) != grid
                seen_diagonal |= any(grid[i][i] for i in range(len(grid)))
                seen_upper |= any(grid[r][c] for r in range(len(grid)) for c in range(r + 1, len(grid)) if grid[r][c])
                seen_lower |= any(grid[c][r] for r in range(len(grid)) for c in range(r + 1, len(grid)) if grid[c][r])
    assert seen_diagonal and seen_upper and seen_lower


def test_exact_override_contract_and_rejections(gen):
    grid = gen.generate(
        91,
        2,
        difficulty="easy",
        side=16,
        n_off_diagonal=12,
        n_diagonal=3,
    )
    assert gen.observe_overrides(grid) == {
        "side": 16,
        "n_off_diagonal": 12,
        "n_diagonal": 3,
    }
    assert gen.self_check(grid, meta={"overrides": gen.observe_overrides(grid)}) == []

    for kwargs in (
        {"unknown": 1},
        {"side": 5},
        {"n_off_diagonal": 2},
        {"n_diagonal": 4},
        {"side": True},
        {"n_off_diagonal": 3.0},
    ):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 0, **kwargs)


def test_call_identity_scalars_are_exact_and_sample_index_is_nonnegative(gen):
    for bad_seed in (True, False, 1.0, 1.75, "1"):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(bad_seed, 0, difficulty="easy")

    for bad_index in (True, False, 1.0, 1.75, "1", -1):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(991, bad_index, difficulty="easy")

    # Negative integer seeds remain deterministic, while valid indexes start at zero.
    assert gen.generate(-7, 0, difficulty="easy") == gen.generate(-7, 0, difficulty="easy")


def test_self_check_rejects_collision_and_identity_impostors(gen):
    collision = [[0] * 6 for _ in range(6)]
    collision[1][4] = 2
    collision[4][1] = 7
    collision[0][2] = 3
    assert any("transpose pair" in reason for reason in gen.self_check(collision))

    identity = [[0] * 6 for _ in range(6)]
    identity[1][4] = identity[4][1] = 2
    identity[2][2] = 3
    reasons = gen.self_check(identity)
    assert any("change" in reason or "one-sided" in reason for reason in reasons)


def test_generated_lesson_refutes_declared_shortcuts(gen):
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(301, index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(301, gen.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(copy.deepcopy(demos), copy.deepcopy(query)) == []
    assert any(gen.SEMANTIC_WITNESSES["lower_triangle_source"](pair["input"]) for pair in demos)
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert not all(rival(pair["input"]) == pair["output"] for pair in demos), name


def test_declared_canonical_shortcut_is_real_but_generated_counterexample_exists(gen):
    shortcut = gen.CANONICAL_SHORTCUTS["upper_triangle_only"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True))
    generated = [gen.generate(811, index, difficulty="hard") for index in range(8)]
    assert any(shortcut(grid) != gen.rule_mirror(grid) for grid in generated)
