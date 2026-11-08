"""Independent oracle and distribution probe for task 96d2d525a266.

This module is reviewer test tooling. The canonical Racket program remains the
label authority; the Python implementation exists to make regressions and rival
hypotheses inspectable and reproducible.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "96d2d525a266"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def positions_by_color(grid):
    result = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                result[value].append((r, c))
    return dict(result)


def colors_in_first_occurrence_order(grid):
    result = []
    seen = set()
    for row in grid:
        for value in row:
            if value != 0 and value not in seen:
                seen.add(value)
                result.append(value)
    return result


def rect_outline(a, b):
    r1, r2 = sorted((a[0], b[0]))
    c1, c2 = sorted((a[1], b[1]))
    return [
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    ]


def qualifying_pairs(grid):
    result = {}
    for color, cells in positions_by_color(grid).items():
        if (
            len(cells) == 2
            and cells[0][0] != cells[1][0]
            and cells[0][1] != cells[1][1]
        ):
            result[color] = tuple(cells)
    return result


def reference_output(grid, *, color_order=None, paint_background_only=False):
    """Independent translation of the canonical rule from original input cells."""
    source = deepcopy(grid)
    out = deepcopy(grid)
    by_color = positions_by_color(source)
    order = colors_in_first_occurrence_order(source) if color_order is None else list(color_order)
    for color in order:
        cells = by_color[color]
        if (
            len(cells) != 2
            or cells[0][0] == cells[1][0]
            or cells[0][1] == cells[1][1]
        ):
            continue
        for r, c in rect_outline(cells[0], cells[1]):
            if not paint_background_only or out[r][c] in (0, color):
                out[r][c] = color
    return out


def aligned_pair_rival(grid):
    """Wrong shortcut: every exact pair expands, including row/column pairs."""
    source = deepcopy(grid)
    out = deepcopy(grid)
    by_color = positions_by_color(source)
    for color in colors_in_first_occurrence_order(source):
        cells = by_color[color]
        if len(cells) != 2:
            continue
        for r, c in rect_outline(cells[0], cells[1]):
            out[r][c] = color
    return out


def multi_bbox_rival(grid):
    """Wrong shortcut: any color spanning two axes expands to its full bbox."""
    source = deepcopy(grid)
    out = deepcopy(grid)
    by_color = positions_by_color(source)
    for color in colors_in_first_occurrence_order(source):
        cells = by_color[color]
        if len(cells) < 2:
            continue
        rows = [p[0] for p in cells]
        cols = [p[1] for p in cells]
        if min(rows) == max(rows) or min(cols) == max(cols):
            continue
        for r, c in rect_outline((min(rows), min(cols)), (max(rows), max(cols))):
            out[r][c] = color
    return out


def background_only_rival(grid):
    """Wrong shortcut: outlines never overwrite another input/output color."""
    return reference_output(grid, paint_background_only=True)


def sorted_color_order_rival(grid):
    """Wrong shortcut: overlapping outlines are applied in numeric color order."""
    return reference_output(grid, color_order=sorted(positions_by_color(grid)))


def observed(grid):
    by_color = positions_by_color(grid)
    pair_count = 0
    for cells in by_color.values():
        if len(cells) == 2 and cells[0][0] != cells[1][0] and cells[0][1] != cells[1][1]:
            pair_count += 1
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pair_colors": pair_count,
        "n_decoy_colors": len(by_color) - pair_count,
    }


def features(grid):
    by_color = positions_by_color(grid)
    pairs = qualifying_pairs(grid)
    boxes = {}
    for color, (a, b) in pairs.items():
        boxes[color] = (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
    overlap = False
    colors = list(boxes)
    for i, color in enumerate(colors):
        a = boxes[color]
        for other in colors[i + 1 :]:
            b = boxes[other]
            if not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]):
                overlap = True
    intended = reference_output(grid)
    changed_nonzero = any(
        grid[r][c] != 0 and intended[r][c] != grid[r][c]
        for r in range(len(grid))
        for c in range(len(grid[0]))
    )
    return {
        # Count a teaching witness, not merely aligned geometry: an aligned
        # pair can be completely masked by later qualifying outlines.
        "aligned_decoy": (
            any(
                len(cells) == 2
                and (cells[0][0] == cells[1][0] or cells[0][1] == cells[1][1])
                and abs(cells[0][0] - cells[1][0]) + abs(cells[0][1] - cells[1][1]) > 1
                for cells in by_color.values()
            )
            and intended != aligned_pair_rival(grid)
        ),
        "multi_cell_decoy": any(len(cells) >= 3 for cells in by_color.values()),
        "overlapping_pair_boxes": overlap,
        "outline_overwrite": changed_nonzero,
        "order_sensitive_overlap": intended != sorted_color_order_rival(grid),
    }


def racket_outputs(grids):
    """Execute the actual canonical Racket authority; never silently fall back."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
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
        request = {"program": canonical()["program_solution"], "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request))
        script = r"""
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path('parity-request.json').read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge, name, g) for g in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count):
    report = {
        "schema": "96d2d525a266-independent-audit-v1",
        "version": module.VERSION,
        "canonical_self_check": [module.self_check(pair["input"]) for pair in canonical_pairs()],
        "canonical_oracle_matches": sum(reference_output(pair["input"]) == pair["output"] for pair in canonical_pairs()),
        "bands": {},
    }
    all_grids = []
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        shapes = set()
        inputs = set()
        pair_counts = set()
        decoy_counts = set()
        for i in range(count):
            grid = module.generate(9100 + i, i * 7 + 3, difficulty=band)
            all_grids.append(grid)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(9100 + i, i * 7 + 3, difficulty=band)
            obs = observed(grid)
            pair_counts.add(obs["n_pair_colors"])
            decoy_counts.add(obs["n_decoy_colors"])
            shapes.add((obs["grid_h"], obs["grid_w"]))
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            for name, present in features(grid).items():
                counts[name] += bool(present)
        report["bands"][str(band)] = dict(
            counts,
            distinct_shapes=len(shapes),
            distinct_inputs=len(inputs),
            pair_counts=sorted(pair_counts),
            decoy_counts=sorted(decoy_counts),
        )
    return report, all_grids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    path = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(any(report["canonical_self_check"]))
    if args.racket:
        sample = [pair["input"] for pair in canonical_pairs()] + grids[:64]
        try:
            outputs = racket_outputs(sample)
            expected = [reference_output(grid) for grid in sample]
            mismatches = [i for i, (a, b) in enumerate(zip(outputs, expected)) if a != b]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
