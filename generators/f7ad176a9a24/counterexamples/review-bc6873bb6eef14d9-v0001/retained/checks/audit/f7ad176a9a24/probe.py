from __future__ import annotations

from collections import deque
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "f7ad176a9a24"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
REQUEST = {
    "seed": 0,
    "sample_index": 0,
    "difficulty": "medium",
    "overrides": {
        "grid_h": 28,
        "grid_w": 28,
        "n_match": 5,
        "n_other": 6,
    },
}


def components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            comp = []
            while queue:
                rr, cc = queue.popleft()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            out.append(comp)
    return out


def normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return [(r - min_r, c - min_c) for r, c in cells]


def topology_signature(cells):
    cells = set(normalize(cells))
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    background = {(r, c) for r in range(h) for c in range(w)} - cells
    seen = set()
    regions = []
    for start in sorted(background):
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        region = []
        while queue:
            r, c = queue.popleft()
            region.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in background and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        regions.append(region)
    border = sum(
        any(r in (0, h - 1) or c in (0, w - 1) for r, c in region)
        for region in regions
    )
    return [border, len(regions) - border]


grid = GEN.generate(
    REQUEST["seed"],
    REQUEST["sample_index"],
    difficulty=REQUEST["difficulty"],
    **REQUEST["overrides"],
)
red = components(grid, 2)
blue = components(grid, 1)
red_signature = topology_signature(red[0]) if len(red) == 1 else None
blue_signatures = [topology_signature(comp) for comp in blue]
match_count = sum(sig == red_signature for sig in blue_signatures)
other_count = len(blue_signatures) - match_count
payload = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA256,
    "rule_hash_declared": getattr(GEN, "RULE_HASH", None),
    "request": REQUEST,
    "observed": {
        "shape": [len(grid), len(grid[0])],
        "red_components": len(red),
        "blue_components": len(blue),
        "matching_blue_components": match_count,
        "nonmatching_blue_components": other_count,
        "red_signature": red_signature,
        "blue_signatures": blue_signatures,
        "self_check": GEN.self_check(grid),
    },
    "honored": {
        "grid_h": len(grid) == REQUEST["overrides"]["grid_h"],
        "grid_w": len(grid[0]) == REQUEST["overrides"]["grid_w"],
        "n_match": match_count == REQUEST["overrides"]["n_match"],
        "n_other": other_count == REQUEST["overrides"]["n_other"],
    },
    "input": grid,
}
(HERE / "probe.json").write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps({k: payload[k] for k in ("generator_sha256", "request", "observed", "honored")}, indent=2))
