#!/usr/bin/env python3
"""Protected finite-rival audit and public-example writer for f891d1ff5dd8.

This tool is intentionally task-local.  It reuses the exact native prototype,
executes every declared rival through Racket, and reports only the finite cases
it actually checked.  Public files contain one query input at a time and use the
SHA-256 of their exact visible bytes as the filename.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from contextlib import nullcontext
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_audit_f891d1ff5dd8_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent marker-phase prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = prototype
_SPEC.loader.exec_module(prototype)

SETTINGS = tuple({"cycle_start": value} for value in prototype.CYCLE_STARTS)


def _literal_ints(values: Any, *, low: int, high: int, name: str) -> list[int]:
    if type(values) is not list or not values:
        raise ValueError(f"{name} must be a nonempty list")
    rows = []
    for value in values:
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"every {name} value must be a literal integer in {low}..{high}")
        rows.append(value)
    if len(set(rows)) != len(rows):
        raise ValueError(f"{name} values must be distinct")
    return rows


def _diff_indices(outputs: list[Any], expected: list[Any]) -> list[int]:
    return [index for index, (actual, wanted) in enumerate(zip(outputs, expected, strict=True)) if actual != wanted]


def run_audit(
    *,
    seeds: list[int],
    demo_counts: list[int],
    queries: int = 4,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    seeds = _literal_ints(seeds, low=0, high=2**63 - 1, name="seeds")
    demo_counts = _literal_ints(
        demo_counts,
        low=prototype.MIN_DEMOS,
        high=prototype.MAX_DEMOS,
        name="demo_counts",
    )
    if type(queries) is not int or not prototype.MIN_QUERIES <= queries <= prototype.MAX_QUERIES:
        raise ValueError("queries must be a literal supported integer")

    rivals = prototype.rival_programs()
    cases: list[dict[str, Any]] = []
    harmful: list[dict[str, Any]] = []
    evaluations = 0
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        identity = {
            "backend": active.runtime_identity.get("backend"),
            "protected": active.runtime_identity.get("protected"),
        }
        for seed in seeds:
            for demos in demo_counts:
                for settings in SETTINGS:
                    episode = prototype.generate(seed, settings, demos, queries)
                    pairs = episode["train"] + episode["test"]
                    expected = [pair["output"] for pair in pairs]
                    selected_source = prototype.program(settings)
                    selected_outputs = [
                        prototype.execute_rule(selected_source, pair["input"], bridge=active)
                        for pair in pairs
                    ]
                    evaluations += len(pairs)
                    if selected_outputs != expected:
                        raise AssertionError("selected native program disagrees with claimed labels")

                    rival_rows = []
                    for name, source in rivals.items():
                        outputs = [
                            prototype.execute_rule(source, pair["input"], bridge=active)
                            for pair in pairs
                        ]
                        evaluations += len(pairs)
                        demo_mismatches = _diff_indices(outputs[:demos], expected[:demos])
                        query_mismatches = _diff_indices(outputs[demos:], expected[demos:])
                        if demo_mismatches:
                            status = "refuted_by_demonstrations"
                        elif query_mismatches:
                            status = "harmful_survivor"
                        else:
                            status = "matches_visible_episode"
                        row = {
                            "name": name,
                            "program_sha256": hashlib.sha256(source.encode()).hexdigest(),
                            "status": status,
                            "demonstration_mismatch_indices": demo_mismatches,
                            "query_mismatch_indices": query_mismatches,
                        }
                        rival_rows.append(row)
                        if status == "harmful_survivor":
                            harmful.append(
                                {
                                    "seed": seed,
                                    "demos": demos,
                                    "settings": copy.deepcopy(settings),
                                    **row,
                                }
                            )
                    cases.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "queries": queries,
                            "settings": copy.deepcopy(settings),
                            "selected_program_sha256": hashlib.sha256(
                                selected_source.encode()
                            ).hexdigest(),
                            "rivals": rival_rows,
                        }
                    )

    return {
        "schema": "f891d1ff5dd8-marker-phase-audit-v1",
        "task_id": prototype.TASK_ID,
        "prototype_version": prototype.VERSION,
        "seeds": seeds,
        "demo_counts": demo_counts,
        "queries": queries,
        "settings": [copy.deepcopy(value) for value in SETTINGS],
        "rival_names": sorted(rivals),
        "episodes": len(cases),
        "cases": cases,
        "harmful_survivors": harmful,
        "racket": identity,
        "racket_evaluations": evaluations,
        "limits": (
            "Finite declared rivals and requested seeds/counts only; no universal "
            "uniqueness or measured learning claim."
        ),
    }


def write_public_examples(
    output: Path,
    *,
    seeds: list[int],
    demos: int = 3,
    queries: int = 4,
) -> list[dict[str, Any]]:
    seeds = _literal_ints(seeds, low=0, high=2**63 - 1, name="seeds")
    if type(demos) is not int or not prototype.MIN_DEMOS <= demos <= prototype.MAX_DEMOS:
        raise ValueError("demos must be a literal supported integer")
    if type(queries) is not int or not prototype.MIN_QUERIES <= queries <= prototype.MAX_QUERIES:
        raise ValueError("queries must be a literal supported integer")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError("public output directory must be empty")

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for seed in seeds:
        for settings in SETTINGS:
            episode = prototype.generate(seed, settings, demos, queries)
            for query_index in range(queries):
                public_id, payload, _ = prototype.public_record(
                    episode, query_index=query_index
                )
                if public_id in seen:
                    raise ValueError("duplicate visible public payload")
                seen.add(public_id)
                name = public_id + ".json"
                path = output / name
                path.write_bytes(payload)
                rows.append(
                    {
                        "file": name,
                        "public_id": public_id,
                        "bytes": len(payload),
                        "query_index": query_index,
                    }
                )
    return sorted(rows, key=lambda row: row["public_id"])


def input_stress(*, seeds: list[int]) -> dict[str, Any]:
    """Cheap structural stress for future authors; no Racket claims."""
    seeds = _literal_ints(seeds, low=0, high=2**63 - 1, name="seeds")
    inputs = 0
    hashes: set[str] = set()
    phases: set[int] = set()
    marker_columns: set[int] = set()
    exact_30 = 0
    for seed in seeds:
        bank = prototype.input_bank(seed)
        for split in ("train", "test"):
            for grid in bank[split]:
                info = prototype.analyze(grid)
                inputs += 1
                hashes.add(hashlib.sha256(json.dumps(grid).encode()).hexdigest())
                phases.add(info["marker_header_index"])
                marker_columns.add(info["marker_column"])
                exact_30 += (len(grid) == 30 and len(grid[0]) == 30)
    if len(hashes) != inputs:
        raise AssertionError("stress run generated duplicate inputs")
    return {
        "schema": "f891d1ff5dd8-marker-phase-input-stress-v1",
        "seeds": seeds,
        "inputs": inputs,
        "unique_inputs": len(hashes),
        "marker_header_indices": sorted(phases),
        "marker_columns": sorted(marker_columns),
        "exact_30x30": exact_30,
        "limits": "Structural Python validation only; labels are not executed here.",
    }


def _write_new(path: Path, value: Any) -> None:
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 17])
    parser.add_argument("--demos", type=int, nargs="+", default=[2, 3, 6])
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--public-out", type=Path)
    parser.add_argument("--stress-seeds", type=int, default=32)
    args = parser.parse_args(argv)

    report = run_audit(
        seeds=args.seeds,
        demo_counts=args.demos,
        queries=args.queries,
    )
    report["input_stress"] = input_stress(seeds=list(range(args.stress_seeds)))
    if args.public_out is not None:
        report["public_examples"] = write_public_examples(
            args.public_out,
            seeds=args.seeds,
            demos=min(args.demos),
            queries=args.queries,
        )
    _write_new(args.out, report)
    print(
        json.dumps(
            {
                "status": "passed" if not report["harmful_survivors"] else "finding",
                "episodes": report["episodes"],
                "racket_evaluations": report["racket_evaluations"],
                "harmful_survivors": len(report["harmful_survivors"]),
                "out": str(args.out),
            },
            indent=2,
        )
    )
    return 0 if not report["harmful_survivors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
