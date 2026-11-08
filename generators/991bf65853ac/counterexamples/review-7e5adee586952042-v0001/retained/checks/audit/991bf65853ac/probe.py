#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "991bf65853ac"
OUT = Path(__file__).resolve().parent


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            q = deque([(r0, c0)])
            seen.add((r0, c0))
            cells = []
            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            result.append(sorted(cells))
    return result


def crop(grid, cells):
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def enclosed_zero_regions(piece):
    h, w = len(piece), len(piece[0])
    zeros = {(r, c) for r in range(h) for c in range(w) if piece[r][c] == 0}
    outside = set()
    q = deque(
        (r, c)
        for r, c in zeros
        if r in (0, h - 1) or c in (0, w - 1)
    )
    outside.update(q)
    while q:
        r, c = q.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            if nxt in zeros and nxt not in outside:
                outside.add(nxt)
                q.append(nxt)
    enclosed = zeros - outside
    regions = []
    seen = set()
    for start in sorted(enclosed):
        if start in seen:
            continue
        region = []
        q = deque([start])
        seen.add(start)
        while q:
            cell = q.popleft()
            region.append(cell)
            r, c = cell
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in enclosed and nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
        regions.append(sorted(region))
    return regions


def filled_crop(piece):
    color = max(v for row in piece for v in row)
    output = [row[:] for row in piece]
    for region in enclosed_zero_regions(piece):
        for r, c in region:
            output[r][c] = color
    return output


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def main():
    root = find_root(__file__)
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    grid = module.generate(0, 0, texture="all_holed")
    comps = components(grid)
    details = []
    rivals = []
    for index, cells in enumerate(comps):
        piece = crop(grid, cells)
        holes = enclosed_zero_regions(piece)
        details.append(
            {
                "component_index": index,
                "color": max(grid[r][c] for r, c in cells),
                "size": len(cells),
                "bbox_shape": [len(piece), len(piece[0])],
                "hole_regions": len(holes),
            }
        )
        if holes:
            rivals.append(
                {
                    "component_index": index,
                    "output": filled_crop(piece),
                    "output_sha256": digest(filled_crop(piece)),
                }
            )

    evidence = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path),
        "generator_sha256": source_sha256,
        "version": module.VERSION,
        "probe": {"seed": 0, "sample_index": 0, "texture": "all_holed"},
        "declared_degenerate": "all_holed" in module.DEGENERATE_TEXTURES,
        "documented_invariant": "exactly one component has a hole",
        "self_check": module.self_check(grid),
        "component_count": len(comps),
        "holed_component_count": sum(d["hole_regions"] > 0 for d in details),
        "components": details,
        "input_sha256": digest(grid),
        "interpretation": (
            "The declared all_holed degenerate contains two eligible target "
            "components but self_check accepts it, contradicting the validator "
            "docstring and generator invariant. The selected rule therefore "
            "silently teaches a size/hole-count/tie-order selector on accepted input."
        ),
    }
    (OUT / "input.json").write_text(json.dumps({"input": grid}, indent=2) + "\n")
    (OUT / "rivals.json").write_text(json.dumps(rivals, indent=2) + "\n")
    (OUT / "probe.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha256,
        "self_check": evidence["self_check"],
        "holed_component_count": evidence["holed_component_count"],
        "rival_output_hashes": [r["output_sha256"] for r in rivals],
    }, sort_keys=True))
    if evidence["self_check"] or evidence["holed_component_count"] != 2:
        raise SystemExit("expected accepted two-holed counterexample")


if __name__ == "__main__":
    main()
