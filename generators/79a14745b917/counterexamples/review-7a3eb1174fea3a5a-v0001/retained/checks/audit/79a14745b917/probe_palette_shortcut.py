#!/usr/bin/env python3
"""Measure the frame-color support and exhibit a lookup-vs-parity counterexample."""
from __future__ import annotations

from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path

HOME = Path(__file__).resolve().parents[3] / "repo" / "generators" / "79a14745b917"
SOURCE = HOME / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_79a14745b917", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, cells))
    return result


def frame_colors(grid):
    found = []
    for color, cells in components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
        border = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)
        }
        if r2 - r1 >= 2 and c2 - c1 >= 2 and set(cells) == border:
            found.append(color)
    return found


def flip_lr(rect):
    return [row[::-1] for row in rect]


def flip_ud(rect):
    return rect[::-1]


def transform_single_frame(grid, use_lr):
    out = [row[:] for row in grid]
    interior = [row[1:-1] for row in grid[1:-1]]
    transformed = flip_lr(interior) if use_lr else flip_ud(interior)
    for r, row in enumerate(transformed, start=1):
        out[r][1:-1] = row
    return out


def main():
    gen = load_generator()
    observed = set()
    samples = 512
    for offset in range(samples):
        grid = gen.generate(1000 + offset, 31 * offset + 7, difficulty=("easy", "medium", "hard")[offset % 3])
        observed.update(frame_colors(grid))

    # Lawful odd frame color 9.  The intended parity rule is LR; a lookup
    # shortcut learned from generated support {3,7}->LR and {4,8}->UD chooses UD.
    counterexample = [
        [9, 9, 9, 9, 9, 9],
        [9, 2, 0, 0, 0, 9],
        [9, 0, 5, 0, 0, 9],
        [9, 0, 0, 0, 0, 9],
        [9, 9, 9, 9, 9, 9],
    ]
    intended = transform_single_frame(counterexample, use_lr=True)
    shortcut = transform_single_frame(counterexample, use_lr=(9 in {3, 7}))
    report = {
        "task_id": gen.TASK_ID,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "samples": samples,
        "observed_frame_colors": sorted(observed),
        "observed_odd_frame_colors": sorted(c for c in observed if c % 2),
        "observed_even_frame_colors": sorted(c for c in observed if c % 2 == 0),
        "lookup_shortcut": "LR iff frame color is 3 or 7; otherwise UD",
        "counterexample_input": counterexample,
        "intended_odd_parity_output": intended,
        "lookup_shortcut_output": shortcut,
        "outputs_differ": intended != shortcut,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if observed == {3, 4, 7, 8} and intended != shortcut else 1


if __name__ == "__main__":
    raise SystemExit(main())
