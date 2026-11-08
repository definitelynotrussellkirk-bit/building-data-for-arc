from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
import sys

import pytest


HERE = Path(__file__).resolve()
try:
    from reviewer_support import canonical_pairs, find_root
except ModuleNotFoundError:
    # Direct-repository fallback. Portable task-test runtimes expose
    # reviewer_support on PYTHONPATH and therefore never depend on source depth.
    for ancestor in HERE.parents:
        candidate = ancestor / "shared" / "runtime"
        if (candidate / "reviewer_support.py").is_file():
            sys.path.insert(0, str(candidate))
            break
    from reviewer_support import canonical_pairs, find_root


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HERE.parents[1] / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
ROOT = find_root(__file__)
CANONICAL = canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)


def _axis_values(name: str) -> tuple[str, ...]:
    raw = gen.AXES[name]["valid"]
    if isinstance(raw, str):
        return tuple(part.strip() for part in raw.split("|") if part.strip())
    return tuple(raw)


def _copy(grid):
    return [list(row) for row in grid]


def test_axes_metadata_is_a_static_literal_for_the_repository_linter():
    tree = ast.parse(Path(gen.__file__).read_text(encoding="utf-8"))
    axes_node = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    )
    assert isinstance(ast.literal_eval(axes_node), dict)


def test_selected_rule_is_pinned_and_python_oracle_matches_every_canonical_label():
    assert gen.RULE_HASH == "64fd3246321b"
    assert CANONICAL
    for pair in CANONICAL:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_override_contract_is_exact_for_every_declared_combination_and_band():
    assert set(gen.AXES) == {"canvas_profile", "density"}
    profiles = _axis_values("canvas_profile")
    densities = _axis_values("density")
    assert len(profiles) >= 4
    assert densities == ("sparse", "balanced", "dense")

    case_index = 0
    for band in ("easy", "medium", "hard"):
        for profile in profiles:
            for density in densities:
                grid = gen.generate(
                    910_000 + case_index,
                    case_index,
                    difficulty=band,
                    canvas_profile=profile,
                    density=density,
                )
                assert gen.self_check(grid) == []
                assert gen.observe_overrides(grid) == {
                    "canvas_profile": profile,
                    "density": density,
                }
                case_index += 1


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, density_typo="sparse")
    with pytest.raises(ValueError, match="canvas_profile"):
        gen.generate(1, 0, canvas_profile="not-a-profile")
    with pytest.raises(ValueError, match="density"):
        gen.generate(1, 0, density="not-a-density")


def test_difficulty_changes_default_curriculum_without_restricting_axes():
    grids = [gen.generate(314159, 7, difficulty=band) for band in ("easy", "medium", "hard")]
    serialized = {tuple(tuple(row) for row in grid) for grid in grids}
    assert len(serialized) == 3


def test_schedule_covers_both_lesson_profiles_and_canonical_exact_profiles():
    schedule = [gen.schedule_profile(123, i, "hard") for i in range(12)]
    assert set(schedule) == set(gen.SCHEDULE_PROFILES)

    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in CANONICAL
    }
    generated_profiles = []
    for index in range(12):
        grid = gen.generate(123, index, difficulty="hard")
        assert gen.self_check(grid) == []
        generated_profiles.append(
            (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        )
    assert canonical_profiles <= set(generated_profiles)


def test_every_declared_semantic_witness_has_a_real_counterexample():
    fired = set()
    for index in range(12):
        grid = gen.generate(77, index, difficulty=("easy", "medium", "hard")[index % 3])
        truth = gen.rule_mirror(grid)
        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
            if witness(grid):
                fired.add(witness_name)
                rival_names = gen.WITNESS_RIVALS[witness_name]
                if isinstance(rival_names, str):
                    rival_names = [rival_names]
                assert any(gen.SEMANTIC_RIVALS[name](grid) != truth for name in rival_names)
    assert fired == set(gen.SEMANTIC_WITNESSES)


def test_every_three_of_four_rotation_identifies_the_rule():
    lesson = []
    for index in range(4):
        grid = gen.generate(20261006, index, difficulty=("easy", "medium", "hard", "medium")[index])
        lesson.append({"input": grid, "output": gen.rule_mirror(grid)})

    for query_index, query in enumerate(lesson):
        demos = [pair for index, pair in enumerate(lesson) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []


def test_structural_self_check_rejects_reproducible_corruptions():
    grid = gen.generate(
        44,
        0,
        canvas_profile=_axis_values("canvas_profile")[0],
        density="balanced",
    )
    analysis = gen._analyze(grid)
    assert gen.self_check(grid) == []

    broken_border = _copy(grid)
    frame = analysis["frames"][0]
    broken_border[frame["r1"]][frame["c1"]] = 0
    assert gen.self_check(broken_border)

    stray_pixel = _copy(grid)
    outside = next(
        (r, c)
        for r, row in enumerate(stray_pixel)
        for c, value in enumerate(row)
        if value == 0 and not any(
            f["r1"] < r < f["r2"] and f["c1"] < c < f["c2"]
            for f in analysis["frames"]
        )
    )
    stray_pixel[outside[0]][outside[1]] = 9
    assert gen.self_check(stray_pixel)

    duplicate_color = _copy(grid)
    first_color = analysis["frames"][0]["interior_color"]
    second = analysis["frames"][1]
    for r in range(second["r1"] + 1, second["r2"]):
        for c in range(second["c1"] + 1, second["c2"]):
            if duplicate_color[r][c] not in (0, 5):
                duplicate_color[r][c] = first_color
    assert any("distinct" in reason for reason in gen.self_check(duplicate_color))


def test_left_to_right_shortcut_fits_canonical_but_generated_conflict_refutes_it():
    shortcut = gen.CANONICAL_SHORTCUTS["left_to_right"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in CANONICAL)
    conflicts = [
        gen.generate(8, index)
        for index in range(8)
        if gen.schedule_profile(8, index) == "row_order_conflict"
    ]
    assert conflicts
    assert all(shortcut(grid) != gen.rule_mirror(grid) for grid in conflicts)
