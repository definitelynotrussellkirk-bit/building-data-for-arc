#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "shared/runtime"))

# The portable rule wrapper imports the retained parser through its historical
# ``scripts.comment_solutions`` name. Point that namespace at this packet only.
scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = [str(REPO / "shared" / "tools")]
sys.modules.setdefault("scripts", scripts_pkg)


def load_source(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def normalize_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(ch) for ch in row] for row in grid]
    return [list(row) for row in grid]


def canonical_row(task_id: str):
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def repeated_pair(grid):
    counts = Counter(v for row in grid for v in row if v)
    colors = [color for color, n in counts.items() if n == 2]
    if len(colors) != 1:
        raise ValueError(f"expected one repeated color, got {counts}")
    color = colors[0]
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    return color, sorted(points)


def fill_repeated_bbox(grid):
    color, points = repeated_pair(grid)
    (r1, c1), (r2, c2) = points
    rlo, rhi = sorted((r1, r2))
    clo, chi = sorted((c1, c2))
    out = [[0] * len(grid[0]) for _ in grid]
    for r in range(rlo, rhi + 1):
        for c in range(clo, chi + 1):
            out[r][c] = color
    return out


def positive_slope_only(grid):
    color, points = repeated_pair(grid)
    (r1, c1), (r2, c2) = points
    if (r2 - r1) * (c2 - c1) <= 0:
        return [[0] * len(grid[0]) for _ in grid]
    return fill_repeated_bbox(grid)


def audit_e282():
    task_id = "e282a664f807"
    gen, path = load_source(task_id)
    generated = {}
    all_match = True
    for band in (None, "easy", "medium", "hard"):
        slopes = Counter()
        self_check_failures = 0
        rival_mismatches = 0
        for index in range(200):
            grid = gen.generate(282_000 + index, index * 11 + 3, difficulty=band)
            color, ((r1, c1), (r2, c2)) = repeated_pair(grid)
            product = (r2 - r1) * (c2 - c1)
            slopes["positive" if product > 0 else "negative" if product < 0 else "zero"] += 1
            self_check_failures += bool(gen.self_check(copy.deepcopy(grid), difficulty=band))
            rival_mismatches += positive_slope_only(grid) != fill_repeated_bbox(grid)
        generated[str(band)] = {
            "draws": 200,
            "slope_counts": dict(slopes),
            "self_check_failures": self_check_failures,
            "positive_slope_rival_mismatches": rival_mismatches,
        }
        all_match &= rival_mismatches == 0

    row = canonical_row(task_id)
    pairs = list(row.get("train", [])) + list(row.get("test", []))
    canonical = []
    for index, pair in enumerate(pairs):
        grid = normalize_grid(pair["input"])
        output = normalize_grid(pair["output"])
        color, ((r1, c1), (r2, c2)) = repeated_pair(grid)
        product = (r2 - r1) * (c2 - c1)
        canonical.append({
            "index": index,
            "pair_color": color,
            "points": [[r1, c1], [r2, c2]],
            "slope": "positive" if product > 0 else "negative" if product < 0 else "zero",
            "oracle_matches_canonical": fill_repeated_bbox(grid) == output,
            "positive_slope_rival_matches_canonical": positive_slope_only(grid) == output,
            "input": grid,
            "canonical_output": output,
            "rival_output": positive_slope_only(grid),
        })

    try:
        bad_override = gen.generate(1, 0, box_height=1)
        bad_override_record = {
            "advertised_valid": "1..8",
            "accepted": True,
            "self_check": gen.self_check(bad_override),
            "grid": bad_override,
        }
    except Exception as exc:
        bad_override_record = {
            "advertised_valid": "1..8",
            "accepted": False,
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        }
    report = {
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "finding": "ordinary sampler has only positive-slope repeated pairs; canonical pair 2 has a negative slope",
        "generated": generated,
        "rival_matches_all_generated": all_match,
        "canonical": canonical,
        "negative_canonical_indices": [x["index"] for x in canonical if x["slope"] == "negative"],
        "box_height_1_override": bad_override_record,
    }
    return report


