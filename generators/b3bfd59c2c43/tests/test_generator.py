"""Regression tests for the b3bfd59c2c43 boundary-peeling input sampler."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
spec = importlib.util.spec_from_file_location("generator_under_test", SOURCE)
assert spec and spec.loader
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)


def _components(grid):
    """Return 4-connected same-color components as (color, frozenset(cells))."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, frozenset(cells)))
    return result


def _core(cells):
    return {
        (r, c)
        for r, c in cells
        if all((nr, nc) in cells for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
    }


def _is_filled_rectangle(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return len(cells) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _blank(h, w):
    return [[0 for _ in range(w)] for _ in range(h)]


def _paint(grid, cells, color):
    for r, c in cells:
        grid[r][c] = color


def _diamond(r0, c0, radius):
    return {
        (r0 + dr, c0 + dc)
        for dr in range(-radius, radius + 1)
        for dc in range(-radius, radius + 1)
        if abs(dr) + abs(dc) <= radius
    }


def _rounded_square(r0, c0, size):
    return {
        (r0 + r, c0 + c)
        for r in range(size)
        for c in range(size)
        if (r, c) not in {(0, 0), (0, size - 1), (size - 1, 0), (size - 1, size - 1)}
    }


def _thick_cross(r0, c0, size):
    mid = size // 2
    return {
        (r0 + r, c0 + c)
        for r in range(size)
        for c in range(size)
        if abs(r - mid) <= 1 or abs(c - mid) <= 1
    }


def _canonical_representatives():
    first = _blank(11, 15)
    _paint(first, {(r, c) for r in range(1, 6) for c in range(1, 6)}, 2)
    _paint(first, _diamond(4, 11, 2), 3)

    second = _blank(12, 12)
    _paint(second, _rounded_square(1, 1, 5), 4)
    _paint(second, {(r, c) for r in range(7, 10) for c in range(8, 11)}, 6)

    third = _blank(13, 15)
    _paint(third, _thick_cross(1, 1, 7), 5)
    _paint(third, _diamond(6, 12, 2), 2)  # right tip touches the grid edge
    return [first, second, third]


def test_pins_authority_and_advertises_only_exact_axes():
    assert GEN.RULE_HASH == "28b8cf49f820"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "object_count"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("grid", _canonical_representatives(), ids=["square-diamond", "rounded-square", "cross-edge-diamond"])
def test_accepts_canonical_component_families(grid):
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("options", [
    {"grid_h": 10, "grid_w": 12, "object_count": 3},
    {"grid_h": 11, "grid_w": 15, "object_count": 2},
    {"grid_h": 18, "grid_w": 20, "object_count": 2},
])
def test_exact_overrides_are_honored_in_every_band(band, options):
    grid = GEN.generate(41, 7, difficulty=band, **options)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == options


@pytest.mark.parametrize("key,value", [
    ("typo", 1),
    ("grid_h", 9),
    ("grid_h", 19),
    ("grid_w", 11),
    ("grid_w", 21),
    ("object_count", 1),
    ("object_count", 4),
    ("grid_h", True),
    ("grid_w", 12.5),
    ("object_count", "2"),
])
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_objects_are_connected_separated_and_have_a_core(band):
    for index in range(160):
        grid = GEN.generate(1200 + index, index * 13, difficulty=band)
        assert grid == GEN.generate(1200 + index, index * 13, difficulty=band)
        assert GEN.self_check(grid) == []
        observed = GEN.observe_overrides(grid)
        components = _components(grid)
        assert len(components) == observed["object_count"]
        assert len({color for color, _ in components}) == len(components)
        for _, cells in components:
            assert _core(cells), "every ordinary object must preserve at least one inner cell"
        occupied = {cell: color for color, cells in components for cell in cells}
        for (r, c), color in occupied.items():
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                assert neighbor not in occupied or occupied[neighbor] == color


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_hits_canonical_profiles_and_irregular_core_witnesses(band):
    canonical_profiles = {(11, 15, 2), (12, 12, 2), (13, 15, 2)}
    profiles = set()
    irregular = 0
    total = 180
    for index in range(total):
        grid = GEN.generate(8000 + index, index, difficulty=band)
        components = _components(grid)
        profiles.add((len(grid), len(grid[0]), len(components)))
        if any(not _is_filled_rectangle(cells) and _core(cells) for _, cells in components):
            irregular += 1
    assert profiles & canonical_profiles
    assert irregular >= total // 4


@pytest.mark.parametrize("grid", [
    [[7]],
    [[7, 7, 7]],
    [[7, 7], [7, 7]],
    [[7 for _ in range(12)] for _ in range(10)],
])
def test_self_check_rejects_minimal_impostors(grid):
    assert GEN.self_check(grid)


def test_semantic_witnesses_refute_named_shortcuts():
    hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for index in range(100):
        grid = GEN.generate(33000 + index, index, difficulty="medium")
        intended = GEN.rule_mirror(grid)
        for name, predicate in GEN.SEMANTIC_WITNESSES.items():
            if not predicate(grid):
                continue
            hits[name] += 1
            for rival_name in GEN.WITNESS_RIVALS[name]:
                assert GEN.SEMANTIC_RIVALS[rival_name](grid) != intended
    assert all(count > 0 for count in hits.values())

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_default_lesson_draw_refutes_bounding_box_shortcut(band):
    """No lesson may need the query itself to disambiguate the boundary rule."""
    witness = GEN.SEMANTIC_WITNESSES["irregular_component_boundary"]
    for index in range(80):
        grid = GEN.generate(91000 + index, index, difficulty=band)
        assert witness(grid), f"{band=} {index=} leaves the bounding-box rival viable"

def _component_refutes_bbox(cells):
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    for r, c in cells:
        true_boundary = any(
            (nr, nc) not in cells
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        )
        bbox_boundary = r in (top, bottom) or c in (left, right)
        if true_boundary != bbox_boundary:
            return True
    return False


def _strip_ordered_witness_pattern(grid):
    components = [cells for _, cells in _components(grid)]
    boxes = [
        (min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells))
        for cells in components
    ]
    columns_separated = all(
        first[3] < second[1] or second[3] < first[1]
        for index, first in enumerate(boxes)
        for second in boxes[index + 1 :]
    )
    order = sorted(
        range(len(components)),
        key=(lambda i: boxes[i][1]) if columns_separated else (lambda i: boxes[i][0]),
    )
    return tuple(_component_refutes_bbox(components[i]) for i in order)


def test_semantic_teaching_object_rotates_across_constructive_strips(monkeypatch):
    def fixed_column_slots(height, width, count, rng):
        del rng
        usable = width - (count - 1)
        base, remainder = divmod(usable, count)
        sizes = [base + (1 if index < remainder else 0) for index in range(count)]
        slots = []
        start = 0
        for size in sizes:
            slots.append((0, start, height, size))
            start += size + 1
        return slots

    monkeypatch.setattr(GEN, "_layout_slots", fixed_column_slots)
    monkeypatch.setattr(
        GEN,
        "_shape_for_slot",
        lambda max_h, max_w, rng, difficulty: GEN._filled_rectangle(3, 3),
    )

    witness_ranks = set()
    for index in range(90):
        grid = GEN.generate(
            120000 + index,
            index,
            difficulty="medium",
            grid_h=10,
            grid_w=12,
            object_count=3,
        )
        components = sorted((cells for _, cells in _components(grid)), key=lambda cells: min(c for _, c in cells))
        ranks = [rank for rank, cells in enumerate(components) if _component_refutes_bbox(cells)]
        assert len(ranks) == 1
        witness_ranks.add(ranks[0])
    assert witness_ranks == {0, 1, 2}
