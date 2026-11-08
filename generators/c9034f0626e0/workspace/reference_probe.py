"""Independent oracle and morphology probes for c9034f0626e0.

This module deliberately does not import implementation helpers from generator.py.
It is test/audit tooling, not a replacement label authority.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

# The staged task-test runtime exposes reviewer_support directly.  In the source
# tree, discover its public module without assuming a fixed repository depth.
try:
    from reviewer_support import canonical_pairs as _canonical_pairs, find_root
except ModuleNotFoundError:
    for ancestor in Path(__file__).resolve().parents:
        support_dir = ancestor / "shared" / "runtime"
        if (support_dir / "reviewer_support.py").is_file():
            sys.path.insert(0, str(support_dir))
            break
    from reviewer_support import canonical_pairs as _canonical_pairs, find_root

ROOT = find_root(__file__)
TASK = "c9034f0626e0"
PROFILE_SPECS = {
    "canonical_13x13": (13, 13, 69),
    "canonical_13x16": (13, 16, 94),
    "canonical_15x17": (15, 17, 81),
}
PARITIES = ("p00", "p01", "p10", "p11")
MARKER_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def load_generator(path=None):
    if path is None:
        candidates = (
            ROOT / f"generators/{TASK}/generator.py",
            ROOT / f"puzzle_generators/per_puzzle/{TASK}/generator.py",
        )
        path = next((candidate for candidate in candidates if candidate.is_file()), None)
        if path is None:
            raise FileNotFoundError(f"cannot locate generator {TASK} under {ROOT}")
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=ROOT, variant=0, labeled_only=True)


def marker(grid):
    hits = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    if len(hits) != 1:
        raise ValueError(f"expected one marker, found {len(hits)}")
    return hits[0]


def parity_name(row, col):
    return f"p{row % 2}{col % 2}"


def apply_rule(grid):
    mr, mc, color = marker(grid)
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 and (r % 2, c % 2) == (mr % 2, mc % 2):
                out[r][c] = color
    return out


def _rival(grid, mode):
    mr, mc, color = marker(grid)
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if mode == "row_only":
                fill = value == 0 and r % 2 == mr % 2
            elif mode == "column_only":
                fill = value == 0 and c % 2 == mc % 2
            elif mode == "sum_parity":
                fill = value == 0 and (r + c) % 2 == (mr + mc) % 2
            elif mode == "fill_all":
                fill = value == 0
            elif mode == "overwrite_gray":
                fill = (r % 2, c % 2) == (mr % 2, mc % 2)
            elif mode == "identity":
                fill = False
            else:
                raise ValueError(mode)
            if fill:
                out[r][c] = color
    return out


RIVALS = {
    name: (lambda grid, name=name: _rival(grid, name))
    for name in (
        "row_only",
        "column_only",
        "sum_parity",
        "fill_all",
        "overwrite_gray",
        "identity",
    )
}


def gray_components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    sizes = []
    while unseen:
        start = unseen.pop()
        queue = deque([start])
        size = 0
        while queue:
            r, c = queue.popleft()
            size += 1
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def independent_observation(grid):
    h, w = len(grid), len(grid[0])
    matches = [
        name
        for name, (ph, pw, gray_count) in PROFILE_SPECS.items()
        if (h, w, sum(value == 5 for row in grid for value in row))
        == (ph, pw, gray_count)
    ]
    if len(matches) != 1:
        raise ValueError(f"grid does not identify one profile: {h}x{w}, matches={matches}")
    mr, mc, color = marker(grid)
    return {
        "scene_profile": matches[0],
        "marker_color": color,
        "marker_parity": parity_name(mr, mc),
    }
