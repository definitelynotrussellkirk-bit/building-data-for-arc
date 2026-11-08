#!/usr/bin/env python3
"""Build the source-bound orientation-intermediate witness after qualification."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "5b18a320e97b"
HERE = Path(__file__).resolve().parent
PROTOTYPE_PATH = HERE / "prototype.py"
STEP_A = (
    "Inspect every nonzero, non-gray color and determine whether all of its visible "
    "cells lie on one row; retain the input-dependent horizontal-versus-vertical "
    "orientation and the corresponding spatial color order."
)
INTERMEDIATE = (
    "The inferred orientation together with the ordered color sequence on that "
    "orientation's coordinate axis."
)
STEP_B = (
    "Use the inferred orientation to choose both the sorting axis and the output "
    "stripe layout, then apply the episode-fixed forward or reverse read direction."
)
WHY_B_DEPENDS_ON_A = (
    "Step B cannot choose row coordinates and solid output rows versus column "
    "coordinates and repeated output columns until Step A supplies the scene's "
    "orientation; forcing the wrong orientation changes the final grid."
)


def _load_prototype():
    name = "_witness_5b18a320e97b_" + hashlib.sha256(
        str(PROTOTYPE_PATH).encode()
    ).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _force_horizontal(source: str, value: bool) -> str:
    start = source.find("(horizontal (andmap")
    marker = "\n                  (sorted-colors"
    end = source.find(marker, start)
    if start < 0 or end < 0 or source.find("(horizontal (andmap", start + 1) >= 0:
        raise ValueError("expected one canonical orientation binding")
    replacement = f"(horizontal {'#t' if value else '#f'})"
    return source[:start] + replacement + source[end:]


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def _changed_cells(left: list[list[int]], right: list[list[int]]) -> int:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        return max(sum(map(len, left)), sum(map(len, right)))
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build(qualification_path: Path, output: Path, *, seed: int = 17) -> dict[str, Any]:
    """Build and execute one wrong-intermediate counterfactual witness."""
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
    if (
        qualification.get("schema") != "arcpuzzles-parametric-qualification-v1"
        or qualification.get("status") != "qualified"
        or qualification.get("task_id") != TASK_ID
        or type(qualification.get("source_binding")) is not dict
        or type(qualification.get("programs")) is not dict
    ):
        raise ValueError("qualification is not a qualified source-bound native receipt")

    prototype = _load_prototype()
    settings = {"read_direction": "forward"}
    setting_key = json.dumps(settings, sort_keys=True, separators=(",", ":"))
    rule = prototype.program(settings)
    if qualification["programs"].get(setting_key) != hashlib.sha256(rule.encode()).hexdigest():
        raise ValueError("qualification does not bind the forward program")

    episode = prototype.generate(seed, settings, 3, 4)
    pair = episode["test"][0]
    facts = prototype._native_analysis(pair["input"])["facts"]
    if facts["orientation"] != "vertical":
        raise AssertionError("witness query must be vertical")
    counterfactual = _force_horizontal(rule, True)

    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("witness builder requires protected Racket")
        literal = _grid_literal(pair["input"])
        correct = bridge.eval_text(f"({wrap_rule(rule)} {literal})")
        wrong = bridge.eval_text(f"({wrap_rule(counterfactual)} {literal})")
    if correct == wrong:
        raise AssertionError("wrong orientation intermediate did not change final output")

    witness = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "task_id": TASK_ID,
        "source_binding": qualification["source_binding"],
        "racket": {"backend": "racket", "protected": True},
        "step_a": STEP_A,
        "intermediate": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY_B_DEPENDS_ON_A,
        "cases": [
            {
                "seed": seed,
                "query_index": 0,
                "input": pair["input"],
                "settings": settings,
                "intermediate_value": {
                    "orientation": facts["orientation"],
                    "ordered_colors": list(facts["ordered_colors"]),
                },
                "counterfactual_intermediate_value": {
                    "orientation": "horizontal",
                    "ordered_colors": "recomputed on the wrong row axis",
                },
                "ablation": "wrong_intermediate",
                "program": rule,
                "counterfactual_program": counterfactual,
                "output": correct,
                "counterfactual_output": wrong,
                "changed_cells": _changed_cells(correct, wrong),
            }
        ],
        "limits": (
            "One bounded authored vertical case; protected execution establishes "
            "the reported counterfactual labels, not universal algorithmic depth."
        ),
    }
    _write(output, witness)
    return witness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args(argv)
    witness = build(args.qualification, args.out, seed=args.seed)
    print(
        json.dumps(
            {
                "status": "built",
                "cases": len(witness["cases"]),
                "changed_cells": witness["cases"][0]["changed_cells"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
