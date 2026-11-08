"""Independent geometry/oracle helpers for reviewing d2f8cb1c91b2.

This file deliberately does not import transformation or merge helpers from the
production generator.  It is usable by task tests and by future reviewers as a
small source-bound census/parity tool.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

from reviewer_support import canonical_pairs as load_canonical_pairs, find_root

TASK_ID = "d2f8cb1c91b2"
TRANSFORMS = ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr")
ROOT = find_root(__file__)


def load_generator(path: str | os.PathLike[str] | None = None):
    default = ROOT / "generators" / TASK_ID / "generator.py"
    if not default.is_file():
        default = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    module_path = Path(path or os.environ.get("GENERATOR_UNDER_TEST", default))
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return load_canonical_pairs(TASK_ID, root=ROOT, variant=0)


def transform_grid(grid: list[list[int]], code: str) -> list[list[int]]:
    """Independent D4 transform in the canonical rule's naming order."""
    if not grid or any(len(row) != len(grid) for row in grid):
        raise ValueError("transform expects a nonempty square grid")
    n = len(grid)
    out = [[0] * n for _ in range(n)]
    for row in range(n):
        for col in range(n):
            if code == "id":
                target = row, col
            elif code == "r1":
                target = col, n - 1 - row
            elif code == "r2":
                target = n - 1 - row, n - 1 - col
            elif code == "r3":
                target = n - 1 - col, row
            elif code == "fh":
                target = row, n - 1 - col
            elif code == "fv":
                target = n - 1 - row, col
            elif code == "tr":
                target = col, row
            elif code == "atr":
                target = n - 1 - col, n - 1 - row
            else:
                raise ValueError(f"unknown transform {code!r}")
            out[target[0]][target[1]] = grid[row][col]
    return out


def split_panels(grid: list[list[int]]) -> tuple[list[list[int]], ...]:
    if not grid or any(len(row) != 15 for row in grid) or len(grid) != 3:
        raise ValueError("expected a 3x15 four-panel input")
    return tuple(
        [list(row[left : left + 3]) for row in grid]
        for left in (0, 4, 8, 12)
    )


def infer_matches(grid: list[list[int]]) -> list[str]:
    panel_a, panel_b, _, _ = split_panels(grid)
    return [code for code in TRANSFORMS if transform_grid(panel_a, code) == panel_b]


def infer_transform(grid: list[list[int]], *, require_unique: bool = False) -> str:
    matches = infer_matches(grid)
    if not matches:
        raise ValueError("no D4 transform maps panel A to panel B")
    if require_unique and len(matches) != 1:
        raise ValueError(f"expected one transform, found {matches}")
    return matches[0]


def merge_layers(tx: list[list[int]], y: list[list[int]], *, conflict: str = "marker") -> list[list[int]]:
    out = [[0] * len(tx[0]) for _ in tx]
    for row in range(len(tx)):
        for col in range(len(tx[0])):
            a, b = tx[row][col], y[row][col]
            if a == 0:
                value = b
            elif b == 0 or a == b:
                value = a
            elif conflict == "marker":
                value = 9
            elif conflict == "keep_x":
                value = a
            elif conflict == "keep_y":
                value = b
            else:
                raise ValueError(conflict)
            out[row][col] = value
    return out


def reference_output(grid: list[list[int]]) -> list[list[int]]:
    _, _, panel_x, panel_y = split_panels(grid)
    return merge_layers(transform_grid(panel_x, infer_transform(grid)), panel_y)


def merge_stats(grid: list[list[int]]) -> dict[str, int]:
    _, _, panel_x, panel_y = split_panels(grid)
    transformed = transform_grid(panel_x, infer_transform(grid))
    stats = {"both_zero": 0, "x_only": 0, "y_only": 0, "match": 0, "conflict": 0}
    for row in range(3):
        for col in range(3):
            a, b = transformed[row][col], panel_y[row][col]
            if a == 0 and b == 0:
                stats["both_zero"] += 1
            elif b == 0:
                stats["x_only"] += 1
            elif a == 0:
                stats["y_only"] += 1
            elif a == b:
                stats["match"] += 1
            else:
                stats["conflict"] += 1
    return stats


def observed(grid: list[list[int]]) -> dict[str, Any]:
    colors = {value for row in grid for value in row if value not in (0, 5)}
    return {
        "transform": infer_transform(grid, require_unique=True),
        "palette_size": len(colors),
    }


def component_count(grid: list[list[int]]) -> int:
    """Count 4-connected same-color non-background components."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    count = 0
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            count += 1
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                rr, cc = stack.pop()
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return count


def transpose_alias_rival(grid: list[list[int]]) -> list[list[int]]:
    _, _, panel_x, panel_y = split_panels(grid)
    code = infer_transform(grid)
    if code in {"r3", "atr"}:
        code = "tr"
    return merge_layers(transform_grid(panel_x, code), panel_y)


def no_transform_rival(grid: list[list[int]]) -> list[list[int]]:
    _, _, panel_x, panel_y = split_panels(grid)
    return merge_layers(panel_x, panel_y)


def keep_y_conflict_rival(grid: list[list[int]]) -> list[list[int]]:
    _, _, panel_x, panel_y = split_panels(grid)
    return merge_layers(transform_grid(panel_x, infer_transform(grid)), panel_y, conflict="keep_y")


def matching_is_conflict_rival(grid: list[list[int]]) -> list[list[int]]:
    _, _, panel_x, panel_y = split_panels(grid)
    tx = transform_grid(panel_x, infer_transform(grid))
    out = merge_layers(tx, panel_y)
    for row in range(3):
        for col in range(3):
            if tx[row][col] != 0 and tx[row][col] == panel_y[row][col]:
                out[row][col] = 9
    return out


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Apply the selected canonical Racket rule to grids through the public runtime."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        catalog = Catalog(ROOT)
        prepare_runtime(catalog, stage, TASK_ID)
        source = catalog.get(TASK_ID)["variants"][0]["program_solution"]
        request = {"program": source, "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request), encoding="utf-8")
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("parity-request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request["grids"]]
    print(json.dumps(outputs))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket parity failed: {result}")
        return json.loads(result["stdout"])


def audit(module: Any, samples_per_band: int = 100) -> dict[str, Any]:
    report: dict[str, Any] = {"task_id": TASK_ID, "bands": {}, "failures": []}
    for band in ("easy", "medium", "hard"):
        transforms: set[str] = set()
        palettes: set[int] = set()
        max_components = 0
        unique: set[str] = set()
        for index in range(samples_per_band):
            grid = module.generate(100_000 + index, index, difficulty=band)
            reasons = module.self_check(deepcopy(grid))
            if reasons:
                report["failures"].append({"band": band, "index": index, "self_check": reasons})
                continue
            facts = observed(grid)
            transforms.add(facts["transform"])
            palettes.add(facts["palette_size"])
            max_components = max(max_components, component_count(grid))
            unique.add(json.dumps(grid, separators=(",", ":")))
            if reference_output(grid) != module.reference_output(deepcopy(grid)):
                report["failures"].append({"band": band, "index": index, "oracle": "mismatch"})
        report["bands"][band] = {
            "transforms": sorted(transforms),
            "palette_sizes": sorted(palettes),
            "max_components": max_components,
            "unique_inputs": len(unique),
        }
    return report
