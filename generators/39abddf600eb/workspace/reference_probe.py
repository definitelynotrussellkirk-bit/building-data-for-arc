"""Independent oracle and distribution probe for 39abddf600eb.

This tool deliberately does not import the production generator's geometry
helpers.  It parses a lawful framed input from pixels, computes the Manhattan
bisector directly, and can compare a repaired generator against the real Racket
authority.  It is reusable by task-local tests and future reviewers.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "39abddf600eb"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as read_pairs, find_root

    return read_pairs(TASK, root=find_root(__file__))


def _validate_grid(grid):
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer colors 0..9")


def parse_scene(grid):
    """Return frame bounds/color and the two seed triples from pixels only."""
    _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    candidates = []
    for color in sorted({grid[r][c] for r, c in nonzero} - {9}):
        points = {(r, c) for r, c in nonzero if grid[r][c] == color}
        if not points:
            continue
        rs = [r for r, _ in points]
        cs = [c for _, c in points]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        if r2 - r1 < 2 or c2 - c1 < 2:
            continue
        border = (
            {(r1, c) for c in range(c1, c2 + 1)}
            | {(r2, c) for c in range(c1, c2 + 1)}
            | {(r, c1) for r in range(r1, r2 + 1)}
            | {(r, c2) for r in range(r1, r2 + 1)}
        )
        if points == border:
            candidates.append((r1, c1, r2, c2, color, border))
    if len(candidates) != 1:
        raise ValueError(f"expected one rectangular frame, found {len(candidates)}")
    r1, c1, r2, c2, frame_color, border = candidates[0]
    if not (0 < r1 < r2 < h - 1 and 0 < c1 < c2 < w - 1):
        raise ValueError("frame must be strictly inset from the grid boundary")
    extras = nonzero - border
    seeds = sorted((r, c, grid[r][c]) for r, c in extras)
    if len(seeds) != 2:
        raise ValueError(f"expected two seeds, found {len(seeds)}")
    for r, c, color in seeds:
        if not (r1 < r < r2 and c1 < c < c2):
            raise ValueError("seed lies outside the strict frame interior")
        if color in (0, 9, frame_color):
            raise ValueError("seed color collides with background, marker, or frame")
    return {
        "height": h,
        "width": w,
        "r1": r1,
        "c1": c1,
        "r2": r2,
        "c2": c2,
        "frame_color": frame_color,
        "border": border,
        "seeds": seeds,
    }


def seed_geometry(grid):
    scene = parse_scene(grid)
    (ar, ac, _), (br, bc, _) = scene["seeds"]
    if (ar + ac - br - bc) % 2:
        return "identity"
    if ar == br or ac == bc:
        return "axis"
    return "diagonal"


def observed(grid):
    scene = parse_scene(grid)
    a, b = scene["seeds"]
    return {
        "grid_h": scene["height"],
        "grid_w": scene["width"],
        "frame_color": scene["frame_color"],
        "seed_geometry": seed_geometry(grid),
        "seed_color_relation": "same" if a[2] == b[2] else "different",
    }


def manhattan_output(grid):
    """Independent intended rule: redraw scene and paint strict-interior ties."""
    scene = parse_scene(grid)
    h, w = scene["height"], scene["width"]
    out = [[0] * w for _ in range(h)]
    for r, c in scene["border"]:
        out[r][c] = scene["frame_color"]
    for r, c, color in scene["seeds"]:
        out[r][c] = color
    (ar, ac, _), (br, bc, _) = scene["seeds"]
    for r in range(scene["r1"] + 1, scene["r2"]):
        for c in range(scene["c1"] + 1, scene["c2"]):
            if abs(r - ar) + abs(c - ac) == abs(r - br) + abs(c - bc):
                out[r][c] = 9
    return out


def diagonal_only_output(grid):
    """Plausible wrong rule: skip aligned seed pairs, otherwise act correctly."""
    scene = parse_scene(grid)
    (ar, ac, _), (br, bc, _) = scene["seeds"]
    if ar == br or ac == bc:
        return deepcopy(grid)
    return manhattan_output(grid)


def witness_input():
    """Exact aligned-seed counterexample to the diagonal-only shortcut."""
    g = [[0] * 12 for _ in range(10)]
    for c in range(1, 11):
        g[1][c] = g[8][c] = 5
    for r in range(1, 9):
        g[r][1] = g[r][10] = 5
    g[4][3] = 2
    g[4][7] = 3
    return g


def racket_outputs(grids):
    """Apply the selected canonical program through the real Racket bridge."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    row = None
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            candidate = json.loads(line)
            if candidate.get("task_id") == TASK:
                row = candidate
                break
    if row is None:
        raise KeyError(TASK)
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": row["program_solution"], "grids": grids})
        )
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket parity worker failed: {result}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket parity worker returned an incomplete batch")
        return outputs


