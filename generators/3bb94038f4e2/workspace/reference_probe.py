"""Independent oracle and reproducible probes for 3bb94038f4e2.

This module is test/review tooling.  The Python oracle is deliberately separate
from the production generator and is not label authority; optional Racket parity
executes the selected canonical program without a silent fallback.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

TASK = "3bb94038f4e2"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def normalized_rule_hash():
    source = canonical_row()["program_solution"]
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def intended_output(grid):
    """Independent mirror: one input-based horizontal pass over 1-0-1."""
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c in range(1, len(row) - 1):
            if row[c - 1] == 1 and row[c] == 0 and row[c + 1] == 1:
                out[r][c] = 1
    return out


def semantic_features(grid):
    h, w = len(grid), len(grid[0])
    true_gaps = []
    vertical_gaps = []
    other_color_gaps = []
    protected_centers = []
    wide_gaps = []
    for r, row in enumerate(grid):
        for c in range(1, w - 1):
            if row[c - 1] == 1 and row[c] == 0 and row[c + 1] == 1:
                true_gaps.append((r, c))
            if row[c] == 0 and row[c - 1] == row[c + 1] not in (0, 1):
                other_color_gaps.append((r, c, row[c - 1]))
            if row[c - 1] == row[c + 1] == 1 and row[c] not in (0, 1):
                protected_centers.append((r, c, row[c]))
        for c in range(w - 3):
            if row[c:c + 4] == [1, 0, 0, 1]:
                wide_gaps.append((r, c))
    for r in range(1, h - 1):
        for c in range(w):
            if grid[r - 1][c] == 1 and grid[r][c] == 0 and grid[r + 1][c] == 1:
                vertical_gaps.append((r, c))
    return {
        "true_gaps": true_gaps,
        "vertical_gaps": vertical_gaps,
        "other_color_gaps": other_color_gaps,
        "protected_centers": protected_centers,
        "wide_gaps": wide_gaps,
    }


def profile(grid):
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def pinned_profile_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def racket_outputs(grids):
    """Execute the selected Racket authority; raise if unavailable/failing."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {
            "program": canonical_row()["program_solution"],
            "grids": grids,
        }
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
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs
