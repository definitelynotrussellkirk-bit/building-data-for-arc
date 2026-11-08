"""Finite demonstration-only shortcut audit for the query-order family.

This deliberately bounded audit asks whether the declared setting or a small set
of plausible shortcuts can fit every visible demonstration.  It is evidence
about the enumerated rivals only, not a universal uniqueness proof.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Iterable

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "arcpuzzles_0938_query_order_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError("cannot load adjacent prototype.py")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)

SCHEMA = "arcpuzzles-query-order-self-audit-v1"
CANDIDATE_FAMILY = "declared order plus fixed-operation/copy/zero shortcuts"


def _literal_sequence(name: str, values: Iterable[int], minimum: int, maximum: int) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be an iterable of literal integers")
    try:
        result = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be an iterable of literal integers") from exc
    if not result:
        raise ValueError(f"{name} must not be empty")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must not contain duplicates")
    for value in result:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must contain literal integers")
        if not minimum <= value <= maximum:
            raise ValueError(f"{name} values must be in {minimum}..{maximum}")
    return result


def _candidate_names() -> tuple[str, ...]:
    fixed = tuple(
        f"fixed:{operation}:{order}"
        for operation in prototype.OPS
        for order in prototype.ORDERS
    )
    return tuple(f"order:{order}" for order in prototype.ORDERS) + fixed + (
        "copy:x",
        "copy:y",
        "zero",
    )


def _predict(candidate: str, grid: list[list[int]]) -> list[list[int]]:
    if candidate.startswith("order:"):
        return prototype.output_for(grid, candidate.split(":", 1)[1])

    panels = prototype._split(grid)
    if candidate.startswith("fixed:"):
        _, operation, order = candidate.split(":")
        left, right = (panels[3], panels[4]) if order == "xy" else (panels[4], panels[3])
        return prototype._apply(operation, left, right)
    if candidate == "copy:x":
        return [row[:] for row in panels[3]]
    if candidate == "copy:y":
        return [row[:] for row in panels[4]]
    if candidate == "zero":
        return [[0 for _ in row] for row in panels[3]]
    raise ValueError(f"unknown audit candidate: {candidate}")


def _audit_case(seed: int, demos: int, queries: int, order: str) -> dict:
    episode = prototype.generate_episode(seed, order, demos, queries)
    candidates = _candidate_names()
    selected = f"order:{order}"
    survivors: list[str] = []
    refutations: dict[str, dict] = {}

    for candidate in candidates:
        first_failure = next(
            (
                index
                for index, pair in enumerate(episode["train"])
                if _predict(candidate, pair["input"]) != pair["output"]
            ),
            None,
        )
        if first_failure is None:
            survivors.append(candidate)
        elif candidate != selected:
            refutations[candidate] = {
                "first_failing_demo": first_failure,
                "reason": "label mismatch",
            }

    ambiguous = [
        candidate
        for candidate in survivors
        if candidate != selected
        and any(
            _predict(candidate, pair["input"]) != pair["output"]
            for pair in episode["test"]
        )
    ]
    return {
        "seed": seed,
        "demos": demos,
        "settings": {"query_operand_order": order},
        "rivals": list(candidates),
        "rival_count": len(candidates) - 1,
        "demo_survivors": survivors,
        "ambiguous_query_rivals": ambiguous,
        "refutations": refutations,
    }


def audit_family(*, seeds: Iterable[int], demo_counts: Iterable[int], queries: int) -> dict:
    checked_seeds = _literal_sequence("seeds", seeds, 0, 2**63 - 1)
    checked_demos = _literal_sequence(
        "demo_counts", demo_counts, prototype.MIN_DEMOS, prototype.MAX_DEMOS
    )
    if isinstance(queries, bool) or not isinstance(queries, int):
        raise TypeError("queries must be a literal integer")
    if queries != prototype.QUERY_COUNT:
        raise ValueError(f"queries must equal {prototype.QUERY_COUNT}")

    cases = [
        _audit_case(seed, demos, queries, order)
        for seed in checked_seeds
        for demos in checked_demos
        for order in prototype.ORDERS
    ]
    passed = all(
        case["demo_survivors"]
        == [f"order:{case['settings']['query_operand_order']}"]
        and not case["ambiguous_query_rivals"]
        for case in cases
    )
    return {
        "schema": SCHEMA,
        "status": "passed" if passed else "failed",
        "limits": {
            "seeds": list(checked_seeds),
            "demo_counts": list(checked_demos),
            "queries": queries,
            "candidate_family": CANDIDATE_FAMILY,
        },
        "cases": cases,
        "conclusion": (
            "The selected setting is the sole survivor among the enumerated "
            "demonstration-only rivals. This finite audit is not a universal uniqueness proof."
            if passed
            else "At least one enumerated rival survives the demonstrations."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--demos", type=int, action="append", dest="demo_counts")
    parser.add_argument("--queries", type=int, default=prototype.QUERY_COUNT)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = audit_family(
        seeds=args.seeds or (0, 17),
        demo_counts=args.demo_counts or (2, 3, 6),
        queries=args.queries,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(rendered, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
