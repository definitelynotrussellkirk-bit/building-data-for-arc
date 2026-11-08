"""Task-local regressions for cf6ef609da0d."""
from __future__ import annotations

from collections import deque
import importlib

import pytest


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.cf6ef609da0d.generator"
)


def _components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 6}
    result = []
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)
        result.append(component)
    return result


def test_exact_n_components_override_is_observable():
    grid = gen.generate(7, 7, difficulty="medium", n_components=5)
    assert len(_components(grid)) == 5
    assert gen.observe_overrides(grid)["n_components"] == 5


def _touches_diagonal(component):
    return any(row == col for row, col in component)


def _bbox_intersects_diagonal(component):
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    return max(min(rows), min(cols)) <= min(max(rows), max(cols))


def _profile(grid):
    components = _components(grid)
    return (
        "mixed_bbox"
        if any(_touches_diagonal(component) for component in components)
        else "none_on_diagonal"
    )


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("scene_pattern", ["mixed_bbox", "none_on_diagonal"])
def test_all_exact_overrides_are_realized_in_every_band(band, scene_pattern):
    expected = {
        "grid_h": 8,
        "grid_w": 14,
        "n_components": 5,
        "scene_pattern": scene_pattern,
    }
    grid = gen.generate(19, 11, difficulty=band, **expected)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == expected
    assert len(grid) == 8
    assert len(grid[0]) == 14
    assert len(_components(grid)) == 5
    assert _profile(grid) == scene_pattern


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 7},
        {"grid_w": 15},
        {"n_components": 1},
        {"n_components": 6},
        {"grid_h": True},
        {"n_components": 3.0},
        {"scene_pattern": "not-a-profile"},
    ],
)
def test_invalid_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_canonical_pairs_remain_lawful_and_rule_bound():
    from reviewer_support import canonical_pairs, find_root

    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("sample_index", range(12))
def test_schedule_alternates_two_teaching_profiles(sample_index):
    grid = gen.generate(31, sample_index, difficulty="medium")
    expected = gen.SCHEDULE_PROFILES[sample_index % len(gen.SCHEDULE_PROFILES)]
    assert gen.schedule_profile(31, sample_index, "medium") == expected
    assert gen.observe_overrides(grid)["scene_pattern"] == expected


def test_mixed_profile_contains_real_cell_touch_and_bbox_only_trap():
    grid = gen.generate(41, 0, scene_pattern="mixed_bbox", n_components=4)
    components = _components(grid)
    assert any(_touches_diagonal(component) for component in components)
    traps = [
        component
        for component in components
        if not _touches_diagonal(component)
        and _bbox_intersects_diagonal(component)
    ]
    assert traps
    assert gen.SEMANTIC_WITNESSES["bbox_without_cell_touch"](grid)
    assert gen.SEMANTIC_RIVALS["bbox_diagonal"](grid) != gen.rule_mirror(grid)


def test_none_profile_teaches_the_no_touch_branch():
    grid = gen.generate(43, 1, scene_pattern="none_on_diagonal", n_components=4)
    assert not any(_touches_diagonal(component) for component in _components(grid))
    assert all(value == 0 for row in gen.rule_mirror(grid) for value in row)
    assert gen.SEMANTIC_WITNESSES["no_component_touches_diagonal"](grid)
    assert gen.SEMANTIC_RIVALS["nearest_diagonal"](grid) != gen.rule_mirror(grid)


def test_default_support_includes_component_sizes_one_through_four():
    sizes = set()
    for index in range(32):
        grid = gen.generate(101 + index, index, difficulty="medium")
        assert gen.self_check(grid) == []
        sizes.update(len(component) for component in _components(grid))
    assert sizes == {1, 2, 3, 4}


def test_five_pair_schedule_is_identifiable_under_every_query_rotation():
    assert gen.EXAMPLES_NEEDED == 4
    assert gen.LESSON_SCHEDULE_PERIOD == 5
    assert gen.SCHEDULE_PROFILES == (
        "mixed_bbox",
        "none_on_diagonal",
        "mixed_bbox",
        "none_on_diagonal",
        "mixed_bbox",
    )
    pairs = []
    for index in range(5):
        grid = gen.generate(211, index, difficulty="medium")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    for query_index in range(5):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_negative_branch_is_below_half_of_default_schedule():
    profiles = [gen.schedule_profile(0, index, "medium") for index in range(20)]
    assert profiles.count("none_on_diagonal") == 8
    assert profiles.count("none_on_diagonal") < len(profiles) / 2


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0], [0, 0]],
        [[0] * 8 for _ in range(8)],
        [[6] + [0] * 7 for _ in range(8)],
        [[True] * 8 for _ in range(8)],
    ],
)
def test_self_check_rejects_malformed_or_non_task_inputs(grid):
    assert gen.self_check(grid)


