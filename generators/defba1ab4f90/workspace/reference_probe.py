"""Independent oracle and review probes for defba1ab4f90.

This file deliberately does not import production parsing, tracing, or rival
helpers.  It is portable with the selected-task test snapshot and gives future
reviewers a source-independent way to check canonical pairs, generated inputs,
Racket parity, overrides, and lesson identifiability.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
TASK = "defba1ab4f90"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | Path | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    from reviewer_support import canonical_pairs as read_pairs, find_root

    return read_pairs(TASK, root=find_root(__file__))


def transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def parse(grid: Any) -> dict[str, Any]:
    """Validate the broad task grammar and normalize entry to the top edge."""
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError("every row must be a nonempty list")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or value not in {0, 1, 2, 3}
           for row in grid for value in row):
        raise ValueError("cells must be literal colors 0,1,2,3")

    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(markers) != 1:
        raise ValueError(f"expected exactly one red marker, found {len(markers)}")
    r, c = markers[0]
    height = len(grid)
    if r == 0 and 0 < c < width - 1:
        orientation = "top"
        latent = deepcopy(grid)
        blue_step = 1
    elif c == 0 and 0 < r < height - 1:
        orientation = "left"
        latent = transpose(grid)
        blue_step = -1
    else:
        raise ValueError("red marker must be non-corner on the top or left edge")
    return {
        "orientation": orientation,
        "latent": latent,
        "blue_step": blue_step,
    }


def _trace_latent(
    latent: list[list[int]],
    blue_step: int,
    *,
    ignore_color: bool = False,
) -> tuple[set[tuple[int, int]], list[dict[str, int]]]:
    h, w = len(latent), len(latent[0])
    markers = [
        (r, c)
        for r, row in enumerate(latent)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(markers) != 1:
        raise ValueError("latent grid must contain one marker")
    r, c = markers[0]
    if r != 0:
        raise ValueError("normalized marker must be on top")
    cells = {(r, c)}
    turns: list[dict[str, int]] = []
    budget = h * w * 4
    while r < h - 1:
        budget -= 1
        if budget <= 0:
            raise ValueError("trace exceeded finite budget")
        below = latent[r + 1][c]
        if below == 0:
            r += 1
            cells.add((r, c))
            continue
        if below not in (1, 3):
            raise ValueError(f"stream hit unsupported color {below}")
        obstacle_color = below
        step = blue_step if (ignore_color or obstacle_color == 1) else -blue_step
        start_c = c
        cc = c + step
        while True:
            if not 0 <= cc < w:
                raise ValueError("stream was steered off the lane")
            cells.add((r, cc))
            if latent[r + 1][cc] == 0:
                cells.add((r + 1, cc))
                turns.append({
                    "bar_row": r + 1,
                    "color": obstacle_color,
                    "from_col": start_c,
                    "to_col": cc,
                    "step": step,
                })
                r += 1
                c = cc
                break
            cc += step
    return cells, turns


def analyze(grid: Any) -> dict[str, Any]:
    info = parse(grid)
    latent = info["latent"]
    path, turns = _trace_latent(latent, info["blue_step"])
    runs: list[dict[str, int]] = []
    for r, row in enumerate(latent):
        c = 0
        while c < len(row):
            if row[c] not in (1, 3):
                c += 1
                continue
            color = row[c]
            start = c
            while c + 1 < len(row) and row[c + 1] == color:
                c += 1
            runs.append({"row": r, "start": start, "end": c, "color": color})
            c += 1
    return {
        "orientation": info["orientation"],
        "flow_length": len(latent),
        "lane_width": len(latent[0]),
        "n_turns": len(turns),
        "n_distractors": len(runs) - len(turns),
        "path": path,
        "turns": turns,
        "runs": runs,
    }


def observed(grid: Any) -> dict[str, Any]:
    info = analyze(grid)
    return {
        key: info[key]
        for key in (
            "orientation", "flow_length", "lane_width", "n_turns", "n_distractors"
        )
    }


def rule_output(grid: Any) -> list[list[int]]:
    info = parse(grid)
    latent = info["latent"]
    path, _turns = _trace_latent(latent, info["blue_step"])
    out = deepcopy(latent)
    for r, c in path:
        out[r][c] = 2
    return transpose(out) if info["orientation"] == "left" else out


def ignore_bar_color_output(grid: Any) -> list[list[int]]:
    info = parse(grid)
    latent = info["latent"]
    try:
        path, _turns = _trace_latent(
            latent, info["blue_step"], ignore_color=True
        )
    except ValueError:
        return deepcopy(grid)
    out = deepcopy(latent)
    for r, c in path:
        out[r][c] = 2
    return transpose(out) if info["orientation"] == "left" else out


def no_left_chirality_flip_output(grid: Any) -> list[list[int]]:
    info = parse(grid)
    latent = info["latent"]
    try:
        path, _turns = _trace_latent(latent, 1)
    except ValueError:
        return deepcopy(grid)
    out = deepcopy(latent)
    for r, c in path:
        out[r][c] = 2
    return transpose(out) if info["orientation"] == "left" else out


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Apply the selected canonical authority with the real Racket bridge."""
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    source = None
    canonical_path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with canonical_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK and row.get("program_solution"):
                source = str(row["program_solution"])
                break
    if source is None:
        raise FileNotFoundError(f"{TASK}: selected canonical rule source not found")
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": source, "grids": grids}), encoding="utf-8"
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
            raise RuntimeError(f"Racket parity worker failed: {result}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket parity worker returned an incomplete batch")
        return outputs


def main() -> int:
    module = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
    report = {
        "canonical_pairs": len(canonical_pairs()),
        "canonical_oracle_matches": sum(
            rule_output(pair["input"]) == pair["output"]
            for pair in canonical_pairs()
        ),
        "bands": {},
    }
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        rows = []
        for index in range(80):
            grid = module.generate(91_000 + band_index * 1000 + index, index, difficulty=band)
            rows.append(observed(grid))
        report["bands"]["default" if band is None else band] = {
            "draws": len(rows),
            "orientations": sorted({row["orientation"] for row in rows}),
            "flow_lengths": sorted({row["flow_length"] for row in rows}),
            "lane_widths": sorted({row["lane_width"] for row in rows}),
            "turn_counts": sorted({row["n_turns"] for row in rows}),
            "distractor_counts": sorted({row["n_distractors"] for row in rows}),
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
