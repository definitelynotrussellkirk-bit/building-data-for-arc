#!/usr/bin/env python3
"""Source-bound sort-key probe for a784ff872856.

The historical filename is retained for existing reviewer commands. The probe
loads every declared canonical shortcut from the live generator, discovers the
task's retained machine-readable counterexamples, and requires each rival to
have both an exact separating case and a firing witness mapped to that rival.
It can additionally execute all retained cases through the pinned Catalog/Racket
rule so the Python mirror never becomes the label authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "a784ff872856"
TASK_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"
COUNTEREXAMPLE_DIR = TASK_DIR / "counterexamples"
ROOT = find_root(__file__)
COUNTEREXAMPLE_SCHEMA = "arcpuzzles-generator-counterexample-v1"
REPORT_SCHEMA = "a784ff872856-sort-lesson-probe-v2"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"authoring_probe_{TASK_ID}_generator", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_counterexamples() -> list[tuple[Path, dict[str, Any]]]:
    rows: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(COUNTEREXAMPLE_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            data.get("schema") == COUNTEREXAMPLE_SCHEMA
            and data.get("task_id") == TASK_ID
            and isinstance(data.get("input"), list)
        ):
            rows.append((path, data))
    return rows


def build_report(*, run_racket: bool = False) -> dict[str, Any]:
    gen = _load_generator()
    generator_sha256 = _sha256(GENERATOR_PATH)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    rivals = dict(gen.CANONICAL_SHORTCUTS)
    semantic_rivals = dict(gen.SEMANTIC_RIVALS)
    witnesses = dict(gen.SEMANTIC_WITNESSES)
    witness_rivals = {
        str(name): ([value] if isinstance(value, str) else list(value))
        for name, value in dict(gen.WITNESS_RIVALS).items()
    }

    shortcut_rows = []
    for name, rival in sorted(rivals.items()):
        canonical_matches = [rival(pair["input"]) == pair["output"] for pair in pairs]
        shortcut_rows.append(
            {
                "name": name,
                "canonical_pairs_checked": len(canonical_matches),
                "fits_all_canonical_pairs": all(canonical_matches),
            }
        )

    coverage: dict[str, dict[str, list[str]]] = {
        name: {"separator_paths": [], "witness_paths": []}
        for name in sorted(rivals)
    }
    case_rows: list[dict[str, Any]] = []
    case_grids: list[list[list[int]]] = []
    case_paths: list[str] = []

    for path, recorded in _load_counterexamples():
        relative = str(path.relative_to(ROOT))
        grid = recorded["input"]
        intended = gen.rule_mirror(grid)
        computed_rivals = {name: fn(grid) for name, fn in sorted(rivals.items())}
        separated = sorted(
            name for name, output in computed_rivals.items() if output != intended
        )
        firing = sorted(name for name, pred in witnesses.items() if bool(pred(grid)))
        witness_supported = sorted(
            rival
            for rival in separated
            if any(rival in witness_rivals.get(witness, []) for witness in firing)
        )
        recorded_rivals = recorded.get("rival_outputs", {})
        recorded_rival_outputs_match = isinstance(recorded_rivals, dict) and all(
            name in computed_rivals and computed_rivals[name] == output
            for name, output in recorded_rivals.items()
        )
        row = {
            "path": relative,
            "witness": recorded.get("witness"),
            "self_check_errors": gen.self_check(grid),
            "recorded_intended_matches_mirror": recorded.get("intended_output") == intended,
            "recorded_rival_outputs_match": recorded_rival_outputs_match,
            "recorded_generator_sha256_matches": recorded.get("generator_sha256")
            == generator_sha256,
            "recorded_generator_version_matches": recorded.get("generator_version")
            == gen.VERSION,
            "recorded_rule_hash_matches": recorded.get("rule_hash") == gen.RULE_HASH,
            "firing_witnesses": firing,
            "separated_rivals": separated,
            "witness_supported_rivals": witness_supported,
            "all_separated_rivals_have_witness_support": set(separated)
            <= set(witness_supported),
        }
        case_rows.append(row)
        case_grids.append(grid)
        case_paths.append(relative)
        for rival in separated:
            if rival in coverage:
                coverage[rival]["separator_paths"].append(relative)
                if rival in witness_supported:
                    coverage[rival]["witness_paths"].append(relative)

    missing_rivals = sorted(
        name for name, row in coverage.items() if not row["separator_paths"]
    )
    unsupported_rivals = sorted(
        name for name, row in coverage.items() if not row["witness_paths"]
    )
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "task_id": TASK_ID,
        "generator_sha256": generator_sha256,
        "declared_rule_hash": gen.RULE_HASH,
        "declaration_sets_match": set(rivals) == set(semantic_rivals),
        "canonical_shortcuts": shortcut_rows,
        "counterexamples": case_rows,
        "rival_coverage": coverage,
        "missing_rivals": missing_rivals,
        "unsupported_rivals": unsupported_rivals,
        # Compatibility summary for existing consumers of the v1 probe.
        "counterexample": {
            "cases_checked": len(case_rows),
            "intended_differs_from_every_declared_rival": bool(rivals)
            and not missing_rivals,
        },
    }

    if run_racket:
        from arcpuzzles import Catalog

        applied = Catalog().apply(TASK_ID, case_grids, timeout=180)
        racket_rows = []
        for path, expected, result in zip(
            case_paths,
            [gen.rule_mirror(grid) for grid in case_grids],
            applied["results"],
        ):
            racket_rows.append(
                {
                    "path": path,
                    "valid_output": result["valid_output"],
                    "error": result["error"],
                    "matches_python_mirror": result["output"] == expected,
                }
            )
        report["racket"] = {
            "rule_hash_matches_catalog": applied["rule_hash_matches_catalog"],
            "cases": racket_rows,
        }
    return report


def report_ok(report: dict[str, Any], *, require_racket: bool = False) -> bool:
    cases = report["counterexamples"]
    ok = (
        bool(report["canonical_shortcuts"])
        and report["declaration_sets_match"]
        and all(row["fits_all_canonical_pairs"] for row in report["canonical_shortcuts"])
        and not report["missing_rivals"]
        and not report["unsupported_rivals"]
        and bool(cases)
        and all(
            not row["self_check_errors"]
            and row["recorded_intended_matches_mirror"]
            and row["recorded_rival_outputs_match"]
            and row["recorded_generator_sha256_matches"]
            and row["recorded_generator_version_matches"]
            and row["recorded_rule_hash_matches"]
            and row["all_separated_rivals_have_witness_support"]
            for row in cases
        )
    )
    if require_racket:
        racket = report.get("racket", {})
        ok = (
            ok
            and bool(racket.get("rule_hash_matches_catalog"))
            and bool(racket.get("cases"))
            and all(
                row["valid_output"]
                and row["error"] is None
                and row["matches_python_mirror"]
                for row in racket["cases"]
            )
        )
    return bool(ok)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--racket",
        action="store_true",
        help="also verify every retained case with Catalog/Racket",
    )
    parser.add_argument("--out", type=Path, help="write JSON to this path")
    args = parser.parse_args()
    report = build_report(run_racket=args.racket)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report_ok(report, require_racket=args.racket) else 1


if __name__ == "__main__":
    raise SystemExit(main())
