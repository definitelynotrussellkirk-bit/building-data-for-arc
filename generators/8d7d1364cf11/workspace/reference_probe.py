"""Independent oracle, contract matrix, and Racket parity probe for 8d7d1364cf11.

This file is review tooling, not a label authority.  Its Python solver is kept
independent from generator helpers.  ``--racket`` calls the supported public
``arcpuzzles apply`` command and fails rather than silently substituting Python.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

TASK = "8d7d1364cf11"
ROOT = Path(__file__).resolve().parents[3]
HOME = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_generator(path: Path | None = None):
    path = (path or HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def canonical_row() -> dict[str, Any]:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise KeyError(f"canonical task {TASK} is absent")


def canonical_pairs() -> list[dict[str, Any]]:
    row = canonical_row()
    test = row.get("test", [])
    if isinstance(test, dict):
        test = [test]
    return list(row.get("train", [])) + list(test)


def components(grid: list[list[int]]) -> list[list[tuple[int, int, int]]]:
    """Independent row-major 8-connected components on background color 4."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int, int]]] = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 4 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col, grid[row][col]))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = row + dr, col + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and grid[nr][nc] != 4
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            result.append(sorted(cells))
    return result


def scene(grid: list[list[int]]) -> dict[str, Any]:
    comps = components(grid)
    shapes = [component for component in comps if len(component) > 1]
    dots = [component[0] for component in comps if len(component) == 1]
    matches: dict[int, list[tuple[int, int, int]]] = {}
    for shape_index, shape in enumerate(shapes):
        for row, col, color in shape:
            matches.setdefault(color, []).append((shape_index, row, col))
    active: list[tuple[int, int, int, int, int, int]] = []
    decoys: list[tuple[int, int, int]] = []
    ambiguous: list[tuple[int, int, int, list[tuple[int, int, int]]]] = []
    per_shape = Counter()
    for row, col, color in dots:
        found = matches.get(color, [])
        if len(found) == 1:
            shape_index, anchor_r, anchor_c = found[0]
            active.append((row, col, color, shape_index, anchor_r, anchor_c))
            per_shape[shape_index] += 1
        elif not found:
            decoys.append((row, col, color))
        else:
            ambiguous.append((row, col, color, found))
    return {
        "components": comps,
        "shapes": shapes,
        "dots": dots,
        "matches": matches,
        "active": active,
        "decoys": decoys,
        "ambiguous": ambiguous,
        "per_shape": per_shape,
    }


def oracle(grid: list[list[int]]) -> list[list[int]]:
    """Independent solver for the generator's documented unique-anchor domain."""
    height, width = len(grid), len(grid[0])
    info = scene(grid)
    output = [[4] * width for _ in range(height)]
    for dot_r, dot_c, color in info["dots"]:
        found = info["matches"].get(color, [])
        if not found:
            continue
        if len(found) != 1:
            raise ValueError(f"color {color} has {len(found)} source anchors")
        shape_index, anchor_r, anchor_c = found[0]
        for row, col, value in info["shapes"][shape_index]:
            nr, nc = dot_r + row - anchor_r, dot_c + col - anchor_c
            if 0 <= nr < height and 0 <= nc < width:
                output[nr][nc] = value
    return output


def ignore_productive_color5(grid: list[list[int]]) -> list[list[int]]:
    """Strong canonical-fitting shortcut: never stamp a color-5 dot."""
    height, width = len(grid), len(grid[0])
    info = scene(grid)
    output = [[4] * width for _ in range(height)]
    for dot_r, dot_c, color in info["dots"]:
        if color == 5:
            continue
        found = info["matches"].get(color, [])
        if len(found) != 1:
            continue
        shape_index, anchor_r, anchor_c = found[0]
        for row, col, value in info["shapes"][shape_index]:
            nr, nc = dot_r + row - anchor_r, dot_c + col - anchor_c
            if 0 <= nr < height and 0 <= nc < width:
                output[nr][nc] = value
    return output


def freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def grid_sha(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def differing_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [
        [row, col]
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def axis_matrix(module, *, enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"status": "not_requested", "cases": 0}
    domains = {
        "grid_h": (16, 20, 24),
        "grid_w": (16, 20, 24),
        "n_shapes": (2, 3),
        "copies_per_shape": (1, 2),
        "n_decoy_dots": (1, 2, 3),
        "shape_variant": tuple(range(6)),
        "shared_body": (False, True),
    }
    bands = (None, "easy", "medium", "hard")
    failures: list[dict[str, Any]] = []
    cases = 0
    for values in itertools.product(*(domains[name] for name in domains), bands):
        options = dict(zip(domains, values[:-1]))
        band = values[-1]
        seed = 20_000 + cases
        sample_index = 1 + 4 * (cases % 997)  # force broad profile while preserving exact axes
        try:
            grid = module.generate(seed, sample_index, difficulty=band, **options)
            observed = module.observe_overrides(grid)
            issues = module.self_check(grid, difficulty=band)
            expected = oracle(grid)
            if observed != options or issues or expected == grid:
                failures.append(
                    {
                        "case": cases,
                        "difficulty": band,
                        "options": options,
                        "observed": observed,
                        "issues": issues,
                        "changed": expected != grid,
                    }
                )
        except Exception as exc:  # retained compactly; full traceback is unnecessary here
            failures.append(
                {
                    "case": cases,
                    "difficulty": band,
                    "options": options,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        cases += 1
    return {
        "status": "passed" if not failures else "failed",
        "cases": cases,
        "domains": {name: list(values) for name, values in domains.items()},
        "bands": list(bands),
        "failures": failures[:50],
        "failure_count": len(failures),
        "sampling_note": "Full product over declared semantic/count axes; grid dimensions use min/mid/max representatives.",
    }


def distribution_audit(module, count: int) -> tuple[dict[str, Any], list[list[list[int]]]]:
    by_band: dict[str, Any] = {}
    racket_candidates: list[list[list[int]]] = []
    all_hashes: set[str] = set()
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        counters = Counter()
        hashes: set[str] = set()
        anchors: set[tuple[int, int]] = set()
        quadrants: set[tuple[bool, bool]] = set()
        dimension_hist = Counter()
        shape_hist = Counter()
        copies_hist = Counter()
        decoy_hist = Counter()
        rival_disagreements = Counter()
        for index in range(count):
            seed = 100_000 + band_index * 10_000 + index
            sample_index = index
            grid = module.generate(seed, sample_index, difficulty=band)
            repeated = module.generate(seed, sample_index, difficulty=band)
            counters["samples"] += 1
            counters["nondeterministic"] += grid != repeated
            self_issues = module.self_check(grid, difficulty=band)
            strict_issues = module.strict_canonical_like(grid)
            counters["self_check_failures"] += bool(self_issues)
            counters["strict_failures"] += bool(strict_issues)
            info = scene(grid)
            counters["ambiguous_anchor_inputs"] += bool(info["ambiguous"])
            counters["missing_decoy_inputs"] += not bool(info["decoys"])
            counters["productive_color5_inputs"] += any(item[2] == 5 for item in info["active"])
            counters["all_shapes_represented"] += set(info["per_shape"]) == set(range(len(info["shapes"])))
            expected = oracle(grid)
            counters["changed_outputs"] += expected != grid
            for name, rival in module.LESSON_COMPETITORS.items():
                try:
                    rival_disagreements[name] += rival(grid) != expected
                except Exception:
                    counters[f"rival_errors:{name}"] += 1
            h, w = len(grid), len(grid[0])
            dimension_hist[f"{h}x{w}"] += 1
            shape_hist[str(len(info["shapes"]))] += 1
            copies = sorted(info["per_shape"].values())
            copies_hist[str(copies[0] if copies and len(set(copies)) == 1 else copies)] += 1
            decoy_hist[str(len(info["decoys"]))] += 1
            for shape in info["shapes"]:
                top = min(row for row, _col, _value in shape)
                left = min(col for _row, col, _value in shape)
                anchors.add((top, left))
                quadrants.add((top >= h // 2, left >= w // 2))
            digest = grid_sha(grid)
            hashes.add(digest)
            all_hashes.add(digest)
            if len(racket_candidates) < 60 and index < 20:
                racket_candidates.append(grid)
        by_band[str(band)] = {
            "counts": dict(counters),
            "unique_inputs": len(hashes),
            "distinct_source_anchors": len(anchors),
            "source_quadrants": [list(item) for item in sorted(quadrants)],
            "dimension_histogram": dict(sorted(dimension_hist.items())),
            "shape_count_histogram": dict(sorted(shape_hist.items())),
            "copies_per_shape_histogram": dict(sorted(copies_hist.items())),
            "decoy_count_histogram": dict(sorted(decoy_hist.items())),
            "rival_disagreements": dict(sorted(rival_disagreements.items())),
        }
    return {
        "count_per_band": count,
        "total_draws": count * 4,
        "union_unique_inputs": len(all_hashes),
        "by_band": by_band,
        "sampling_note": "Disjoint seed ranges are used per band; union-unique counts are not sums of lesson windows.",
    }, racket_candidates


def canonical_audit(module) -> dict[str, Any]:
    pairs = canonical_pairs()
    declared = module.LESSON_COMPETITORS
    fit = {name: [] for name in declared}
    oracle_matches = []
    self_check = []
    for pair in pairs:
        oracle_matches.append(oracle(pair["input"]) == pair["output"])
        self_check.append(module.self_check(pair["input"]))
        for name, rival in declared.items():
            fit[name].append(rival(pair["input"]) == pair["output"])
    return {
        "pairs": len(pairs),
        "oracle_matches": oracle_matches,
        "self_check_issues": self_check,
        "declared_rival_fits": fit,
        "ignore_productive_color5_fits_all": all(fit.get("ignore_productive_color5", [])),
    }


def run_public_racket(grids: list[list[list[int]]], timeout: int) -> dict[str, Any]:
    if len(grids) > 64:
        raise ValueError("public apply accepts at most 64 grids")
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-apply-") as directory:
        temp = Path(directory)
        input_path = temp / "input.json"
        output_path = temp / "output.json"
        input_path.write_text(json.dumps({"inputs": grids}))
        env = dict(os.environ)
        src = str(ROOT / "src")
        env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        command = [
            sys.executable,
            "-B",
            "-m",
            "arcpuzzles",
            "apply",
            TASK,
            "--input",
            str(input_path),
            "--reference",
            "canonical",
            "--timeout",
            str(timeout),
            "--out",
            str(output_path),
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout + 60,
            check=False,
        )
        if completed.returncode != 0 or not output_path.exists():
            return {
                "status": "failed",
                "command": command,
                "cwd": str(ROOT),
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        payload = json.loads(output_path.read_text())
        outputs = [item["output"] for item in payload.get("results", [])]
        expected = [oracle(grid) for grid in grids]
        mismatches = [index for index, (left, right) in enumerate(zip(outputs, expected)) if left != right]
        if len(outputs) != len(grids):
            mismatches.extend(range(len(outputs), len(grids)))
        return {
            "status": "passed" if not mismatches else "failed",
            "command": command,
            "cwd": str(ROOT),
            "exit_code": completed.returncode,
            "checked": len(outputs),
            "mismatches": mismatches,
            "executed_rule_hash": payload.get("executed_rule_hash"),
            "catalog_rule_hash": payload.get("catalog_rule_hash"),
            "rule_hash_matches_catalog": payload.get("rule_hash_matches_catalog"),
            "generator_sha256": payload.get("generator_sha256"),
            "elapsed_seconds": payload.get("elapsed_seconds"),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--axis-matrix", action="store_true")
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--racket-timeout", type=int, default=240)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")

    module, generator_path = load_generator(args.generator)
    canonical_report = canonical_audit(module)
    distribution, candidates = distribution_audit(module, args.count)
    matrix = axis_matrix(module, enabled=args.axis_matrix)

    witness_input = module.generate(70_001, 1, difficulty="hard")
    intended = oracle(witness_input)
    shortcut = ignore_productive_color5(witness_input)
    witness = {
        "seed": 70_001,
        "sample_index": 1,
        "difficulty": "hard",
        "input": witness_input,
        "intended_python": intended,
        "ignore_productive_color5": shortcut,
        "differing_cells": differing_cells(intended, shortcut),
        "validator_issues": module.self_check(witness_input, difficulty="hard"),
        "belongs_to_final_sampler": True,
    }

    racket = {"status": "not_requested", "checked": 0}
    if args.racket:
        grids = [pair["input"] for pair in canonical_pairs()] + [witness_input]
        for grid in candidates:
            if len(grids) >= 64:
                break
            grids.append(grid)
        racket = run_public_racket(grids, args.racket_timeout)
        if racket.get("status") == "passed":
            witness["intended_racket"] = intended

    canonical_program = canonical_row()["program_solution"]
    report = {
        "schema": f"{TASK}-independent-reference-probe-v1",
        "task_id": TASK,
        "generator_version": module.VERSION,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical_rule_hash": hashlib.sha256(" ".join(canonical_program.split()).encode()).hexdigest()[:12],
        "canonical": canonical_report,
        "distribution": distribution,
        "axis_matrix": matrix,
        "canonical_shortcut_witness": witness,
        "racket": racket,
        "limits": [
            "The Python oracle covers the generator's documented unique-anchor domain, not ambiguous first-match behavior outside that domain.",
            "Finite declared-rival checks do not prove uniqueness against undeclared programs.",
            "The dimension portion of the axis matrix uses min/mid/max representatives rather than all 81 dimension pairs.",
        ],
    }
    args.out = args.out.resolve()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")

    failures = []
    failures += ["canonical oracle mismatch"] if not all(canonical_report["oracle_matches"]) else []
    failures += ["canonical self_check failure"] if any(canonical_report["self_check_issues"]) else []
    for band, data in distribution["by_band"].items():
        counts = data["counts"]
        for key in ("nondeterministic", "self_check_failures", "strict_failures", "ambiguous_anchor_inputs", "missing_decoy_inputs"):
            if counts.get(key):
                failures.append(f"{band}: {key}={counts[key]}")
    if matrix["status"] == "failed":
        failures.append(f"axis matrix failures={matrix['failure_count']}")
    if not witness["differing_cells"]:
        failures.append("color-5 shortcut witness does not disagree")
    if args.racket and racket.get("status") != "passed":
        failures.append(f"Racket parity status={racket.get('status')}")

    print(
        json.dumps(
            {
                "generator_version": module.VERSION,
                "generator_sha256": report["generator_sha256"],
                "canonical": canonical_report,
                "total_draws": distribution["total_draws"],
                "union_unique_inputs": distribution["union_unique_inputs"],
                "axis_matrix": {k: matrix[k] for k in ("status", "cases", "failure_count") if k in matrix},
                "witness_differences": len(witness["differing_cells"]),
                "racket": racket,
                "failures": failures,
                "out": str(args.out),
            },
            indent=2,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
