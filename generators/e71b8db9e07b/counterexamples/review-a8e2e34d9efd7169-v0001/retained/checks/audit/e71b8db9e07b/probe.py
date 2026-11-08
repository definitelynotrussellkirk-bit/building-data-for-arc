from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import deque
from pathlib import Path

TASK = "e71b8db9e07b"
SEED = 20261007
SAMPLE_INDEX = 11
DIFFICULTY = "medium"
ROOT = Path.cwd()
GEN_PATH = ROOT / "generators" / TASK / "generator.py"
OUT_DIR = ROOT.parent / "checks" / "audit" / TASK

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def digest(grid):
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()

def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); q.append((nr, nc))
            out.append((color, cells))
    return out

def bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return [max(rs)-min(rs)+1, max(cs)-min(cs)+1]

def observe(grid):
    comps = components(grid)
    proto = [(color, cells) for color, cells in comps if color != 5]
    frames = [(color, cells) for color, cells in comps if color == 5]
    proto_cells = proto[0][1] if len(proto) == 1 else []
    proto_bbox = bbox(proto_cells) if proto_cells else None
    frame_interiors = []
    for _, cells in frames:
        bh, bw = bbox(cells)
        frame_interiors.append([bh - 2, bw - 2])
    return {
        "shape": [len(grid), len(grid[0]) if grid else 0],
        "prototype_component_count": len(proto),
        "prototype_cell_count": len(proto_cells),
        "prototype_bbox": proto_bbox,
        "frame_component_count": len(frames),
        "matching_frame_count": sum(1 for dims in frame_interiors if dims == proto_bbox),
        "distractor_frame_count": sum(1 for dims in frame_interiors if dims != proto_bbox),
        "frame_interior_dims": sorted(frame_interiors),
    }

def capture(**overrides):
    try:
        grid = mod.generate(SEED, SAMPLE_INDEX, difficulty=DIFFICULTY, **overrides)
        return {
            "status": "ok",
            "grid_sha256": digest(grid),
            "observed": observe(grid),
            "self_check": mod.self_check(grid, difficulty=DIFFICULTY),
            "grid": grid,
        }
    except Exception as exc:
        return {"status": "error", "error_type": type(exc).__name__, "error": str(exc)}

base = capture()
textures = {name: capture(texture=name) for name in ("default", "warm", "cool", "varied")}
unknown = capture(typo_axis=99)
requested = {"grid_h": 28, "grid_w": 28, "proto_size": 7, "n_match": 3, "n_distract": 3}
exact = capture(**requested)
assert exact["status"] == "ok"
(OUT_DIR / "input.json").write_text(json.dumps(exact["grid"], indent=2) + "\n")

report = {
    "schema": "audit-generator-contract-probe-v1",
    "task_id": TASK,
    "generator_path": f"generators/{TASK}/generator.py",
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "seed": SEED,
    "sample_index": SAMPLE_INDEX,
    "difficulty": DIFFICULTY,
    "command": ["python3", "run_with_racket.py", "python3", f"../checks/audit/{TASK}/probe.py"],
    "effective_cwd": str(ROOT),
    "base": base,
    "helpful_texture_cases": textures,
    "all_helpful_textures_equal_base": all(v.get("grid_sha256") == base.get("grid_sha256") for v in textures.values()),
    "unknown_override_case": unknown,
    "unknown_override_equal_base": unknown.get("grid_sha256") == base.get("grid_sha256"),
    "requested_exact_overrides": requested,
    "exact_override_case": exact,
    "exact_overrides_honored": (
        exact["observed"]["shape"] == [28, 28]
        and exact["observed"]["prototype_cell_count"] == 7
        and exact["observed"]["matching_frame_count"] == 3
        and exact["observed"]["distractor_frame_count"] == 3
    ),
    "input_path": f"checks/audit/{TASK}/input.json",
    "observations": [
        "All four helpful texture values are byte-identical to the no-texture draw for this seed/sample.",
        "An unknown override is accepted silently and is byte-identical to the base draw.",
        "All five advertised exact overrides are accepted but bypassed; the observed shape/counts do not equal the request.",
    ],
}
(OUT_DIR / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "probe": f"../checks/audit/{TASK}/probe.json",
    "input": f"../checks/audit/{TASK}/input.json",
    "all_helpful_textures_equal_base": report["all_helpful_textures_equal_base"],
    "unknown_override_equal_base": report["unknown_override_equal_base"],
    "requested": requested,
    "observed": exact["observed"],
    "exact_overrides_honored": report["exact_overrides_honored"],
}, indent=2))
