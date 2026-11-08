"""Independent oracle, shortcut witnesses, and repeatable audit for 5bcc776c32fb.

This module is reviewer tooling, not label authority.  ``--racket`` executes the
canonical Racket program and fails loudly when that runtime is unavailable; it
never substitutes the Python oracle for authority evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import sys
from typing import Iterable, Sequence

TASK = "5bcc776c32fb"
HERE = Path(__file__).resolve()
HOME = HERE.parents[1]

# Both the source repository and the portable task-test runtime expose this path.
for candidate in (HERE.parents[3] / "shared/runtime", HERE.parents[2] / "shared/runtime"):
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

ROOT = find_root(HERE)


def load_generator(path: str | os.PathLike[str] | None = None):
    selected = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", selected)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {selected}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=ROOT, labeled_only=True)


def _grid_copy(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def components(grid: Sequence[Sequence[int]], *, colors: Iterable[int] | None = None):
    """Return monochromatic 4-connected non-background components."""
    allowed = None if colors is None else set(colors)
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (allowed is not None and color not in allowed) or (row, col) in seen:
                continue
            frontier = [(row, col)]
            seen.add((row, col))
            cells = []
            for current_row, current_col in frontier:
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    frontier.append((next_row, next_col))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "r1": min(rows),
                    "r2": max(rows),
                    "c1": min(cols),
                    "c2": max(cols),
                    "h": max(rows) - min(rows) + 1,
                    "w": max(cols) - min(cols) + 1,
                }
            )
    return result


def _horizontal_target(component, *, minimum: int = 3) -> bool:
    return (
        component["color"] == 1
        and component["h"] == 1
        and component["size"] >= minimum
        and component["size"] % 2 == 1
    )


def intended_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    output = _grid_copy(grid)
    for component in components(grid, colors={1}):
        if _horizontal_target(component):
            output[component["r1"]][(component["c1"] + component["c2"]) // 2] = 2
    return output


def _solve_components(grid, predicate, *, colors: Iterable[int] | None = None):
    output = _grid_copy(grid)
    for component in components(grid, colors=colors):
        if predicate(component):
            row = (component["r1"] + component["r2"]) // 2
            col = (component["c1"] + component["c2"]) // 2
            output[row][col] = 2
    return output


def rival_color_blind(grid):
    """Shortcut: mark every odd horizontal component, ignoring its color."""
    return _solve_components(
        grid,
        lambda obj: obj["h"] == 1 and obj["size"] >= 3 and obj["size"] % 2 == 1,
    )


def rival_no_minimum(grid):
    """Shortcut: treat a singleton blue component as an odd horizontal line."""
    return _solve_components(
        grid,
        lambda obj: obj["color"] == 1 and obj["h"] == 1 and obj["size"] % 2 == 1,
        colors={1},
    )


def rival_lengths_357(grid):
    """Shortcut: memorize the only qualifying canonical lengths 3, 5, and 7."""
    return _solve_components(
        grid,
        lambda obj: obj["color"] == 1 and obj["h"] == 1 and obj["size"] in {3, 5, 7},
        colors={1},
    )


def rival_parity_blind(grid):
    """Wrong rule: mark the left-middle of every horizontal blue line >=2."""
    return _solve_components(
        grid,
        lambda obj: obj["color"] == 1 and obj["h"] == 1 and obj["size"] >= 2,
        colors={1},
    )


def rival_orientation_blind(grid):
    """Wrong rule: mark the midpoint of every odd straight blue component."""
    return _solve_components(
        grid,
        lambda obj: (
            obj["color"] == 1
            and (obj["h"] == 1 or obj["w"] == 1)
            and obj["size"] >= 3
            and obj["size"] % 2 == 1
        ),
        colors={1},
    )


def rival_row_runs(grid):
    """Wrong rule: operate on odd blue row-runs without object segmentation."""
    output = _grid_copy(grid)
    for row_index, row in enumerate(grid):
        col = 0
        while col < len(row):
            if row[col] != 1:
                col += 1
                continue
            start = col
            while col < len(row) and row[col] == 1:
                col += 1
            length = col - start
            if length >= 3 and length % 2 == 1:
                output[row_index][start + length // 2] = 2
    return output


def observed(grid):
    non_rule_colors = sorted({value for row in grid for value in row if value not in {0, 1}})
    if len(non_rule_colors) != 1:
        raise ValueError(f"expected exactly one distractor color, found {non_rule_colors}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_targets": sum(_horizontal_target(obj) for obj in components(grid, colors={1})),
        "distractor_color": non_rule_colors[0],
    }


def _row_runs(component):
    by_row: dict[int, list[int]] = {}
    for row, col in component["cells"]:
        by_row.setdefault(row, []).append(col)
    lengths = []
    for cols in by_row.values():
        cols = sorted(cols)
        start = previous = cols[0]
        for col in cols[1:]:
            if col != previous + 1:
                lengths.append(previous - start + 1)
                start = col
            previous = col
        lengths.append(previous - start + 1)
    return lengths


def features(grid):
    blue = components(grid, colors={1})
    other = [obj for obj in components(grid) if obj["color"] != 1]
    return {
        "positive_target": any(_horizontal_target(obj) for obj in blue),
        "even_horizontal_negative": any(
            obj["h"] == 1 and obj["size"] >= 2 and obj["size"] % 2 == 0 for obj in blue
        ),
        "vertical_negative": any(
            obj["w"] == 1 and obj["h"] >= 3 and obj["size"] % 2 == 1 for obj in blue
        ),
        "junction_negative": any(
            obj["h"] > 1
            and obj["w"] > 1
            and any(length >= 3 and length % 2 == 1 for length in _row_runs(obj))
            for obj in blue
        ),
        "singleton_negative": any(obj["size"] == 1 for obj in blue),
        "color_specific_distractor": any(
            obj["h"] == 1 and obj["size"] >= 3 and obj["size"] % 2 == 1 for obj in other
        ),
        "length9_target": any(_horizontal_target(obj) and obj["size"] >= 9 for obj in blue),
    }


def shortcut_witness():
    """Exact color-blind counterexample used in QUESTION_ANSWER.md."""
    grid = [[0] * 10 for _ in range(8)]
    grid[1][1:4] = [1, 1, 1]
    grid[5][4:9] = [7, 7, 7, 7, 7]
    return grid


def racket_outputs(grids):
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    source_root = ROOT
    # A portable runtime can already be the staged root.  The full source tree
    # uses Catalog + prepare_runtime to construct the executable layout.
    if (source_root / "catalog/puzzles.jsonl").is_file():
        import tempfile

        source_src = source_root / "src"
        if str(source_src) not in sys.path:
            sys.path.insert(0, str(source_src))
        from arcpuzzles import Catalog
        from arcpuzzles.runtime import prepare_runtime, run_process

        program = None
        with (source_root / "shared/data/canonical/puzzles.jsonl").open() as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    program = row["program_solution"]
                    break
        if program is None:
            raise KeyError(TASK)
        with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
            stage = Path(directory)
            prepare_runtime(Catalog(source_root), stage, TASK)
            (stage / "parity-request.json").write_text(
                json.dumps({"program": program, "grids": grids})
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
            return json.loads(result["stdout"])

    raise RuntimeError("Racket parity helper requires the full source repository layout")


def audit(module, count: int):
    """Run a source-bound semantic, distribution, and curriculum audit."""
    canonical = canonical_pairs()
    canonical_oracle_errors = [
        pair["variant"]
        for pair in canonical
        if intended_output(pair["input"]) != pair["output"]
    ]
    rivals = {
        "color_blind": rival_color_blind,
        "no_minimum": rival_no_minimum,
        "lengths_357": rival_lengths_357,
        "parity_blind": rival_parity_blind,
        "orientation_blind": rival_orientation_blind,
        "row_runs": rival_row_runs,
    }
    shortcut_fit = {
        name: all(rival(pair["input"]) == pair["output"] for pair in canonical)
        for name, rival in {
            "color_blind": rival_color_blind,
            "no_minimum": rival_no_minimum,
            "lengths_357": rival_lengths_357,
        }.items()
    }
    report = {
        "schema": f"{TASK}-independent-audit-v2",
        "canonical_pairs": len(canonical),
        "canonical_oracle_errors": canonical_oracle_errors,
        "canonical_shortcut_fit": shortcut_fit,
        "bands": {},
    }
    sample_grids = []
    band_failures: list[str] = []
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        profiles = Counter()
        object_counts = Counter()
        hashes = set()
        for index in range(count):
            grid = module.generate(9000 + index, index * 11 + 3, difficulty=band)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            strict_hook = getattr(module, "strict_canonical_like", None)
            if callable(strict_hook):
                counts["strict_errors"] += bool(strict_hook(grid))
            counts["nondeterministic"] += grid != module.generate(
                9000 + index, index * 11 + 3, difficulty=band
            )
            hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            palette = len({value for row in grid for value in row})
            profiles[(len(grid), len(grid[0]), palette)] += 1
            object_counts[len(components(grid))] += 1
            for name, present in features(grid).items():
                counts[f"witness_{name}"] += bool(present)
            intended = intended_output(grid)
            for name, rival in rivals.items():
                counts[f"rival_disagreements_{name}"] += rival(grid) != intended
            if len(sample_grids) < 24:
                sample_grids.append(grid)
        counts["distinct_inputs"] = len(hashes)
        label = str(band)
        report["bands"][label] = {
            "counts": dict(counts),
            "profiles": {str(key): value for key, value in sorted(profiles.items())},
            "object_counts": {str(key): value for key, value in sorted(object_counts.items())},
        }
        required_full = ("positive_target", "length9_target")
        required_some = (
            "even_horizontal_negative",
            "vertical_negative",
            "junction_negative",
            "singleton_negative",
            "color_specific_distractor",
        )
        if counts["samples"] != count:
            band_failures.append(f"{label}: generated {counts['samples']} of {count}")
        if counts["self_check_errors"] or counts["strict_errors"] or counts["nondeterministic"]:
            band_failures.append(
                f"{label}: self={counts['self_check_errors']} strict={counts['strict_errors']} "
                f"nondeterministic={counts['nondeterministic']}"
            )
        if counts["distinct_inputs"] < max(1, int(count * 0.9)):
            band_failures.append(
                f"{label}: only {counts['distinct_inputs']}/{count} distinct inputs"
            )
        for witness in required_full:
            if counts[f"witness_{witness}"] != count:
                band_failures.append(
                    f"{label}: witness {witness} fired {counts[f'witness_{witness}']}/{count}"
                )
        for witness in required_some:
            if not counts[f"witness_{witness}"]:
                band_failures.append(f"{label}: witness {witness} never fired")
        for rival_name in rivals:
            if not counts[f"rival_disagreements_{rival_name}"]:
                band_failures.append(f"{label}: rival {rival_name} was never refuted")

    curriculum = Counter()
    curriculum_examples: list[dict[str, object]] = []
    lesson_hook = getattr(module, "lesson_identifiable", None)
    for band in (None, "easy", "medium", "hard"):
        for start_index in range(12):
            pairs = []
            for offset in range(4):
                grid = module.generate(17000 + start_index, start_index + offset, difficulty=band)
                pairs.append({"input": grid, "output": intended_output(grid)})
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                curriculum["checked_rotations"] += 1
                reasons = (
                    list(lesson_hook(demos, query))
                    if callable(lesson_hook)
                    else ["missing lesson_identifiable"]
                )
                if reasons:
                    curriculum["ambiguous_rotations"] += 1
                    if len(curriculum_examples) < 8:
                        curriculum_examples.append(
                            {
                                "band": band,
                                "start_index": start_index,
                                "query_index": query_index,
                                "reasons": reasons,
                            }
                        )
    report["curriculum"] = {
        "checked_rotations": curriculum["checked_rotations"],
        "ambiguous_rotations": curriculum["ambiguous_rotations"],
        "examples": curriculum_examples,
    }
    report["band_failures"] = band_failures

    witness = shortcut_witness()
    intended = intended_output(witness)
    rival = rival_color_blind(witness)
    report["shortcut_witness"] = {
        "input": witness,
        "intended_python": intended,
        "color_blind_python": rival,
        "differing_cells": [
            [row, col]
            for row in range(len(witness))
            for col in range(len(witness[0]))
            if intended[row][col] != rival[row][col]
        ],
    }
    report["passed"] = (
        not canonical_oracle_errors
        and all(shortcut_fit.values())
        and not band_failures
        and curriculum["checked_rotations"] > 0
        and curriculum["ambiguous_rotations"] == 0
    )
    return report, [pair["input"] for pair in canonical] + [witness] + sample_grids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=128, help="samples per difficulty band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true", help="require real canonical Racket parity")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    generator_path = Path(args.generator or os.environ.get("GENERATOR_UNDER_TEST") or HOME / "generator.py")
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(HERE.read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = 0 if report["passed"] else 1
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            expected = [intended_output(grid) for grid in grids]
            mismatches = [index for index, pair in enumerate(zip(outputs, expected)) if pair[0] != pair[1]]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            if not mismatches:
                canonical_count = len(canonical_pairs())
                report["shortcut_witness"]["intended_racket"] = outputs[canonical_count]
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # loud evidence, never a Python fallback
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "racket": report["racket"]}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
