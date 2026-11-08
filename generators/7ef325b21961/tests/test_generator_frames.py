"""Focused regressions for the ordinary 7ef325b21961 frame generator."""
from __future__ import annotations

from collections import Counter, deque
import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]


def load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("_test_frame_generator", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return load_generator()


def components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    rows = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                point = queue.popleft()
                cells.append(point)
                pr, pc = point
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = pr + dr, pc + dc
                    if (0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows.append((color, cells))
    return rows


def frame_records(grid):
    result = []
    for color, cells in components(grid):
        if len(cells) < 12:
            continue
        r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
        border = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                  if r in (r1, r2) or c in (c1, c2)}
        if set(cells) != border:
            continue
        interior = [grid[r][c] for r in range(r1 + 1, r2)
                    for c in range(c1 + 1, c2) if grid[r][c] != 0]
        result.append({"color": color, "bbox": (r1, c1, r2, c2),
                       "interior_counts": Counter(interior)})
    return sorted(result, key=lambda row: row["bbox"])


def test_rule_hash_is_pinned(generator):
    assert generator.RULE_HASH == "450273ee54ad"


def test_three_frame_scene_has_independent_local_majorities(generator):
    for seed in range(20):
        grid = generator.generate(seed, 0, difficulty="hard", frame_count=3)
        frames = frame_records(grid)
        assert len(frames) == 3, f"seed {seed} silently emitted {len(frames)} frames"
        winners = []
        for frame in frames:
            counts = frame["interior_counts"]
            assert len(counts) == 2
            ordered = counts.most_common()
            assert ordered[0][1] > ordered[1][1] >= 1
            winners.append(ordered[0][0])
        assert len(set(winners)) == len(winners), (
            f"seed {seed} reused a global majority across frames: {winners}")


def test_interior_dot_components_cannot_be_mistaken_for_frames(generator):
    for seed in range(12):
        grid = generator.generate(seed, 1, difficulty="hard", frame_count=3)
        frames = frame_records(grid)
        frame_cells = set()
        for frame in frames:
            r1, c1, r2, c2 = frame["bbox"]
            frame_cells |= {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                            if r in (r1, r2) or c in (c1, c2)}
        for color, cells in components(grid):
            if set(cells) <= frame_cells:
                continue
            assert len(cells) < 5, (seed, color, cells)


def test_self_check_rejects_non_frame_colored_blobs(generator):
    bad = [[0] * 8 for _ in range(8)]
    bad[2][2] = bad[2][3] = bad[3][2] = bad[3][3] = 1
    bad[5][5] = 2
    messages = generator.self_check(bad)
    assert messages
    assert any("frame" in message.lower() for message in messages)


@pytest.mark.parametrize("difficulty", [None, "medium"])
def test_ordinary_preflight_difficulties_are_deterministic_and_valid(generator, difficulty):
    first = generator.generate(17, 2, difficulty=difficulty)
    second = generator.generate(17, 2, difficulty=difficulty)
    assert first == second
    assert generator.self_check(first, difficulty=difficulty) == []
    assert frame_records(first)


def test_declared_axes_are_implemented_and_non_degenerate(generator):
    assert set(generator.AXES) == {"grid_h", "grid_w", "frame_count", "texture"}
    a = generator.generate(23, 0, grid_h=18, grid_w=19, frame_count=2)
    b = generator.generate(23, 0, grid_h=22, grid_w=23, frame_count=3)
    assert [len(a), len(a[0])] == [18, 19]
    assert [len(b), len(b[0])] == [22, 23]
    assert len(frame_records(a)) == 2
    assert len(frame_records(b)) == 3