def audit(module, count):
    canonical = canonical_pairs()
    canonical_errors = [module.self_check(pair["input"]) for pair in canonical]
    canonical_matches = sum(manhattan_output(pair["input"]) == pair["output"] for pair in canonical)
    rows = {}
    all_inputs = set()
    samples = []
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        key = "default" if band is None else band
        counter = Counter()
        shapes, geometries, relations, colors = set(), set(), set(), set()
        exact_profiles = 0
        for index in range(count):
            # Walk consecutive sample indices so periodic production branches
            # (notably the seven-step seed-color schedule) are all exercised.
            seed = 3109 + band_index * 100_000 + index
            sample_index = band_index * count + index
            grid = module.generate(seed, sample_index, difficulty=band)
            issues = module.self_check(grid)
            obs = observed(grid)
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            all_inputs.add(digest)
            counter["draws"] += 1
            counter["self_check_failures"] += bool(issues)
            counter["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            counter["identity"] += manhattan_output(grid) == grid
            counter["rival_disagreements"] += diagonal_only_output(grid) != manhattan_output(grid)
            shapes.add((obs["grid_h"], obs["grid_w"]))
            geometries.add(obs["seed_geometry"])
            relations.add(obs["seed_color_relation"])
            colors.add(obs["frame_color"])
            exact_profiles += (obs["grid_h"], obs["grid_w"], len({v for row in grid for v in row})) in {
                (11, 13, 4), (10, 12, 4), (12, 14, 4), (11, 11, 4), (12, 13, 4)
            }
            if index < 8:
                samples.append(grid)
        rows[key] = {
            **counter,
            "distinct_shapes": len(shapes),
            "geometries": sorted(geometries),
            "relations": sorted(relations),
            "frame_colors": sorted(colors),
            "exact_profile_hits": exact_profiles,
        }
    rotation_counts = Counter()
    rotation_failures = []
    rotation_inputs = []
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        band_name = "default" if band is None else band
        for start in range(12):
            seed = 910_000 + band_index * 1_000 + start
            pairs = []
            for sample_index in range(start, start + 4):
                grid = module.generate(seed, sample_index, difficulty=band)
                rotation_inputs.append(grid)
                pairs.append({"input": grid, "output": manhattan_output(grid)})
            rotation_counts["windows"] += 1
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                rival_refuted = any(
                    diagonal_only_output(pair["input"]) != pair["output"] for pair in demos
                )
                try:
                    hook_reasons = module.lesson_identifiable(deepcopy(demos), deepcopy(query))
                except Exception as exc:  # pragma: no cover - diagnostic capture
                    hook_reasons = [f"{type(exc).__name__}: {exc}"]
                rotation_counts["rotations"] += 1
                rotation_counts["unrefuted_rotations"] += int(not rival_refuted)
                rotation_counts["hook_failures"] += int(bool(hook_reasons))
                if (not rival_refuted or hook_reasons) and len(rotation_failures) < 12:
                    rotation_failures.append({
                        "band": band_name,
                        "start": start,
                        "query_index": query_index,
                        "demo_geometries": [seed_geometry(pair["input"]) for pair in demos],
                        "query_geometry": seed_geometry(query["input"]),
                        "rival_refuted": rival_refuted,
                        "hook_reasons": list(hook_reasons),
                    })

    witness = witness_input()
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical_pairs": len(canonical),
        "canonical_oracle_matches": canonical_matches,
        "canonical_self_check_errors": canonical_errors,
        "by_band": rows,
        "distinct_inputs": len(all_inputs),
        "cyclic_query_rotation": {
            **rotation_counts,
            "failure_examples": rotation_failures,
            "design": "For each band and starts 0..11, rotate each member of a four-example consecutive window into the query slot; score the other three demonstrations.",
        },
        "witness": {
            "input": witness,
            "intended_python": manhattan_output(witness),
            "diagonal_only_rival": diagonal_only_output(witness),
            "differing_cells": [
                [r, c]
                for r in range(len(witness))
                for c in range(len(witness[0]))
                if manhattan_output(witness)[r][c] != diagonal_only_output(witness)[r][c]
            ],
        },
        "sampling_design": "Four band-specific deterministic consecutive schedules; distinct-input count is a set union, not a sum.",
        "warning": "Python geometry is an independent supplementary oracle; --racket performs authority validation.",
    }
    parity_grids = [pair["input"] for pair in canonical] + [witness] + samples + rotation_inputs
    unique_parity_grids = []
    seen = set()
    for grid in parity_grids:
        digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
        if digest not in seen:
            seen.add(digest)
            unique_parity_grids.append(grid)
    return report, unique_parity_grids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250, help="draws per difficulty band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    exit_code = int(
        report["canonical_oracle_matches"] != report["canonical_pairs"]
        or any(report["canonical_self_check_errors"])
        or any(row["self_check_failures"] or row["nondeterministic"] for row in report["by_band"].values())
        or report["cyclic_query_rotation"]["unrefuted_rotations"]
        or report["cyclic_query_rotation"]["hook_failures"]
    )
    report["racket"] = {"status": "not_requested", "checked": 0}
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            expected = [manhattan_output(grid) for grid in grids]
            mismatches = [i for i, (actual, want) in enumerate(zip(outputs, expected)) if actual != want]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # pragma: no cover - environment diagnostic
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "version": report["version"],
        "canonical_self_check_errors": report["canonical_self_check_errors"],
        "by_band": report["by_band"],
        "cyclic_query_rotation": report["cyclic_query_rotation"],
        "racket": report["racket"],
    }, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
