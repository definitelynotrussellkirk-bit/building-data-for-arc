"""Independent oracle and reproducible audit for generator ad5a6c1521b3.

This module is test tooling, not label authority.  The Python implementation is
written independently from the generator and can optionally be checked against
the repository's real canonical Racket program.  It is intentionally usable by
future reviewers from either the authoring tree or a staged task-test runtime.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK = "ad5a6c1521b3"
ROOT = find_root(__file__)


def load_generator(path: str | os.PathLike[str] | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(TASK, root=ROOT, labeled_only=True)


def rectangular_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a non-empty row sequence"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "rows must be non-empty sequences"
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            return "grid must be rectangular"
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return "cells must be integer ARC colors 0..9"
    return None


def modal_background(grid: list[list[int]]) -> int:
    counts = Counter(value for row in grid for value in row)
    best = max(counts.values())
    winners = [color for color, count in counts.items() if count == best]
    if len(winners) != 1:
        raise ValueError(f"background mode is ambiguous: {winners}")
    return winners[0]


def color_components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if 0 <= nxt[0] < h and 0 <= nxt[1] < w and nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def bbox(component: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(component)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def selected_component(components: list[set[tuple[int, int]]], *, top_left_tie: bool = False):
    if top_left_tie:
        return max(components, key=lambda comp: (len(comp), -sum(bbox(comp)[:2])))
    return max(components, key=lambda comp: (len(comp), sum(bbox(comp)[:2])))


def rule_output(
    grid: list[list[int]],
    *,
    first_split_only: bool = False,
    top_left_tie: bool = False,
    preserve_winner_holes: bool = False,
    omit_left_column: bool = False,
) -> list[list[int]]:
    """Independent mirror of the canonical operation plus explicit rivals."""
    error = rectangular_error(grid)
    if error:
        raise ValueError(error)
    bg = modal_background(grid)
    out = deepcopy(grid)
    processed = 0
    for color in range(10):
        if color == bg:
            continue
        components = color_components(grid, color)
        if len(components) < 2:
            continue
        if first_split_only and processed:
            continue
        processed += 1
        winner = selected_component(components, top_left_tie=top_left_tie)
        r0, c0, r1, c1 = bbox(winner)
        for r, row in enumerate(out):
            for c, value in enumerate(row):
                if value == color:
                    out[r][c] = bg
        if preserve_winner_holes:
            for r, c in winner:
                out[r][c] = color
            if not omit_left_column:
                for r in range(r0, r1 + 1):
                    out[r][max(0, c0 - 1)] = color
        else:
            left = c0 if omit_left_column else max(0, c0 - 1)
            for r in range(r0, r1 + 1):
                for c in range(left, c1 + 1):
                    out[r][c] = color
    return out


def analysis(grid: list[list[int]]) -> dict[str, Any]:
    error = rectangular_error(grid)
    if error:
        return {"errors": [error]}
    bg = modal_background(grid)
    colors = sorted({value for row in grid for value in row if value != bg})
    per_color = []
    for color in colors:
        components = color_components(grid, color)
        rows = [
            {
                "cells": component,
                "size": len(component),
                "bbox": bbox(component),
            }
            for component in components
        ]
        rows.sort(key=lambda row: (row["bbox"][0], row["bbox"][1]))
        per_color.append({"color": color, "components": rows})
    signature = tuple(sorted(tuple(sorted(row["size"] for row in item["components"])) for item in per_color))
    active = [item for item in per_color if len(item["components"]) >= 2]
    passive = [item for item in per_color if len(item["components"]) == 1]
    return {
        "errors": [],
        "height": len(grid),
        "width": len(grid[0]),
        "background": bg,
        "palette_size": len(colors) + 1,
        "colors": colors,
        "per_color": per_color,
        "signature": signature,
        "active": active,
        "passive": passive,
    }


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Require and execute the repository's real Racket authority; no fallback."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = None
    canonical_path = None
    for relative in ("shared/data/canonical/puzzles.jsonl", "data/canonical/puzzles.jsonl"):
        candidate = ROOT / relative
        if candidate.is_file():
            canonical_path = candidate
            break
    if canonical_path is None:
        raise FileNotFoundError("canonical ledger unavailable")
    with canonical_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                program = row["program_solution"]
                break
    if program is None:
        raise KeyError(TASK)

    import tempfile

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
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
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


def audit(module, count: int) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": f"{TASK}-independent-audit-v1",
        "generator_version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "canonical": [],
        "bands": {},
    }
    for pair in canonical_pairs():
        report["canonical"].append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "oracle_matches": rule_output(pair["input"]) == pair["output"],
                "self_check": module.self_check(pair["input"]),
            }
        )
    samples_for_racket: list[list[list[int]]] = [pair["input"] for pair in canonical_pairs()]
    for band in (None, "easy", "medium", "hard"):
        stats = Counter()
        profiles = Counter()
        backgrounds = Counter()
        signatures = Counter()
        hashes = set()
        for index in range(count):
            grid = module.generate(9100 + index, index, difficulty=band)
            stats["samples"] += 1
            stats["self_check_errors"] += bool(module.self_check(grid))
            stats["nondeterministic"] += grid != module.generate(9100 + index, index, difficulty=band)
            facts = analysis(grid)
            profiles.update([module.observe_overrides(grid).get("scene_profile")])
            backgrounds.update([facts["background"]])
            signatures.update([str(facts["signature"])])
            hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            intended = rule_output(grid)
            stats["changed"] += intended != grid
            stats["first_split_counterexamples"] += intended != rule_output(grid, first_split_only=True)
            stats["top_left_tie_counterexamples"] += intended != rule_output(grid, top_left_tie=True)
            stats["hole_fill_counterexamples"] += intended != rule_output(grid, preserve_winner_holes=True)
            stats["left_column_counterexamples"] += intended != rule_output(grid, omit_left_column=True)
            if index < 8:
                samples_for_racket.append(grid)
        stats["distinct_inputs"] = len(hashes)
        report["bands"][str(band)] = {
            "counts": dict(stats),
            "profiles": dict(profiles),
            "backgrounds": dict(backgrounds),
            "component_signatures": dict(signatures),
        }
    report["racket"] = {"status": "not_requested", "checked": 0}
    report["_racket_grids"] = samples_for_racket
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.count)
    grids = report.pop("_racket_grids")
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [
                index
                for index, (grid, output) in enumerate(zip(grids, outputs))
                if rule_output(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
        except Exception as exc:
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
    path = Path(args.generator or ROOT / f"generators/{TASK}/generator.py")
    report["generator_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"bands": report["bands"], "racket": report["racket"]}, indent=2))
    failures = [row for row in report["canonical"] if not row["oracle_matches"] or row["self_check"]]
    failures += [
        band
        for band, row in report["bands"].items()
        if row["counts"].get("self_check_errors") or row["counts"].get("nondeterministic")
    ]
    if args.racket and report["racket"]["status"] != "passed":
        return 2
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
