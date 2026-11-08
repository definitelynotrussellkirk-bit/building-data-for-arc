"""Independent oracle and source-bound qualification probe for 2b7bcfbf942b.

This file deliberately does not import geometry helpers from the reviewed
module.  The canonical Racket rule remains label authority; ``--racket``
executes that rule and never silently falls back to the Python oracle.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
TASK = "2b7bcfbf942b"
sys.path.insert(0, str(ROOT / "shared/runtime"))

CANONICAL_PROFILES = {(8, 10, 2), (9, 12, 3), (10, 10, 2), (8, 13, 3), (9, 11, 2)}
CANONICAL_BBOXES = {(5, 5), (6, 4), (6, 6), (6, 7)}


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _decode_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(ch) for ch in row] for row in grid]
    return deepcopy(grid)


def canonical():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [
        {"input": _decode_grid(pair["input"]), "output": _decode_grid(pair["output"])}
        for pair in row["train"] + test
    ]


def components(grid):
    """Return same-color 4-connected components as (color, frozenset(cells))."""
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            out.append((color, frozenset(cells)))
    return out


def bbox(cells: Iterable[tuple[int, int]]):
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _perimeter(box):
    r1, c1, r2, c2 = box
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def classify_shape(cells):
    cells = set(cells)
    box = bbox(cells)
    r1, c1, r2, c2 = box
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return None
    perimeter = _perimeter(box)
    if cells == perimeter:
        return "frame"
    gaps = (
        {(r1, c) for c in range(c1 + 1, c2)},
        {(r2, c) for c in range(c1 + 1, c2)},
        {(r, c1) for r in range(r1 + 1, r2)},
        {(r, c2) for r in range(r1 + 1, r2)},
    )
    if any(cells == perimeter - gap for gap in gaps):
        return "open"
    mr, mc = (r1 + r2) // 2, (c1 + c2) // 2
    cross = {(mr, c) for c in range(c1, c2 + 1)} | {(r, mc) for r in range(r1, r2 + 1)}
    if cells == cross:
        return "cross"
    return None


def geometry_output(grid):
    """Independent transliteration of the selected Racket bbox rule."""
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for color, cells in components(grid):
        r1, c1, r2, c2 = bbox(cells)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                border = r in (r1, r2) or c in (c1, c2)
                local_even = ((r - (r1 + 1)) + (c - (c1 + 1))) % 2 == 0
                out[r][c] = color if border or local_even else 0
    return out


def frames_only_output(grid):
    """Canonical-demo shortcut: only complete frames receive checker fill."""
    out = deepcopy(grid)
    for color, cells in components(grid):
        box = bbox(cells)
        if set(cells) != _perimeter(box):
            continue
        r1, c1, r2, c2 = box
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                out[r][c] = color if ((r - r1 - 1) + (c - c1 - 1)) % 2 == 0 else 0
    return out


def canonical_sizes_only_output(grid):
    """Second shortcut: transform only bbox sizes seen in canonical examples."""
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    for color, cells in components(grid):
        r1, c1, r2, c2 = bbox(cells)
        if (r2 - r1 + 1, c2 - c1 + 1) not in CANONICAL_BBOXES:
            continue
        transformed = geometry_output([[grid[r][c] for c in range(w)] for r in range(h)])
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                out[r][c] = transformed[r][c]
    return out


def observed(grid):
    comps = components(grid)
    styles = {classify_shape(cells) for _, cells in comps}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len(comps),
        "object_style": next(iter(styles)) if len(styles) == 1 else None,
        "palette_size": len({value for row in grid for value in row}),
        "bboxes": sorted(
            (r2 - r1 + 1, c2 - c1 + 1, r1, c1)
            for _, cells in comps
            for r1, c1, r2, c2 in [bbox(cells)]
        ),
    }


def witness_input():
    """A 5x5 open frame: prose shortcut leaves it open; authority closes/fills bbox."""
    g = [[0] * 9 for _ in range(8)]
    for r in range(1, 6):
        for c in range(2, 7):
            if r in (1, 5) or c in (2, 6):
                g[r][c] = 4
    for c in range(3, 6):
        g[1][c] = 0
    return g


def novel_size_witness():
    """A complete 4x8 frame, outside every canonical bbox size."""
    g = [[0] * 12 for _ in range(8)]
    for r in range(2, 6):
        for c in range(2, 10):
            if r in (2, 5) or c in (2, 9):
                g[r][c] = 7
    return g


def racket_outputs(grids):
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"program": program, "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.shutdown()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count):
    canonical_rows = canonical_pairs()
    canonical_checks = [module.self_check(pair["input"]) for pair in canonical_rows]
    if any(geometry_output(pair["input"]) != pair["output"] for pair in canonical_rows):
        raise AssertionError("independent oracle disagrees with canonical data")

    by_band = {}
    parity_grids = [pair["input"] for pair in canonical_rows] + [witness_input(), novel_size_witness()]
    totals = Counter()
    all_shapes, all_styles, all_boxes, all_inputs = set(), set(), set(), set()
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        shapes, styles, boxes, inputs, profiles = set(), set(), set(), set(), set()
        for i in range(count):
            g = module.generate(4100 + i, i, difficulty=band)
            obs = observed(g)
            issues = module.self_check(g)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(issues)
            counts["nondeterministic"] += g != module.generate(4100 + i, i, difficulty=band)
            counts["authority_changes_input"] += geometry_output(g) != g
            counts["frames_only_disagreements"] += geometry_output(g) != frames_only_output(g)
            counts["canonical_size_disagreements"] += geometry_output(g) != canonical_sizes_only_output(g)
            shapes.add((obs["grid_h"], obs["grid_w"]))
            styles.add(obs["object_style"])
            boxes.update((bh, bw) for bh, bw, _, _ in obs["bboxes"])
            profiles.add((obs["grid_h"], obs["grid_w"], obs["palette_size"]))
            digest = hashlib.sha256(json.dumps(g, separators=(",", ":")).encode()).hexdigest()
            inputs.add(digest)
            if i < 8:
                parity_grids.append(g)
        counts.update({
            "distinct_shapes": len(shapes),
            "distinct_styles": len(styles),
            "distinct_bboxes": len(boxes),
            "distinct_inputs": len(inputs),
            "canonical_profiles_hit": len(profiles & CANONICAL_PROFILES),
        })
        by_band[str(band)] = dict(counts)
        totals.update(counts)
        all_shapes.update(shapes)
        all_styles.update(styles)
        all_boxes.update(boxes)
        all_inputs.update(inputs)
    totals.update({
        "distinct_shapes": len(all_shapes),
        "distinct_styles": len(all_styles),
        "distinct_bboxes": len(all_boxes),
        "distinct_inputs": len(all_inputs),
    })
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "rule_hash": getattr(module, "RULE_HASH", None),
        "canonical_self_check_errors": canonical_checks,
        "counts": dict(totals),
        "by_band": by_band,
        "witnesses": {
            "frames_only": {
                "input": witness_input(),
                "authority": geometry_output(witness_input()),
                "rival": frames_only_output(witness_input()),
            },
            "canonical_sizes_only": {
                "input": novel_size_witness(),
                "authority": geometry_output(novel_size_witness()),
                "rival": canonical_sizes_only_output(novel_size_witness()),
            },
        },
        "sampling_design": (
            "Each difficulty band uses the same deterministic seed/index schedule; "
            "distinct counts are set-union diagnostics, not independent estimates."
        ),
        "warning": "Python geometry is supplementary evidence, not Racket label authority.",
    }
    return report, parity_grids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=120, help="samples per difficulty band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true", help="require canonical Racket parity")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    path = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    exit_code = int(any(report["canonical_self_check_errors"]) or report["counts"]["self_check_errors"])
    report["racket"] = {"status": "not_requested", "checked": 0}
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [i for i, (g, out) in enumerate(zip(grids, outputs)) if geometry_output(g) != out]
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
    print(json.dumps({k: report[k] for k in ("version", "canonical_self_check_errors", "counts", "racket")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
