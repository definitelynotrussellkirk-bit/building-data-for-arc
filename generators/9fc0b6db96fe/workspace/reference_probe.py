"""Independent oracle and probes for generator 9fc0b6db96fe.

The Python implementation here is test tooling, not label authority.  The optional
``racket_outputs`` path executes the selected canonical Racket program and never
silently falls back to this oracle.
"""
from __future__ import annotations

from collections import deque
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "9fc0b6db96fe"
sys.path.insert(0, str(ROOT / "shared/runtime"))

PROFILE_SPECS = {
    "h9_w15_n4": (9, 15, 4),
    "h9_w14_n4": (9, 14, 4),
    "h12_w15_n3": (12, 15, 3),
    "h11_w13_n4": (11, 13, 4),
    "h9_w15_n3": (9, 15, 3),
}
LEGEND_POSITIONS = {
    3: {
        "contiguous": (1, 2, 3),
        "spaced": (1, 3, 5),
        "mixed": (1, 2, 4),
    },
    4: {
        "contiguous": (1, 2, 3, 4),
        "spaced": (1, 3, 5, 7),
        "mixed": (1, 3, 4, 5),
    },
}


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise LookupError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def legend_entries(grid):
    return [(c, value) for c, value in enumerate(grid[0][1:], start=1) if value != 0]


def nonzero_components(grid):
    """Racket-equivalent 4-connected nonzero components of the body, row-major."""
    body = grid[2:]
    h = len(body)
    w = len(body[0]) if body else 0
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if body[r][c] == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and body[nr][nc] != 0):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)
    return components


def component_crop(grid, cells):
    body = grid[2:]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    cell_set = set(cells)
    return [
        [body[r][c] if (r, c) in cell_set else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def transform(crop, key):
    if key == 1:
        return [list(row) for row in crop]
    if key == 2:
        return [list(row) for row in zip(*crop[::-1])]
    if key == 3:
        return [list(reversed(row)) for row in reversed(crop)]
    if key == 4:
        return [list(reversed(row)) for row in crop]
    return [list(row) for row in crop]


def pack_gallery(parts, gap=1):
    if not parts:
        return [[0]]
    height = max(len(part) for part in parts)
    width = sum(len(part[0]) for part in parts) + gap * (len(parts) - 1)
    out = [[0] * width for _ in range(height)]
    left = 0
    for part in parts:
        for r, row in enumerate(part):
            for c, value in enumerate(row):
                if value:
                    out[r][left + c] = value
        left += len(part[0]) + gap
    return out


def gallery_output(grid, *, legend_order=True, apply_key=True):
    """Independent mirror of the canonical rule for lawful task inputs."""
    comps = nonzero_components(grid)
    body = grid[2:]
    keyed = []
    for cells in comps:
        first_r, first_c = cells[0]
        keyed.append((body[first_r][first_c], cells))
    if legend_order:
        ordered = []
        for _, color in legend_entries(grid):
            matches = [cells for first_color, cells in keyed if first_color == color]
            if not matches:
                raise ValueError(f"legend color {color} has no body component")
            ordered.append(matches[0])
    else:
        ordered = [cells for _, cells in keyed]
    key = grid[0][0] if apply_key else 1
    return pack_gallery([transform(component_crop(grid, cells), key) for cells in ordered])


def observed(grid):
    entries = legend_entries(grid)
    n = len(entries)
    spec = (len(grid), len(grid[0]), n)
    profile = next((name for name, value in PROFILE_SPECS.items() if value == spec), None)
    positions = tuple(c for c, _ in entries)
    layout = next(
        (name for name, expected in LEGEND_POSITIONS.get(n, {}).items() if positions == expected),
        None,
    )
    return {"profile": profile, "key": grid[0][0], "legend_layout": layout}


def body_scan_order(grid):
    body = grid[2:]
    return [body[cells[0][0]][cells[0][1]] for cells in nonzero_components(grid)]


def legend_order(grid):
    return [value for _, value in legend_entries(grid)]


def racket_outputs(grids):
    """Execute the selected Racket authority for parity; no Python fallback."""
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
        return json.loads(result["stdout"])
