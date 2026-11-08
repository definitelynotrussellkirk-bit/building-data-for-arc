"""Independent oracle and reproducible audit for fdffdd0bbde7.

The Python oracle is supplementary test evidence. ``--racket`` executes the
canonical Racket authority and never silently substitutes the Python oracle.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
from itertools import product
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK = "fdffdd0bbde7"
ROOT = Path(__file__).resolve().parents[3]
for candidate in (ROOT, ROOT / "shared/runtime", ROOT / "src"):
    if candidate.exists():
        sys.path.insert(0, str(candidate))


def load_generator(path=None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as load_pairs, find_root
    return load_pairs(TASK, root=find_root(__file__))


def parse(grid):
    """Parse a lawful library/body grid without importing production code."""
    if not isinstance(grid, (list, tuple)) or not grid or not grid[0]:
        raise ValueError("expected a nonempty grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    separator = next((r for r, row in enumerate(grid) if all(value == 0 for value in row)), None)
    if separator is None:
        raise ValueError("missing blank separator")
    dividers = [c for c in range(width) if all(grid[r][c] == 9 for r in range(separator))]
    spans = []
    start = 0
    for divider in dividers + [width]:
        if divider > start:
            spans.append((start, divider - 1))
        start = divider + 1
    entries = []
    for c1, c2 in spans:
        anchors = [(r, c) for r in range(separator) for c in range(c1, c2 + 1) if grid[r][c] == 9]
        colors = sorted({grid[r][c] for r in range(separator) for c in range(c1, c2 + 1)
                         if grid[r][c] not in (0, 9)})
        if len(anchors) != 1 or len(colors) != 1:
            raise ValueError(f"malformed panel {c1}-{c2}")
        anchor = anchors[0]
        color = colors[0]
        offsets = tuple(sorted((r - anchor[0], c - anchor[1])
                               for r in range(separator) for c in range(c1, c2 + 1)
                               if grid[r][c] == color))
        entries.append({"span": (c1, c2), "anchor": anchor, "color": color, "offsets": offsets})
    body = tuple((r, c, grid[r][c]) for r in range(separator + 1, len(grid))
                 for c in range(width) if grid[r][c] != 0)
    return {"height": len(grid), "width": width, "separator": separator,
            "dividers": tuple(dividers), "entries": tuple(entries), "body": body}


def _paint(parsed, offsets_by_color):
    out = [[0] * parsed["width"] for _ in range(parsed["height"])]
    for row, col, color in parsed["body"]:
        for dr, dc in offsets_by_color[color]:
            rr, cc = row + dr, col + dc
            if 0 <= rr < parsed["height"] and 0 <= cc < parsed["width"]:
                out[rr][cc] = color
    return out


def geometry_output(grid):
    parsed = parse(grid)
    offsets = {entry["color"]: entry["offsets"] for entry in parsed["entries"]}
    return _paint(parsed, offsets)


def _assumed_anchor_output(grid, *, use_actual_row, use_actual_col):
    parsed = parse(grid)
    offsets = {}
    for entry in parsed["entries"]:
        c1, c2 = entry["span"]
        center = (parsed["separator"] // 2, (c1 + c2) // 2)
        anchor = (
            entry["anchor"][0] if use_actual_row else center[0],
            entry["anchor"][1] if use_actual_col else center[1],
        )
        offsets[entry["color"]] = tuple(sorted(
            (r - anchor[0], c - anchor[1])
            for r in range(parsed["separator"])
            for c in range(c1, c2 + 1)
            if grid[r][c] == entry["color"]
        ))
    return _paint(parsed, offsets)


def panel_center_output(grid):
    """Shortcut: ignore both anchor coordinates and use the panel center."""
    return _assumed_anchor_output(grid, use_actual_row=False, use_actual_col=False)


def center_row_anchor_output(grid):
    """Shortcut: use the 9's column but assume the anchor row is centered."""
    return _assumed_anchor_output(grid, use_actual_row=False, use_actual_col=True)


def center_col_anchor_output(grid):
    """Shortcut: use the 9's row but assume the anchor column is centered."""
    return _assumed_anchor_output(grid, use_actual_row=True, use_actual_col=False)


def observed(grid):
    parsed = parse(grid)
    sizes = {len(entry["offsets"]) for entry in parsed["entries"]}
    if len(sizes) != 1:
        raise ValueError(f"stencil sizes are not uniform: {sorted(sizes)}")
    return {
        "grid_h": parsed["height"],
        "grid_w": parsed["width"],
        "lib_h": parsed["separator"],
        "n_entries": len(parsed["entries"]),
        "stencil_size": sizes.pop(),
        "n_body": len(parsed["body"]),
    }


