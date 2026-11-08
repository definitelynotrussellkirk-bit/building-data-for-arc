#!/usr/bin/env python3
"""Finite teaching and causal audit for the native densest-segment family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable


HOME = Path(__file__).resolve().parent
PROTOTYPE = HOME / "prototype.py"
SCHEMA = "arcpuzzles-d185-densest-self-audit-v1"


def _load_prototype():
    digest = hashlib.sha256(str(PROTOTYPE).encode() + PROTOTYPE.read_bytes()).hexdigest()
    name = "_d185_audit_family_" + digest
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {PROTOTYPE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


FAMILY = _load_prototype()


def _sha(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _integer_list(values: list[object], low: int, high: int, name: str) -> list[int]:
    if not values or any(type(value) is not int or not low <= value <= high for value in values):
        raise ValueError(f"{name} must contain exact integers in {low}..{high}")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must be unique")
    return values


def _segments(row: list[int]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    start = 0
    for end in range(len(row) + 1):
        if end < len(row) and row[end] != 8:
            continue
        values = [value for value in row[start:end] if value != 0]
        records.append({"start": start, "end": end, "values": values, "count": len(values), "width": end - start})
        start = end + 1
    return records


def _pack_rival(grid: list[list[int]], name: str) -> list[list[int]]:
    output: list[list[int]] = []
    for row in grid:
        records = _segments(row)
        best_count = max(record["count"] for record in records)
        best_width = max(record["width"] for record in records)
        row_total = sum(record["count"] for record in records)
        result = list(row)
        for record in records:
            count = record["count"]
            if name == "all_left":
                left = True
            elif name == "first_segment_left":
                left = record["start"] == 0
            elif name == "last_segment_left":
                left = record["end"] == len(row)
            elif name == "odd_count_left":
                left = count % 2 == 1
            elif name == "at_least_two_left":
                left = count >= 2
            elif name == "row_odd_left":
                left = row_total % 2 == 1
            elif name == "widest_left":
                left = count > 0 and record["width"] == best_width
            elif name == "inverse_densest":
                left = count > 0 and count != best_count
            elif name == "reverse_order_densest":
                left = count > 0 and count == best_count
            else:
                raise ValueError(name)
            values = list(record["values"])
            if name == "reverse_order_densest":
                values.reverse()
            empty = [0] * (record["width"] - len(values))
            result[record["start"] : record["end"]] = values + empty if left else empty + values
        output.append(result)
    return output


class _RacketEvaluator:
    def __init__(self):
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        self._wrap_rule = wrap_rule
        self._bridge = RacketBridge()
        self.identity = self._bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self._bridge.close()
            raise RuntimeError("protected Racket backend is required")
        self._wrapped: dict[str, str] = {}
        self.evaluations = 0

    def apply(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        self._wrapped.setdefault(source, self._wrap_rule(source))
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        self.evaluations += 1
        return self._bridge.eval_text(f"({self._wrapped[source]} {literal})")

    def close(self) -> None:
        self._bridge.close()


def _case_for(
    seed: int,
    demos: int,
    settings: dict[str, str],
    rivals: dict[str, str],
    evaluator: _RacketEvaluator | None,
) -> dict[str, Any]:
    episode = FAMILY.generate(seed, settings, demos, 4)
    intended = FAMILY.program(settings)
    if evaluator is None:
        labels_match = all(
            FAMILY.solve(pair["input"], settings) == pair["output"]
            for split in ("train", "test")
            for pair in episode[split]
        )
        declared_survivors = [
            candidate
            for candidate in FAMILY.SETTINGS
            if all(FAMILY.solve(pair["input"], candidate) == pair["output"] for pair in episode["train"])
        ]
        rival_survivors = [
            name
            for name in rivals
            if all(_pack_rival(pair["input"], name) == pair["output"] for pair in episode["train"])
        ]
    else:
        labels_match = all(
            evaluator.apply(intended, pair["input"]) == pair["output"]
            for split in ("train", "test")
            for pair in episode[split]
        )
        declared_survivors = [
            candidate
            for candidate in FAMILY.SETTINGS
            if all(
                evaluator.apply(FAMILY.program(candidate), pair["input"]) == pair["output"]
                for pair in episode["train"]
            )
        ]
        rival_survivors = [
            name
            for name, source in rivals.items()
            if all(evaluator.apply(source, pair["input"]) == pair["output"] for pair in episode["train"])
        ]
    return {
        "seed": seed,
        "demos": demos,
        "queries": 4,
        "settings": settings,
        "input_sha256": _sha({
            "train": [pair["input"] for pair in episode["train"]],
            "test": [pair["input"] for pair in episode["test"]],
        }),
        "output_sha256": _sha({
            "train": [pair["output"] for pair in episode["train"]],
            "test": [pair["output"] for pair in episode["test"]],
        }),
        "program_sha256": hashlib.sha256(intended.encode()).hexdigest(),
        "labels_match": labels_match,
        "declared_survivors": declared_survivors,
        "rival_survivors": rival_survivors,
        "query_outputs_consulted": False,
        "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
    }


def build_report(
    *,
    seeds: Iterable[int] = (0, 17),
    demo_counts: Iterable[int] = (2, 3, 6),
    run_racket: bool = True,
) -> dict[str, Any]:
    normalized_seeds = _integer_list(list(seeds), 0, 2**63 - 1, "seeds")
    normalized_counts = _integer_list(list(demo_counts), 2, 6, "demo_counts")
    if type(run_racket) is not bool:
        raise ValueError("run_racket must be boolean")
    rivals = FAMILY.rival_programs()
    evaluator = _RacketEvaluator() if run_racket else None
    cases: list[dict[str, Any]] = []
    try:
        for seed in normalized_seeds:
            for demos in normalized_counts:
                baseline_input_sha: str | None = None
                for settings in FAMILY.SETTINGS:
                    case = _case_for(seed, demos, settings, rivals, evaluator)
                    if baseline_input_sha is None:
                        baseline_input_sha = case["input_sha256"]
                    case["inputs_match_other_settings"] = case["input_sha256"] == baseline_input_sha
                    cases.append(case)

        causal_input = FAMILY.sample_input(17, "query", 3)
        intended_source = FAMILY.program(FAMILY.SETTINGS[1])
        counterfactual_source = (HOME / "wrong_widest.rkt").read_text()
        if evaluator is None:
            expected_output = FAMILY.solve(causal_input, FAMILY.SETTINGS[1])
            counterfactual_output = FAMILY.solve_widest_left(causal_input)
        else:
            expected_output = evaluator.apply(intended_source, causal_input)
            counterfactual_output = evaluator.apply(counterfactual_source, causal_input)
        if expected_output == counterfactual_output:
            raise ValueError("wrong-intermediate witness did not change the final output")
        changed_cells = sum(
            left != right
            for expected_row, wrong_row in zip(expected_output, counterfactual_output, strict=True)
            for left, right in zip(expected_row, wrong_row, strict=True)
        )
        analysis = FAMILY.analyze(causal_input)
        causal_case = {
            "task_id": FAMILY.TASK_ID,
            "seed": 17,
            "split": "query",
            "index": 3,
            "settings": FAMILY.SETTINGS[1],
            "step_a": "split each row at color-8 walls and count pebbles in every maximal segment",
            "intermediate": {
                "kind": "per-row unique count-argmax segment",
                "rows": [
                    {
                        "row": row["row"],
                        "segment_counts": row["segment_counts"],
                        "segment_widths": row["segment_widths"],
                        "winner_index": row["winner_index"],
                        "widest_index": row["widest_index"],
                    }
                    for row in analysis["rows"]
                ],
            },
            "step_b": "pack the count-argmax segment left and all other segments right, preserving order",
            "why_b_depends_on_a": "the segment receiving left packing is not known until the per-segment counts are compared",
            "ablation": "wrong_intermediate_widest_segment",
            "input": causal_input,
            "expected_output": expected_output,
            "counterfactual_output": counterfactual_output,
            "changed_cells": changed_cells,
            "intended_program_sha256": hashlib.sha256(intended_source.encode()).hexdigest(),
            "counterfactual_program_sha256": hashlib.sha256(counterfactual_source.encode()).hexdigest(),
        }
    finally:
        if evaluator is not None:
            evaluator.close()

    report: dict[str, Any] = {
        "schema": SCHEMA,
        "task_id": FAMILY.TASK_ID,
        "scope": {
            "seeds": normalized_seeds,
            "demo_counts": normalized_counts,
            "queries": 4,
            "settings": list(FAMILY.SETTINGS),
            "rival_names": sorted(rivals),
            "claim": "finite protected-Racket teaching audit" if run_racket else "finite Python preflight",
        },
        "programs": [
            {
                "settings": settings,
                "sha256": hashlib.sha256(FAMILY.program(settings).encode()).hexdigest(),
            }
            for settings in FAMILY.SETTINGS
        ],
        "rivals": {name: hashlib.sha256(source.encode()).hexdigest() for name, source in sorted(rivals.items())},
        "cases": cases,
        "causal_case": causal_case,
        "summary": {
            "cases": len(cases),
            "all_inputs_setting_independent": all(case["inputs_match_other_settings"] for case in cases),
            "all_labels_match": all(case["labels_match"] for case in cases),
            "all_declared_unique": all(case["declared_survivors"] == [case["settings"]] for case in cases),
            "all_rivals_rejected": all(not case["rival_survivors"] for case in cases),
            "query_outputs_consulted": any(case["query_outputs_consulted"] for case in cases),
            "racket_checked": run_racket,
        },
    }
    if evaluator is not None:
        report["racket"] = {**evaluator.identity, "evaluations": evaluator.evaluations}
    return report


def write_report(path: Path | str, report: dict[str, Any]) -> None:
    target = Path(path)
    if target.is_symlink():
        raise ValueError("audit output cannot be a symlink")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False).encode() + b"\n"
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--demos", type=int, action="append", dest="demo_counts")
    parser.add_argument("--python-only", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = build_report(
        seeds=args.seeds if args.seeds is not None else (0, 17),
        demo_counts=args.demo_counts if args.demo_counts is not None else (2, 3, 6),
        run_racket=not args.python_only,
    )
    write_report(args.out, report)
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
