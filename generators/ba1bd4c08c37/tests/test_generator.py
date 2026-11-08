"""Behavioral regressions for the symmetric-quadrant curriculum.

The expected crop, symmetry checks, override observations, and rivals below are
implemented independently from the generator. Racket parity is exercised by the
review battery and lesson census.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from importlib import util
import json
from pathlib import Path
import sys

import pytest

try:
    from reviewer_support import canonical_pairs, find_root
except ModuleNotFoundError as exc:
    if exc.name != "reviewer_support":
        raise
    for ancestor in Path(__file__).resolve().parents:
        runtime = ancestor / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    else:
        raise
    from reviewer_support import canonical_pairs, find_root


TASK_ID = "ba1bd4c08c37"
ROOT = find_root(__file__)
BANDS = (None, "easy", "medium", "hard")
PLACEMENTS = ("top_left", "top_right", "bottom_left", "bottom_right", "center")


def load_generator():
    candidates = (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    source = next((path for path in candidates if path.is_file()), None)
    if source is None:
        raise FileNotFoundError(f"No selected generator under {ROOT}")
    name = "symmetric_quadrant_generator_under_review"
    spec = util.spec_from_file_location(name, source)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return load_generator()


def pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def test_task_local_base_rules_exactly_match_canonical_authority(gen):
    canonical_path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    canonical_sources = {
        row["program_solution"]
        for line in canonical_path.read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(canonical_sources) == 1
    canonical = canonical_sources.pop()
    normalized_hash = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert normalized_hash == gen.RULE_HASH

    base_paths = (
        ROOT / "shared" / "data" / "base" / "solutions" / "training" / "73182012__ba1bd4c08c37.json",
        ROOT / "shared" / "data" / "base" / "solutions" / "augmented" / "73182012__6a077390e0ff.json",
    )
    for path in base_paths:
        racket_target = json.loads(path.read_text())["racket_target"]
        # Archival source stays byte-identical to the original base record.
        assert hashlib.sha256(racket_target["raw_code"].encode()).hexdigest() == '10aafa233f43110140eec8c335ba793ace2dd584ac9e52cc2bb122404e7b6d90'
        assert racket_target["target_code"] == canonical


def bbox(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not points:
        raise ValueError("grid has no foreground")
    top = min(r for r, _ in points)
    bottom = max(r for r, _ in points)
    left = min(c for _, c in points)
    right = max(c for _, c in points)
    return top, left, bottom, right


def correct(grid):
    top, left, bottom, right = bbox(grid)
    half_h = (bottom - top + 1) // 2
    half_w = (right - left + 1) // 2
    return [row[left:left + half_w] for row in grid[top:top + half_h]]


def observed(grid):
    top, left, bottom, right = bbox(grid)
    height, width = len(grid), len(grid[0])
    bbox_h, bbox_w = bottom - top + 1, right - left + 1
    positions = {
        (0, 0): "top_left",
        (0, width - bbox_w): "top_right",
        (height - bbox_h, 0): "bottom_left",
        (height - bbox_h, width - bbox_w): "bottom_right",
        ((height - bbox_h) // 2, (width - bbox_w) // 2): "center",
    }
    return {
        "grid_h": height,
        "grid_w": width,
        "quadrant_h": bbox_h // 2,
        "quadrant_w": bbox_w // 2,
        "palette_size": len({value for row in grid for value in row if value != 0}),
        "placement": positions[(top, left)],
    }


def assert_domain(grid):
    assert isinstance(grid, list) and 12 <= len(grid) <= 20
    assert all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    assert 12 <= len(grid[0]) <= 20
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    top, left, bottom, right = bbox(grid)
    bbox_h, bbox_w = bottom - top + 1, right - left + 1
    assert bbox_h % 2 == bbox_w % 2 == 0
    assert 6 <= bbox_h <= 10 and 6 <= bbox_w <= 10
    patch = [row[left:right + 1] for row in grid[top:bottom + 1]]
    assert patch == patch[::-1]
    assert patch == [row[::-1] for row in patch]
    quadrant = correct(grid)
    assert 0 in {value for row in quadrant for value in row}
    assert quadrant != quadrant[::-1]
    assert quadrant != [row[::-1] for row in quadrant]
    assert 2 <= len({value for row in grid for value in row if value != 0}) <= 6


def rival_fixed_four(grid):
    top, left, _, _ = bbox(grid)
    return [row[left:left + 4] for row in grid[top:top + 4]]


def rival_fixed_height(grid):
    top, left, _, right = bbox(grid)
    half_w = (right - left + 1) // 2
    return [row[left:left + half_w] for row in grid[top:top + 4]]


def rival_fixed_width(grid):
    top, left, bottom, _ = bbox(grid)
    half_h = (bottom - top + 1) // 2
    return [row[left:left + 4] for row in grid[top:top + half_h]]


def rival_grid_origin(grid):
    top, left, bottom, right = bbox(grid)
    half_h = (bottom - top + 1) // 2
    half_w = (right - left + 1) // 2
    return [row[:half_w] for row in grid[:half_h]]


def rival_raw_top_right(grid):
    top, left, bottom, right = bbox(grid)
    half_h = (bottom - top + 1) // 2
    half_w = (right - left + 1) // 2
    return [row[right - half_w + 1:right + 1] for row in grid[top:top + half_h]]


def rival_raw_bottom_left(grid):
    top, left, bottom, right = bbox(grid)
    half_h = (bottom - top + 1) // 2
    half_w = (right - left + 1) // 2
    return [row[left:left + half_w] for row in grid[bottom - half_h + 1:bottom + 1]]


def rival_raw_bottom_right(grid):
    top, left, bottom, right = bbox(grid)
    half_h = (bottom - top + 1) // 2
    half_w = (right - left + 1) // 2
    return [row[right - half_w + 1:right + 1]
            for row in grid[bottom - half_h + 1:bottom + 1]]


def rival_whole_bbox(grid):
    top, left, bottom, right = bbox(grid)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


RIVALS = {
    "fixed_four": rival_fixed_four,
    "fixed_height_four": rival_fixed_height,
    "fixed_width_four": rival_fixed_width,
    "grid_origin": rival_grid_origin,
    "raw_top_right": rival_raw_top_right,
    "raw_bottom_left": rival_raw_bottom_left,
    "raw_bottom_right": rival_raw_bottom_right,
    "whole_bbox": rival_whole_bbox,
}


@pytest.mark.parametrize("pair", pairs(), ids=lambda item: f"{item['variant']}-{item['split']}-{item['pair_index']}")
def test_canonical_pairs_are_accepted_and_match_independent_crop(gen, pair):
    assert gen.RULE_HASH == "5394b465fb89"
    assert gen.self_check(deepcopy(pair["input"])) == []
    assert correct(pair["input"]) == pair["output"]
    assert gen.strict_canonical_like(deepcopy(pair["input"])) == []


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "axes",
    [
        {"grid_h": 12, "grid_w": 12, "quadrant_h": 3, "quadrant_w": 3,
         "palette_size": 2, "placement": "top_left"},
        {"grid_h": 20, "grid_w": 20, "quadrant_h": 5, "quadrant_w": 5,
         "palette_size": 6, "placement": "bottom_right"},
        {"grid_h": 13, "grid_w": 17, "quadrant_h": 4, "quadrant_w": 5,
         "palette_size": 5, "placement": "center"},
    ],
)
def test_joint_exact_overrides_are_realized_in_every_band(gen, band, axes):
    grid = gen.generate(819, 7, difficulty=band, **axes)
    assert observed(grid) == axes
    assert gen.observe_overrides(deepcopy(grid)) == axes
    assert gen.self_check(deepcopy(grid), difficulty=band) == []
    assert_domain(grid)


@pytest.mark.parametrize("placement", PLACEMENTS)
def test_every_placement_is_pixel_observable(gen, placement):
    request = {"grid_h": 19, "grid_w": 18, "quadrant_h": 4, "quadrant_w": 3,
               "palette_size": 4, "placement": placement}
    grid = gen.generate(25, 2, **request)
    assert observed(grid) == request


@pytest.mark.parametrize("band", BANDS)
def test_default_population_is_lawful_deterministic_and_diverse(gen, band):
    hashes = set()
    shapes = set()
    placements = set()
    for index in range(50):
        first = gen.generate(123456, index, difficulty=band)
        second = gen.generate(123456, index, difficulty=band)
        assert first == second
        assert gen.self_check(deepcopy(first), difficulty=band) == []
        assert_domain(first)
        hashes.add(repr(first))
        values = observed(first)
        shapes.add((values["quadrant_h"], values["quadrant_w"]))
        placements.add(values["placement"])
    assert len(hashes) == 50
    assert {(4, 4), (3, 5), (5, 3)} <= shapes
    assert set(PLACEMENTS) <= placements


def test_self_check_rejects_structural_impostors_and_broken_symmetry(gen):
    grid = gen.generate(17, 0)
    assert gen.self_check(grid) == []
    assert gen.self_check([[0] * 12 for _ in range(12)])
    assert gen.self_check([[1] * 12 for _ in range(12)])
    broken = deepcopy(grid)
    top, left, _, _ = bbox(broken)
    broken[top][left] = 9 if broken[top][left] != 9 else 8
    assert gen.self_check(broken)
    injected = deepcopy(grid)
    injected[-1][-1] = 9
    assert gen.self_check(injected)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown": 1}, {"grid_h": True}, {"grid_w": 12.0},
        {"quadrant_h": 2}, {"quadrant_w": 6}, {"palette_size": 1},
        {"palette_size": 7}, {"placement": "random"},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(gen, kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, **kwargs)


def test_schedule_contract_covers_six_distinct_profiles_without_shape_axis_lock(gen):
    assert gen.EXAMPLES_NEEDED == 5
    assert gen.LESSON_SCHEDULE_PERIOD == 6
    assert len(gen.SCHEDULE_PROFILES) == 6
    assert {gen.schedule_profile(4, index, "medium") for index in range(6)} == set(gen.SCHEDULE_PROFILES)
    assert gen.schedule_profile(99, 7, "easy") == gen.schedule_profile(0, 1, "hard")

    defaults = [observed(gen.generate(991, index)) for index in range(6)]
    widths_by_height = {}
    heights_by_width = {}
    for values in defaults:
        widths_by_height.setdefault(values["quadrant_h"], set()).add(values["quadrant_w"])
        heights_by_width.setdefault(values["quadrant_w"], set()).add(values["quadrant_h"])
    assert any(len(widths) > 1 for widths in widths_by_height.values())
    assert any(len(heights) > 1 for heights in heights_by_width.values())


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_cyclic_lesson_and_query_rotation_refutes_all_declared_rivals(gen, band):
    period = gen.LESSON_SCHEDULE_PERIOD
    for start in range(period):
        grids = [gen.generate(7001, start + offset, difficulty=band) for offset in range(period)]
        labelled = [{"input": grid, "output": correct(grid)} for grid in grids]
        for query_index in range(period):
            query = labelled[query_index]
            demos = [pair for index, pair in enumerate(labelled) if index != query_index]
            assert gen.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
            for name, rival in RIVALS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    band, start, query_index, name
                )


def test_semantic_hooks_match_independent_rivals_and_witnesses(gen):
    assert set(gen.SEMANTIC_RIVALS) == set(RIVALS)
    assert set(gen.LESSON_COMPETITORS) == set(RIVALS)
    assert set(gen.SEMANTIC_WITNESSES) == set(RIVALS)
    assert set(gen.WITNESS_RIVALS) == set(RIVALS)
    for index in range(gen.LESSON_SCHEDULE_PERIOD):
        grid = gen.generate(203, index)
        expected = correct(grid)
        for name, rival in RIVALS.items():
            assert gen.SEMANTIC_RIVALS[name](deepcopy(grid)) == rival(grid)
            assert gen.SEMANTIC_WITNESSES[name](deepcopy(grid)) is (rival(grid) != expected)
            assert gen.WITNESS_RIVALS[name] == [name]


def test_only_canonical_fitting_shortcuts_are_declared_and_are_refuted_by_schedule(gen):
    expected_names = {"fixed_four", "fixed_height_four", "fixed_width_four"}
    assert set(gen.CANONICAL_SHORTCUTS) == expected_names
    for pair in pairs():
        for name in expected_names:
            assert RIVALS[name](pair["input"]) == pair["output"]
    generated = [gen.generate(88, index) for index in range(gen.LESSON_SCHEDULE_PERIOD)]
    for name in expected_names:
        assert any(RIVALS[name](grid) != correct(grid) for grid in generated)
