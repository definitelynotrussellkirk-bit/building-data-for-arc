"""Independent authoring oracle and portable test helpers for b91a3b0baac4."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

TASK_ID = "b91a3b0baac4"

# Local repository runs do not install the authoring helpers. Portable task-test
# runtimes do, so prefer an existing import and otherwise add the nearest
# shared/runtime directory without consulting cwd.
try:
    from reviewer_support import canonical_pairs as _canonical_pairs
    from reviewer_support import find_root, load_selected_generator
except ImportError:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "shared" / "runtime"
        if (candidate / "reviewer_support.py").is_file():
            sys.path.insert(0, str(candidate))
            break
    from reviewer_support import canonical_pairs as _canonical_pairs
    from reviewer_support import find_root, load_selected_generator


def root() -> Path:
    return find_root(__file__)


def load_generator():
    module, _path, _sha = load_selected_generator(TASK_ID, root=root())
    return module


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=root(), labeled_only=True)


def marker(grid):
    h, w = len(grid), len(grid[0])
    corners = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
    hits = [(r, c, grid[r][c]) for r, c in corners if grid[r][c] in {1, 2, 3, 4}]
    if len(hits) != 1:
        raise ValueError(f"expected one marker corner, found {hits}")
    return hits[0]


def beam_output(grid, *, blockers_enabled=True):
    """Independent direct transcription of the canonical beam rule."""
    h, w = len(grid), len(grid[0])
    mr, mc, color = marker(grid)
    dr, dc = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}[color]
    blockers = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    out = deepcopy(grid)
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value in (0, 5) or (r, c) == (mr, mc):
                continue
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w:
                if blockers_enabled and (rr, cc) in blockers:
                    break
                out[rr][cc] = value
                rr += dr
                cc += dc
    return out


def active_and_inactive_blockers(grid):
    """Return blockers that are/are not the first blocker on an emitter ray."""
    h, w = len(grid), len(grid[0])
    mr, mc, color = marker(grid)
    dr, dc = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}[color]
    all_blockers = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    active = set()
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value in (0, 5) or (r, c) == (mr, mc):
                continue
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w:
                if (rr, cc) in all_blockers:
                    active.add((rr, cc))
                    break
                rr += dr
                cc += dc
    return active, all_blockers - active


def observed(grid):
    h, w = len(grid), len(grid[0])
    mr, mc, direction = marker(grid)
    corner = {(0, 0): "tl", (0, w - 1): "tr", (h - 1, 0): "bl", (h - 1, w - 1): "br"}[(mr, mc)]
    emitter_cells = [
        grid[r][c]
        for r in range(h)
        for c in range(w)
        if (r, c) != (mr, mc) and grid[r][c] not in (0, 5)
    ]
    return {
        "grid_h": h,
        "grid_w": w,
        "n_emitters": len(emitter_cells),
        "n_blockers": sum(value == 5 for row in grid for value in row),
        "emitter_palette_size": len(set(emitter_cells)),
        "marker_corner": corner,
        "marker_direction": direction,
    }


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})
