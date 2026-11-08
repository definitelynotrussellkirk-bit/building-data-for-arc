"""Focused regression tests for review-9800191c3bc69293.

The oracle below is intentionally independent of the reviewed generator.  It
implements the selected nested-frame rule directly from grid structure so the
Python mirror cannot certify itself.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from collections import Counter, deque
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
HOME = HERE.parents[1]
REPO = HERE.parents[3]
GEN_PATH = HOME / "generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))

spec = importlib.util.spec_from_file_location("reviewed_cad61106e2b9", GEN_PATH)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

CANONICAL_SHAPES = {(13, 14), (13, 15), (14, 15), (14, 16)}
DISTRACTOR_COLORS = {5, 6, 7, 9}


def _normalize_grid(grid):
    return [
        [int(ch) for ch in row] if isinstance(row, str) else [int(value) for value in row]
        for row in grid
    ]


def _canonical_pairs():
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != gen.TASK_ID:
                continue
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [
                {"input": _normalize_grid(pair["input"]), "output": _normalize_grid(pair["output"])}
                for pair in [*row["train"], *test]
            ]
    raise AssertionError("canonical task not found")


def _components_of_four(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 4 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 4
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)
    return components


def _rect_frame_box(cells):
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    expected = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    assert cells == expected
    return r1, c1, r2, c2


def independent_output(grid, *, forced_control=None, whole_interior=False):
    out = copy.deepcopy(grid)
    control = forced_control
    if control is None:
        control = next(
            value
            for row in grid
            for value in row
            if value in (1, 2, 3)
        )
    boxes = [_rect_frame_box(cells) for cells in _components_of_four(grid)]
    boxes.sort(key=lambda box: (box[2] - box[0] + 1) * (box[3] - box[1] + 1), reverse=True)
    selected = boxes[control - 1]
    inner = boxes[control] if control < len(boxes) else None
    r1, c1, r2, c2 = selected
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            if grid[r][c] != 0:
                continue
            if not whole_interior and inner is not None:
                ir1, ic1, ir2, ic2 = inner
                if ir1 <= r <= ir2 and ic1 <= c <= ic2:
                    continue
            out[r][c] = 8
    return out


def _singletons(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and counts[value] == 1
    ]


def test_identity_and_public_contract_are_exact():
    assert gen.GENERATOR_ID == gen.TASK_ID == "cad61106e2b9"
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "a3ad6fb565b1"
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == {"grid_h", "grid_w", "ctrl_value", "distractor_color"}
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "outer_band",
        "middle_band",
        "inner_interior",
    )
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_every_canonical_pair_is_owned_and_matches_independent_oracle(pair):
    before = copy.deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert independent_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == before


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_override_boundaries_are_lawful_and_observable(difficulty):
    cases = [
        {"grid_h": 13, "grid_w": 14, "ctrl_value": 1, "distractor_color": 5},
        {"grid_h": 24, "grid_w": 24, "ctrl_value": 3, "distractor_color": 9},
        {"grid_h": 13, "grid_w": 24, "ctrl_value": 2, "distractor_color": 6},
        {"grid_h": 24, "grid_w": 14, "ctrl_value": 1, "distractor_color": 7},
    ]
    for offset, overrides in enumerate(cases):
        grid = gen.generate(7021 + offset, 91 + offset, difficulty=difficulty, **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, difficulty=difficulty, meta={"overrides": overrides}) == []
        assert gen.rule_mirror(grid) == independent_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 12},
        {"grid_h": 25},
        {"grid_w": 13},
        {"grid_w": 25},
        {"ctrl_value": 0},
        {"ctrl_value": 4},
        {"distractor_color": 4},
        {"distractor_color": 8},
        {"ctrl_value": True},
        {"grid_h": 13.5},
        {"distractor_color": "7"},
        {"typo_axis": 1},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_default_curriculum_has_canonical_anchors_four_colors_and_all_controls():
    for difficulty in (None, "easy", "medium", "hard"):
        controls = set()
        distractors = set()
        exact_profiles = 0
        for index in range(20):
            grid = gen.generate(8801, index, difficulty=difficulty)
            assert grid == gen.generate(8801, index, difficulty=difficulty)
            assert 13 <= len(grid) <= 24
            assert 14 <= len(grid[0]) <= 24
            if index % 4 == 0:
                assert (len(grid), len(grid[0])) in CANONICAL_SHAPES
                exact_profiles += 1
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert len(_components_of_four(grid)) == 3
            assert len(set(value for row in grid for value in row)) == 4
            observed = gen.observe_overrides(grid)
            controls.add(observed["ctrl_value"])
            distractors.add(observed["distractor_color"])
            assert observed["ctrl_value"] == index % 3 + 1
            assert observed["distractor_color"] in DISTRACTOR_COLORS
            assert gen.rule_mirror(grid) == independent_output(grid)
        assert exact_profiles >= 5
        assert controls == {1, 2, 3}
        assert distractors == DISTRACTOR_COLORS


def test_difficulty_bands_are_behaviorally_live_and_scale_ordered():
    saw_band_difference = False
    easy_sizes = []
    medium_sizes = []
    hard_sizes = []
    for seed in range(12):
        for index in range(1, 12):
            if index % 4 == 0:
                continue
            easy = gen.generate(seed, index, difficulty="easy")
            medium = gen.generate(seed, index, difficulty="medium")
            hard = gen.generate(seed, index, difficulty="hard")
            saw_band_difference |= len({
                tuple(map(tuple, easy)),
                tuple(map(tuple, medium)),
                tuple(map(tuple, hard)),
            }) > 1
            easy_sizes.append((len(easy), len(easy[0])))
            medium_sizes.append((len(medium), len(medium[0])))
            hard_sizes.append((len(hard), len(hard[0])))
    assert saw_band_difference
    assert max(h for h, _ in easy_sizes) <= 16
    assert max(w for _, w in easy_sizes) <= 17
    assert min(h for h, _ in medium_sizes) >= 15
    assert min(w for _, w in medium_sizes) >= 16
    assert min(h for h, _ in hard_sizes) >= 19
    assert min(w for _, w in hard_sizes) >= 20
    assert max(h for h, _ in hard_sizes) >= 23
    assert max(w for _, w in hard_sizes) >= 23


def test_three_consecutive_examples_refute_every_declared_competitor():
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(5):
            for start in range(6):
                demos = []
                for offset in range(gen.EXAMPLES_NEEDED):
                    grid = gen.generate(seed, start + offset, difficulty=difficulty)
                    demos.append({"input": grid, "output": independent_output(grid)})
                query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=difficulty)
                query = {"input": query_grid, "output": independent_output(query_grid)}
                assert {gen.schedule_profile(seed, start + i, difficulty) for i in range(3)} == set(
                    gen.SCHEDULE_PROFILES
                )
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), name
                assert gen.lesson_identifiable(demos, query) == []


def test_generated_counterexamples_refute_both_canonical_fitting_shortcuts():
    canonical = _canonical_pairs()
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical), name

    grids = [gen.generate(4301, index) for index in range(6)]
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert any(shortcut(grid) != independent_output(grid) for grid in grids), name

    earlier_distractor = []
    for grid in grids:
        singletons = _singletons(grid)
        control = next(cell for cell in singletons if cell[2] in (1, 2, 3))
        distractor = next(cell for cell in singletons if cell[2] in DISTRACTOR_COLORS)
        if distractor[:2] < control[:2]:
            earlier_distractor.append(grid)
    assert earlier_distractor
    assert all(gen.SEMANTIC_WITNESSES["distractor_precedes_control"](g) for g in earlier_distractor)


def test_self_check_rejects_nearest_structural_impostors():
    grid = gen.generate(6123, 4)
    assert gen.self_check(grid) == []

    no_distractor = copy.deepcopy(grid)
    for r, row in enumerate(no_distractor):
        for c, value in enumerate(row):
            if value in DISTRACTOR_COLORS:
                no_distractor[r][c] = 0
    assert gen.self_check(no_distractor)

    duplicate_control = copy.deepcopy(grid)
    duplicate_control[-1][-1] = gen.observe_overrides(grid)["ctrl_value"]
    assert gen.self_check(duplicate_control)

    broken_frame = copy.deepcopy(grid)
    r, c = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4)
    broken_frame[r][c] = 0
    assert gen.self_check(broken_frame)

    prefilled_output = copy.deepcopy(grid)
    expected = independent_output(grid)
    rr, cc = next(
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if expected[r][c] == 8 and grid[r][c] == 0
    )
    prefilled_output[rr][cc] = 8
    assert gen.self_check(prefilled_output)


def test_retained_probe_is_source_bound_and_clean():
    probe_path = HOME / "workspace" / "review_probe.py"
    probe_spec = importlib.util.spec_from_file_location("cad61106e2b9_review_probe", probe_path)
    assert probe_spec is not None and probe_spec.loader is not None
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)
    report = probe.run_probe(lessons_per_band=2, seed=1907)
    assert report["generator_sha256"] == probe.file_sha256(GEN_PATH)
    assert report["canonical_pairs"] == 5
    assert report["canonical_oracle_mismatches"] == 0
    assert report["generated_examples"] == 24
    assert report["generation_failures"] == []
    assert report["lesson_failures"] == []
    assert report["surviving_competitors"] == {
        name: 0 for name in sorted(gen.LESSON_COMPETITORS)
    }
