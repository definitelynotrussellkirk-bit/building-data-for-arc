"""Independent oracle and structural probe for task 5a215cef8bd1.

This module is reviewer tooling, not label authority.  ``panel_output`` mirrors
only the compact task rule visible in the canonical program.  ``racket_outputs``
uses the selected canonical Racket source when authoritative parity is needed.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from itertools import permutations
from pathlib import Path
import sys
from typing import Any, Iterable

TASK = "5a215cef8bd1"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

CONTROL_COLORS = (1, 3, 4, 6)
CONTROL_ORDERS = tuple(permutations(CONTROL_COLORS))


def load_generator(path: str | Path | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(TASK, root=find_root(ROOT))


def canonical_rule_source() -> str:
    """Read the selected canonical program from this repository tree."""
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK and row.get("program_solution"):
                return str(row["program_solution"])
    raise FileNotFoundError(f"{TASK}: selected canonical program not found")


def _rectangular_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid contains a non-ARC value")
    return len(grid), width


def _neighbors(cell: tuple[int, int]):
    r, c = cell
    yield r - 1, c
    yield r + 1, c
    yield r, c - 1
    yield r, c + 1


def color_components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    _rectangular_grid(grid)
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        stack = [start]
        seen: set[tuple[int, int]] = set()
        while stack:
            cell = stack.pop()
            if cell in seen:
                continue
            seen.add(cell)
            stack.extend(n for n in _neighbors(cell) if n in remaining and n not in seen)
        components.append(seen)
        remaining -= seen
    return components


def bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("empty cells")
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def crop_template(grid: list[list[int]]) -> list[list[int]]:
    components = color_components(grid, 2)
    if len(components) != 1:
        raise ValueError(f"expected one color-2 component, found {len(components)}")
    r1, c1, r2, c2 = bbox(components[0])
    return [
        [2 if grid[r][c] == 2 else 0 for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]


def rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def _recolor(grid: list[list[int]], color: int = 7) -> list[list[int]]:
    return [[color if value else 0 for value in row] for row in grid]


def _paste_clip(out: list[list[int]], block: list[list[int]], top: int, left: int) -> None:
    h, w = len(out), len(out[0])
    for r, row in enumerate(block):
        for c, value in enumerate(row):
            rr, cc = top + r, left + c
            if value and 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = value


def controls(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    _rectangular_grid(grid)
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in CONTROL_COLORS
    ]


def panel_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python rendition of the selected compact Racket rule."""
    template = crop_template(grid)
    th, tw = len(template), len(template[0])
    markers = controls(grid)
    rows = sorted({r for r, _, _ in markers})
    cols = sorted({c for _, c, _ in markers})
    out = [[0] * (2 * tw + 1) for _ in range(2 * th + 1)]
    transform = {
        1: lambda x: deepcopy(x),
        3: rotate_cw,
        4: rotate_180,
        6: flip_lr,
    }
    for r, c, color in markers:
        qr, qc = rows.index(r), cols.index(c)
        block = _recolor(transform[color](template))
        _paste_clip(out, block, qr * (th + 1), qc * (tw + 1))
    return out


def template_cells(grid: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    }


def template_size(grid: list[list[int]]) -> int:
    r1, c1, r2, c2 = bbox(template_cells(grid))
    if r2 - r1 != c2 - c1:
        raise ValueError("template bbox is not square")
    return r2 - r1 + 1


def control_order(grid: list[list[int]]) -> int:
    markers = controls(grid)
    rows = sorted({r for r, _, _ in markers})
    cols = sorted({c for _, c, _ in markers})
    ordered = tuple(
        next(color for r, c, color in markers if r == rr and c == cc)
        for rr in rows
        for cc in cols
    )
    return CONTROL_ORDERS.index(ordered)


def layout_mode(grid: list[list[int]]) -> str:
    tr1, tc1, tr2, tc2 = bbox(template_cells(grid))
    markers = controls(grid)
    cr1, cc1, cr2, cc2 = bbox((r, c) for r, c, _ in markers)
    candidates = []
    if cr2 < tr1:
        candidates.append("controls_above")
    if cr1 > tr2:
        candidates.append("controls_below")
    if cc2 < tc1:
        candidates.append("controls_left")
    if cc1 > tc2:
        candidates.append("controls_right")
    if not candidates:
        raise ValueError("template and control rectangle have no separating axis")
    # Generated layouts have a designated separating axis; diagonal layouts can
    # satisfy two names.  Prefer the axis with the greater blank moat, matching
    # the generator's observer convention.
    gaps = {
        "controls_above": tr1 - cr2 - 1,
        "controls_below": cr1 - tr2 - 1,
        "controls_left": tc1 - cc2 - 1,
        "controls_right": cc1 - tc2 - 1,
    }
    return max(candidates, key=lambda name: (gaps[name], -list(gaps).index(name)))


