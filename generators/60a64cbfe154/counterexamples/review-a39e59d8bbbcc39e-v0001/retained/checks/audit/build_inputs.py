from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
sys.path.insert(0, str(REPO / "src"))


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components8(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < h
                            and 0 <= nc < w
                            and grid[nr][nc] != 0
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            result.append(tuple(sorted(cells)))
    return result


def ff_rival_no_mirror(grid):
    out = [row[:] for row in grid]
    comps = components8(grid)
    singles = [comp[0] for comp in comps if len(comp) == 1]
    sources = [comp for comp in comps if len(comp) > 1]
    for source in sources:
        colors = {grid[r][c] for r, c in source}
        for anchor_color in colors:
            anchors = [(r, c) for r, c in source if grid[r][c] == anchor_color]
            if len(anchors) != 1:
                continue
            ar, ac = anchors[0]
            for tr, tc in singles:
                if grid[tr][tc] != anchor_color:
                    continue
                for sr, sc in source:
                    dr, dc = sr - ar, sc - ac
                    if dr == dc == 0:
                        continue
                    rr, cc = tr + dr, tc + dc  # deliberately never mirror color 2
                    if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                        out[rr][cc] = grid[sr][sc]
    return out


def color_components4(grid, color):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        comp = []
        while queue:
            r, c = queue.popleft()
            comp.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
        result.append(tuple(sorted(comp)))
    return result


def move_first_occupied_to_marker(grid):
    """Rival: align lexicographically first occupied shape cell to marker."""
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    colors = sorted({value for row in grid for value in row if value})
    for color in colors:
        comps = color_components4(grid, color)
        marker = min(comps, key=lambda comp: (len(comp), comp))
        shape = max(comps, key=lambda comp: (len(comp), tuple(reversed(comp))))
        mr, mc = marker[0]
        ar, ac = min(shape)
        for r, c in shape:
            out[mr + r - ar][mc + c - ac] = color
    return out


# Audit target 1: reproduce the previously indexed lead from the current bytes.
ff, ff_path = load("ff76baf6c2d9")
ff_inputs = [ff.generate(800009, i, difficulty="easy") for i in range(36, 40)]
ff_valid = [ff.self_check(grid) for grid in ff_inputs]
assert all(not errors for errors in ff_valid), ff_valid
ff_dir = ROOT / "checks/audit/ff76baf6c2d9"
(ff_dir / "input.json").write_text(json.dumps(ff_inputs, indent=2) + "\n")
(ff_dir / "rival.json").write_text(
    json.dumps([ff_rival_no_mirror(grid) for grid in ff_inputs], indent=2) + "\n"
)

# Diagnostic scan using the task's own mirror for intended outputs.  The supported
# Racket command below is used for the retained four-grid counterexample.
scan_counts = {}
for band in ("easy", "medium", "hard"):
    ambiguous = 0
    total = 1000
    for start in range(total):
        lesson = [ff.generate(800009, start + j, difficulty=band) for j in range(4)]
        intended = [ff.rule_mirror(grid) for grid in lesson]
        rival = [ff_rival_no_mirror(grid) for grid in lesson]
        if intended[:3] == rival[:3] and intended[3] != rival[3]:
            ambiguous += 1
    scan_counts[band] = {"windows": total, "query_only_mirror_branch": ambiguous}
(ff_dir / "scan.json").write_text(
    json.dumps(
        {
            "task_id": ff.TASK_ID,
            "generator_sha256": sha256(ff_path),
            "seed": 800009,
            "sample_start_range": [0, 999],
            "lesson_policy": "three consecutive demonstrations followed by one query",
            "diagnostic_oracle": "generator.rule_mirror (counterexample itself rechecked with supported Racket apply)",
            "counts": scan_counts,
        },
        indent=2,
        sort_keys=True,
    ) + "\n"
)

# Audit target 2: a validator-accepted shape with an empty bbox top-left.
sixty, sixty_path = load("60a64cbfe154")
grid = [[0] * 10 for _ in range(10)]
# Color 3 shape: bbox top-left is (1,1), but (1,1) is empty.
for r, c in ((1, 2), (2, 1), (2, 2)):
    grid[r][c] = 3
grid[6][1] = 3
# Color 4 control shape has an occupied bbox top-left.
for r, c in ((1, 7), (1, 8), (2, 7)):
    grid[r][c] = 4
grid[6][7] = 4
errors = sixty.self_check(grid)
assert errors == [], errors
sixty_dir = ROOT / "checks/audit/60a64cbfe154"
(sixty_dir / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(sixty_dir / "rival.json").write_text(
    json.dumps(move_first_occupied_to_marker(grid), indent=2) + "\n"
)

# Verify the structural restriction empirically and from the finite source library.
all_static_shapes_have_bbox_tl = all((0, 0) in shape for shape in sixty._SHAPES)
observed = 0
violations = 0
for band in ("easy", "medium", "hard"):
    for sample_index in range(1000):
        generated = sixty.generate(910031, sample_index, difficulty=band)
        colors = sorted({v for row in generated for v in row if v})
        for color in colors:
            comps = color_components4(generated, color)
            shape = max(comps, key=len)
            top = min(r for r, _ in shape)
            left = min(c for _, c in shape)
            observed += 1
            if (top, left) not in shape:
                violations += 1
(sixty_dir / "domain_scan.json").write_text(
    json.dumps(
        {
            "task_id": sixty.TASK_ID,
            "generator_sha256": sha256(sixty_path),
            "seed": 910031,
            "sample_index_range_per_band": [0, 999],
            "difficulty_bands": ["easy", "medium", "hard"],
            "generated_shapes_checked": observed,
            "empty_bbox_top_left_seen": violations,
            "static_shape_library_size": len(sixty._SHAPES),
            "all_static_shapes_have_occupied_bbox_top_left": all_static_shapes_have_bbox_tl,
            "custom_counterexample_self_check": errors,
        },
        indent=2,
        sort_keys=True,
    ) + "\n"
)

print(json.dumps({
    "ff_generator_sha256": sha256(ff_path),
    "ff_self_check": ff_valid,
    "ff_scan": scan_counts,
    "sixty_generator_sha256": sha256(sixty_path),
    "sixty_self_check": errors,
    "sixty_generated_shapes_checked": observed,
    "sixty_empty_bbox_top_left_seen": violations,
}, indent=2, sort_keys=True))
