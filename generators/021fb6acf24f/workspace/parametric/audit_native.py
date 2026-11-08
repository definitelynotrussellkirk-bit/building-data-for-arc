"""Bounded protected-Racket learnability audit for the native color-order family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import normalize_grid

TASK_ID = "021fb6acf24f"
SCHEMA = "arcpuzzles-parametric-self-audit-v1"
_HOME = Path(__file__).resolve().parent

# Preserve first occurrence in row-major grid-cells order, rather than sorting
# numeric colors as the canonical `unique` helper does.
SCAN_ORDER_COLOR_EXPRESSION = """(reverse
                                  (foldl (lambda (v acc)
                                           (if (or (= v 0) (member v acc))
                                               acc
                                               (cons v acc)))
                                         '()
                                         (map third (grid-cells g))))"""
IDENTITY_PROGRAM = "(rule! (lambda (g) g))"


def _load_adjacent(filename: str) -> ModuleType:
    path = (_HOME / filename).resolve()
    if path.parent != _HOME or not path.is_file():
        raise ValueError(f"missing adjacent audit resource: {filename}")
    name = "_audit_021fb6acf24f_" + path.stem + "_" + hashlib.sha256(str(path).encode()).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adjacent audit resource: {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_ADAPTER = _load_adjacent("adapter.py")
_PROTOTYPE = _load_adjacent("prototype.py")


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"cannot materialize {label}: expected one replacement site")
    result = source.replace(old, new, 1)
    if result == source:
        raise AssertionError(f"{label} did not change the source")
    return result


def _rivals(color_order: str) -> dict[str, str]:
    chosen = _ADAPTER.program({"color_order": color_order})
    opposite = "descending" if color_order == "ascending" else "ascending"
    canonical = _ADAPTER.program({"color_order": "ascending"})
    scan_order = _replace_once(
        canonical,
        _PROTOTYPE.CANONICAL_COLOR_EXPRESSION,
        SCAN_ORDER_COLOR_EXPRESSION,
        "row-major first-occurrence rival",
    )
    late_overwrite = _replace_once(
        chosen,
        "(zero? (at acc r c))",
        "(zero? (at g r c))",
        "original-zero late-overwrite rival",
    )
    return {
        "opposite_numeric_order": _ADAPTER.program({"color_order": opposite}),
        "row_major_first_occurrence": scan_order,
        "original_zero_late_overwrite": late_overwrite,
        "identity": IDENTITY_PROGRAM,
    }


def _literal(grid: Any) -> str:
    normalized = normalize_grid(grid)
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in normalized) + ")"


def _execute(bridge: RacketBridge, cache: dict[str, str], program: str, grid: Any) -> list[list[int]]:
    callable_source = cache.setdefault(program, wrap_rule(program))
    return normalize_grid(bridge.eval_text(f"({callable_source} {_literal(grid)})"))


def _first_nonzero(grid: list[list[int]]) -> int:
    return next(value for row in grid for value in row if value != 0)


def _counterexample(
    pairs: list[dict[str, list[list[int]]]],
    chosen_outputs: list[list[list[int]]],
    rival_outputs: list[list[list[int]]],
    demos: int,
) -> dict[str, Any]:
    for index, (pair, chosen, rival) in enumerate(zip(pairs, chosen_outputs, rival_outputs, strict=True)):
        if chosen != rival:
            return {
                "split": "train" if index < demos else "test",
                "index": index if index < demos else index - demos,
                "input": deepcopy(pair["input"]),
                "chosen_output": deepcopy(chosen),
                "rival_output": deepcopy(rival),
            }
    raise AssertionError("rival had no counterexample")


def audit(seed: int = 0) -> dict[str, Any]:
    """Execute a finite four-rival audit for both settings with two demos."""
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative integer; bool is forbidden")
    if seed < 0:
        raise ValueError("seed must be nonnegative")

    demos, queries = 2, 4
    rows: list[dict[str, Any]] = []
    evaluations = 0
    with RacketBridge() as bridge:
        identity = deepcopy(bridge.runtime_identity)
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("self-audit requires protected Racket")
        cache: dict[str, str] = {}
        for color_order in ("ascending", "descending"):
            settings = {"color_order": color_order}
            episode = _ADAPTER.generate(seed, settings, demos, queries)
            pairs = [*episode["train"], *episode["test"]]
            chosen_program = _ADAPTER.program(settings)
            chosen_outputs = []
            for pair in pairs:
                chosen_outputs.append(_execute(bridge, cache, chosen_program, pair["input"]))
                evaluations += 1
            chosen_matches = all(
                output == pair["output"]
                for output, pair in zip(chosen_outputs, pairs, strict=True)
            )

            rival_rows: dict[str, Any] = {}
            for name, rival_program in _rivals(color_order).items():
                rival_outputs = []
                for pair in pairs:
                    rival_outputs.append(_execute(bridge, cache, rival_program, pair["input"]))
                    evaluations += 1
                demo_matches = [
                    output == chosen_outputs[index]
                    for index, output in enumerate(rival_outputs[:demos])
                ]
                query_matches = [
                    output == chosen_outputs[demos + index]
                    for index, output in enumerate(rival_outputs[demos:])
                ]
                rival_rows[name] = {
                    "program_sha256": hashlib.sha256(rival_program.encode()).hexdigest(),
                    "demo_matches": demo_matches,
                    "query_matches": query_matches,
                    "fits_demonstrations": all(demo_matches),
                    "query_differs": not all(query_matches),
                    "counterexample": _counterexample(
                        pairs, chosen_outputs, rival_outputs, demos
                    ),
                }

            rows.append(
                {
                    "settings": settings,
                    "chosen_program_sha256": hashlib.sha256(chosen_program.encode()).hexdigest(),
                    "chosen_labels_match_racket": chosen_matches,
                    "teaching_profile": [
                        {
                            "demo_index": index,
                            "first_nonzero": _first_nonzero(pair["input"]),
                            "colors": sorted(
                                {value for row in pair["input"] for value in row if value != 0}
                            ),
                        }
                        for index, pair in enumerate(episode["train"])
                    ],
                    "rivals": rival_rows,
                }
            )

    passed = all(
        row["chosen_labels_match_racket"]
        and all(
            not rival["fits_demonstrations"] and rival["query_differs"]
            for rival in row["rivals"].values()
        )
        for row in rows
    )
    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "status": "pass" if passed else "fail",
        "scope": {
            "seed": seed,
            "demos": demos,
            "queries": queries,
            "settings": len(rows),
            "rivals_per_setting": 4,
        },
        "racket": identity,
        "racket_evaluations": evaluations,
        "settings": rows,
        "limitation": (
            "This is a finite audit of four named rivals on one matched-input seed; "
            "it is not a proof of universal rule uniqueness."
        ),
    }


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = audit(args.seed)
    _write(args.out, report)
    print(json.dumps({
        "status": report["status"],
        "path": str(args.out),
        "racket_evaluations": report["racket_evaluations"],
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
