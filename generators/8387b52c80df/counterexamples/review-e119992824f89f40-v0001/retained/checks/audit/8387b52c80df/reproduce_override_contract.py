from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "8387b52c80df"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
gen, source_path, source_sha = load_selected_generator(TASK, root=ROOT)


def frame_observations(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    rows = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0 = min(rr for rr, _ in cells)
            r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            c1 = max(cc for _, cc in cells)
            if r1 - r0 < 2 or c1 - c0 < 2:
                continue
            border = {
                (rr, cc)
                for rr in range(r0, r1 + 1)
                for cc in range(c0, c1 + 1)
                if rr in (r0, r1) or cc in (c0, c1)
            }
            if set(cells) != border:
                continue
            seeds = sorted(
                {
                    grid[rr][cc]
                    for rr in range(r0 + 1, r1)
                    for cc in range(c0 + 1, c1)
                    if grid[rr][cc] not in (0, color)
                }
            )
            rows.append(
                {
                    "frame_color": color,
                    "bbox": [r0, c0, r1, c1],
                    "seed_colors": seeds,
                }
            )
    return sorted(rows, key=lambda x: x["bbox"])


def call(**kwargs):
    try:
        grid = gen.generate(0, 0, **kwargs)
        return {
            "accepted": True,
            "grid": grid,
            "grid_sha256": hashlib.sha256(
                json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "shape": [len(grid), len(grid[0])],
            "observed_frames": frame_observations(grid),
            "self_check": list(gen.self_check(grid, difficulty=kwargs.get("difficulty"))),
        }
    except Exception as exc:
        return {
            "accepted": False,
            "exception": f"{type(exc).__name__}: {exc}",
        }


baseline = call(difficulty="medium")
requested_overrides = {
    "difficulty": "medium",
    "frame_color": 1,
    "seed_color": 9,
    "palette_kind": "warm_frame",
    "palette_size": 2,
    "position_bias": "scattered",
    "n_distinct_colors": 7,
}
requested = call(**requested_overrides)
unknown = call(difficulty="medium", mystery_override=12345)

report = {
    "schema": "audit-override-contract-v1",
    "task_id": TASK,
    "generator_path": str(source_path.relative_to(ROOT)),
    "generator_sha256": source_sha,
    "version": getattr(gen, "VERSION", None),
    "axes": getattr(gen, "AXES", None),
    "seed": 0,
    "sample_index": 0,
    "baseline": baseline,
    "requested_overrides": requested_overrides,
    "requested": requested,
    "requested_equals_baseline": requested.get("grid") == baseline.get("grid"),
    "advertised_but_rejected": {
        "easy_grid_h_6": call(difficulty="easy", grid_h=6),
        "easy_n_frames_2": call(difficulty="easy", n_frames=2),
    },
    "unknown_override": unknown,
    "unknown_equals_baseline": unknown.get("grid") == baseline.get("grid"),
    "finding": (
        "Accepted exact semantic overrides do not affect the returned grid; "
        "advertised easy values can be rejected, and an unknown key is accepted."
    ),
}

out = HERE / "override-contract-witness.json"
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "out": str(out),
    "generator_sha256": source_sha,
    "requested_equals_baseline": report["requested_equals_baseline"],
    "requested_observed_frames": requested.get("observed_frames"),
    "requested_self_check": requested.get("self_check"),
    "easy_grid_h_6": report["advertised_but_rejected"]["easy_grid_h_6"],
    "easy_n_frames_2": report["advertised_but_rejected"]["easy_n_frames_2"],
    "unknown_accepted": unknown.get("accepted"),
    "unknown_equals_baseline": report["unknown_equals_baseline"],
}, indent=2, sort_keys=True))