def has_off_center_anchor(grid):
    parsed = parse(grid)
    return any(entry["anchor"] != (parsed["separator"] // 2,
                                    (entry["span"][0] + entry["span"][1]) // 2)
               for entry in parsed["entries"])


def isolated_anchor_witness(grid):
    """Whether the top-center seed cleanly separates all declared anchor shortcuts."""
    parsed = parse(grid)
    true_offsets = {entry["color"]: entry["offsets"] for entry in parsed["entries"]}
    rival_offsets = {
        "panel_center_anchor": {},
        "center_row_anchor": {},
        "center_col_anchor": {},
    }
    for entry in parsed["entries"]:
        c1, c2 = entry["span"]
        center = (parsed["separator"] // 2, (c1 + c2) // 2)
        ar, ac = entry["anchor"]
        cells_in_panel = [
            (row, col)
            for row in range(parsed["separator"])
            for col in range(c1, c2 + 1)
            if grid[row][col] == entry["color"]
        ]
        rival_offsets["panel_center_anchor"][entry["color"]] = tuple(
            (row - center[0], col - center[1]) for row, col in cells_in_panel
        )
        rival_offsets["center_row_anchor"][entry["color"]] = tuple(
            (row - center[0], col - ac) for row, col in cells_in_panel
        )
        rival_offsets["center_col_anchor"][entry["color"]] = tuple(
            (row - ar, col - center[1]) for row, col in cells_in_panel
        )

    witness = (parsed["separator"] + 1, parsed["width"] // 2)
    witness_rows = [item for item in parsed["body"] if item[:2] == witness]
    if len(witness_rows) != 1:
        return False
    witness_color = witness_rows[0][2]

    def cells(position, offsets):
        row, col = position
        return {
            (row + dr, col + dc)
            for dr, dc in offsets
            if 0 <= row + dr < parsed["height"] and 0 <= col + dc < parsed["width"]
        }

    true_cells = cells(witness, true_offsets[witness_color])
    disagreements = {}
    other_touched = {name: set() for name in rival_offsets}
    for name, offsets_by_color in rival_offsets.items():
        rival_cells = cells(witness, offsets_by_color[witness_color])
        disagreements[name] = true_cells ^ rival_cells
        if not disagreements[name]:
            return False
    for row, col, color in parsed["body"]:
        if (row, col) == witness:
            continue
        true_touched = cells((row, col), true_offsets[color])
        for name, offsets_by_color in rival_offsets.items():
            rival_touched = cells((row, col), offsets_by_color[color])
            other_touched[name].update(true_touched | rival_touched)
    return all(disagreements[name] - other_touched[name] for name in rival_offsets)


def grid_sha256(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def racket_outputs(grids):
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    canonical = next(row for row in _canonical_rows() if row.get("task_id") == TASK)
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(json.dumps({"program": canonical["program_solution"], "grids": grids}))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
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


def _canonical_rows():
    from reviewer_support import canonical_path, find_root
    with canonical_path(find_root(__file__)).open() as handle:
        for line in handle:
            yield json.loads(line)


DEFAULT_AXIS_VALUES = {
    "grid_h": tuple(range(10, 17)),
    "grid_w": tuple(range(13, 22)),
    "lib_h": tuple(range(3, 7)),
    "n_entries": tuple(range(2, 5)),
    "stencil_size": tuple(range(1, 6)),
    "n_body": tuple(range(4, 9)),
}


def exhaustive_axis_probe(module, value_sets=None, bands=(None, "easy", "medium", "hard")):
    """Exercise the Cartesian product of exact controls through public generation."""
    values_by_axis = value_sets or DEFAULT_AXIS_VALUES
    axes = tuple(DEFAULT_AXIS_VALUES)
    if set(values_by_axis) != set(axes):
        raise ValueError(f"value_sets must define exactly {axes}")
    failures = []
    failure_count = 0
    cases = 0
    isolated = 0
    rival_disagreements = Counter()
    unique_inputs = set()
    combinations = list(product(*(values_by_axis[name] for name in axes)))
    for band_index, band in enumerate(bands):
        for combination_index, values in enumerate(combinations):
            overrides = dict(zip(axes, values))
            seed = 700000 + band_index * 100000 + combination_index
            sample_index = combination_index * 7 + band_index
            cases += 1
            reasons = []
            try:
                grid = module.generate(seed, sample_index, difficulty=band, **overrides)
                issues = module.self_check(grid)
                if issues:
                    reasons.append(f"self_check: {issues}")
                actual = observed(grid)
                if actual != overrides:
                    reasons.append(f"observed {actual}")
                witness = isolated_anchor_witness(grid)
                isolated += int(witness)
                if not witness:
                    reasons.append("designated witness is not isolated")
                intended = geometry_output(grid)
                rival_outputs = {
                    "panel_center_anchor": panel_center_output(grid),
                    "center_row_anchor": center_row_anchor_output(grid),
                    "center_col_anchor": center_col_anchor_output(grid),
                }
                for rival_name, rival_output in rival_outputs.items():
                    disagreement = intended != rival_output
                    rival_disagreements[rival_name] += int(disagreement)
                    if not disagreement:
                        reasons.append(f"{rival_name} agrees")
                unique_inputs.add(grid_sha256(grid))
            except Exception as exc:
                reasons.append(f"{type(exc).__name__}: {exc}")
            if reasons:
                failure_count += 1
                if len(failures) < 100:
                    failures.append({
                        "band": band, "seed": seed, "sample_index": sample_index,
                        "overrides": overrides, "reasons": reasons,
                    })
    return {
        "axes": {name: list(values_by_axis[name]) for name in axes},
        "bands": list(bands),
        "cases": cases,
        "failure_count": failure_count,
        "failures": failures,
        "isolated_witnesses": isolated,
        "rival_disagreements": dict(rival_disagreements),
        "unique_inputs": len(unique_inputs),
    }


def audit(module, per_band=100):
    report = {"schema": f"{TASK}-independent-audit-v1", "task_id": TASK,
              "version": module.VERSION, "per_band": per_band, "bands": {}}
    totals = Counter()
    samples = []
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        shapes = set()
        inputs = set()
        for index in range(per_band):
            grid = module.generate(9100 + index, index * 17 + 3, difficulty=band)
            issues = module.self_check(grid)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(issues)
            counts["nondeterministic"] += grid != module.generate(9100 + index, index * 17 + 3, difficulty=band)
            counts["off_center_witnesses"] += has_off_center_anchor(grid)
            counts["isolated_witnesses"] += isolated_anchor_witness(grid)
            intended = geometry_output(grid)
            counts["panel_center_disagreements"] += intended != panel_center_output(grid)
            counts["center_row_disagreements"] += intended != center_row_anchor_output(grid)
            counts["center_col_disagreements"] += intended != center_col_anchor_output(grid)
            shapes.add((len(grid), len(grid[0])))
            inputs.add(grid_sha256(grid))
            if index < 8:
                samples.append(grid)
        counts["distinct_shapes"] = len(shapes)
        counts["distinct_inputs"] = len(inputs)
        report["bands"][str(band)] = dict(counts)
        totals.update(counts)
    report["totals"] = dict(totals)
    report["canonical"] = {
        "pairs": len(canonical_pairs()),
        "oracle_matches": sum(geometry_output(pair["input"]) == pair["output"] for pair in canonical_pairs()),
        "panel_center_rival_matches": sum(panel_center_output(pair["input"]) == pair["output"] for pair in canonical_pairs()),
        "center_row_rival_matches": sum(center_row_anchor_output(pair["input"]) == pair["output"] for pair in canonical_pairs()),
        "center_col_rival_matches": sum(center_col_anchor_output(pair["input"]) == pair["output"] for pair in canonical_pairs()),
        "self_check_errors": [module.self_check(pair["input"]) for pair in canonical_pairs()],
    }
    return report, [pair["input"] for pair in canonical_pairs()] + samples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--exhaustive-axes", action="store_true",
                        help="also enumerate the full exact-axis Cartesian product")
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.per_band)
    source = Path(args.generator or os.environ.get("GENERATOR_UNDER_TEST") or ROOT / f"generators/{TASK}/generator.py")
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    if args.exhaustive_axes:
        report["joint_axes"] = exhaustive_axis_probe(module)
    code = int(report["canonical"]["oracle_matches"] != report["canonical"]["pairs"]
               or any(report["canonical"]["self_check_errors"])
               or report["totals"].get("self_check_errors", 0)
               or report["totals"].get("nondeterministic", 0)
               or report.get("joint_axes", {}).get("failure_count", 0))
    if args.racket:
        try:
            actual = racket_outputs(grids)
            expected = [geometry_output(grid) for grid in grids]
            mismatches = [i for i, (a, b) in enumerate(zip(actual, expected)) if a != b]
            report["racket"] = {"status": "passed" if not mismatches else "failed",
                                "checked": len(actual), "mismatches": mismatches}
            code = max(code, int(bool(mismatches)))
        except Exception as exc:
            report["racket"] = {"status": "unavailable_or_failed", "checked": 0,
                                "error": f"{type(exc).__name__}: {exc}"}
            code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"version": report["version"], "canonical": report["canonical"],
                      "totals": report["totals"], "racket": report["racket"],
                      "joint_axes": report.get("joint_axes")}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
