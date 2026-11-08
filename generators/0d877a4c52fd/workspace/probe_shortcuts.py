#!/usr/bin/env python3
"""Reproduce the canonical ``spaced_only`` shortcut and its adjacent-span refutation.

The probe uses only public reviewer helpers plus the selected generator's declared
rivals. Run it through ``run_with_racket.py`` when requesting the authority
receipt so the exact hand-made witness is checked by the canonical Racket rule.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arcpuzzles.catalog import Catalog
from reviewer_support import canonical_pairs, find_root

TASK_ID = "0d877a4c52fd"


def _load_generator():
    """Load the selected module in both copied runtimes and source checkouts."""
    try:
        return importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
    except ModuleNotFoundError as exc:
        if not (exc.name or "").startswith("puzzle_generators.per_puzzle"):
            raise
        path = Path(__file__).resolve().parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location(f"source_generator_{TASK_ID}", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load selected generator from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


GEN = _load_generator()


def grid_sha256(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def adjacent_witness() -> list[list[int]]:
    """Return a lawful 6x6 input that distinguishes the canonical shortcut."""
    grid = [[0 for _ in range(6)] for _ in range(6)]
    for r, c in ((1, 1), (1, 2), (2, 1)):
        grid[r][c] = 2
    for r, c in ((0, 4), (4, 0), (4, 4)):
        grid[r][c] = 7
    return grid


def build_local_report(*, root: str | Path | None = None) -> dict[str, Any]:
    """Check canonical fit, the exact witness, and every sampled 3-demo window."""
    resolved_root = Path(root).resolve() if root is not None else find_root(__file__)
    pairs = canonical_pairs(TASK_ID, root=resolved_root)
    spaced = GEN.CANONICAL_SHORTCUTS["spaced_only"]
    canonical_records = []
    for pair in pairs:
        prediction = spaced(pair["input"])
        canonical_records.append({
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "input_sha256": grid_sha256(pair["input"]),
            "expected_output_sha256": grid_sha256(pair["output"]),
            "spaced_only_matches": prediction == pair["output"],
        })

    witness = adjacent_witness()
    intended = GEN.rule_mirror(witness)
    rival = spaced(witness)
    if GEN.self_check(witness):
        raise AssertionError(GEN.self_check(witness))
    if intended == rival:
        raise AssertionError("adjacent witness no longer distinguishes spaced_only")

    window_records = []
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            lesson = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                inp = GEN.generate(3400 + start, sample_index, difficulty=band)
                lesson.append({"input": inp, "output": GEN.rule_mirror(inp)})
            reasons = GEN.lesson_identifiable(lesson[:-1], lesson[-1])
            window_records.append({
                "difficulty": band,
                "start": start,
                "identifiable": not reasons,
                "reasons": reasons,
            })

    emitted = {band: {"adjacent": 0, "spaced": 0, "mixed": 0} for band in ("easy", "medium", "hard")}
    for band in emitted:
        for sample_index in range(60):
            facts = GEN.semantic_observables(GEN.generate(7000, sample_index, difficulty=band))
            emitted[band][facts["span_pattern"]] += 1

    source = Path(GEN.__file__).resolve()
    return {
        "schema": "0d877a4c52fd-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "declared_rule_hash": GEN.RULE_HASH,
        "canonical": {
            "pair_count": len(canonical_records),
            "spaced_only_matches": sum(record["spaced_only_matches"] for record in canonical_records),
            "records": canonical_records,
        },
        "witness": {
            "input": witness,
            "intended_output": intended,
            "spaced_only_output": rival,
            "outputs_differ": intended != rival,
            "input_sha256": grid_sha256(witness),
            "intended_output_sha256": grid_sha256(intended),
            "spaced_only_output_sha256": grid_sha256(rival),
            "distinguishing_cell": {
                "row": 2,
                "column": 2,
                "intended": intended[2][2],
                "spaced_only": rival[2][2],
            },
        },
        "schedule": {
            "examples_needed": GEN.EXAMPLES_NEEDED,
            "windows_checked": len(window_records),
            "all_three_demo_windows_identifiable": all(row["identifiable"] for row in window_records),
            "failures": [row for row in window_records if not row["identifiable"]],
            "sampled_span_patterns": emitted,
        },
        "limits": [
            "The local window probe checks declared rivals over 24 consecutive starts per band, not every possible hypothesis.",
            "The authoritative Racket receipt is separate and requires the packet wrapper.",
        ],
    }


def add_authority_receipt(report: dict[str, Any], *, root: str | Path | None = None) -> None:
    resolved_root = Path(root).resolve() if root is not None else find_root(__file__)
    witness = report["witness"]["input"]
    receipt = Catalog(resolved_root).apply(TASK_ID, [witness], timeout=120)
    result = receipt["results"][0]
    report["authority"] = {
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "executed_rule_hash": receipt["executed_rule_hash"],
        "input_sha256": result["input_sha256"],
        "output_sha256": result["output_sha256"],
        "error": result["error"],
        "output_matches_python_mirror": result["output"] == report["witness"]["intended_output"],
        "output": result["output"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write the complete JSON report")
    parser.add_argument("--no-authority", action="store_true", help="skip the canonical Racket receipt")
    args = parser.parse_args()
    root = find_root(__file__)
    report = build_local_report(root=root)
    if not args.no_authority:
        add_authority_receipt(report, root=root)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "generator_sha256": report["generator_sha256"],
        "canonical_spaced_only_matches": f"{report['canonical']['spaced_only_matches']}/{report['canonical']['pair_count']}",
        "witness_outputs_differ": report["witness"]["outputs_differ"],
        "distinguishing_cell": report["witness"]["distinguishing_cell"],
        "windows_checked": report["schedule"]["windows_checked"],
        "all_windows_identifiable": report["schedule"]["all_three_demo_windows_identifiable"],
        "authority_matches": report.get("authority", {}).get("output_matches_python_mirror"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