def test_generation_is_deterministic_and_does_not_share_rows():
    first = gen.generate(313, 9, difficulty="hard")
    second = gen.generate(313, 9, difficulty="hard")
    assert first == second
    if len(first) > 1:
        original = second[1][0]
        first[0][0] = 9
        assert second[1][0] == original


def test_all_background_negative_branch_has_explicit_task_justification():
    grid = gen.generate(701, 1, scene_pattern="none_on_diagonal")
    assert all(value == 0 for row in gen.rule_mirror(grid) for value in row)
    assert len(gen.SOLID_OUTPUT_JUSTIFICATION.strip()) >= 30


def test_difficulty_changes_the_default_distribution_not_exact_overrides():
    draws = [gen.generate(719, 7, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({repr(grid) for grid in draws}) == 3


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_has_a_deterministic_canonical_size_anchor(band):
    grid = gen.generate(811, 0, difficulty=band)
    assert (len(grid), len(grid[0])) in {(9, 9), (10, 10)}
    assert gen.self_check(grid) == []


def test_every_cyclic_schedule_start_survives_every_query_rotation():
    for start in range(gen.LESSON_SCHEDULE_PERIOD):
        pairs = []
        for offset in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(877, start + offset, difficulty="medium")
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for query_index in range(len(pairs)):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_saved_semantic_counterexamples_remain_minimal_and_distinguishing():
    import hashlib
    import json
    from pathlib import Path

    from reviewer_support import find_root

    root = Path(find_root(__file__))
    generator_path = root / "generators" / gen.TASK_ID / "generator.py"
    counterexample_path = (
        root
        / "generators"
        / gen.TASK_ID
        / "counterexamples"
        / "review-3400f37203458cb4"
        / "semantic-shortcuts.json"
    )
    payload = json.loads(counterexample_path.read_text(encoding="utf-8"))
    assert payload["task_id"] == gen.TASK_ID
    assert payload["rule_hash"] == gen.RULE_HASH
    assert payload["generator_sha256"] == hashlib.sha256(
        generator_path.read_bytes()
    ).hexdigest()

    cases = {case["id"]: case for case in payload["cases"]}
    assert set(cases) == {
        "bbox_intersection_without_occupied_touch",
        "nearest_component_when_nothing_touches",
    }
    for case in cases.values():
        grid = case["input"]
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == case["expected_output"]
        rival = gen.SEMANTIC_RIVALS[case["rival"]]
        assert rival(grid) == case["rival_output"]
        assert case["rival_output"] != case["expected_output"]

    bbox = cases["bbox_intersection_without_occupied_touch"]
    assert gen.SEMANTIC_WITNESSES["bbox_without_cell_touch"](bbox["input"])
    nearest = cases["nearest_component_when_nothing_touches"]
    assert gen.SEMANTIC_WITNESSES["no_component_touches_diagonal"](
        nearest["input"]
    )


def test_workspace_generation_profiler_emits_source_bound_report(tmp_path):
    import hashlib
    import json
    from pathlib import Path
    import subprocess
    import sys

    from reviewer_support import find_root

    root = Path(find_root(__file__))
    script = root / "generators" / gen.TASK_ID / "workspace" / "profile_generate.py"
    output = tmp_path / "profile.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--seeds",
            "2",
            "--output",
            str(output),
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["task_id"] == gen.TASK_ID
    assert report["generator_sha256"] == hashlib.sha256(
        (root / "generators" / gen.TASK_ID / "generator.py").read_bytes()
    ).hexdigest()
    assert report["bands"] == ["easy", "medium", "hard"]
    assert report["requested_seeds_per_band"] == 2
    assert len(report["draws"]) == 6
    assert report["failures"] == []
    assert all(draw["elapsed_seconds"] >= 0 for draw in report["draws"])
