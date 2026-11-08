#!/usr/bin/env python3
"""Independent oracle and reproducible curriculum audit for f41ae450c30b.

The geometry below intentionally does not import generator helpers.  It extracts
components, orders them, computes unobstructed line of sight, observes the three
public controls, and scores the blocker-blind alignment shortcut independently.
With ``--racket`` it additionally executes the repository's canonical Racket
program; failure or unavailability is reported as failure, never as a fallback.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
TARGET = Path(__file__).resolve().parents[1]
TASK_ID = "f41ae450c30b"
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

Grid = list[list[int]]
Cell = tuple[int, int]
Cells = tuple[Cell, ...]

PROFILE_DIMS = {
    "canonical_7x10": (7, 10),
    "canonical_8x11": (8, 11),
    "canonical_8x12": (8, 12),
    "canonical_9x12": (9, 12),
    "expanded_10x14": (10, 14),
    "expanded_12x16": (12, 16),
}
PROFILE_BY_DIMS = {dims: name for name, dims in PROFILE_DIMS.items()}
BANDS = ("easy", "medium", "hard")
LAYOUT_AXES = ("horizontal", "vertical")


def load_generator(path: Path | None = None):
    path = Path(path or TARGET / "generator.py").resolve()
    name = "f41ae450c30b_reviewed_generator"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict[str, Any]:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise ValueError(f"canonical task {TASK_ID} is absent")


def canonical_pairs() -> list[dict[str, Grid]]:
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    return len(grid), width


def extract_components(grid: Grid) -> list[dict[str, Any]]:
    """Extract nonzero same-color 4-connected components from first principles."""
    height, width = _validate_grid(grid)
    seen: set[Cell] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                rr, cc = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells))})
    return result


def ordered_components(grid: Grid) -> list[dict[str, Any]]:
    return sorted(
        extract_components(grid),
        key=lambda component: (
            Fraction(sum(col for _, col in component["cells"]), len(component["cells"])),
            Fraction(sum(row for row, _ in component["cells"]), len(component["cells"])),
        ),
    )


def aligned(a: Cells, b: Cells) -> bool:
    return any(ra == rb or ca == cb for ra, ca in a for rb, cb in b)


def visible(grid: Grid, a: Cells, b: Cells) -> bool:
    """Whether any aligned endpoint pair has only background or endpoints between."""
    a_set, b_set = set(a), set(b)
    for ra, ca in a:
        for rb, cb in b:
            if ra == rb:
                if all(
                    (ra, col) in a_set or (ra, col) in b_set or grid[ra][col] == 0
                    for col in range(min(ca, cb), max(ca, cb) + 1)
                ):
                    return True
            if ca == cb:
                if all(
                    (row, ca) in a_set or (row, ca) in b_set or grid[row][ca] == 0
                    for row in range(min(ra, rb), max(ra, rb) + 1)
                ):
                    return True
    return False


def solve_visibility_matrix(grid: Grid) -> Grid:
    components = ordered_components(grid)
    size = len(components)
    output = [[0 for _ in range(size)] for _ in range(size)]
    for row, left in enumerate(components):
        for col, right in enumerate(components):
            if row == col:
                output[row][col] = left["color"]
            elif visible(grid, left["cells"], right["cells"]):
                output[row][col] = 8
    return output


def solve_alignment_only(grid: Grid) -> Grid:
    """Plausible wrong rule: shared row/column counts despite third objects."""
    components = ordered_components(grid)
    size = len(components)
    output = [[0 for _ in range(size)] for _ in range(size)]
    for row, left in enumerate(components):
        for col, right in enumerate(components):
            if row == col:
                output[row][col] = left["color"]
            elif aligned(left["cells"], right["cells"]):
                output[row][col] = 8
    return output


def has_third_object_occlusion(grid: Grid) -> bool:
    components = extract_components(grid)
    for left_index in range(len(components)):
        for right_index in range(left_index + 1, len(components)):
            left = components[left_index]["cells"]
            right = components[right_index]["cells"]
            if aligned(left, right) and not visible(grid, left, right):
                return True
    return False


def observe_contract(grid: Grid) -> dict[str, Any]:
    """Recover public controls independently from geometry and dimensions."""
    height, width = _validate_grid(grid)
    try:
        scene_profile = PROFILE_BY_DIMS[(height, width)]
    except KeyError as exc:
        raise ValueError(f"unrecognized scene dimensions: {(height, width)}") from exc

    components = extract_components(grid)
    horizontal_dominoes = 0
    vertical_dominoes = 0
    for component in components:
        cells = component["cells"]
        if len(cells) != 2:
            raise ValueError(f"component is not a domino: {component}")
        (r1, c1), (r2, c2) = cells
        horizontal_dominoes += int(r1 == r2)
        vertical_dominoes += int(c1 == c2)
    if vertical_dominoes >= 3 and vertical_dominoes > horizontal_dominoes:
        layout_axis = "horizontal"
    elif horizontal_dominoes >= 3 and horizontal_dominoes > vertical_dominoes:
        layout_axis = "vertical"
    else:
        raise ValueError(
            "cannot infer layout_axis: "
            f"horizontal_dominoes={horizontal_dominoes}, vertical_dominoes={vertical_dominoes}"
        )
    return {
        "scene_profile": scene_profile,
        "n": len(components),
        "layout_axis": layout_axis,
    }


def _grid_digest(grid: Grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def audit(module: Any, per_band: int) -> tuple[dict[str, Any], list[Grid]]:
    if per_band < 1:
        raise ValueError("per_band must be positive")

    pairs = canonical_pairs()
    canonical_solver_mismatches = [
        index for index, pair in enumerate(pairs) if solve_visibility_matrix(pair["input"]) != pair["output"]
    ]
    canonical_self_check_errors = [module.self_check(pair["input"]) for pair in pairs]
    canonical_alignment_shortcut_matches = sum(
        solve_alignment_only(pair["input"]) == pair["output"] for pair in pairs
    )

    combinations = list(product(PROFILE_DIMS, (3, 4), LAYOUT_AXES))
    totals = Counter(
        {
            "samples": 0,
            "self_check_errors": 0,
            "nondeterministic": 0,
            "solver_mismatches": 0,
            "observer_mismatches": 0,
            "missing_occlusion_witness": 0,
            "alignment_rival_agreements": 0,
        }
    )
    by_band: dict[str, Any] = {}
    parity_grids: list[Grid] = [pair["input"] for pair in pairs]

    for band_index, band in enumerate(BANDS):
        band_counts = Counter()
        shapes: set[tuple[int, int]] = set()
        profiles: set[str] = set()
        component_counts: set[int] = set()
        axes: set[str] = set()
        digests: set[str] = set()
        for index in range(per_band):
            profile, n, layout_axis = combinations[(index + 7 * band_index) % len(combinations)]
            expected = {
                "scene_profile": profile,
                "n": n,
                "layout_axis": layout_axis,
            }
            seed = 910_000 + 100_000 * band_index + index
            sample_index = 17 * index + 3
            grid = module.generate(seed, sample_index, difficulty=band, **expected)
            repeated = module.generate(seed, sample_index, difficulty=band, **expected)
            issues = module.self_check(grid)
            solved = solve_visibility_matrix(grid)
            witness = has_third_object_occlusion(grid)
            observed = observe_contract(grid)

            totals["samples"] += 1
            totals["self_check_errors"] += bool(issues)
            totals["nondeterministic"] += grid != repeated
            totals["solver_mismatches"] += solved != module.rule_mirror(grid)
            totals["observer_mismatches"] += observed != expected or module.observe_overrides(grid) != expected
            totals["missing_occlusion_witness"] += not witness
            totals["alignment_rival_agreements"] += solved == solve_alignment_only(grid)

            band_counts["samples"] += 1
            band_counts["self_check_errors"] += bool(issues)
            band_counts["nondeterministic"] += grid != repeated
            band_counts["solver_mismatches"] += solved != module.rule_mirror(grid)
            band_counts["observer_mismatches"] += observed != expected
            band_counts["occlusion_witnesses"] += witness
            band_counts["alignment_rival_disagreements"] += solved != solve_alignment_only(grid)
            shapes.add((len(grid), len(grid[0])))
            profiles.add(observed["scene_profile"])
            component_counts.add(observed["n"])
            axes.add(observed["layout_axis"])
            digests.add(_grid_digest(grid))
            parity_grids.append(grid)

        by_band[band] = {
            **dict(band_counts),
            "distinct_inputs": len(digests),
            "shapes": sorted([list(shape) for shape in shapes]),
            "profiles": sorted(profiles),
            "component_counts": sorted(component_counts),
            "layout_axes": sorted(axes),
        }

    report = {
        "schema": "f41ae450c30b-independent-curriculum-audit-v1",
        "generator_version": getattr(module, "VERSION", None),
        "sampling": {
            "per_band": per_band,
            "bands": list(BANDS),
            "design": (
                "Each band cycles deterministically through the Cartesian product of six scene "
                "profiles, n in {3,4}, and both layout axes. Seeds and sample indices are fixed."
            ),
        },
        "canonical": {
            "pairs": len(pairs),
            "solver_mismatches": canonical_solver_mismatches,
            "self_check_errors": canonical_self_check_errors,
            "alignment_shortcut_matches": canonical_alignment_shortcut_matches,
        },
        "counts": dict(totals),
        "by_band": by_band,
        "independence_note": (
            "Component extraction, ordering, visibility, control observation, and the alignment "
            "rival are implemented in this probe. Generator public hooks are used only as cross-checks."
        ),
        "authority_note": (
            "The Python oracle is supplementary. Use --racket for direct canonical-program parity; "
            "that mode fails rather than silently falling back."
        ),
    }
    return report, parity_grids


def racket_outputs(grids: list[Grid]) -> list[Grid]:
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_row()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-reference-probe-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        request_path = stage / "parity-request.json"
        request_path.write_text(json.dumps({"program": program, "grids": grids}), encoding="utf-8")
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path('parity-request.json').read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request['grids']]
    print(json.dumps(outputs))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=300)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket parity worker failed: stdout={result['stdout']!r} stderr={result['stderr']!r}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError(f"Racket returned {len(outputs)} outputs for {len(grids)} grids")
        return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=TARGET / "generator.py")
    parser.add_argument("--per-band", type=int, default=250)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true", help="require direct canonical Racket parity")
    parser.add_argument(
        "--racket-samples",
        type=int,
        default=96,
        help="maximum generated samples sent to Racket, in addition to canonical pairs",
    )
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    if args.racket_samples < 1:
        parser.error("--racket-samples must be positive")

    generator_path = args.generator.resolve()
    module = load_generator(generator_path)
    report, grids = audit(module, args.per_band)
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    normalized_rule = " ".join(canonical_row()["program_solution"].split()).encode()
    report["canonical_rule_hash"] = hashlib.sha256(normalized_rule).hexdigest()[:12]
    report["racket"] = {"status": "not_requested", "checked": 0, "mismatches": []}

    canonical_count = len(canonical_pairs())
    selected = [*grids[:canonical_count], *grids[canonical_count:canonical_count + args.racket_samples]]
    if args.racket:
        try:
            outputs = racket_outputs(selected)
            mismatches = [
                index
                for index, (grid, output) in enumerate(zip(selected, outputs))
                if solve_visibility_matrix(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
        except Exception as exc:  # explicit in report; never a silent fallback
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "mismatches": [],
                "error": f"{type(exc).__name__}: {exc}",
            }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "schema": report["schema"],
                "canonical": report["canonical"],
                "counts": report["counts"],
                "by_band": report["by_band"],
                "racket": report["racket"],
            },
            indent=2,
            sort_keys=True,
        )
    )

    count_failures = sum(report["counts"][key] for key in report["counts"] if key != "samples")
    canonical_failed = bool(report["canonical"]["solver_mismatches"]) or any(
        report["canonical"]["self_check_errors"]
    )
    racket_failed = args.racket and report["racket"]["status"] != "passed"
    return int(bool(count_failures or canonical_failed or racket_failed))


if __name__ == "__main__":
    raise SystemExit(main())
