from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit"


def load(task: str):
    path = ROOT / "generators" / task / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, tuple(sorted(cells))))
    return out


def color_group_rival(grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for color in sorted({v for row in grid for v in row if v != 0}):
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        shift = h - 1 - max(r for r, _ in cells)
        for r, c in cells:
            out[r + shift][c] = color
    return out


def border_cache_rival(module, grid):
    analysis = module._analysis(grid)
    out = [row[:] for row in analysis["grid"]]
    cache = {}
    for frame in analysis["frames"]:
        if frame["seed"] is None:
            continue
        border = frame["color"]
        cache.setdefault(border, frame["seed"][2])
        for r, c in frame["interior"]:
            out[r][c] = cache[border]
    return out


def sha(obj: Any) -> str:
    raw = json.dumps(obj, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


m = load("11fc1931b5ef")
custom = json.loads((OUT / "11fc1931b5ef" / "input.json").read_text())
racket = json.loads((OUT / "11fc1931b5ef" / "racket.json").read_text())["results"][0]["output"]
rival = color_group_rival(custom)
repeated = 0
draws = 0
component_counts = []
for band in ("easy", "medium", "hard"):
    for seed in range(200):
        grid = m.generate(seed, seed * 7 + 3, difficulty=band)
        comps = components(grid)
        counts = {}
        for color, _ in comps:
            counts[color] = counts.get(color, 0) + 1
        repeated += int(any(n > 1 for n in counts.values()))
        component_counts.append(len(comps))
        draws += 1

override_counts = []
override_errors = []
for seed in range(50):
    try:
        grid = m.generate(seed, seed, difficulty="medium", n_blobs=5)
        override_counts.append(len(components(grid)))
    except Exception as exc:
        override_errors.append(repr(exc))

report = {
    "task_id": "11fc1931b5ef",
    "generator_sha256": hashlib.sha256((ROOT / "generators/11fc1931b5ef/generator.py").read_bytes()).hexdigest(),
    "custom_input_self_check": m.self_check(custom),
    "custom_input_component_count": len(components(custom)),
    "custom_input_same_color_component_count": sum(1 for color, _ in components(custom) if color == 2),
    "racket_output_sha256": sha(racket),
    "rival": "shift every nonzero color as one global group until that color bbox touches bottom",
    "rival_output": rival,
    "rival_output_sha256": sha(rival),
    "rival_differs_from_racket": rival != racket,
    "generated_probe": {
        "bands": ["easy", "medium", "hard"],
        "seeds_per_band": 200,
        "draws": draws,
        "draws_with_repeated_color_components": repeated,
        "component_count_min": min(component_counts),
        "component_count_max": max(component_counts),
    },
    "n_blobs_5_override_probe": {
        "draws": 50,
        "errors": override_errors,
        "observed_component_counts": sorted(set(override_counts)),
        "max_observed": max(override_counts) if override_counts else None,
    },
}
(OUT / "11fc1931b5ef" / "probe.json").write_text(json.dumps(report, indent=2) + "\n")

m = load("a2eace95c1cf")
custom = json.loads((OUT / "a2eace95c1cf" / "input.json").read_text())
racket = json.loads((OUT / "a2eace95c1cf" / "racket.json").read_text())["results"][0]["output"]
rival = border_cache_rival(m, custom)
repeated = 0
role_reuse = 0
draws = 0
for band in ("easy", "medium", "hard"):
    for seed in range(200):
        grid = m.generate(seed, seed * 7 + 3, difficulty=band)
        analysis = m._analysis(grid)
        repeated += int(len(set(analysis["border_colors"])) < len(analysis["border_colors"]))
        role_reuse += int(any(seed_color in analysis["border_colors"] for seed_color in analysis["seed_colors"]))
        draws += 1

canonical = []
for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
    row = json.loads(line)
    if row.get("task_id") == "a2eace95c1cf":
        tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
        for pair in [*row["train"], *tests]:
            grid = [[int(x) for x in r] if isinstance(r, str) else list(r) for r in pair["input"]]
            a = m._analysis(grid)
            canonical.append({
                "border_colors": a["border_colors"],
                "has_repeated_border": len(set(a["border_colors"])) < len(a["border_colors"]),
            })
        break

report = {
    "task_id": "a2eace95c1cf",
    "generator_sha256": hashlib.sha256((ROOT / "generators/a2eace95c1cf/generator.py").read_bytes()).hexdigest(),
    "custom_input_self_check": m.self_check(custom),
    "custom_input_analysis": {
        "n_frames": m._analysis(custom)["n_frames"],
        "border_colors": m._analysis(custom)["border_colors"],
        "seed_colors": m._analysis(custom)["seed_colors"],
    },
    "local_python_matches_racket": m._fill_local(custom) == racket,
    "racket_output_sha256": sha(racket),
    "rival": "cache the first fill color by frame border color and reuse it for later frames",
    "rival_output": rival,
    "rival_output_sha256": sha(rival),
    "rival_differs_from_racket": rival != racket,
    "generated_probe": {
        "bands": ["easy", "medium", "hard"],
        "seeds_per_band": 200,
        "draws": draws,
        "draws_with_repeated_border_color": repeated,
        "draws_with_seed_color_reused_as_some_border": role_reuse,
    },
    "canonical_pairs": canonical,
    "canonical_pairs_with_repeated_border_color": sum(item["has_repeated_border"] for item in canonical),
}
(OUT / "a2eace95c1cf" / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
