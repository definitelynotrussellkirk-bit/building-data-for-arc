from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest
from reviewer_support import find_root, canonical_path

TASK = "a2d296c74658"
ROOT = find_root(__file__)
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

SPEC = importlib.util.spec_from_file_location(
    f"review_{TASK}", ROOT / "generators" / TASK / "generator.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CANONICAL = canonical_path(ROOT)


def _norm(grid):
    return [
        [int(ch) for ch in row] if isinstance(row, str) else list(row)
        for row in grid
    ]


def canonical_row():
    rows = [
        json.loads(line)
        for line in CANONICAL.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("task_id") == TASK
    ]
    assert len(rows) == 1
    return rows[0]


def canonical_pairs():
    row = canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def independent_oracle(grid):
    values = _norm(grid)
    out = [row[:] for row in values]
    h, w = len(values), len(values[0])
    for r in range(1, h - 1):
        for c in range(w):
            if values[r][c] == 0 and values[r - 1][c] == 7 and values[r + 1][c] == 7:
                out[r][c] = 4
    return out


def pair(grid):
    return {"input": grid, "output": independent_oracle(grid)}


def frozen(grid):
    return tuple(map(tuple, grid))


def test_rule_pin_and_exact_axis_surface_are_minimal():
    program = canonical_row()["program_solution"]
    normalized = " ".join(program.split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH
    assert MODULE.VERSION == "3.0.0"
    assert set(MODULE.AXES) == {"grid_h", "grid_w", "num_triplets"}
    assert MODULE.HELPFUL_TEXTURES == ()
    assert MODULE.DEGENERATE_TEXTURES == ()
    assert MODULE.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()


def test_every_canonical_input_is_owned_and_oracle_exact():
    signatures = {
        (7, 6): (2, [1, 1]),
        (8, 8): (2, [1, 1]),
        (9, 9): (2, [1, 1]),
        (10, 9): (3, [1, 1, 1]),
    }
    for raw in canonical_pairs():
        grid, expected = _norm(raw["input"]), _norm(raw["output"])
        analysis = MODULE._analysis(grid)
        dims = (len(grid), len(grid[0]))
        assert MODULE.self_check(grid) == []
        assert MODULE.strict_canonical_like(grid) == []
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == expected
        assert analysis["target_count"] == signatures[dims][0]
        assert sorted(count for count in analysis["column_target_counts"] if count) == signatures[dims][1]


def test_default_schedule_covers_all_anchors_and_complete_contrast_bundles():
    seen_profiles = set()
    strict_dims = set()
    contrast = []
    all_grids = []
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in range(32):
            seed = 100_000 + 101 * sample_index
            grid = MODULE.generate(seed, sample_index, difficulty=difficulty)
            all_grids.append(grid)
            seen_profiles.add(MODULE.schedule_profile(seed, sample_index, difficulty))
            assert MODULE.self_check(grid) == []
            assert MODULE.rule_mirror(grid) == independent_oracle(grid)
            analysis = MODULE._analysis(grid)
            assert MODULE.observe_overrides(grid) == {
                "grid_h": analysis["height"],
                "grid_w": analysis["width"],
                "num_triplets": analysis["target_count"],
            }
            if MODULE.strict_canonical_like(grid) == []:
                strict_dims.add((analysis["height"], analysis["width"]))
            else:
                contrast.append(grid)
    assert seen_profiles == set(MODULE.SCHEDULE_PROFILES)
    assert strict_dims == {(7, 6), (8, 8), (9, 9), (10, 9)}
    assert len(contrast) == len(all_grids) // 2
    assert len({frozen(grid) for grid in all_grids}) >= len(all_grids) * 0.85

    required = {
        "multiple_targets",
        "horizontal_7_gap_control",
        "long_vertical_gap_control",
        "blocked_midpoint_control",
        "wrong_color_vertical_control",
        "shared_endpoint_chain",
        "complete_contrast_bundle",
    }
    for grid in contrast:
        fired = {name for name, pred in MODULE.SEMANTIC_WITNESSES.items() if pred(grid)}
        assert required <= fired
        intended = MODULE.rule_mirror(grid)
        for rival in MODULE.SEMANTIC_RIVALS.values():
            assert rival(grid) != intended


def test_all_cartesian_exact_axis_boundaries_are_honored_and_observable():
    for h in (7, 10):
        for w in (6, 9):
            for num_triplets in (2, 4):
                for difficulty in (None, "easy", "medium", "hard"):
                    grid = MODULE.generate(
                        7301,
                        19,
                        difficulty=difficulty,
                        grid_h=h,
                        grid_w=w,
                        num_triplets=num_triplets,
                    )
                    assert MODULE.self_check(grid) == []
                    assert MODULE.observe_overrides(grid) == {
                        "grid_h": h,
                        "grid_w": w,
                        "num_triplets": num_triplets,
                    }
                    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


@pytest.mark.parametrize(
    "kwargs, error_type",
    [
        ({"unknown_axis": 1}, TypeError),
        ({"grid_h": 6}, ValueError),
        ({"grid_w": 10}, ValueError),
        ({"num_triplets": 1}, ValueError),
        ({"difficulty": "expert"}, ValueError),
        ({"grid_h": True}, ValueError),
    ],
)
def test_unknown_and_out_of_range_controls_fail_closed(kwargs, error_type):
    with pytest.raises(error_type):
        MODULE.generate(1, 0, **kwargs)


def test_each_three_demo_window_identifies_the_rule():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(24):
            pairs = []
            for offset in range(4):
                grid = MODULE.generate(50_000 + start, start + offset, difficulty=difficulty)
                pairs.append(pair(grid))
            assert MODULE.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_named_canonical_shortcuts_fit_canonical_and_are_refuted_generated():
    canonical = canonical_pairs()
    for name, shortcut in MODULE.CANONICAL_SHORTCUTS.items():
        assert name in MODULE.SEMANTIC_RIVALS
        assert all(shortcut(_norm(item["input"])) == _norm(item["output"]) for item in canonical)
        assert any(
            shortcut(MODULE.generate(90_000 + index, 8 * index + 1))
            != MODULE.rule_mirror(MODULE.generate(90_000 + index, 8 * index + 1))
            for index in range(8)
        )


def test_determinism_fresh_returns_and_global_random_isolation():
    random.seed(123_456)
    before = random.getstate()
    first = MODULE.generate(731, 19, difficulty="hard")
    assert random.getstate() == before
    second = MODULE.generate(731, 19, difficulty="hard")
    assert first == second
    assert first is not second and first[0] is not second[0]
    original = second[0][0]
    first[0][0] = 9
    assert second[0][0] == original
    assert MODULE.generate(731, 20, difficulty="hard") != second


def test_self_check_rejects_structural_mutations():
    grid = MODULE.generate(404, 1)
    broken = [row[:] for row in grid]
    r, c = MODULE._analysis(grid)["targets"][0]
    broken[r - 1][c] = 0
    assert MODULE.self_check(broken)

    malformed = [row[:] for row in grid]
    malformed[0] = malformed[0][:-1]
    assert MODULE.self_check(malformed)


def _same_color_object_count(grid):
    values = _norm(grid)
    h, w = len(values), len(values[0])
    seen = set()
    count = 0
    for r in range(h):
        for c in range(w):
            if values[r][c] == 0 or (r, c) in seen:
                continue
            count += 1
            color = values[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and values[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return count


def test_contrast_bundle_stays_within_three_times_canonical_object_count():
    # The strict defect gate compares same-color 4-connected components.  The
    # canonical training median is four, so every scheduled contrast bundle is
    # capped at 12 rather than relying on aggregate anchor/contrast averaging.
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in range(32):
            grid = MODULE.generate(910_000 + sample_index, sample_index, difficulty=difficulty)
            if MODULE.strict_canonical_like(grid):
                assert _same_color_object_count(grid) <= 12
