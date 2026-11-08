"""Independent oracle and probes for ARC task 76e0bd03e098.

This module is reviewer tooling, not label authority.  It deliberately derives
paths from the visible input instead of importing production helpers.  The
optional Racket parity helper executes the packet's canonical authority and
fails loudly when that runtime is unavailable.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

TASK = "76e0bd03e098"
HERE = Path(__file__).resolve()


def _find_repo_root() -> Path:
    for parent in HERE.parents:
        if (parent / "shared" / "data" / "canonical" / "puzzles.jsonl").exists():
            return parent
    raise RuntimeError("could not locate repository root")


ROOT = _find_repo_root()
sys.path.insert(0, str(ROOT / "shared" / "runtime"))


def load_generator(path=None):
    source = Path(path or ROOT / "generators" / TASK / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as _pairs, find_root
    return _pairs(TASK, root=find_root(__file__))


def _between(a: int, b: int):
    step = 1 if b >= a else -1
    return list(range(a, b + step, step))


def elbow_path(a, b, first: str):
    """Independent translation of the public H-first/V-first geometry."""
    r1, c1 = a
    r2, c2 = b
    if first == "h":
        return [(r1, c) for c in _between(c1, c2)] + [
            (r, c2) for r in _between(r1, r2)[1:]
        ]
    if first == "v":
        return [(r, c1) for r in _between(r1, r2)] + [
            (r2, c) for c in _between(c1, c2)[1:]
        ]
    raise ValueError(first)


def color_order(grid):
    seen = set()
    result = []
    for row in grid:
        for value in row:
            if value not in (0, 8) and value not in seen:
                seen.add(value)
                result.append(value)
    return result


def endpoints(grid, color):
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def path_clear(grid, path, pair):
    allowed = set(pair)
    return all(grid[r][c] == 0 or (r, c) in allowed for r, c in path)


def selected_paths(grid, *, order="reading", policy="authority"):
    colors = color_order(grid)
    if order == "numeric":
        colors = sorted(colors)
    elif order != "reading":
        raise ValueError(order)
    result = []
    for color in colors:
        pair = endpoints(grid, color)
        if len(pair) != 2:
            continue
        hp = elbow_path(pair[0], pair[1], "h")
        vp = elbow_path(pair[0], pair[1], "v")
        hc = path_clear(grid, hp, pair)
        vc = path_clear(grid, vp, pair)
        if policy == "authority":
            chosen = hp if hc else vp
        elif policy == "vertical_first":
            chosen = vp if vc else hp
        elif policy == "clear_required":
            chosen = hp if hc else (vp if vc else [])
        elif policy == "horizontal_only":
            chosen = hp
        else:
            raise ValueError(policy)
        result.append((color, pair, hp, vp, hc, vc, chosen))
    return result


def oracle_output(grid, *, order="reading", policy="authority", first_wins=False):
    original = deepcopy(grid)
    out = deepcopy(grid)
    claimed = set()
    for color, _pair, _hp, _vp, _hc, _vc, chosen in selected_paths(
        original, order=order, policy=policy
    ):
        for r, c in chosen:
            if out[r][c] == 8:
                continue
            if first_wins and (r, c) in claimed:
                continue
            out[r][c] = color
            claimed.add((r, c))
    return out


def branch_summary(grid):
    paths = selected_paths(grid)
    selected_sets = []
    summary = Counter()
    for color, _pair, _hp, _vp, hc, vc, chosen in paths:
        summary["pairs"] += 1
        summary["both_clear"] += bool(hc and vc)
        summary["h_blocked_v_clear"] += bool((not hc) and vc)
        summary["both_blocked"] += bool((not hc) and (not vc))
        selected_sets.append((color, set(chosen)))
    overlaps = []
    for i, (left_color, left) in enumerate(selected_sets):
        for right_color, right in selected_sets[i + 1 :]:
            cells = sorted(left & right)
            if cells:
                overlaps.append((left_color, right_color, cells))
    summary["overlap_pairs"] = len(overlaps)
    summary["numeric_order_diff"] = oracle_output(grid) != oracle_output(grid, order="numeric")
    summary["first_wins_diff"] = oracle_output(grid) != oracle_output(grid, first_wins=True)
    return dict(summary), overlaps


def observed(grid):
    shape = f"{len(grid)}x{len(grid[0])}"
    return {
        "scene_profile": shape,
        "n_walls": sum(value == 8 for row in grid for value in row),
    }


def blocked_fallback_witness():
    """Explicit 8x10 scene containing H-preference, V-detour and both-blocked fallback."""
    grid = [[0] * 10 for _ in range(8)]
    # Reading order is 7,2,5 while numeric order is 2,5,7.
    for r, c, value in [
        (0, 3, 7), (5, 8, 7),       # both H and V blocked: authority uses V
        (1, 1, 2), (3, 4, 2),       # both routes clear: authority prefers H
        (2, 7, 5), (6, 5, 5),       # H blocked, V clear
        (0, 6, 8), (4, 3, 8), (2, 6, 8), (7, 0, 8),
    ]:
        grid[r][c] = value
    return grid


def racket_outputs(grids):
    """Execute the canonical Racket program; never substitute the Python oracle."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    import tempfile

    canonical = None
    with (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                canonical = row
                break
    if canonical is None:
        raise ValueError("canonical task missing")

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"program": canonical["program_solution"], "grids": grids}
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
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(result["stderr"] or result["stdout"])
        return json.loads(result["stdout"])
