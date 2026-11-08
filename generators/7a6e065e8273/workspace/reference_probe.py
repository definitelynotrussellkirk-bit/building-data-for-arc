"""Independent oracle and repeatable audit for generator 7a6e065e8273.

This is reviewer tooling, not an alternate label authority. ``--racket``
requires the repository's selected Racket rule and never falls back to Python.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "7a6e065e8273"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_7a6e065e8273", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator at {path}")
    module = importlib.util.module_from_spec(spec)
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


def centers(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def geometry_output(grid):
    """Literal independent statement of the selected rule's geometry."""
    height, width = len(grid), len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    for r, c, _value in centers(grid):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < height and 0 <= cc < width:
                out[rr][cc] = 8
    return out


def observed(grid):
    points = centers(grid)
    colors = {value for _r, _c, value in points}
    if colors == {5}:
        profile = "canonical"
    elif len(colors) == 1:
        profile = "monochrome"
    else:
        profile = "mixed"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "seed_count": len(points),
        "color_profile": profile,
    }


def racket_outputs(grids):
    """Apply the unchanged selected Racket authority to a batch of grids."""
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
        script = r'''\
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
    rows = {}
    racket_sample = [pair["input"] for pair in canonical_pairs()]
    for band in (None, "easy", "medium", "hard"):
        counter = Counter()
        shapes, profiles, inputs = set(), set(), set()
        for index in range(count):
            seed = 7001 + index
            sample_index = 13 * index + 5
            grid = module.generate(seed, sample_index, difficulty=band)
            again = module.generate(seed, sample_index, difficulty=band)
            issues = module.self_check(grid)
            stats = observed(grid)
            counter["samples"] += 1
            counter["self_check_errors"] += bool(issues)
            counter["nondeterministic"] += grid != again
            counter["changed_outputs"] += geometry_output(grid) != grid
            counter["canonical_shape_palette"] += (
                (stats["grid_h"], stats["grid_w"]) in {(8, 8), (9, 9)}
                and stats["color_profile"] != "mixed"
            )
            shapes.add((stats["grid_h"], stats["grid_w"]))
            profiles.add(stats["color_profile"])
            inputs.add(hashlib.sha256(json.dumps(grid).encode()).hexdigest())
            if index < 16:
                racket_sample.append(grid)
        rows[str(band)] = dict(
            counter,
            distinct_shapes=len(shapes),
            color_profiles=sorted(profiles),
            distinct_inputs=len(inputs),
        )
    return {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "canonical_self_check": [module.self_check(p["input"]) for p in canonical_pairs()],
        "canonical_geometry_matches": sum(
            geometry_output(p["input"]) == p["output"] for p in canonical_pairs()
        ),
        "by_band": rows,
        "warning": "Python geometry is supplementary; Racket is authoritative.",
    }, racket_sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    generator_path = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["rule_hash"] = hashlib.sha256(
        " ".join(canonical()["program_solution"].split()).encode()
    ).hexdigest()[:12]
    if args.racket:
        expected = [geometry_output(grid) for grid in grids]
        actual = racket_outputs(grids)
        report["racket"] = {
            "status": "passed" if actual == expected else "failed",
            "checked": len(grids),
            "matches": sum(a == b for a, b in zip(actual, expected)),
        }
    else:
        report["racket"] = {"status": "not_requested", "checked": 0}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["racket"]["status"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
