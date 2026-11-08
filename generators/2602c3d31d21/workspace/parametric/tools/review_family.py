#!/usr/bin/env python3
"""Build bounded protected-Racket self-review evidence for this family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


HERE = Path(__file__).resolve().parent
PARAMETRIC = HERE.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load("review_2602c3d31d21_prototype", PARAMETRIC / "prototype.py")
ORACLE = _load("review_2602c3d31d21_oracle", PARAMETRIC / "oracle.py")


def _execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def _normalize(cells: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    top = min(row for row, _col in cells)
    left = min(col for _row, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _transform(
    cells: list[tuple[int, int]], transform: int
) -> tuple[tuple[int, int], ...]:
    points: list[tuple[int, int]] = []
    for row, col in cells:
        x, y = row, -col if transform >= 4 else col
        for _ in range(transform % 4):
            x, y = y, -x
        points.append((x, y))
    return _normalize(points)


def _congruence(cells: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_transform(cells, transform) for transform in range(8))


def _rival_signatures(analysis: dict[str, Any], rival: str) -> list[Any]:
    shapes = analysis["shapes"]
    if rival == "congruence":
        return [_congruence(shape["cells"]) for shape in shapes]
    if rival == "body_size":
        return [shape["size"] for shape in shapes]
    if rival == "always_equal":
        return [0 for _shape in shapes]
    if rival == "always_unequal":
        return list(range(len(shapes)))
    raise ValueError(rival)


def _rival_output(grid: list[list[int]], rival: str) -> list[list[int]]:
    analysis = ORACLE.analyze_input(grid)
    return ORACLE.render_comparison(
        analysis["key_colors"], _rival_signatures(analysis, rival)
    )


def build() -> dict[str, Any]:
    programs = {metric: PROTOTYPE.rule_text(metric) for metric in PROTOTYPE.METRICS}
    reviews: list[dict[str, Any]] = []
    executions: list[dict[str, Any]] = []
    rivals = ("congruence", "body_size", "always_equal", "always_unequal")
    with RacketBridge(timeout=30, max_calls_before_restart=64) as bridge:
        identity = {
            key: value
            for key, value in bridge.runtime_identity.items()
            if key
            in {
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            }
        }
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("self-review requires the protected Racket backend")
        for metric in PROTOTYPE.METRICS:
            episode = PROTOTYPE.generate_episode(101, metric=metric, demos=2, queries=4)
            survivors: list[str] = []
            for candidate, program in programs.items():
                if all(
                    _execute(bridge, program, pair["input"]) == pair["output"]
                    for pair in episode["train"]
                ):
                    survivors.append(candidate)
            if survivors != [metric]:
                raise RuntimeError(f"unexpected finite survivors for {metric}: {survivors}")
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    actual = _execute(bridge, programs[metric], pair["input"])
                    if actual != pair["output"]:
                        raise RuntimeError(f"Racket label mismatch: {metric} {split} {index}")
                    executions.append(
                        {
                            "metric": metric,
                            "split": split,
                            "index": index,
                            "input_sha256": hashlib.sha256(
                                json.dumps(pair["input"], separators=(",", ":")).encode()
                            ).hexdigest(),
                            "output_sha256": hashlib.sha256(
                                json.dumps(actual, separators=(",", ":")).encode()
                            ).hexdigest(),
                        }
                    )
            for rival in rivals:
                witness = None
                for index, pair in enumerate(episode["train"]):
                    prediction = _rival_output(pair["input"], rival)
                    if prediction != pair["output"]:
                        witness = {
                            "demo_index": index,
                            "input": pair["input"],
                            "racket_output": pair["output"],
                            "rival_output": prediction,
                        }
                        break
                if witness is None:
                    raise RuntimeError(f"{rival} survived both demos for {metric}")
                reviews.append(
                    {
                        "chosen_metric": metric,
                        "rival": rival,
                        "status": "refuted_by_visible_demo",
                        **witness,
                    }
                )
    return {
        "schema": "arcpuzzles-parametric-self-review-v1",
        "task_id": PROTOTYPE.TASK_ID,
        "status": "bounded_rivals_refuted",
        "settings": list(PROTOTYPE.METRICS),
        "program_sha256": {
            metric: hashlib.sha256(program.encode()).hexdigest()
            for metric, program in programs.items()
        },
        "racket": identity,
        "demo_only_survivor": True,
        "query_labels_replayed": len(PROTOTYPE.METRICS) * 4,
        "rivals": reviews,
        "executions": executions,
        "limits": (
            "Finite authored checks against congruence, body-size, always-equal, "
            "and always-unequal rivals; this is not a universal uniqueness proof."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    value = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": value["status"],
                "rival_checks": len(value["rivals"]),
                "racket_executions": len(value["executions"]),
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
