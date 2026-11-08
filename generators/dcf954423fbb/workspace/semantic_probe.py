"""Independent semantic oracle and reusable audit for dcf954423fbb.

This module deliberately does not import helpers from the production generator.
It computes 4-connected components directly, supplies plausible rival rules, and
can sample a candidate generator for repeatable curriculum evidence.  The Racket
rule remains the label authority; :func:`rule_output` is supplementary test
oracle code.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Iterable

TASK_ID = "dcf954423fbb"
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if RUNTIME.is_dir():
    sys.path.insert(0, str(RUNTIME))

Grid = list[list[int]]
Cell = tuple[int, int]


def load_generator(path: str | os.PathLike[str] | None = None):
    """Load the selected or staged generator without package-cache reuse."""
    candidate = Path(
        path
        or os.environ.get("GENERATOR_UNDER_TEST", "")
        or (REPO_ROOT / "generators" / TASK_ID / "generator.py")
    ).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_dcf954423fbb", candidate)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {candidate}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    """Load normalized public canonical pairs through the portable helper."""
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK_ID, root=find_root(__file__))


def components(grid: Grid, color: int = 1) -> list[list[Cell]]:
    """Return deterministic 4-connected components of ``color``."""
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    answer: list[list[Cell]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            part: list[Cell] = []
            while stack:
                cell = stack.pop()
                part.append(cell)
                r, c = cell
                for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            answer.append(sorted(part))
    return answer


def touches_border(cells: Iterable[Cell], height: int, width: int) -> bool:
    return any(r in (0, height - 1) or c in (0, width - 1) for r, c in cells)


def border_sides(cells: Iterable[Cell], height: int, width: int) -> frozenset[str]:
    cells = tuple(cells)
    sides = set()
    if any(r == 0 for r, _ in cells):
        sides.add("top")
    if any(r == height - 1 for r, _ in cells):
        sides.add("bottom")
    if any(c == 0 for _, c in cells):
        sides.add("left")
    if any(c == width - 1 for _, c in cells):
        sides.add("right")
    return frozenset(sides)


def min_border_distance(cells: Iterable[Cell], height: int, width: int) -> int:
    return min(min(r, height - 1 - r, c, width - 1 - c) for r, c in cells)


def _paint_components(grid: Grid, predicate) -> Grid:
    output = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for part in components(grid, 1):
        if predicate(part, height, width):
            for row, col in part:
                output[row][col] = 2
    return output


def rule_output(grid: Grid) -> Grid:
    """Independent mirror: recolor whole 1-components that touch any border."""
    return _paint_components(grid, lambda part, h, w: touches_border(part, h, w))


def horizontal_edges_only(grid: Grid) -> Grid:
    """Wrong rival: only top/bottom contact counts as border contact."""
    return _paint_components(
        grid,
        lambda part, h, w: any(r in (0, h - 1) for r, _ in part),
    )


def near_border_recolors(grid: Grid) -> Grid:
    """Wrong rival: components at distance one also count as border-touching."""
    return _paint_components(
        grid,
        lambda part, h, w: min_border_distance(part, h, w) <= 1,
    )


def border_cells_only(grid: Grid) -> Grid:
    """Wrong rival: recolor literal border cells, not their whole components."""
    height, width = len(grid), len(grid[0])
    output = deepcopy(grid)
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 1 and (
                row in (0, height - 1) or col in (0, width - 1)
            ):
                output[row][col] = 2
    return output


def all_blue_recolors(grid: Grid) -> Grid:
    """Wrong rival: every blue component is recolored."""
    return [[2 if value == 1 else value for value in row] for row in grid]


def nearest_k_components(grid: Grid, count: int) -> Grid:
    """Wrong family: recolor a fixed number of components nearest an edge.

    Ties use component scan order only to make the rival deterministic.  The
    important shortcut is the fixed transformed-component count, not tie order.
    """
    height, width = len(grid), len(grid[0])
    parts = components(grid, 1)
    ranked = sorted(
        range(len(parts)),
        key=lambda index: (
            min_border_distance(parts[index], height, width),
            parts[index],
        ),
    )
    selected = set(ranked[:count])
    output = deepcopy(grid)
    for index, part in enumerate(parts):
        if index in selected:
            for row, col in part:
                output[row][col] = 2
    return output


def two_nearest_components(grid: Grid) -> Grid:
    """Wrong rival: always recolor exactly the two edge-nearest components."""
    return nearest_k_components(grid, 2)


def three_nearest_components(grid: Grid) -> Grid:
    """Wrong rival: always recolor exactly the three edge-nearest components."""
    return nearest_k_components(grid, 3)


RIVALS = {
    "horizontal_edges_only": horizontal_edges_only,
    "near_border_recolors": near_border_recolors,
    "border_cells_only": border_cells_only,
    "all_blue_recolors": all_blue_recolors,
}
LESSON_RIVALS = {
    **RIVALS,
    "two_nearest_components": two_nearest_components,
    "three_nearest_components": three_nearest_components,
}


def observed(grid: Grid) -> dict[str, object]:
    height, width = len(grid), len(grid[0])
    parts = components(grid, 1)
    side_sets = [border_sides(part, height, width) for part in parts]
    decoration = sorted({v for row in grid for v in row} - {0, 1})
    return {
        "grid_h": height,
        "grid_w": width,
        "n_blobs": len(parts),
        "palette": sorted({v for row in grid for v in row}),
        "decoration_colors": decoration,
        "border_blobs": sum(bool(sides) for sides in side_sets),
        "interior_blobs": sum(not sides for sides in side_sets),
        "side_only_blobs": sum(
            sides in ({"left"}, {"right"}) for sides in side_sets
        ),
        "near_border_interior": sum(
            not sides and min_border_distance(part, height, width) == 1
            for part, sides in zip(parts, side_sets)
        ),
        "touched_sides": sorted(set().union(*side_sets) if side_sets else set()),
    }


def explicit_right_edge_witness() -> Grid:
    """Small lawful scene where a right-only component must be recolored."""
    grid = [[0] * 10 for _ in range(8)]
    # Top-border component with an inward cell.
    for row, col in ((0, 2), (0, 3), (1, 3)):
        grid[row][col] = 1
    # Right-only component; it does not touch top or bottom.
    for row, col in ((2, 9), (3, 9), (3, 8)):
        grid[row][col] = 1
    # Near-border interior component, still fully interior.
    for row, col in ((5, 1), (5, 2), (6, 2)):
        grid[row][col] = 1
    for row, col in ((3, 4), (3, 5), (4, 4), (4, 5)):
        grid[row][col] = 7
    return grid


def racket_outputs(grids: list[Grid]) -> list[Grid]:
    """Execute the selected Racket authority in a portable staged runtime."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    src = REPO_ROOT / "src"
    if src.is_dir():
        sys.path.insert(0, str(src))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(REPO_ROOT), stage, TASK_ID)
        request = stage / "parity-request.json"
        request.write_text(json.dumps({"grids": grids}), encoding="utf-8")
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
bundle = runner._load_bundle("dcf954423fbb")
bridge, name = runner._open_bridge_with_rule(bundle.rule_callable_text)
try:
    grids = json.loads(Path("parity-request.json").read_text())["grids"]
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in grids]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket parity worker failed: {result['stderr']} {result['stdout']}"
            )
        return json.loads(result["stdout"])


