"""Color must determine a target's role even when its geometry is uninformative."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "34f8510e39d0"
ROOT = find_root(__file__)


def _load_generator():
    candidates = (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    source = next((p for p in candidates if p.is_file()), None)
    if source is None:
        raise FileNotFoundError(f"Selected generator missing under {ROOT}")
    spec = importlib.util.spec_from_file_location("color_role_selected_generator", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _rectangles(grid):
    """Independent four-connected, single-color solid-rectangle extraction."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    rectangles = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        comp, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for cell in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if cell in remaining and grid[cell[0]][cell[1]] == color:
                    remaining.remove(cell)
                    comp.add(cell)
                    stack.append(cell)
        rs, cs = zip(*comp)
        box = min(rs), min(cs), max(rs), max(cs)
        shape = box[2] - box[0] + 1, box[3] - box[1] + 1
        if len(comp) == shape[0] * shape[1]:
            rectangles.append((color, box, shape))
    return rectangles


def _outline_selected(grid, predicate):
    out = [row[:] for row in grid]
    for color, (r0, c0, r1, c1), shape in _rectangles(grid):
        if predicate(color, shape):
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if r in (r0, r1) or c in (c0, c1):
                        out[r][c] = 8
    return out


def size_only_rival(grid):
    return _outline_selected(grid, lambda color, shape: min(shape) >= 2 and shape[0] * shape[1] >= 6)


def _matched_pair(grid):
    rects = _rectangles(grid)
    targets = [rect for rect in rects if rect[0] == 3]
    largest_area = max(h * w for _, _, (h, w) in targets)
    for target in targets:
        if target[2][0] * target[2][1] != largest_area:
            continue
        for distractor in rects:
            if distractor[0] not in (0, 3, 8) and distractor[2] == target[2]:
                return target, distractor
    return None


def _assert_role_support(grid):
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    pair = _matched_pair(grid)
    assert pair is not None, "largest green target has no same-shape non-green distractor"
    expected = _outline_selected(grid, lambda color, shape: color == 3)
    assert gen.rule_mirror(grid) == expected
    assert size_only_rival(grid) != expected, "size-only rival survives this generated draw"
    target, distractor = pair
    swapped = [row[:] for row in grid]
    for new_color, (_, (r0, c0, r1, c1), _) in ((distractor[0], target), (3, distractor)):
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                swapped[r][c] = new_color
    # Same shapes and locations, different color roles: either position can be
    # a lawful target, and outlining follows green after the exchange.
    assert swapped != grid
    assert gen.self_check(swapped) == []
    assert gen.strict_canonical_like(swapped) == []
    swapped_expected = _outline_selected(swapped, lambda color, shape: color == 3)
    assert gen.rule_mirror(swapped) == swapped_expected
    assert size_only_rival(swapped) != swapped_expected
    for before, after in ((grid, expected), (swapped, swapped_expected)):
        assert all(after[r][c] == value for r, row in enumerate(before) for c, value in enumerate(row) if value != 3)


def test_size_only_rival_fits_all_five_labeled_canonical_pairs():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert size_only_rival(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("profile", gen.PROFILE_NAMES)
def test_every_profile_and_band_has_matched_geometry_and_lawful_role_swaps(band, profile):
    for seed in (0, 1, 7, 99):
        for index in range(4):
            _assert_role_support(gen.generate(seed, index, difficulty=band, scene_profile=profile))


@pytest.mark.parametrize("profile", gen.PROFILE_NAMES)
def test_fallback_keeps_matched_geometry(monkeypatch, profile):
    monkeypatch.setattr(gen, "_try_place_scene", lambda *args: None)
    _assert_role_support(gen.generate(123, 0, difficulty="hard", scene_profile=profile))


def test_size_rival_is_declared_for_semantic_lesson_and_canonical_review():
    for namespace in (gen.SEMANTIC_RIVALS, gen.LESSON_COMPETITORS, gen.CANONICAL_SHORTCUTS):
        assert "outline_rectangles_by_size" in namespace
        rival = namespace["outline_rectangles_by_size"]
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            assert rival(pair["input"]) == size_only_rival(pair["input"])
        for index, profile in enumerate(gen.PROFILE_NAMES):
            grid = gen.generate(42, index, difficulty="medium", scene_profile=profile)
            assert rival(grid) == size_only_rival(grid)
            assert rival(grid) != gen.rule_mirror(grid)