def observed(grid: list[list[int]]) -> dict[str, int | str]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_size": template_size(grid),
        "control_order": control_order(grid),
        "layout_mode": layout_mode(grid),
    }


def transform_signatures(grid: list[list[int]]) -> tuple[tuple[tuple[int, ...], ...], ...]:
    template = crop_template(grid)
    variants = (template, rotate_cw(template), rotate_180(template), flip_lr(template))
    return tuple(tuple(tuple(row) for row in variant) for variant in variants)


def fixed_3x3_panel(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: always crop/pad the template to 3x3 and emit 7x7."""
    template = crop_template(grid)
    fixed = [[0] * 3 for _ in range(3)]
    for r, row in enumerate(template[:3]):
        for c, value in enumerate(row[:3]):
            fixed[r][c] = value
    markers = controls(grid)
    rows = sorted({r for r, _, _ in markers})
    cols = sorted({c for _, c, _ in markers})
    out = [[0] * 7 for _ in range(7)]
    transform = {1: lambda x: deepcopy(x), 3: rotate_cw, 4: rotate_180, 6: flip_lr}
    for r, c, color in markers:
        _paste_clip(out, _recolor(transform[color](fixed)), rows.index(r) * 4, cols.index(c) * 4)
    return out


def rectangular_counterexample() -> list[list[int]]:
    """Law-looking 2x3 template whose rotation cannot fit the Racket slot."""
    g = [[0] * 10 for _ in range(8)]
    for r, c in ((1, 1), (1, 2), (1, 3), (2, 1), (2, 3)):
        g[r][c] = 2
    for (r, c), color in zip(((4, 5), (4, 7), (6, 5), (6, 7)), CONTROL_COLORS):
        g[r][c] = color
    return g


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"program": canonical_rule_source(), "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request))
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path("parity-request.json").read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=240)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])


def audit(module, count: int = 200) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": f"{TASK}-review-probe-v1",
        "version": getattr(module, "VERSION", None),
        "canonical_pairs": len(canonical_pairs()),
        "canonical_python_matches": 0,
        "samples": 0,
        "self_check_failures": 0,
        "nondeterministic": 0,
        "oracle_cell_loss": 0,
        "template_sizes": {},
        "layout_modes": {},
        "control_orders": set(),
        "input_shapes": set(),
        "fixed_3x3_disagreements": 0,
    }
    report["canonical_python_matches"] = sum(
        panel_output(pair["input"]) == pair["output"] for pair in canonical_pairs()
    )
    from collections import Counter
    sizes, layouts = Counter(), Counter()
    for band in ("easy", "medium", "hard"):
        for index in range(count):
            seed = 100_003 + index
            sample_index = index * 17 + 5
            grid = module.generate(seed, sample_index, difficulty=band)
            report["samples"] += 1
            report["self_check_failures"] += bool(module.self_check(grid))
            report["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            stats = observed(grid)
            sizes[stats["template_size"]] += 1
            layouts[stats["layout_mode"]] += 1
            report["control_orders"].add(stats["control_order"])
            report["input_shapes"].add((stats["grid_h"], stats["grid_w"]))
            output = panel_output(grid)
            expected_sevens = 4 * len(template_cells(grid))
            report["oracle_cell_loss"] += sum(value == 7 for row in output for value in row) != expected_sevens
            report["fixed_3x3_disagreements"] += fixed_3x3_panel(grid) != output
    report["template_sizes"] = dict(sorted(sizes.items()))
    report["layout_modes"] = dict(sorted(layouts.items()))
    report["control_orders"] = sorted(report["control_orders"])
    report["input_shapes"] = sorted(report["input_shapes"])
    report["generator_sha256"] = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    module = load_generator(args.generator)
    report = audit(module, args.count)
    report["racket"] = {"status": "not_requested", "checked": 0}
    if args.racket:
        grids = [pair["input"] for pair in canonical_pairs()]
        grids += [module.generate(919, index, difficulty="hard") for index in range(24)]
        outputs = racket_outputs(grids)
        mismatches = [i for i, (grid, out) in enumerate(zip(grids, outputs)) if panel_output(grid) != out]
        report["racket"] = {
            "status": "passed" if not mismatches else "failed",
            "checked": len(grids),
            "mismatches": mismatches,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return int(
        report["canonical_python_matches"] != report["canonical_pairs"]
        or report["self_check_failures"]
        or report["nondeterministic"]
        or report["oracle_cell_loss"]
        or report["racket"]["status"] == "failed"
    )


if __name__ == "__main__":
    raise SystemExit(main())