def audit(module, per_band: int) -> dict:
    """Return reproducible counts for final-source curriculum review."""
    bands = (None, "easy", "medium", "hard")
    report: dict[str, object] = {
        "schema": "dcf954423fbb-semantic-probe-v2",
        "task_id": TASK_ID,
        "version": getattr(module, "VERSION", None),
        "per_band": {},
        "canonical_rival_fit": {},
    }
    public_pairs = canonical_pairs()
    for name, rival in LESSON_RIVALS.items():
        report["canonical_rival_fit"][name] = {
            "fits": sum(
                rival(pair["input"]) == pair["output"] for pair in public_pairs
            ),
            "pairs": len(public_pairs),
        }
    total = Counter()
    distinct_inputs: set[str] = set()
    for band in bands:
        counts = Counter()
        sides: set[str] = set()
        dimensions: set[tuple[int, int]] = set()
        blob_counts: set[int] = set()
        for index in range(per_band):
            seed = 4001 + index
            sample_index = 13 * index + 5
            grid = module.generate(seed, sample_index, difficulty=band)
            replay = module.generate(seed, sample_index, difficulty=band)
            counts["draws"] += 1
            counts["deterministic"] += grid == replay
            counts["self_check_clean"] += not module.self_check(grid)
            stats = observed(grid)
            sides.update(stats["touched_sides"])
            dimensions.add((stats["grid_h"], stats["grid_w"]))
            blob_counts.add(stats["n_blobs"])
            digest = hashlib.sha256(
                json.dumps(grid, separators=(",", ":")).encode()
            ).hexdigest()
            distinct_inputs.add(digest)
            truth = rule_output(grid)
            for name, rival in RIVALS.items():
                counts[f"refutes_{name}"] += rival(grid) != truth
        counts["distinct_dimensions"] = len(dimensions)
        counts["distinct_blob_counts"] = len(blob_counts)

        # A separate contiguous schedule catches lesson-level rivals that can
        # agree on individual grids but survive all three demonstrations.
        cycle_pairs = []
        for index in range(16):
            grid = module.generate(7301 + index, index, difficulty=band)
            cycle_pairs.append({"input": grid, "output": rule_output(grid)})
        counts["lesson_windows"] = len(cycle_pairs)
        for start in range(len(cycle_pairs)):
            demos = [
                cycle_pairs[(start + offset) % len(cycle_pairs)]
                for offset in range(3)
            ]
            query = cycle_pairs[(start + 3) % len(cycle_pairs)]
            for name, rival in LESSON_RIVALS.items():
                survives = all(
                    rival(demo["input"]) == demo["output"] for demo in demos
                )
                counts[f"lesson_survives_{name}"] += survives
                counts[f"lesson_changes_query_{name}"] += (
                    survives and rival(query["input"]) != query["output"]
                )

        row = dict(counts)
        row["touched_sides"] = sorted(sides)
        row["blob_counts"] = sorted(blob_counts)
        report["per_band"][str(band)] = row
        total.update(counts)
    report["totals"] = dict(total)
    report["unique_inputs"] = len(distinct_inputs)
    report["sampling"] = {
        "per_band": per_band,
        "seed": "4001+i",
        "sample_index": "13*i+5",
        "bands": [None, "easy", "medium", "hard"],
        "note": "Bands reuse seed/index tuples; unique_inputs is a set union.",
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.per_band)
    source = (args.generator or REPO_ROOT / "generators" / TASK_ID / "generator.py").resolve()
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    exit_code = 0
    expected = args.per_band
    for row in report["per_band"].values():
        required = (
            row.get("deterministic") == expected
            and row.get("self_check_clean") == expected
            and all(row.get(f"refutes_{name}") == expected for name in RIVALS)
            and row.get("lesson_windows") == 16
            and all(
                row.get(f"lesson_survives_{name}") == 0
                and row.get(f"lesson_changes_query_{name}") == 0
                for name in LESSON_RIVALS
            )
        )
        exit_code = max(exit_code, int(not required))
    if args.racket:
        grids = [pair["input"] for pair in canonical_pairs()]
        grids += [module.generate(9001 + i, i, difficulty="medium") for i in range(32)]
        try:
            outputs = racket_outputs(grids)
            mismatches = [
                index
                for index, (grid, output) in enumerate(zip(grids, outputs))
                if output != rule_output(grid)
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(grids),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # preserve unavailable/failure honestly
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    else:
        report["racket"] = {"status": "not_requested", "checked": 0}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
