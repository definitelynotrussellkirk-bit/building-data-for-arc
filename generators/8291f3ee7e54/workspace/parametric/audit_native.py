"""Bounded protected-Racket learnability audit for the native ring-order family."""
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

TASK_ID = "8291f3ee7e54"
SCHEMA = "arcpuzzles-parametric-self-audit-v1"
_HOME = Path(__file__).resolve().parent

BEST_OBJECT_BLOCK = '''             (define (best-object color)
               (pick-max (filter (lambda (obj) (= (obj-color obj) color)) objs)
                         obj-size))'''

UNION_BBOX_BLOCK = '''             (define (best-object color)
               (let* ((cells (map (lambda (cell) (list (first cell) (second cell)))
                                  (filter (lambda (cell) (= (third cell) color))
                                          (grid-cells g))))
                      (rs (map first cells))
                      (cs (map second cells)))
                 (hasheq 'color color
                         'cells cells
                         'bbox (list (apply min rs) (apply min cs)
                                     (apply max rs) (apply max cs))
                         'size (length cells))))'''


def _numeric_tail(comparator: str) -> str:
    if comparator not in {"<", ">"}:
        raise ValueError("numeric comparator must be < or >")
    return f'''             (define n (obj-size (first layers)))
             (define ring-colors (sort (map obj-color layers) {comparator}))
             (define (paint-layer out obj color)
               (let* ((s (obj-size obj))
                      (off (quotient (- n s) 2)))
                 (for*/fold ((acc out))
                            ((r (in-range off (+ off s))) (c (in-range off (+ off s))))
                            (if (or
                                  (= r off)
                                  (= r (- (+ off s) 1))
                                  (= c off)
                                  (= c (- (+ off s) 1)))
                                (set-cell acc r c color)
                                acc))))
             (for/fold ((out (empty-grid n n 0)))
                       ((obj layers) (color ring-colors))
               (paint-layer out obj color))))))'''


def _load_adjacent(filename: str) -> ModuleType:
    path = (_HOME / filename).resolve()
    if path.parent != _HOME or not path.is_file():
        raise ValueError(f"missing adjacent audit resource: {filename}")
    name = "_audit_8291f3ee7e54_" + path.stem + "_" + hashlib.sha256(str(path).encode()).hexdigest()
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


def _rivals(ring_order: str) -> dict[str, str]:
    chosen = _ADAPTER.program({"ring_order": ring_order})
    opposite = (
        "smallest_outside" if ring_order == "largest_outside" else "largest_outside"
    )
    canonical = _ADAPTER.program({"ring_order": "largest_outside"})
    return {
        "opposite_ring_order": _ADAPTER.program({"ring_order": opposite}),
        "union_bbox_per_color": _replace_once(
            chosen,
            BEST_OBJECT_BLOCK,
            UNION_BBOX_BLOCK,
            "union-bbox component shortcut",
        ),
        "numeric_ascending_outside": _replace_once(
            canonical,
            _PROTOTYPE.CANONICAL_TAIL,
            _numeric_tail("<"),
            "numeric-ascending ring shortcut",
        ),
        "numeric_descending_outside": _replace_once(
            canonical,
            _PROTOTYPE.CANONICAL_TAIL,
            _numeric_tail(">"),
            "numeric-descending ring shortcut",
        ),
    }


def _literal(grid: Any) -> str:
    normalized = normalize_grid(grid)
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in normalized) + ")"


def _execute(
    bridge: RacketBridge,
    cache: dict[str, str],
    program: str,
    grid: Any,
) -> list[list[int]]:
    callable_source = cache.setdefault(program, wrap_rule(program))
    return normalize_grid(bridge.eval_text(f"({callable_source} {_literal(grid)})"))


def _counterexample(
    pairs: list[dict[str, list[list[int]]]],
    chosen_outputs: list[list[list[int]]],
    rival_outputs: list[list[list[int]]],
    demos: int,
) -> dict[str, Any]:
    for index, (pair, chosen, rival) in enumerate(
        zip(pairs, chosen_outputs, rival_outputs, strict=True)
    ):
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
    """Execute four named rivals for both settings with the minimum lesson."""
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
        for ring_order in ("largest_outside", "smallest_outside"):
            settings = {"ring_order": ring_order}
            episode = _ADAPTER.generate(seed, settings, demos, queries)
            pairs = [*episode["train"], *episode["test"]]
            chosen_program = _ADAPTER.program(settings)
            chosen_outputs = [
                _execute(bridge, cache, chosen_program, pair["input"])
                for pair in pairs
            ]
            evaluations += len(pairs)
            chosen_matches = all(
                output == pair["output"]
                for output, pair in zip(chosen_outputs, pairs, strict=True)
            )

            rival_rows: dict[str, Any] = {}
            for name, rival_program in _rivals(ring_order).items():
                rival_outputs = [
                    _execute(bridge, cache, rival_program, pair["input"])
                    for pair in pairs
                ]
                evaluations += len(pairs)
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
            "Finite audit of four named rivals on one matched-input seed; "
            "not a proof of universal rule uniqueness."
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
    print(
        json.dumps(
            {
                "status": report["status"],
                "path": str(args.out),
                "racket_evaluations": report["racket_evaluations"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
