#!/usr/bin/env python3
"""Retain exact generic tiny mutations and public Racket audit observations.

This diagnostic does not decide legality, waive a lint finding, change approval,
or create training labels. Run through the packet's run_with_racket.py wrapper.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def is_grid(grid):
    """Match the linter's shape gate, including its list-only convention."""
    return (isinstance(grid, list) and bool(grid)
            and isinstance(grid[0], list) and bool(grid[0])
            and all(isinstance(row, list) for row in grid))


def minimal_impostors(grid):
    """Exact recipe inspected in generator_defect_lint.py::_minimal_impostors.

    Counter.most_common resolves modal ties in row-major first-seen order.
    Foreground is the numerically smallest color different from the mode.
    The names are the linter's heuristic names, not claims of illegality.
    """
    height, width = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    modal = counts.most_common(1)[0][0] if counts else 0
    foregrounds = sorted({value for row in grid for value in row} - {modal})
    if not foregrounds:
        return []
    foreground = foregrounds[0]
    result = [
        ("all_background", [[modal] * width for _ in range(height)]),
        ("full_one_color", [[foreground] * width for _ in range(height)]),
    ]
    for name, cells in (
        ("singleton", [(height // 2, width // 2)]),
        ("solid_2x2", [(r, c) for r in range(min(2, height))
                       for c in range(min(2, width))]),
        ("short_line", [(height // 2, c) for c in range(min(4, width))]),
    ):
        mutation = [[modal] * width for _ in range(height)]
        for row, col in cells:
            mutation[row][col] = foreground
        result.append((name, mutation))
    return result


def validator_observation(self_check, grid, band):
    """Match the linter's call/fallback and truthiness interpretation."""
    try:
        try:
            result = self_check(deepcopy(grid), difficulty=band)
        except TypeError:
            result = self_check(deepcopy(grid))
        if result is None or isinstance(result, (bool, str, int, float, list, tuple, dict)):
            serializable = result
        else:
            serializable = repr(result)
        return {"accepted": not bool(result), "validator_result": serializable,
                "validator_exception": None}
    except Exception as exc:
        return {"accepted": False, "validator_result": None,
                "validator_exception": {"type": type(exc).__name__, "message": str(exc)}}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def bounded_samples(text):
    value = int(text)
    if not 1 <= value <= 6:
        raise argparse.ArgumentTypeError("samples must be in 1..6")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id", help="Exact per-puzzle task ID (aliases resolve through Catalog)")
    parser.add_argument("--seed", type=int, default=0, help="Generator seed, constant across sampled indices")
    parser.add_argument("--samples", type=bounded_samples, default=6, help="Baseline draws, 1..6 (default 6)")
    parser.add_argument("--out", required=True, type=Path, help="New diagnostic JSON path, relative to effective cwd")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"output already exists; choose a fresh report path: {args.out}")

    # Public helpers bind this file to its own checkout, independent of cwd.
    # Imports occur after argument parsing so --help needs only the stdlib.
    sys.dont_write_bytecode = True
    from reviewer_support import find_root
    from arcpuzzles import Catalog

    root = find_root(__file__)
    catalog = Catalog(root)
    description = catalog.describe(args.task_id)
    task_id = description["id"]
    if description["kind"] != "per_puzzle" or not description["has_generator"]:
        parser.error("diagnostic requires an existing per-puzzle generator")
    source = root / description["generator"]
    spec = importlib.util.spec_from_file_location("minimal_impostor_diagnostic_target", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    self_check = getattr(module, "self_check", None)
    if not callable(self_check):
        parser.error("selected generator has no callable self_check")
    linter = root / "shared/tools/generator_defect_lint.py"
    report = {
        "schema": "arcpuzzles-minimal-impostors-diagnostic-v1",
        "status": "diagnostic_complete",
        "interpretation": "Validator acceptance and reference execution are observations; they do not certify legality, waive lint, change approval, or create training labels.",
        "task_id": task_id,
        "generator_sha256": sha256_bytes(source.read_bytes()),
        "catalog_generator_sha256": description["generator_sha256"],
        "catalog_rule_hash": description["rule_hash"],
        "generator_declared_rule_hash": getattr(module, "RULE_HASH", None),
        "diagnostic_source_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "linter_source_sha256": sha256_bytes(linter.read_bytes()) if linter.is_file() else None,
        "recipe": {
            "source": "shared/tools/generator_defect_lint.py::_minimal_impostors",
            "modal_ties": "Counter.most_common: row-major first-seen order",
            "foreground": "smallest numerical color different from modal",
            "names": ["all_background", "full_one_color", "singleton", "solid_2x2", "short_line"],
            "population": "Diagnostic draws use supplied seed, indices 0..samples-1, cycling easy/medium/hard; this is not the linter's full sampling population.",
            "canonical_exemptions": "Not evaluated; no aggregate lint verdict is recreated.",
        },
        "command": {"argv": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
                    "cwd": str(Path.cwd()), "source_root": str(root), "exit_code": None},
        "requested_samples": args.samples,
        "seed": args.seed,
        "baselines": [], "mutations": [], "reference_execution": None, "errors": [],
    }
    for index in range(args.samples):
        band = ("easy", "medium", "hard")[index % 3]
        baseline = {"seed": args.seed, "sample_index": index, "difficulty": band, "overrides": {}}
        try:
            grid = module.generate(args.seed, index, difficulty=band)
            baseline.update({"input": grid, "input_sha256": grid_hash(grid), "passes_linter_grid_gate": bool(is_grid(grid))})
            if is_grid(grid):
                baseline.update(validator_observation(self_check, grid, band))
            else:
                baseline.update({"accepted": False, "validator_result": None,
                                 "validator_exception": None})
            if baseline["accepted"]:
                modal = Counter(value for row in grid for value in row).most_common(1)[0][0]
                foregrounds = sorted({value for row in grid for value in row} - {modal})
                baseline.update({"modal_background": modal, "foreground": foregrounds[0] if foregrounds else None})
                for name, mutation in minimal_impostors(grid):
                    report["mutations"].append({"baseline_index": index, "name": name,
                                                "modal_background": modal, "foreground": foregrounds[0],
                                                "input": mutation, "input_sha256": grid_hash(mutation),
                                                **validator_observation(self_check, mutation, band),
                                                "racket": None})
        except Exception as exc:
            baseline.update({"accepted": False, "generation_exception": {"type": type(exc).__name__, "message": str(exc)}})
            report["errors"].append(f"baseline {index}: {type(exc).__name__}: {exc}")
        report["baselines"].append(baseline)

    accepted = [mutation for mutation in report["mutations"] if mutation["accepted"]]
    if accepted:
        try:
            applied = catalog.apply(task_id, [item["input"] for item in accepted], reference="canonical", timeout=120)
            report["reference_execution"] = {key: value for key, value in applied.items() if key != "results"}
            if applied["generator_sha256"] != report["generator_sha256"]:
                raise RuntimeError("generator changed between mutation generation and reference execution")
            for mutation, result in zip(accepted, applied["results"], strict=True):
                if result["input"] != mutation["input"]:
                    raise RuntimeError("reference result input does not match retained mutation")
                mutation["racket"] = result
                if result.get("error") is not None or not result.get("valid_output"):
                    report["errors"].append(f"{mutation['name']} baseline {mutation['baseline_index']}: reference returned an error or invalid output")
        except Exception as exc:
            report["errors"].append(f"reference execution: {type(exc).__name__}: {exc}")
    if sha256_bytes(source.read_bytes()) != report["generator_sha256"]:
        report["errors"].append("generator source changed during diagnostic")
    totals = Counter(item["name"] for item in report["mutations"])
    accepted_totals = Counter(item["name"] for item in accepted)
    report["summary"] = {"accepted_baselines": sum(item.get("accepted", False) for item in report["baselines"]),
                         "mutations": len(report["mutations"]), "accepted_mutations": len(accepted),
                         "by_name": {name: {"accepted": accepted_totals[name], "probed": total}
                                     for name, total in sorted(totals.items())},
                         "accepted_with_reference_result": sum(item["racket"] is not None for item in accepted)}
    if report["errors"] or any(not item.get("accepted") for item in report["baselines"]):
        report["status"] = "diagnostic_incomplete"
    exit_code = 0 if report["status"] == "diagnostic_complete" else 2
    report["command"]["exit_code"] = exit_code
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(args.out), "summary": report["summary"]}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