def gravity_up(grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for c in range(w):
        values = [grid[r][c] for r in range(h) if grid[r][c] != 0]
        for r, value in enumerate(values):
            out[r][c] = value
    return out


def force_global_first_color(grid):
    """Wrong outside the sampler: prefer the first occupied column's top color."""
    h, w = len(grid), len(grid[0])
    occupied = [c for c in range(w) if any(grid[r][c] for r in range(h))]
    if not occupied:
        return [[0] * w for _ in range(h)]
    first_col = occupied[0]
    preferred = next(grid[r][first_col] for r in range(h) if grid[r][first_col] != 0)
    out = [[0] * w for _ in range(h)]
    for c in range(w):
        values = [grid[r][c] for r in range(h) if grid[r][c] != 0]
        if values and values[0] != preferred:
            values = [v for v in values if v == preferred] + [v for v in values if v != preferred]
        for r, value in enumerate(values):
            out[r][c] = value
    return out


def racket_apply(task_id, grid):
    from puzzle_generators import runner
    rule_source, _source_label = runner._load_rule(task_id)
    callable_text = runner.wrap_rule(rule_source)
    bridge, fn_name = runner._open_bridge_with_rule(callable_text)
    try:
        return runner._apply_rule(bridge, fn_name, copy.deepcopy(grid))
    finally:
        bridge.shutdown()


def audit_b43():
    task_id = "b43d103c28d9"
    gen, path = load_source(task_id)
    generated = {}
    total_matches = 0
    total = 0
    for band in ("easy", "medium", "hard"):
        matches = 0
        mixed_first_columns = 0
        self_check_failures = 0
        for index in range(200):
            grid = gen.generate(430_000 + index, index, difficulty=band)
            truth = gravity_up(grid)
            matches += force_global_first_color(grid) == truth
            info, errors = gen._analyse(grid)
            self_check_failures += bool(errors)
            firsts = {
                next(grid[r][c] for r in range(len(grid)) if grid[r][c] != 0)
                for c in info.get("occupied_columns", ())
            }
            mixed_first_columns += len(firsts) > 1
        generated[band] = {
            "draws": 200,
            "wrong_rule_matches": matches,
            "mixed_first_color_inputs": mixed_first_columns,
            "self_check_failures": self_check_failures,
        }
        total_matches += matches
        total += 200

    # A compact authority-valid grid with contiguous occupied columns but a
    # different top color in the middle column. Stable gravity preserves B,A;
    # the sampler-fitting rival forces the global first color A before B.
    custom = [[0] * 8 for _ in range(8)]
    custom[1][2] = 1
    custom[6][2] = 2
    custom[2][3] = 2
    custom[7][3] = 1
    custom[0][4] = 1
    custom[4][4] = 2
    custom[7][4] = 1
    truth = gravity_up(custom)
    racket = racket_apply(task_id, custom)
    rival = force_global_first_color(custom)

    row = canonical_row(task_id)
    pairs = list(row.get("train", [])) + list(row.get("test", []))
    canonical_rival_matches = []
    for index, pair in enumerate(pairs):
        grid = normalize_grid(pair["input"])
        output = normalize_grid(pair["output"])
        canonical_rival_matches.append({
            "index": index,
            "matches": force_global_first_color(grid) == output,
        })

    return {
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "classification": "domain question / possible shortcut, not a reproduced in-domain failure",
        "generated": generated,
        "wrong_rule_matches_generated": total_matches,
        "generated_draws": total,
        "canonical_wrong_rule_matches": canonical_rival_matches,
        "custom_counterexample": {
            "input": custom,
            "python_truth": truth,
            "racket_output": racket,
            "python_matches_racket": truth == racket,
            "wrong_rule_output": rival,
            "wrong_rule_differs": rival != truth,
            "self_check_findings": gen.self_check(custom),
        },
        "interpretation": (
            "All generated and canonical occupied columns share one first nonzero color. "
            "A solver may therefore behave correctly only when that global role appears first; "
            "the selected authority itself is general stable per-column packing."
        ),
    }


def main():
    out_dir = Path(__file__).resolve().parent
    reports = {
        "e282a664f807": audit_e282(),
        "b43d103c28d9": audit_b43(),
    }
    for task_id, report in reports.items():
        (out_dir / f"{task_id}_probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        task_id: {
            "generator_sha256": report["generator_sha256"],
            "finding": report.get("finding", report.get("classification")),
        }
        for task_id, report in reports.items()
    }, indent=2))


if __name__ == "__main__":
    main()
