#!/usr/bin/env python3
"""Independent review probe for generator 2a40849f3961.

This tool deliberately reimplements both the selected BFS and the strongest
canonical-fitting rival instead of importing production semantic helpers.  It
checks canonical parity, exact axes, generated morphology, deterministic replay,
left/right tie witnesses, and every query rotation of consecutive lessons.
Python results are supplemental; authoritative labels remain Racket-owned.

Portable invocation from an extracted review packet::

    python3 run_with_racket.py python3 \
      generators/2a40849f3961/workspace/reference_probe.py \
      --per-band 100 --lesson-starts 40 \
      --json-out ../checks/reference-probe.json
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "2a40849f3961"
HOME = Path(__file__).resolve().parents[1]
UDLR = ((-1, 0), (1, 0), (0, -1), (0, 1))
UDRL = ((-1, 0), (1, 0), (0, 1), (0, -1))


def load_generator():
    spec = importlib.util.spec_from_file_location(
        f"probe_generator_{TASK_ID}", HOME / "generator.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load selected generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = load_generator()


def checkpoints(grid):
    found = {color: [] for color in (1, 2, 3, 4)}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in found:
                found[value].append((row, col))
    if any(len(points) != 1 for points in found.values()):
        raise ValueError(f"checkpoint multiplicities: {found}")
    return {color: points[0] for color, points in found.items()}


def path(grid, start, goal, order):
    height, width = len(grid), len(grid[0])
    queue = deque([start])
    parent = {start: None}
    while queue:
        point = queue.popleft()
        if point == goal:
            break
        for delta_row, delta_col in order:
            neighbor = point[0] + delta_row, point[1] + delta_col
            if (
                0 <= neighbor[0] < height
                and 0 <= neighbor[1] < width
                and grid[neighbor[0]][neighbor[1]] != 5
                and neighbor not in parent
            ):
                parent[neighbor] = point
                queue.append(neighbor)
    if goal not in parent:
        return []
    answer = []
    point = goal
    while point is not None:
        answer.append(point)
        point = parent[point]
    return list(reversed(answer))


def solve(grid, order=UDLR):
    positions = checkpoints(grid)
    output = deepcopy(grid)
    route = set()
    for first, second in ((1, 2), (2, 3), (3, 4)):
        route.update(path(grid, positions[first], positions[second], order)[1:-1])
    for row, col in route:
        if output[row][col] == 0:
            output[row][col] = 8
    return output


def wall_component_sizes(grid):
    walls = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    }
    seen = set()
    sizes = []
    for start in sorted(walls):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        size = 0
        while stack:
            row, col = stack.pop()
            size += 1
            for delta_row, delta_col in UDLR:
                neighbor = row + delta_row, col + delta_col
                if neighbor in walls and neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def canonical_report():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    intended_mismatches = []
    rival_mismatches = []
    for index, pair in enumerate(pairs):
        if solve(pair["input"], UDLR) != pair["output"]:
            intended_mismatches.append(index)
        if solve(pair["input"], UDRL) != pair["output"]:
            rival_mismatches.append(index)
    return {
        "labeled_pairs": len(pairs),
        "selected_oracle_mismatches": intended_mismatches,
        "right_before_left_mismatches": rival_mismatches,
    }


def override_report():
    failures = []
    cases = 0
    for band in (None, "easy", "medium", "hard"):
        for height in range(11, 14):
            for width in range(12, 15):
                for pattern in GEN.SCHEDULE_PROFILES:
                    cases += 1
                    expected = {
                        "grid_h": height,
                        "grid_w": width,
                        "scene_pattern": pattern,
                    }
                    try:
                        grid = GEN.generate(
                            40_000 + cases,
                            cases,
                            difficulty=band,
                            **expected,
                        )
                        observed = GEN.observe_overrides(grid)
                        findings = GEN.self_check(grid)
                        truth = solve(grid, UDLR)
                        rival = solve(grid, UDRL)
                        if (
                            findings
                            or observed != expected
                            or (truth != rival) != (pattern == "tie_break")
                        ):
                            failures.append(
                                {
                                    "band": band,
                                    "expected": expected,
                                    "observed": observed,
                                    "findings": findings,
                                    "rival_differs": truth != rival,
                                }
                            )
                    except Exception as exc:
                        failures.append(
                            {
                                "band": band,
                                "expected": expected,
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )
    return {"cases": cases, "failures": failures}


def band_report(band, per_band):
    patterns = Counter()
    shapes = Counter()
    max_objects = Counter()
    failures = []
    replay_failures = []
    inputs = set()
    witness_count = 0
    for index in range(per_band):
        seed = 90_000 + index * 997
        grid = GEN.generate(seed, index, difficulty=band)
        if grid != GEN.generate(seed, index, difficulty=band):
            replay_failures.append(index)
        findings = GEN.self_check(grid)
        if findings:
            failures.append({"index": index, "findings": findings})
            continue
        observed = GEN.observe_overrides(grid)
        truth = solve(grid, UDLR)
        rival = solve(grid, UDRL)
        if truth == grid:
            failures.append({"index": index, "findings": ["identity output"]})
        pattern = observed["scene_pattern"]
        patterns[pattern] += 1
        witness_count += truth != rival
        shapes[f"{len(grid)}x{len(grid[0])}"] += 1
        sizes = wall_component_sizes(grid)
        max_objects[str(max(sizes))] += 1
        inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
    return {
        "draws": per_band,
        "patterns": dict(sorted(patterns.items())),
        "tie_witnesses": witness_count,
        "shapes": dict(sorted(shapes.items())),
        "max_wall_object_sizes": dict(sorted(max_objects.items(), key=lambda item: int(item[0]))),
        "distinct_inputs": len(inputs),
        "self_check_or_oracle_failures": failures,
        "deterministic_replay_failures": replay_failures,
    }


def lesson_report(starts):
    failures = []
    rotations_checked = 0
    for band in ("easy", "medium", "hard"):
        for start in range(starts):
            pairs = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = GEN.generate(700_000 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": solve(grid, UDLR)})
            for query_index, query in enumerate(pairs):
                rotations_checked += 1
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                rival_fits = all(
                    solve(pair["input"], UDRL) == pair["output"] for pair in demos
                )
                rival_changes_query = solve(query["input"], UDRL) != query["output"]
                hook = GEN.lesson_identifiable(deepcopy(demos), deepcopy(query))
                if (rival_fits and rival_changes_query) or hook:
                    failures.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "rival_fits_demos": rival_fits,
                            "rival_changes_query": rival_changes_query,
                            "hook_findings": hook,
                        }
                    )
    return {"rotations_checked": rotations_checked, "failures": failures}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--lesson-starts", type=int, default=40)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    report = {
        "schema": "2a40849f3961-reference-probe-v1",
        "task_id": TASK_ID,
        "generator_version": GEN.VERSION,
        "generator_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(),
        "canonical": canonical_report(),
        "overrides": override_report(),
        "bands": {
            band: band_report(band, args.per_band)
            for band in ("easy", "medium", "hard")
        },
        "lessons": lesson_report(args.lesson_starts),
        "warning": "Independent Python oracle is supplemental; authoritative labels are Racket-owned.",
    }
    failures = []
    if report["canonical"]["selected_oracle_mismatches"]:
        failures.append("selected Python oracle mismatched canonical labels")
    if report["canonical"]["right_before_left_mismatches"]:
        failures.append("declared shortcut did not fit every canonical label")
    if report["overrides"]["failures"]:
        failures.append("exact override matrix failed")
    for band, data in report["bands"].items():
        if data["self_check_or_oracle_failures"] or data["deterministic_replay_failures"]:
            failures.append(f"{band} sampling failures")
        if set(data["patterns"]) != set(GEN.SCHEDULE_PROFILES):
            failures.append(f"{band} missing a schedule profile")
    if report["lessons"]["failures"]:
        failures.append("at least one lesson rotation retained the shortcut")
    report["failures"] = failures
    report["status"] = "PASS" if not failures else "FAIL"
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "failures": failures, "out": str(args.json_out)}))
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
