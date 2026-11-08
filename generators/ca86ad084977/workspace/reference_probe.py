#!/usr/bin/env python3
"""Independent, source-bound review probe for generator ca86ad084977.

The probe intentionally reimplements the selected BFS and its two retained
rivals instead of importing production semantic helpers.  It checks canonical
parity, exact override construction, generated morphology, deterministic replay,
canonical-observed input->output transition coverage, declared rival parity, and
every query rotation of consecutive four-pair lessons.

Python observations are supplemental.  Authoritative labels remain Racket-owned.
Run this through the packet wrapper so staged imports and the pinned runtime match
normal review checks::

    python3 review.py run python3 \
      generators/ca86ad084977/workspace/reference_probe.py \
      --per-band 100 --lesson-starts 40 \
      --json-out ../checks/reference-probe-final.json
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Callable

from reviewer_support import canonical_pairs, find_root

TASK_ID = "ca86ad084977"
HOME = Path(__file__).resolve().parents[1]
CHECKPOINTS = (2, 3, 4, 7)
LEGS = ((2, 3), (3, 4), (4, 7))
UDLR = ((-1, 0), (1, 0), (0, -1), (0, 1))
UDRL = ((-1, 0), (1, 0), (0, 1), (0, -1))
BANDS = ("easy", "medium", "hard")


def load_generator():
    source = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"reference_probe_{TASK_ID}", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load selected generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = load_generator()


def checkpoint_positions(grid):
    found = {color: [] for color in CHECKPOINTS}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in found:
                found[value].append((row, col))
    if any(len(points) != 1 for points in found.values()):
        raise ValueError(f"checkpoint multiplicities: {found}")
    return {color: points[0] for color, points in found.items()}


def shortest_path(grid, start, goal, order):
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


def solve_all_interiors(grid, order=UDLR):
    points = checkpoint_positions(grid)
    route = set()
    for first, second in LEGS:
        path = shortest_path(grid, points[first], points[second], order)
        route.update(path[1:-1])
    output = deepcopy(grid)
    for row, col in route:
        output[row][col] = 8
    return output


def solve_preserving_checkpoints(grid):
    points = checkpoint_positions(grid)
    route = set()
    for first, second in LEGS:
        path = shortest_path(grid, points[first], points[second], UDLR)
        route.update(path[1:-1])
    output = deepcopy(grid)
    for row, col in route:
        if output[row][col] == 0:
            output[row][col] = 8
    return output


INDEPENDENT_RIVALS: dict[str, Callable] = {
    "right_before_left": lambda grid: solve_all_interiors(grid, UDRL),
    "preserve_checkpoints": solve_preserving_checkpoints,
}


def changed_transitions(before, after):
    counts = Counter()
    for input_row, output_row in zip(before, after):
        for source, target in zip(input_row, output_row):
            if source != target:
                counts[f"{source}->{target}"] += 1
    return counts


def overwritten_checkpoint_colors(before, after):
    return sorted(
        {
            source
            for input_row, output_row in zip(before, after)
            for source, target in zip(input_row, output_row)
            if source in CHECKPOINTS and target == 8
        }
    )


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


def independent_rival(name):
    try:
        return INDEPENDENT_RIVALS[name]
    except KeyError as exc:
        raise ValueError(f"probe has no independent oracle for declared rival {name!r}") from exc


def canonical_report():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    selected_mismatches = []
    shortcut_mismatches = {name: [] for name in GEN.CANONICAL_SHORTCUTS}
    production_rival_mismatches = {
        name: [] for name in set(GEN.CANONICAL_SHORTCUTS) | set(GEN.LESSON_COMPETITORS)
    }
    transition_counts = Counter()
    per_pair = []
    for index, pair in enumerate(pairs):
        expected = pair["output"]
        selected = solve_all_interiors(pair["input"])
        if selected != expected:
            selected_mismatches.append(index)
        transitions = changed_transitions(pair["input"], expected)
        transition_counts.update(transitions)
        per_pair.append(
            {
                "index": index,
                "shape": [len(pair["input"]), len(pair["input"][0])],
                "transitions": dict(sorted(transitions.items())),
                "overwritten_checkpoints": overwritten_checkpoint_colors(
                    pair["input"], expected
                ),
            }
        )
        for name, production_rival in {
            **GEN.CANONICAL_SHORTCUTS,
            **GEN.LESSON_COMPETITORS,
        }.items():
            independent = independent_rival(name)(pair["input"])
            production = production_rival(pair["input"])
            if production != independent:
                production_rival_mismatches[name].append(index)
        for name in GEN.CANONICAL_SHORTCUTS:
            if independent_rival(name)(pair["input"]) != expected:
                shortcut_mismatches[name].append(index)
    return {
        "labeled_pairs": len(pairs),
        "selected_oracle_mismatches": selected_mismatches,
        "canonical_shortcut_mismatches": shortcut_mismatches,
        "production_vs_independent_rival_mismatches": production_rival_mismatches,
        "transition_counts": dict(sorted(transition_counts.items())),
        "observed_transition_types": sorted(transition_counts),
        "pairs": per_pair,
    }


def override_report():
    failures = []
    cases = 0
    for band in (None, *BANDS):
        for height in (12, 13):
            for width in (12, 13, 14):
                for pattern in GEN.SCHEDULE_PROFILES:
                    cases += 1
                    expected = {
                        "grid_h": height,
                        "grid_w": width,
                        "scene_pattern": pattern,
                    }
                    sample_index = cases * 2 + (1 if pattern == "semantic_witness" else 0)
                    try:
                        grid = GEN.generate(
                            40_000 + cases,
                            sample_index,
                            difficulty=band,
                            **expected,
                        )
                        observed = GEN.observe_overrides(grid)
                        findings = GEN.self_check(grid)
                        strict_findings = GEN.strict_canonical_like(grid)
                        truth = solve_all_interiors(grid)
                        production_rival_drift = {}
                        for name, production_rival in GEN.LESSON_COMPETITORS.items():
                            independent = independent_rival(name)(grid)
                            if production_rival(grid) != independent:
                                production_rival_drift[name] = True
                        tie_differs = independent_rival("right_before_left")(grid) != truth
                        preserve_differs = independent_rival("preserve_checkpoints")(grid) != truth
                        if (
                            findings
                            or strict_findings
                            or observed != expected
                            or tie_differs != (pattern == "semantic_witness")
                            or preserve_differs != (pattern == "semantic_witness")
                            or production_rival_drift
                        ):
                            failures.append(
                                {
                                    "band": band,
                                    "expected": expected,
                                    "observed": observed,
                                    "self_check": findings,
                                    "strict": strict_findings,
                                    "tie_differs": tie_differs,
                                    "preserve_differs": preserve_differs,
                                    "production_rival_drift": production_rival_drift,
                                }
                            )
                    except Exception as exc:  # evidence wants the exact case
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
    component_counts = Counter()
    wall_counts = Counter()
    overwrite_sets = Counter()
    transitions = Counter()
    failures = []
    replay_failures = []
    rival_drift = []
    inputs = set()
    for index in range(per_band):
        seed = 90_000 + index * 997
        grid = GEN.generate(seed, index, difficulty=band)
        if grid != GEN.generate(seed, index, difficulty=band):
            replay_failures.append(index)
        findings = GEN.self_check(grid)
        strict_findings = GEN.strict_canonical_like(grid)
        if findings or strict_findings:
            failures.append(
                {
                    "index": index,
                    "self_check": findings,
                    "strict": strict_findings,
                }
            )
            continue
        truth = solve_all_interiors(grid)
        observed = GEN.observe_overrides(grid)
        pattern = observed["scene_pattern"]
        expected_pattern = GEN.schedule_profile(seed, index, band)
        if pattern != expected_pattern:
            failures.append(
                {
                    "index": index,
                    "finding": f"schedule {expected_pattern!r}, observed {pattern!r}",
                }
            )
        for name, production_rival in GEN.LESSON_COMPETITORS.items():
            if production_rival(grid) != independent_rival(name)(grid):
                rival_drift.append({"index": index, "rival": name})
        sizes = wall_component_sizes(grid)
        transition_counts = changed_transitions(grid, truth)
        transitions.update(transition_counts)
        patterns[pattern] += 1
        shapes[f"{len(grid)}x{len(grid[0])}"] += 1
        component_counts[str(len(sizes))] += 1
        wall_counts[str(sum(sizes))] += 1
        overwrite_sets[json.dumps(overwritten_checkpoint_colors(grid, truth))] += 1
        inputs.add(
            hashlib.sha256(
                json.dumps(grid, separators=(",", ":")).encode()
            ).hexdigest()
        )
    return {
        "draws": per_band,
        "patterns": dict(sorted(patterns.items())),
        "shapes": dict(sorted(shapes.items())),
        "wall_component_counts": dict(sorted(component_counts.items())),
        "wall_cell_counts": dict(sorted(wall_counts.items(), key=lambda item: int(item[0]))),
        "checkpoint_overwrite_sets": dict(sorted(overwrite_sets.items())),
        "transition_counts": dict(sorted(transitions.items())),
        "observed_transition_types": sorted(transitions),
        "distinct_inputs": len(inputs),
        "self_check_or_profile_failures": failures,
        "deterministic_replay_failures": replay_failures,
        "production_vs_independent_rival_mismatches": rival_drift,
    }


def lesson_report(starts):
    failures = []
    rotations_checked = 0
    lessons_checked = 0
    demo_witness_counts = Counter()
    rival_refutations = Counter()
    schedule_residues = Counter()
    for band in BANDS:
        for start in range(starts):
            lessons_checked += 1
            schedule_residues[str(start % GEN.LESSON_SCHEDULE_PERIOD)] += 1
            pairs = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = GEN.generate(700_000 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": solve_all_interiors(grid)})
            for query_index, query in enumerate(pairs):
                rotations_checked += 1
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                demo_witness_counts[str(sum(
                    GEN.observe_overrides(pair["input"])["scene_pattern"]
                    == "semantic_witness"
                    for pair in demos
                ))] += 1
                hook_findings = GEN.lesson_identifiable(deepcopy(demos), deepcopy(query))
                for name, production_rival in GEN.LESSON_COMPETITORS.items():
                    independent = independent_rival(name)
                    if any(
                        production_rival(pair["input"]) != independent(pair["input"])
                        for pair in (*demos, query)
                    ):
                        failures.append(
                            {
                                "band": band,
                                "start": start,
                                "query_index": query_index,
                                "rival": name,
                                "finding": "production rival disagrees with independent probe",
                            }
                        )
                        continue
                    refuting_indices = [
                        index
                        for index, pair in enumerate(demos)
                        if independent(pair["input"]) != pair["output"]
                    ]
                    rival_refutations[name] += bool(refuting_indices)
                    rival_fits = not refuting_indices
                    rival_changes_query = independent(query["input"]) != query["output"]
                    if rival_fits and rival_changes_query:
                        failures.append(
                            {
                                "band": band,
                                "start": start,
                                "query_index": query_index,
                                "rival": name,
                                "finding": "rival fits all demos and changes query",
                            }
                        )
                if hook_findings:
                    failures.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "finding": "lesson_identifiable returned findings",
                            "hook_findings": hook_findings,
                        }
                    )
    return {
        "examples_needed": GEN.EXAMPLES_NEEDED,
        "pairs_per_lesson": GEN.EXAMPLES_NEEDED + 1,
        "lesson_starts_per_band": starts,
        "lessons_checked": lessons_checked,
        "rotations_checked": rotations_checked,
        "declared_schedule_period": GEN.LESSON_SCHEDULE_PERIOD,
        "schedule_start_residue_counts": dict(sorted(schedule_residues.items())),
        "semantic_witnesses_per_demo_set": dict(sorted(demo_witness_counts.items())),
        "rotations_refuted_by_rival": dict(sorted(rival_refutations.items())),
        "failures": failures,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--lesson-starts", type=int, default=40)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band <= 0 or args.lesson_starts <= 0:
        parser.error("--per-band and --lesson-starts must be positive")

    canonical = canonical_report()
    overrides = override_report()
    bands = {band: band_report(band, args.per_band) for band in BANDS}
    lessons = lesson_report(args.lesson_starts)
    generated_transition_types = sorted(
        {
            transition
            for data in bands.values()
            for transition in data["observed_transition_types"]
        }
    )
    canonical_transition_types = canonical["observed_transition_types"]
    missing_transitions = sorted(
        set(canonical_transition_types) - set(generated_transition_types)
    )

    report = {
        "schema": "ca86ad084977-reference-probe-v1",
        "task_id": TASK_ID,
        "generator_version": GEN.VERSION,
        "rule_hash": GEN.RULE_HASH,
        "generator_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(),
        "canonical": canonical,
        "overrides": overrides,
        "bands": bands,
        "transition_coverage": {
            "canonical_observed": canonical_transition_types,
            "generated_observed": generated_transition_types,
            "missing": missing_transitions,
        },
        "lessons": lessons,
        "warning": (
            "Independent Python oracle is supplemental; authoritative labels are "
            "Racket-owned. Coverage is limited to declared rivals and observed "
            "canonical transitions."
        ),
    }

    failures = []
    if canonical["selected_oracle_mismatches"]:
        failures.append("selected independent oracle mismatched canonical labels")
    if any(canonical["canonical_shortcut_mismatches"].values()):
        failures.append("a declared canonical shortcut did not fit every canonical label")
    if any(canonical["production_vs_independent_rival_mismatches"].values()):
        failures.append("production rival helper disagreed with independent probe on canonical data")
    if overrides["failures"]:
        failures.append("exact override matrix failed")
    for band, data in bands.items():
        if (
            data["self_check_or_profile_failures"]
            or data["deterministic_replay_failures"]
            or data["production_vs_independent_rival_mismatches"]
        ):
            failures.append(f"{band} sampling failures")
        if set(data["patterns"]) != set(GEN.SCHEDULE_PROFILES):
            failures.append(f"{band} missing a declared schedule profile")
        if data["distinct_inputs"] < max(1, int(args.per_band * 0.95)):
            failures.append(f"{band} generated too few distinct inputs")
    if missing_transitions:
        failures.append(
            "generated corpus missed canonical-observed transitions: "
            + ", ".join(missing_transitions)
        )
    if lessons["failures"]:
        failures.append("at least one lesson rotation retained a declared rival")

    report["failures"] = failures
    report["status"] = "PASS" if not failures else "FAIL"
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "failures": failures,
                "generator_sha256": report["generator_sha256"],
                "out": str(args.json_out),
            }
        )
    )
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
