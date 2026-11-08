"""Independent oracle, rival probes, and audit CLI for 3799ce10ce15.

This module deliberately does not import implementation helpers from generator.py.
The Python oracle is supplementary evidence; ``--racket`` invokes the canonical
Racket authority and never silently substitutes the Python implementation.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "3799ce10ce15"
_HERE = Path(__file__).resolve()

# In the library the helper lives under shared/runtime; copied task-test runtimes
# may expose it directly at their root. Locate the module by existence first,
# then let reviewer_support.find_root bind canonical data to this file's tree.
for _ancestor in (_HERE.parent, *_HERE.parents):
    for _candidate in (_ancestor, _ancestor / "shared" / "runtime"):
        if (_candidate / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_candidate))
            break
    else:
        continue
    break
else:  # fail loudly instead of guessing a fixed parent depth
    raise FileNotFoundError(f"reviewer_support.py not found above {_HERE}")

from reviewer_support import (  # noqa: E402
    canonical_pairs as _canonical_pairs,
    canonical_path,
    find_root,
)

ROOT = find_root(__file__)


def _default_generator_path():
    candidates = (
        ROOT / f"generators/{TASK}/generator.py",
        ROOT / f"puzzle_generators/per_puzzle/{TASK}/generator.py",
        _HERE.parents[1] / "generator.py",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"generator {TASK} not found under {ROOT}")


def load_generator(path=None):
    path = Path(path or _default_generator_path()).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs():
    return list(_canonical_pairs(TASK, root=ROOT))


def _rectangular(grid):
    return (
        isinstance(grid, list)
        and bool(grid)
        and isinstance(grid[0], list)
        and bool(grid[0])
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    )


def _components_of_nine(grid):
    if not _rectangular(grid):
        raise ValueError("grid must be a non-empty rectangle")
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        todo = deque([start])
        cells = {start}
        while todo:
            r, c = todo.popleft()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in unseen:
                    unseen.remove((rr, cc))
                    cells.add((rr, cc))
                    todo.append((rr, cc))
        components.append(cells)
    return components


def frames(grid):
    result = []
    for cells in _components_of_nine(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
            continue
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if cells == border:
            result.append((r0, c0, r1, c1))
    return sorted(result)


def legend(grid):
    if not _rectangular(grid):
        raise ValueError("grid must be a non-empty rectangle")
    return [value for value in grid[0] if value not in (0, 9)]


def intended_output(grid):
    pal = legend(grid)
    out = []
    for r0, c0, r1, c1 in frames(grid):
        present = {
            grid[r][c]
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, 9)
        }
        out.append([color if color in present else 0 for color in pal])
    return out


def fixed_canonical_windows(grid):
    """Shortcut that exactly fits public pairs: fixed legend/frame windows."""
    if not _rectangular(grid):
        return []
    h, w = len(grid), len(grid[0])
    positions = (2, 5, 8)
    pal = [grid[0][c] if c < w else 0 for c in positions]
    boxes = ((3, 1, 9, 5), (3, 7, 9, 11), (3, 13, 9, 17))
    out = []
    for r0, c0, r1, c1 in boxes:
        present = set()
        for r in range(r0 + 1, min(r1, h)):
            for c in range(c0 + 1, min(c1, w)):
                present.add(grid[r][c])
        out.append([color if color not in (0, 9) and color in present else 0 for color in pal])
    return out


def exactly_once_presence(grid):
    pal = legend(grid)
    out = []
    for r0, c0, r1, c1 in frames(grid):
        counts = Counter(
            grid[r][c]
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, 9)
        )
        out.append([color if counts[color] == 1 else 0 for color in pal])
    return out


def observed(grid):
    pal = legend(grid)
    bboxes = frames(grid)
    counts = []
    for r0, c0, r1, c1 in bboxes:
        cc = Counter(
            grid[r][c]
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] in pal
        )
        counts.extend(value for value in cc.values() if value)
    copies = counts[0] if counts and len(set(counts)) == 1 else None
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_size": len(pal),
        "n_frames": len(bboxes),
        "copies_per_present": copies,
        "legend_columns": tuple(c for c, value in enumerate(grid[0]) if value not in (0, 9)),
        "frame_bboxes": tuple(bboxes),
    }


def racket_outputs(grids):
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_row()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    outputs=[runner._apply_rule(bridge,name,g) for g in request['grids']]
    print(json.dumps(outputs))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count):
    totals = Counter()
    per_band = {}
    samples = []
    all_shapes = set()
    all_boxes = set()
    for band in (None, "easy", "medium", "hard"):
        cc = Counter()
        shapes, boxes, palettes, frame_counts, copies = set(), set(), set(), set(), set()
        for index in range(count):
            grid = module.generate(1709 + index, index * 11 + 3, difficulty=band)
            obs = observed(grid)
            cc["samples"] += 1
            cc["self_check_errors"] += bool(module.self_check(grid))
            cc["nondeterministic"] += grid != module.generate(
                1709 + index, index * 11 + 3, difficulty=band
            )
            cc["fixed_window_disagreements"] += (
                fixed_canonical_windows(grid) != intended_output(grid)
            )
            cc["exactly_once_disagreements"] += (
                exactly_once_presence(grid) != intended_output(grid)
            )
            shapes.add((obs["grid_h"], obs["grid_w"]))
            boxes.update(obs["frame_bboxes"])
            palettes.add(obs["palette_size"])
            frame_counts.add(obs["n_frames"])
            copies.add(obs["copies_per_present"])
            if index < 12:
                samples.append(grid)
        cc["distinct_shapes"] = len(shapes)
        cc["distinct_frame_bboxes"] = len(boxes)
        cc["palette_sizes"] = sorted(palettes)
        cc["frame_counts"] = sorted(frame_counts)
        cc["copies_per_present"] = sorted(x for x in copies if x is not None)
        per_band[str(band)] = dict(cc)
        totals.update(cc)
        all_shapes.update(shapes)
        all_boxes.update(boxes)
    totals["distinct_shapes"] = len(all_shapes)
    totals["distinct_frame_bboxes"] = len(all_boxes)
    canonical_errors = [module.self_check(pair["input"]) for pair in canonical_pairs()]
    return {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "canonical_self_check_errors": canonical_errors,
        "canonical_python_matches": sum(
            intended_output(pair["input"]) == pair["output"] for pair in canonical_pairs()
        ),
        "counts": dict(totals),
        "by_band": per_band,
        "warning": "Python oracle is supplementary evidence, not the label authority.",
    }, [pair["input"] for pair in canonical_pairs()] + samples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100, help="samples per difficulty band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    path = args.generator or _default_generator_path()
    report["generator_sha256"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["rule_hash"] = hashlib.sha256(
        " ".join(canonical_row()["program_solution"].split()).encode()
    ).hexdigest()[:12]
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        any(report["canonical_self_check_errors"])
        or report["canonical_python_matches"] != len(canonical_pairs())
        or report["counts"].get("self_check_errors", 0)
        or report["counts"].get("nondeterministic", 0)
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            expected = [intended_output(grid) for grid in grids]
            mismatches = [i for i, pair in enumerate(zip(outputs, expected)) if pair[0] != pair[1]]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # surfaced in the report; never a silent fallback
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("version", "canonical_python_matches", "counts", "racket")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
