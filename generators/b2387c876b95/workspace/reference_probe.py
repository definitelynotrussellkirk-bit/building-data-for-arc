"""Independent geometry probes for b2387c876b95 review and future maintenance."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "b2387c876b95"


def load_generator(path=None):
    path = Path(path) if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_path():
    for parent in Path(__file__).resolve().parents:
        direct = parent / "shared" / "data" / "canonical" / "puzzles.jsonl"
        if direct.is_file():
            return direct
        staged = parent / "data" / "canonical" / "puzzles.jsonl"
        if staged.is_file():
            return staged
    try:
        from reviewer_support import canonical_path, find_root
        return canonical_path(find_root(__file__))
    except Exception as exc:  # pragma: no cover - only diagnostic fallback
        raise FileNotFoundError("canonical puzzles.jsonl not found") from exc


def canonical_examples(include_unlabeled=True):
    for line in _canonical_path().read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            result = []
            for split in ("train", "test"):
                for index, pair in enumerate(row.get(split, [])):
                    if include_unlabeled or "output" in pair:
                        result.append({**pair, "split": split, "pair_index": index})
            return result
    raise AssertionError(f"canonical task {TASK_ID} not found")


def divider(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(rows) + len(cols) != 1:
        raise ValueError(f"expected one divider, got rows={rows}, cols={cols}")
    return ("horizontal", rows[0]) if rows else ("vertical", cols[0])


def red_cells(grid):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}


def reflected(point, orientation, d):
    r, c = point
    return (r, 2 * d - c) if orientation == "vertical" else (2 * d - r, c)


def intended_output(grid):
    """Independent oracle matching the pinned Racket rule on lawful inputs."""
    out = [row[:] for row in grid]
    orientation, d = divider(grid)
    h, w = len(grid), len(grid[0])
    for point in red_cells(grid):
        rr, cc = reflected(point, orientation, d)
        if 0 <= rr < h and 0 <= cc < w and out[rr][cc] == 0:
            out[rr][cc] = 3
    return out


def normalize(cells):
    cells = set(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def source_side(grid):
    orientation, d = divider(grid)
    offsets = [(c - d if orientation == "vertical" else r - d) for r, c in red_cells(grid)]
    if max(offsets) < 0:
        return "negative"
    if min(offsets) > 0:
        return "positive"
    return "crosses"


def distractor_cells(grid):
    colors = sorted({value for row in grid for value in row} - {0, 2, 5})
    # Inputs must not contain output color 3, so exactly one remaining color is the distractor.
    colors = [color for color in colors if color != 3]
    if len(colors) != 1:
        raise ValueError(f"expected one distractor color, got {colors}")
    color = colors[0]
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    return color, cells


def observed(grid, source_shapes=None, distractor_shapes=None):
    orientation, _ = divider(grid)
    color, distractor = distractor_cells(grid)
    source_norm = normalize(red_cells(grid))
    distractor_norm = normalize(distractor)
    result = {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "orientation": orientation,
        "source_side": source_side(grid),
        "distractor_color": color,
    }
    if source_shapes is not None:
        result["shape_variant"] = tuple(source_shapes).index(source_norm)
    if distractor_shapes is not None:
        result["distractor_shape"] = tuple(distractor_shapes).index(distractor_norm)
    return result


def changed_cells(a, b):
    return [
        (r, c, a[r][c], b[r][c])
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]
