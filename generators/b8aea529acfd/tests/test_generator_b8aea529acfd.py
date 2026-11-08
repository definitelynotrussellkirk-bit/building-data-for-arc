from __future__ import annotations

import importlib.util
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "b8aea529acfd"
ROOT = find_root(__file__)
GENERATOR_PATH = next(
    path for path in (
        ROOT / "generators" / TASK / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
    ) if path.is_file()
)
SPEC = importlib.util.spec_from_file_location("anchor_generator", GENERATOR_PATH)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_inputs_are_owned():
    assert gen.RULE_HASH == "8e26e8f07755"
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_schedule_is_strict_observable_and_semantically_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        made = []
        for sample_index in range(12):
            grid = gen.generate(7301, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.observe_overrides(grid)["scene_profile"] == gen.schedule_profile(
                7301, sample_index, difficulty
            )
            made.append(_pair(grid))
        for start in range(len(made) - gen.EXAMPLES_NEEDED):
            demos = made[start:start + gen.EXAMPLES_NEEDED]
            query = made[start + gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == []


def test_every_scene_profile_override_round_trips_and_unknown_keys_reject():
    for profile in gen.SCENE_PROFILES:
        grid = gen.generate(91, 7, difficulty="hard", scene_profile=profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.self_check(grid, meta={"overrides": {"scene_profile": profile}}) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __typo_axis__="x")
    with pytest.raises(ValueError):
        gen.generate(1, 0, scene_profile="not_a_profile")


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(1234567)
    state = random.getstate()
    a = gen.generate(44, 3, difficulty="medium")
    assert random.getstate() == state
    b = gen.generate(44, 3, difficulty="medium")
    assert a == b
    assert a is not b
    assert all(row_a is not row_b for row_a, row_b in zip(a, b))
    a[0][0] = 9
    assert gen.generate(44, 3, difficulty="medium") == b


def test_self_check_rejects_four_targeted_impostors():
    valid = gen.generate(808, 0, difficulty="easy")

    # 1. Remove all padding: the rule would no longer demonstrate cropping.
    fills_grid = gen._crop(valid)
    assert any("padding" in msg for msg in gen.self_check(fills_grid))

    # 2. Add a third foreground color inside the body.
    third_color = [row[:] for row in valid]
    r0, c0, _, _ = gen._bbox(third_color)
    existing = {v for row in third_color for v in row}
    new_color = next(c for c in range(1, 10) if c not in existing)
    third_color[r0][c0] = new_color
    assert any("two foreground colors" in msg for msg in gen.self_check(third_color))

    # 3. Make the crop horizontally symmetric, hiding flip-lr.
    symmetric = [row[:] for row in valid]
    r0, c0, r1, c1 = gen._bbox(symmetric)
    for r in range(r0, r1 + 1):
        for off in range((c1 - c0 + 1) // 2):
            symmetric[r][c1 - off] = symmetric[r][c0 + off]
    assert any("LR-symmetric" in msg for msg in gen.self_check(symmetric))

    # 4. Delete the foreground entirely.
    blank = [[0 for _ in row] for row in valid]
    assert any("foreground" in msg for msg in gen.self_check(blank))


def test_canonically_refuted_rivals_are_killed_by_every_ordinary_draw():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(8):
            grid = gen.generate(20260815, sample_index, difficulty=difficulty)
            truth = _freeze(gen.rule_mirror(grid))
            for name, rival in gen.SEMANTIC_RIVALS.items():
                if name in gen.CANONICAL_SHORTCUTS:
                    continue  # These are refuted by complete lesson windows.
                assert _freeze(rival(grid)) != truth
