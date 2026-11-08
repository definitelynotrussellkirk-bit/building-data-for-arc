#!/usr/bin/env python3
"""Protected-Racket parity and wrong-intermediate audit for task 6145142974ff.

This is a bounded executable audit.  It proves parity for the requested
seed/count grid and refutes one explicit sequential counterfactual; it is not a
proof of unique induction over all possible rules or inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import normalize_grid

HERE = Path(__file__).resolve().parent
TASK_ID = "6145142974ff"


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_6145142974ff_racket_audit_prototype"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return normalize_grid(bridge.eval_text(f"({wrap_rule(program)} {_literal(grid)})"))


def _changed_cells(first: list[list[int]], second: list[list[int]]) -> int:
    return sum(a != b for row_a, row_b in zip(first, second) for a, b in zip(row_a, row_b))


def audit(
    seeds: Iterable[int] = (0, 17),
    demo_counts: Iterable[int] = (2, 3, 6),
    queries: int = 4,
) -> dict[str, Any]:
    prototype = _load_prototype()
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    programs = {finish: prototype.program({"finish": finish}) for finish in prototype.FINISHES}
    counterfactual_program = (HERE / "all_green_bridge.rkt").read_text(encoding="utf-8")
    failures: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    selected_label_evaluations = 0

    with RacketBridge(max_calls_before_restart=48) as bridge:
        identity = dict(bridge.runtime_identity)
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError(f"audit requires protected Racket, got {identity}")

        for seed in seeds:
            for demos in demo_counts:
                for finish, program in programs.items():
                    episode = prototype.generate(
                        seed, {"finish": finish}, demos=demos, queries=queries
                    )
                    case_failures = []
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            actual = _execute(bridge, program, pair["input"])
                            selected_label_evaluations += 1
                            if actual != pair["output"]:
                                item = {
                                    "seed": seed,
                                    "demos": demos,
                                    "queries": queries,
                                    "finish": finish,
                                    "split": split,
                                    "index": index,
                                    "expected": pair["output"],
                                    "actual": actual,
                                }
                                failures.append(item)
                                case_failures.append({"split": split, "index": index})
                    cases.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "queries": queries,
                            "finish": finish,
                            "evaluations": demos + queries,
                            "failures": case_failures,
                        }
                    )

        witness_seed = seeds[0]
        witness_demos = demo_counts[0]
        witness_episode = prototype.generate(
            witness_seed,
            {"finish": "bridge_matches"},
            demos=witness_demos,
            queries=queries,
        )
        demonstration_mismatches: list[int] = []
        query_mismatches: list[int] = []
        witness_rows: list[dict[str, Any]] = []
        counterfactual_evaluations = 0
        for split, mismatch_indices in (
            ("train", demonstration_mismatches),
            ("test", query_mismatches),
        ):
            for index, pair in enumerate(witness_episode[split]):
                wrong = _execute(bridge, counterfactual_program, pair["input"])
                counterfactual_evaluations += 1
                if wrong != pair["output"]:
                    mismatch_indices.append(index)
                    witness_rows.append(
                        {
                            "split": split,
                            "index": index,
                            "changed_cells": _changed_cells(pair["output"], wrong),
                        }
                    )

        if not demonstration_mismatches:
            failures.append({"kind": "counterfactual_not_refuted_by_demonstrations"})
        if not query_mismatches:
            failures.append({"kind": "counterfactual_does_not_change_query"})

        causal_index = query_mismatches[0] if query_mismatches else 0
        causal_pair = witness_episode["test"][causal_index]
        causal_wrong = _execute(bridge, counterfactual_program, causal_pair["input"])
        # This extra execution duplicates one query intentionally so the saved
        # witness contains a direct fresh causal replay independent of the scan.
        counterfactual_evaluations += 1
        # Keep the public count contract simple: the scan count is the declared
        # counterfactual audit count; the direct replay is reported separately.
        scan_counterfactual_evaluations = witness_demos + queries

    counterfactual = {
        "seed": witness_seed,
        "demos": witness_demos,
        "queries": queries,
        "demonstration_mismatch_indices": demonstration_mismatches,
        "query_mismatch_indices": query_mismatches,
        "rows": witness_rows,
        "causal_query_index": causal_index,
        "changed_cells": _changed_cells(causal_pair["output"], causal_wrong),
        "selected_program_sha256": _sha256(programs["bridge_matches"]),
        "counterfactual_program_sha256": _sha256(counterfactual_program),
        "ablation": "wrong_intermediate",
        "claim": (
            "Replacing the exact-match Stage-A intermediate with all color-3 "
            "components changes the Stage-B bridge chain and final output."
        ),
    }
    return {
        "schema": "arcpuzzles-parametric-racket-audit-v1",
        "task_id": TASK_ID,
        "status": "pass" if not failures else "fail",
        "racket": identity,
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "queries": queries,
        "programs": {
            finish: {"path": f"{finish if finish != 'canonical' else 'canonical'}.rkt", "sha256": _sha256(program)}
            for finish, program in programs.items()
        },
        "counterfactual_program": {
            "path": "all_green_bridge.rkt",
            "sha256": _sha256(counterfactual_program),
        },
        "selected_label_evaluations": selected_label_evaluations,
        "counterfactual_evaluations": scan_counterfactual_evaluations,
        "direct_causal_replays": 1,
        "cases": cases,
        "counterfactual": counterfactual,
        "failures": failures,
        "limits": (
            "Bounded to the listed seeds, counts, and explicit wrong-intermediate "
            "counterfactual; no universal uniqueness claim."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17])
    parser.add_argument("--demos", nargs="+", type=int, default=[2, 3, 6])
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.seeds, args.demos, args.queries)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "selected_label_evaluations": report["selected_label_evaluations"],
                "counterfactual_evaluations": report["counterfactual_evaluations"],
                "direct_causal_replays": report["direct_causal_replays"],
                "failures": len(report["failures"]),
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
