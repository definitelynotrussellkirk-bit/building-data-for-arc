from __future__ import annotations

import copy
import hashlib
import importlib.util
import os
import json
import random
from collections import deque
from pathlib import Path
from typing import Any

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "142a3a64b02a"
ROOT = find_root(__file__)

def _load_generator():
    home = Path(__file__).resolve().parents[1]
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", home / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_142a3a64b02a", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def pairs() -> list[dict[str, Any]]:
    return canonical_pairs(TASK_ID, root=ROOT, variant=0)


def canonical_source() -> str:
    candidates = (
        Path(ROOT) / "shared/data/canonical/puzzles.jsonl",
        Path(ROOT) / "data/canonical/puzzles.jsonl",
    )
    path = next(path for path in candidates if path.is_file())
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical source missing")


def red_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = next(iter(remaining))
        component = {start}
        queue = deque([start])
        remaining.remove(start)
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = row + drow, col + dcol
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def is_straight(component: set[tuple[int, int]]) -> bool:
    rows = {row for row, _ in component}
    cols = {col for _, col in component}
    return len(rows) == 1 or len(cols) == 1


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    out = copy.deepcopy(grid)
    for component in red_components(grid):
        if not is_straight(component):
            continue
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        row0, row1 = min(rows), max(rows)
        col0, col1 = min(cols), max(cols)
        if row0 == row1:
            out[row0][col0] = 4
            out[row0][col1] = 4
        else:
            out[row0][col0] = 4
            out[row1][col0] = 4
    return out


def recolor_each_maximal_run(grid: list[list[int]]) -> list[list[int]]:
    """Plausible shortcut: cap every maximal red row/column run separately."""
    out = copy.deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for row in range(height):
        col = 0
        while col < width:
            if grid[row][col] != 2:
                col += 1
                continue
            end = col
            while end + 1 < width and grid[row][end + 1] == 2:
                end += 1
            if end - col + 1 >= 2:
                out[row][col] = out[row][end] = 4
            col = end + 1
    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] != 2:
                row += 1
                continue
            end = row
            while end + 1 < height and grid[end + 1][col] == 2:
                end += 1
            if end - row + 1 >= 2:
                out[row][col] = out[end][col] = 4
            row = end + 1
    return out


def test_rule_hash_is_pinned_to_normalized_canonical_source():
    expected = hashlib.sha256(" ".join(canonical_source().split()).encode()).hexdigest()[:12]
    assert expected == "ffb5719ce1e2"
    assert gen.RULE_HASH == expected


def test_python_mirror_and_self_check_cover_every_canonical_pair():
    canonical = pairs()
    assert len(canonical) == 5
    for pair in canonical:
        assert gen.self_check(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_strongest_train_only_shortcut_fits_demos_but_fails_heldout_t_shape():
    canonical = pairs()
    training = [pair for pair in canonical if pair["split"] == "train"]
    heldout = [pair for pair in canonical if pair["split"] == "test"]
    assert len(training) == 4 and len(heldout) == 1
    assert all(recolor_each_maximal_run(pair["input"]) == pair["output"] for pair in training)
    assert recolor_each_maximal_run(heldout[0]["input"]) != heldout[0]["output"]
    assert independent_rule(heldout[0]["input"]) == heldout[0]["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_normal_draw_teaches_straight_object_and_nonstraight_object_boundary(difficulty):
    for index in range(24):
        grid = gen.generate(12000 + index, index, difficulty=difficulty)
        original = copy.deepcopy(grid)
        components = red_components(grid)
        assert any(is_straight(component) for component in components)
        assert any(not is_straight(component) for component in components)
        assert gen.self_check(grid, difficulty=difficulty) == []
        expected = independent_rule(grid)
        assert gen.rule_mirror(grid) == expected
        assert expected != grid
        assert recolor_each_maximal_run(grid) != expected
        assert grid == original


def test_exact_overrides_are_observable_at_boundaries_and_profiles():
    for height, width in ((7, 8), (7, 13), (12, 8), (12, 13)):
        for profile in gen.SCENE_PROFILES:
            grid = gen.generate(
                451,
                9,
                difficulty="hard",
                grid_h=height,
                grid_w=width,
                scene_profile=profile,
            )
            assert gen.observe_overrides(grid) == {
                "grid_h": height,
                "grid_w": width,
                "scene_profile": profile,
            }
            assert gen.self_check(grid) == []


def test_three_consecutive_examples_cover_the_nonstraight_profile_schedule():
    for start in range(9):
        observed = {
            gen.observe_overrides(gen.generate(77, index))["scene_profile"]
            for index in range(start, start + 3)
        }
        assert observed == set(gen.SCENE_PROFILES)


def test_generated_lessons_falsify_declared_rivals():
    for difficulty in ("easy", "medium", "hard"):
        lesson = []
        for index in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(8080, index, difficulty=difficulty)
            lesson.append({"input": grid, "output": independent_rule(grid)})
        assert gen.lesson_identifiable(lesson[:-1], lesson[-1]) == []


def test_determinism_fresh_returns_and_global_random_state():
    random.seed(90210)
    state = random.getstate()
    first = gen.generate(19, 23, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(19, 23, difficulty="hard")
    assert first == second
    assert first is not second and all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(19, 23, difficulty="hard") == second


def test_self_check_rejects_minimal_impostors_and_malformed_values():
    impostors = {
        "all_background": [[0] * 8 for _ in range(7)],
        "singleton": [[2] + [0] * 7] + [[0] * 8 for _ in range(6)],
        "short_line": [[2, 2] + [0] * 6] + [[0] * 8 for _ in range(6)],
        "solid_2x2": [[2, 2] + [0] * 6, [2, 2] + [0] * 6] + [[0] * 8 for _ in range(5)],
        "boolean_cell": [[False] + [0] * 7] + [[0] * 8 for _ in range(6)],
        "ragged": [[0] * 8, [0] * 7],
    }
    for name, grid in impostors.items():
        assert gen.self_check(grid), name


def test_unknown_impossible_overrides_and_difficulty_fail_loudly():
    with pytest.raises(ValueError, match="unsupported override"):
        gen.generate(1, 1, unknown_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 1, difficulty="nightmare")
    with pytest.raises(ValueError):
        gen.generate(1, 1, grid_h=6)
    with pytest.raises(ValueError):
        gen.generate(1, 1, scene_profile="circle")


def test_workspace_semantic_audit_rotates_every_query_without_leaving_a_rival_alive():
    tool_path = Path(__file__).resolve().parents[1] / "workspace" / "semantic_audit.py"
    spec = importlib.util.spec_from_file_location("semantic_audit_142a3a64b02a", tool_path)
    assert spec is not None and spec.loader is not None
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)

    report = tool.audit_generator(
        gen,
        generator_path=Path(gen.__file__),
        bands=("easy",),
        seeds=range(2),
        starts=range(3),
    )
    assert report["lessons"] == 6
    assert report["rotations"] == 24
    assert report["failure_count"] == 0
    assert report["unique_inputs"] == 12
    assert report["rivals"] == sorted(gen.LESSON_COMPETITORS)
