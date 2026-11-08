"""Independent oracle and reproducible audit for af373b71d67d.

This module is test/reviewer tooling, not label authority.  The Python geometry
is intentionally independent of the production generator.  ``--racket``
executes the selected canonical Racket program and never silently falls back.
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

ROOT = Path(__file__).resolve().parents[3]
TASK = "af373b71d67d"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=find_root(__file__))


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    p = r + dr, c + dc
                    if 0 <= p[0] < h and 0 <= p[1] < w and p not in seen:
                        if grid[p[0]][p[1]] == color:
                            seen.add(p)
                            stack.append(p)
            result.append(cells)
    return result


def _border(r0, c0, r1, c1):
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def scene(grid):
    motif_parts = _components(grid, 3)
    if len(motif_parts) != 1:
        raise ValueError(f"expected one color-3 object, found {len(motif_parts)}")
    candidates = []
    for color in sorted({v for row in grid for v in row} - {0, 3}):
        for cells in _components(grid, color):
            rs, cs = [p[0] for p in cells], [p[1] for p in cells]
            box = min(rs), min(cs), max(rs), max(cs)
            if set(cells) == _border(*box):
                candidates.append((len(cells), box, color, cells))
    if len(candidates) != 1:
        raise ValueError(f"expected one exact non-3 rectangular outline, found {len(candidates)}")
    _, box, color, frame_cells = candidates[0]
    return {
        "motif": sorted(motif_parts[0]),
        "frame_bbox": box,
        "frame_color": color,
        "frame_cells": sorted(frame_cells),
    }


def normalize(cells):
    cells = list(cells)
    if not cells:
        raise ValueError("cannot normalize an empty cell set")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def rotate_cw(cells):
    cells = normalize(cells)
    max_r = max(r for r, _ in cells)
    return normalize((c, max_r - r) for r, c in cells)


def rotate_ccw(cells):
    result = normalize(cells)
    for _ in range(3):
        result = rotate_cw(result)
    return result


def _stamp(grid, offsets, *, erase=True, centered=False, preserve_frame=False):
    facts = scene(grid)
    out = deepcopy(grid)
    if erase:
        for r, c in facts["motif"]:
            out[r][c] = 0
    r0, c0, r1, c1 = facts["frame_bbox"]
    offsets = normalize(offsets)
    oh = max(r for r, _ in offsets) + 1
    ow = max(c for _, c in offsets) + 1
    dr = dc = 0
    if centered:
        dr = max(0, ((r1 - r0 - 1) - oh) // 2)
        dc = max(0, ((c1 - c0 - 1) - ow) // 2)
    frame = set(facts["frame_cells"])
    for r, c in offsets:
        p = r0 + 1 + dr + r, c0 + 1 + dc + c
        if not (0 <= p[0] < len(out) and 0 <= p[1] < len(out[0])):
            raise ValueError(f"target cell {p} is out of bounds")
        if preserve_frame and p in frame:
            continue
        out[p[0]][p[1]] = 3
    return out


def intended_output(grid):
    return _stamp(grid, rotate_cw(scene(grid)["motif"]))


def unrotated_output(grid):
    return _stamp(grid, normalize(scene(grid)["motif"]))


def counterclockwise_output(grid):
    return _stamp(grid, rotate_ccw(scene(grid)["motif"]))


def keep_source_output(grid):
    return _stamp(grid, rotate_cw(scene(grid)["motif"]), erase=False)


def centered_output(grid):
    return _stamp(grid, rotate_cw(scene(grid)["motif"]), centered=True)


def preserve_frame_output(grid):
    return _stamp(grid, rotate_cw(scene(grid)["motif"]), preserve_frame=True)


def witness_flags(grid):
    intended = intended_output(grid)
    return {
        "clockwise_direction": (
            intended != unrotated_output(grid)
            and intended != counterclockwise_output(grid)
        ),
        "erase_source": intended != keep_source_output(grid),
        "top_left_anchor": intended != centered_output(grid),
        "frame_overwrite": intended != preserve_frame_output(grid),
    }


def profile_floor_schedule(band, count=20):
    profiles = set()
    for pair in canonical_pairs():
        grid = pair["input"]
        profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
    rows = []
    for index in range(count):
        seed = int(hashlib.sha256(
            f"profile-floor:v1:{TASK}:{band}:{index}".encode()
        ).hexdigest()[:12], 16)
        rows.append((seed, seed % 7919 + index, profiles))
    return rows


def racket_outputs(grids):
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    canonical_path = ROOT / "shared/data/canonical/puzzles.jsonl"
    program = None
    with canonical_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                program = row["program_solution"]
                break
    if not program:
        raise ValueError("canonical program is absent")
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
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
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "canonical": {},
        "bands": {},
    }
    pairs = canonical_pairs()
    report["canonical"] = {
        "pairs": len(pairs),
        "self_check_findings": [module.self_check(p["input"]) for p in pairs],
        "python_oracle_matches": sum(intended_output(p["input"]) == p["output"] for p in pairs),
        "centered_shortcut_matches": sum(centered_output(p["input"]) == p["output"] for p in pairs),
    }
    saved = [p["input"] for p in pairs]
    for band in ("easy", "medium", "hard"):
        counters = Counter()
        colors, shapes, inputs = set(), set(), set()
        for index in range(count):
            grid = module.generate(9000 + index, index, difficulty=band)
            counters["samples"] += 1
            counters["self_check_errors"] += bool(module.self_check(grid))
            counters["nondeterministic"] += grid != module.generate(9000 + index, index, difficulty=band)
            flags = witness_flags(grid)
            counters.update({f"witness_{name}": int(hit) for name, hit in flags.items()})
            facts = scene(grid)
            colors.add(facts["frame_color"])
            shapes.add((len(grid), len(grid[0])))
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            if index < 12:
                saved.append(grid)
        report["bands"][band] = dict(
            counters,
            frame_colors=sorted(colors),
            shapes=sorted(shapes),
            distinct_inputs=len(inputs),
        )
    return report, saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    source = (args.generator or ROOT / f"generators/{TASK}/generator.py").resolve()
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        any(report["canonical"]["self_check_findings"])
        or any(row["self_check_errors"] or row["nondeterministic"] for row in report["bands"].values())
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [i for i, (g, out) in enumerate(zip(grids, outputs)) if intended_output(g) != out]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # loud; no Python fallback
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
