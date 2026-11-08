"""Source-bound contract tests for ARC generator 067449d7a3b3.

The tests inspect returned pixels, canonical examples, executable rivals, and
selected authority text.  They intentionally do not trust GenCtx bookkeeping.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "067449d7a3b3"
TASK_DIR = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_067449d7a3b3_under_test", TASK_DIR / "generator.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=ROOT, variant=0)


def _signature(grid):
    return tuple(tuple(row) for row in grid)


def _components8(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            todo = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if not (dr or dc):
                            continue
                        point = (r + dr, c + dc)
                        if (
                            0 <= point[0] < h
                            and 0 <= point[1] < w
                            and point not in seen
                            and grid[point[0]][point[1]] != 0
                        ):
                            seen.add(point)
                            todo.append(point)
            components.append(cells)
    return components


def _canonical_program():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                return row["program_solution"]
    raise AssertionError("canonical program missing")


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == "fb156b8e3aee"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", ["canonical", "counterexample"])
def test_exact_overrides_are_observable_in_returned_pixels(band, profile):
    requested = {
        "grid_h": 10,
        "grid_w": 10,
        "n_objects": 4,
        "scene_profile": profile,
    }
    grid = gen.generate(1701, 13, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 9},
        {"grid_h": 31},
        {"grid_w": 9},
        {"grid_w": 31},
        {"n_objects": 1},
        {"n_objects": 5},
        {"scene_profile": "unknown"},
        {"grid_h": True},
        {"grid_h": 10.0},
        {"grid_w": "10"},
        {"n_objects": False},
        {"scene_profile": 1},
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("difficulty", ["", "normal", 0, 0.5, True])
def test_rejects_undeclared_difficulty_values(difficulty):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=difficulty)


def test_full_axis_boundaries_are_constructive_in_every_band():
    cases = [
        (10, 10, 2, "canonical"),
        (10, 30, 4, "counterexample"),
        (30, 10, 4, "canonical"),
        (30, 30, 2, "counterexample"),
    ]
    for band in (None, "easy", "medium", "hard"):
        for index, (h, w, count, profile) in enumerate(cases):
            requested = {
                "grid_h": h,
                "grid_w": w,
                "n_objects": count,
                "scene_profile": profile,
            }
            grid = gen.generate(730 + index, index, difficulty=band, **requested)
            assert gen.observe_overrides(grid) == requested
            assert gen.self_check(grid) == []


def test_generation_is_deterministic_and_schedule_is_explicit():
    assert set(gen.SCHEDULE_PROFILES) == {"canonical", "counterexample"}
    expected = ["canonical", "counterexample", "counterexample", "canonical"]
    for band in (None, "easy", "medium", "hard"):
        for index in range(12):
            first = gen.generate(9917, index, difficulty=band)
            second = gen.generate(9917, index, difficulty=band)
            assert first == second
            assert gen.schedule_profile(9917, index, difficulty=band) == expected[index % 4]
            assert gen.observe_overrides(first)["scene_profile"] == expected[index % 4]


def test_adjacent_counterexamples_are_structurally_distinct_for_one_seed():
    # run_one rejects duplicate labelled pairs and advances to the next index.
    # The two X slots must therefore differ by construction, not by lucky color RNG.
    seeds = (198222630054986, 17, 9917)
    for band in ("easy", "medium", "hard"):
        for seed in seeds:
            for cycle in range(4):
                left = gen.generate(seed, 4 * cycle + 1, difficulty=band)
                right = gen.generate(seed, 4 * cycle + 2, difficulty=band)
                assert left != right
                assert gen._mirror(left) != gen._mirror(right)


def test_default_bands_include_exact_canonical_dimension_palette_profiles():
    expected_shape = {"easy": (10, 10), "medium": (20, 20), "hard": (30, 30)}
    for band, shape in expected_shape.items():
        grid = gen.generate(41, 0, difficulty=band)
        assert (len(grid), len(grid[0])) == shape
        assert set(value for row in grid for value in row) == {0, 9}
        assert gen.observe_overrides(grid)["scene_profile"] == "canonical"


@pytest.mark.parametrize("pair", PAIRS)
def test_canonical_inputs_are_accepted_and_python_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen._mirror(pair["input"]) == pair["output"]


def test_canonical_profile_reaches_canonical_maximum_six_by_six_object():
    grid = gen.generate(
        83,
        0,
        difficulty="hard",
        grid_h=30,
        grid_w=30,
        n_objects=4,
        scene_profile="canonical",
    )
    assert 36 in {len(component) for component in _components8(grid)}


def test_every_declared_shortcut_fits_every_canonical_pair():
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "maroon_only",
        "solid_rectangles_only",
        "ignore_singletons",
    }
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in PAIRS:
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_counterexample_profile_refutes_every_declared_competitor(band):
    for index in (1, 2, 5, 6):
        grid = gen.generate(2027, index, difficulty=band)
        assert gen.observe_overrides(grid)["scene_profile"] == "counterexample"
        intended = gen._mirror(grid)
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert rival(grid) != intended, name
        assert all(witness(grid) for witness in gen.SEMANTIC_WITNESSES.values())


@pytest.mark.parametrize("start", range(12))
@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_pair_window_is_identifiable_under_every_query_rotation(start, band):
    grids = [gen.generate(6007, start + offset, difficulty=band) for offset in range(4)]
    pairs = [{"input": grid, "output": gen._mirror(grid)} for grid in grids]
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_lesson_hook_rejects_wrong_labels_and_shortcut_only_demos():
    canonical = gen.generate(91, 0, scene_profile="canonical")
    demos = [{"input": canonical, "output": gen._mirror(canonical)} for _ in range(3)]
    query = {"input": gen.generate(91, 1), "output": gen._mirror(gen.generate(91, 1))}
    findings = gen.lesson_identifiable(demos, query)
    assert any("survives" in finding for finding in findings)

    bad = [{"input": canonical, "output": canonical} for _ in range(3)]
    findings = gen.lesson_identifiable(bad, query)
    assert any("disagrees" in finding for finding in findings)


@pytest.mark.parametrize(
    "mutator, expected",
    [
        (lambda grid: [], "nonempty"),
        (lambda grid: [[0] * 10 for _ in range(10)], "objects"),
        (lambda grid: [row[:-1] if index == 0 else row for index, row in enumerate(grid)], "ragged"),
        (lambda grid: [[11] + row[1:] for row in grid], "colors"),
    ],
)
def test_self_check_rejects_malformed_or_empty_inputs(mutator, expected):
    grid = gen.generate(17, 1, grid_h=10, grid_w=10, n_objects=2, scene_profile="counterexample")
    findings = gen.self_check(mutator([row[:] for row in grid]))
    assert findings
    assert any(expected in finding for finding in findings)


def test_self_check_rejects_minimal_canonical_shortcut_impostors():
    one_rect = [[0] * 10 for _ in range(10)]
    for r in range(2, 4):
        for c in range(2, 4):
            one_rect[r][c] = 9
    assert any("2..4" in finding for finding in gen.self_check(one_rect))

    arbitrary_nonmaroon_rects = [[0] * 10 for _ in range(10)]
    for r in range(2, 4):
        for c in range(2, 4):
            arbitrary_nonmaroon_rects[r][c] = 2
    for r in range(6, 8):
        for c in range(6, 8):
            arbitrary_nonmaroon_rects[r][c] = 4
    assert any("profile" in finding for finding in gen.self_check(arbitrary_nonmaroon_rects))


def test_selected_solution_target_code_matches_canonical_authority_exactly():
    expected = _canonical_program()
    paths = [
        ROOT / "shared/data/base/solutions/training/db93a21d__067449d7a3b3.json",
        ROOT / "shared/data/base/solutions/augmented/db93a21d__36852b4c2e76.json",
    ]
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["racket_target"]["target_code"] == expected


def test_curriculum_probe_reports_rotation_safe_unique_windows():
    probe_path = TASK_DIR / "workspace" / "probe_curriculum.py"
    spec = importlib.util.spec_from_file_location(
        "probe_curriculum_067449d7a3b3_under_test", probe_path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    report = module.audit_curriculum(
        seeds=(6007, 198222630054986, 20261007),
        starts=range(32),
        bands=("easy", "medium", "hard"),
    )
    assert report["status"] == "pass"
    assert report["windows_checked"] == 288
    assert report["rotations_checked"] == 1152
    assert report["duplicate_windows"] == 0
    assert report["failures"] == []


def test_curriculum_probe_runs_standalone_without_pythonpath(tmp_path):
    probe_path = TASK_DIR / "workspace" / "probe_curriculum.py"
    out_path = tmp_path / "curriculum.json"
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [
            sys.executable,
            str(probe_path),
            "--seeds",
            "6007",
            "--starts",
            "0:2",
            "--bands",
            "easy",
            "--out",
            str(out_path),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert report["windows_checked"] == 2
