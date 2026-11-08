#!/usr/bin/env python3
"""Hash-bound, findings-only probes for the two assigned audit targets."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

WORK = Path(__file__).resolve().parents[2]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "shared" / "runtime"), str(REPO / "src")]

TARGETS = {
    "d172afae0ee5": REPO / "shared/data/base/solutions/banks/9397d19eada0/easy_55_move_object_to_marker__d172afae0ee5.json",
    "fd24427a4ff0": REPO / "shared/data/base/solutions/training/9772c176__fd24427a4ff0.json",
}


def load_module(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def grid_sha(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def normalize_cells(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    h = max(r for r, _ in cells) - r0 + 1
    w = max(c for _, c in cells) - c0 + 1
    rows = [[0] * w for _ in range(h)]
    for r, c in cells:
        rows[r - r0][c - c0] = 1
    return ["".join(map(str, row)) for row in rows]


def color_components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def row_profile(cells):
    by_row = defaultdict(list)
    for r, c in cells:
        by_row[r].append(c)
    return [len(by_row[r]) for r in sorted(by_row)]


def examples(payload):
    vc = payload["visible_context"]
    pairs = list(vc.get("train", []))
    for entry in vc.get("test_inputs", []):
        pairs.append(entry if isinstance(entry, dict) else {"input": entry})
    return pairs


def call(module, *, seed=17, sample_index=3, **overrides):
    try:
        grid = module.generate(seed, sample_index, **overrides)
        return {"accepted": True, "grid_sha256": grid_sha(grid), "dims": [len(grid), len(grid[0])]}
    except Exception as exc:  # evidence capture
        return {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}


def main():
    report = {"probe_version": 1, "targets": {}}
    for task_id, canonical_path in TARGETS.items():
        module, source_path = load_module(task_id)
        payload = json.loads(canonical_path.read_text())
        item = {
            "generator_source": str(source_path.relative_to(WORK)),
            "generator_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            "canonical_source": str(canonical_path.relative_to(WORK)),
            "canonical_source_sha256": hashlib.sha256(canonical_path.read_bytes()).hexdigest(),
            "version": module.VERSION,
        }

        scalar_cases = [
            ("float_seed", {"seed": 1.0, "sample_index": 3}),
            ("negative_sample_index", {"seed": 17, "sample_index": -1}),
            ("float_sample_index", {"seed": 17, "sample_index": 1.0}),
        ]
        item["scalar_contract"] = {name: call(module, **kwargs) for name, kwargs in scalar_cases}

        if task_id == "d172afae0ee5":
            comparisons = [
                ("palette_kind", "warm", "cool"),
                ("texture", "warm", "cool"),
            ]
            item["override_comparisons"] = {}
            for axis, left, right in comparisons:
                a = call(module, **{axis: left})
                b = call(module, **{axis: right})
                item["override_comparisons"][axis] = {
                    "left": left, "right": right, "left_result": a, "right_result": b,
                    "outputs_identical": a.get("grid_sha256") == b.get("grid_sha256"),
                }
            canonical_shapes = []
            canonical_checks = []
            for i, ex in enumerate(examples(payload)):
                grid = ex["input"]
                cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)]
                canonical_shapes.append({"example_index": i, "occupancy": normalize_cells(cells), "cell_count": len(cells)})
                canonical_checks.append({"example_index": i, "errors": module.self_check(grid)})
            generated_shapes = {}
            for seed in range(20):
                grid = module.generate(seed, 0)
                cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)]
                sig = "/".join(normalize_cells(cells))
                generated_shapes[sig] = generated_shapes.get(sig, 0) + 1
            item["canonical_object_shapes"] = canonical_shapes
            item["canonical_self_check"] = canonical_checks
            item["generated_object_shapes_seed_0_19"] = generated_shapes
        else:
            comparisons = [
                ("body_h", 2, 8),
                ("top_w", 3, 9),
                ("position_bias", "center", "top_left"),
                ("body_w_delta", 1, 3),
            ]
            item["override_comparisons"] = {}
            for axis, left, right in comparisons:
                a = call(module, **{axis: left})
                b = call(module, **{axis: right})
                item["override_comparisons"][axis] = {
                    "left": left, "right": right, "left_result": a, "right_result": b,
                    "outputs_identical": a.get("grid_sha256") == b.get("grid_sha256"),
                }
            canonical_checks = []
            for i, ex in enumerate(examples(payload)):
                grid = ex["input"]
                comps = color_components(grid, 8)
                canonical_checks.append({
                    "example_index": i,
                    "self_check_errors": module.self_check(grid),
                    "component_row_widths": [row_profile(comp) for comp in comps],
                })
            item["canonical_self_check_and_profiles"] = canonical_checks

        report["targets"][task_id] = item

    output = Path(__file__).with_suffix(".json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
