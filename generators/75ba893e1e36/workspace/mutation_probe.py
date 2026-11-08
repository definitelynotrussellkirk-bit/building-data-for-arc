#!/usr/bin/env python3
"""Source-bound diagnostic for accepted generic minimal mutations.

README / usage
==============
Run from the packet's outer directory, after the blind solve is finished::

    python3 WORK/run_with_racket.py python3 \
      generators/75ba893e1e36/workspace/mutation_probe.py \
      --out ../checks/mutation-lawfulness/new-run

Focused tests use the same wrapper and require only the standard library plus
this repository's reference-runtime dependencies (Python 3.12+, Racket, NumPy,
Pillow); no pytest installation is needed::

    python3 WORK/run_with_racket.py python3 \
      generators/75ba893e1e36/tests/test_mutation_probe.py

The wrapper supplies this checkout's src/ and shared/runtime/ import paths.
find_root(__file__) and load_selected_generator bind reads to this source tree,
independent of cwd. An installed library may instead use --root explicitly.
Catalog.apply needs a complete catalog-bearing checkout, not a bare copied
runtime. Its temporary execution tree follows TMPDIR; put that outside retained
checks. The output directory must be new and contains report.json and exact
selected generator, probe, test, and canonical-program source snapshots.

By default the one hand-made input is [[7,7,5],[7,7,5],[5,5,5]]. The report keeps
both that original and the identical solid_2x2 mutation, with unique-input
counts so this duplication is visible. --input accepts the public apply JSON
formats (a grid, {"input": grid}, {"inputs": [...]}, or a list of grids).
--task-id permits reuse with explicit inputs; select --rival none unless the
horizontal-copy-4 rival is meaningful for that task. Expansion is bounded to
64 original/mutated grids in one Catalog.apply call; no generators are sampled.

The generic enumerator reconstructs the five minimal shapes in the current
shared/tools/generator_defect_lint.py, including row-major modal ties. It is
separate from the pure four-copy rival, and never imports the linter's private
API. The source hash of that linter is retained for comparison if it changes.
"Background" in mutation names means the modal color, not a semantic claim.

Catalog.apply(reference="canonical", check_generator_domain=True) executes the
actual selected Racket rule and reports self_check separately. Every raw output,
error, domain finding, and reference/source identity is retained. A legal
reference output does not establish intended-domain membership. Accepted tiny
shapes are diagnostic observations: they do not themselves prove safety or
lesson identifiability. Rival disagreement distinguishes only the named rival
on the recorded input; it is not a universal identifiability proof. This tool
changes no canonical authority, generator, audit disposition, or approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from arcpuzzles import Catalog
from arcpuzzles.runtime import parse_apply_inputs
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TASK_ID = "75ba893e1e36"
DEFAULT_INPUT = [[7, 7, 5], [7, 7, 5], [5, 5, 5]]


def minimal_mutations(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    """Generic named shapes on the input's modal color; returns fresh grids."""
    grid = normalize_grid(grid)
    height, width = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    modal = counts.most_common(1)[0][0]
    other_colors = sorted(color for color in counts if color != modal)
    if not other_colors:
        return {}
    foreground = other_colors[0]
    mutations = {
        "all_background": [[modal] * width for _ in range(height)],
        "full_one_color": [[foreground] * width for _ in range(height)],
    }
    for name, cells in (
        ("singleton", [(height // 2, width // 2)]),
        ("solid_2x2", [(r, c) for r in range(min(2, height)) for c in range(min(2, width))]),
        ("short_line", [(height // 2, c) for c in range(min(4, width))]),
    ):
        mutated = [[modal] * width for _ in range(height)]
        for row, column in cells:
            mutated[row][column] = foreground
        mutations[name] = mutated
    return mutations


def horizontal_copy_rival(grid: list[list[int]]) -> list[list[int]]:
    """Task-specific pure rival: four unchanged copies across each row."""
    return [list(row) * 4 for row in grid]


def grid_metrics(grid: list[list[int]]) -> dict[str, Any]:
    counts = Counter(value for row in grid for value in row)
    return {
        "dimensions": [len(grid), len(grid[0])],
        "cell_count": sum(counts.values()),
        "color_counts": {str(color): counts[color] for color in sorted(counts)},
        "sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_probe(*, task_id: str, base_inputs: list, root: Path, out: Path,
              rival_name: str = "none", timeout: float = 120) -> dict[str, Any]:
    """Write bounded, source-bound observations; retain failed execution receipts."""
    root, out = Path(root).resolve(), Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {
        "schema": "minimal-mutation-reference-probe-v1", "status": "running",
        "task_id": task_id, "created_utc": datetime.now(timezone.utc).isoformat(),
        "invocation": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv],
                       "explicit_source_root": str(root),
                       "environment": {name: os.environ.get(name) for name in ("RACKET_PATH", "TMPDIR")}},
        "settings": {"reference": "canonical", "check_generator_domain": True,
                     "domain_context": "self_check defaults; no overrides or difficulty passed",
                     "rival_name": rival_name, "timeout_seconds": timeout,
                     "base_input_count": len(base_inputs)},
        "claims": {"generic_mutation_acceptance_proves_safety": False,
                   "generic_mutation_acceptance_proves_identifiability": False,
                   "legal_reference_output_proves_domain_membership": False},
        "limitations": [
            "Only the supplied inputs and five named minimal mutation kinds are examined.",
            "The original and a named mutation can be identical; unique counts are reported.",
            "Domain acceptance is the selected generator's self_check report, not a safety verdict.",
            "One rival's disagreement on a grid does not establish lesson identifiability.",
            "Canonical execution and approval/admission are separate; no status is promoted.",
        ],
        "sources": {}, "cases": [], "failures": [],
    }
    _write_json(out / "report.json", report)
    try:
        if rival_name not in {"none", "horizontal-copy-4"}:
            raise ValueError("Supported rivals: none, horizontal-copy-4")
        normalized = [normalize_grid(grid) for grid in base_inputs]
        for base_index, grid in enumerate(normalized):
            for kind, mutated in (("original", grid), *minimal_mutations(grid).items()):
                report["cases"].append({
                    "base_input_index": base_index, "mutation_kind": kind,
                    "input": mutated, "input_metrics": grid_metrics(mutated),
                })
        if not 1 <= len(report["cases"]) <= 64:
            raise ValueError("Expanded probe must contain 1..64 original/mutated grids")

        _, generator_path, selected_hash = load_selected_generator(task_id, root=root)
        source_paths = {
            "generator": generator_path,
            "probe": Path(__file__).resolve(),
            "tests": Path(__file__).resolve().parents[1] / "tests/test_mutation_probe.py",
            "mutation_heuristic": root / "shared/tools/generator_defect_lint.py",
            "reviewer_support": root / "shared/runtime/reviewer_support.py",
            "catalog_api": root / "src/arcpuzzles/catalog.py",
            "apply_runtime": root / "src/arcpuzzles/runtime.py",
            "apply_worker": root / "src/arcpuzzles/worker.py",
        }
        source_dir = out / "source"
        source_dir.mkdir()
        for name, path in source_paths.items():
            body = path.read_bytes()
            identity = {"path": path.relative_to(root).as_posix(),
                        "sha256": hashlib.sha256(body).hexdigest()}
            if name in {"generator", "probe", "tests"}:
                snapshot = source_dir / path.name
                snapshot.write_bytes(body)
                identity["snapshot"] = snapshot.relative_to(out).as_posix()
            report["sources"][name] = identity
        if report["sources"]["generator"]["sha256"] != selected_hash:
            raise RuntimeError("Selected generator changed before its source snapshot")

        catalog = Catalog(root)
        task = catalog.get(task_id)
        if task["id"] != task_id:
            raise ValueError("Use an exact generator ID, not an alias")
        programs = list(dict.fromkeys(variant["program_solution"] for variant in task["variants"]))
        report["canonical_authority"] = {
            "ledger_path": canonical_path(root).relative_to(root).as_posix(),
            "ledger_sha256": hashlib.sha256(canonical_path(root).read_bytes()).hexdigest(),
            "programs": [],
        }
        for index, program in enumerate(programs):
            snapshot = source_dir / f"canonical-program-{index}.rkt"
            snapshot.write_text(program, encoding="utf-8")
            report["canonical_authority"]["programs"].append({
                "text": program, "exact_text_sha256": hashlib.sha256(program.encode()).hexdigest(),
                "normalized_rule_hash": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12],
                "snapshot": snapshot.relative_to(out).as_posix(),
            })
        _write_json(out / "report.json", report)
        receipt = catalog.apply(task_id, [row["input"] for row in report["cases"]],
                                reference="canonical", check_generator_domain=True, timeout=timeout)
        report["apply_receipt"] = receipt
        if receipt["generator_sha256"] != selected_hash:
            report["failures"].append({"type": "source_identity", "error": "Apply used a different generator source"})
        if not receipt["rule_hash_matches_catalog"]:
            report["failures"].append({"type": "rule_identity", "error": "Executed rule differs from catalog"})
        if {p["normalized_rule_hash"] for p in report["canonical_authority"]["programs"]} != {receipt["executed_rule_hash"]}:
            report["failures"].append({"type": "rule_identity", "error": "Executed rule differs from saved canonical program"})
        for case, result in zip(report["cases"], receipt["results"], strict=True):
            case["generator_domain"] = result.get("generator_domain", {"status": "not_reported", "errors": []})
            output = result["output"]
            case["reference"] = {"output": output, "valid_output": result["valid_output"],
                                 "error": result["error"],
                                 "metrics": grid_metrics(output) if output is not None else None}
            if not result["valid_output"] or result["error"]:
                report["failures"].append({"type": "reference_execution", "case_index": result["index"], "error": result["error"]})
            if rival_name != "none":
                rival = horizontal_copy_rival(case["input"])
                same_shape = output is not None and [len(r) for r in output] == [len(r) for r in rival]
                case["rival"] = {
                    "name": rival_name, "output": rival, "metrics": grid_metrics(rival),
                    "equal_to_reference": rival == output if output is not None else None,
                    "differing_cells": sum(a != b for row_a, row_b in zip(output, rival)
                                           for a, b in zip(row_a, row_b)) if same_shape else None,
                }
        for name, path in source_paths.items():
            if hashlib.sha256(path.read_bytes()).hexdigest() != report["sources"][name]["sha256"]:
                report["failures"].append({"type": "source_changed_during_probe", "source": name})
        accepted = [case for case in report["cases"] if case["generator_domain"]["status"] == "valid"]
        report["summary"] = {
            "cases": len(report["cases"]),
            "unique_inputs": len({case["input_metrics"]["sha256"] for case in report["cases"]}),
            "domain_accepted": len(accepted),
            "unique_domain_accepted_inputs": len({case["input_metrics"]["sha256"] for case in accepted}),
            "legal_reference_outputs": sum(case["reference"]["valid_output"] for case in report["cases"]),
            "accepted_and_distinguishes_rival": sum(case.get("rival", {}).get("equal_to_reference") is False for case in accepted),
            "domain_status_counts": dict(Counter(case["generator_domain"]["status"] for case in report["cases"])),
        }
        report["status"] = "failed" if report["failures"] else "completed"
    except Exception as exc:
        failure = {"type": type(exc).__name__, "error": str(exc)}
        if hasattr(exc, "run"):
            failure["process_receipt"] = exc.run
        report["failures"].append(failure)
        report["status"] = "failed"
    _write_json(out / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe generic minimal mutations through the canonical Racket authority.")
    parser.add_argument("--task-id", default=TASK_ID)
    parser.add_argument("--input", type=Path, help="Public apply JSON input formats")
    parser.add_argument("--root", type=Path, help="Explicit catalog checkout; default is this file's tree")
    parser.add_argument("--out", type=Path, required=True, help="New evidence directory")
    parser.add_argument("--rival", choices=("none", "horizontal-copy-4"))
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    if args.task_id != TASK_ID and args.input is None:
        parser.error("--input is required for a task other than the default witness")
    inputs = parse_apply_inputs(json.loads(args.input.read_text())) if args.input else [DEFAULT_INPUT]
    rival = args.rival or ("horizontal-copy-4" if args.task_id == TASK_ID else "none")
    report = run_probe(task_id=args.task_id, base_inputs=inputs, root=args.root or find_root(__file__),
                       out=args.out, rival_name=rival, timeout=args.timeout)
    print(json.dumps({"status": report["status"], "summary": report.get("summary"),
                      "failures": report["failures"], "report": str((args.out / "report.json").resolve())}, sort_keys=True))
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
