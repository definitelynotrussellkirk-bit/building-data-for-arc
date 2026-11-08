"""Finite demonstration-only shortcut audit for the fill-pass family."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
from typing import Iterable

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "arcpuzzles_fe54_fill_passes_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover
    raise RuntimeError("cannot load adjacent prototype.py")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)

SCHEMA = "arcpuzzles-fill-passes-self-audit-v1"
CANDIDATE_FAMILY = (
    "declared pass counts plus closure, copy, axis-only, precedence, broad-gap, "
    "diagonal, blocked-overwrite, fixed-color and first-pair shortcuts"
)


def _literal_sequence(
    name: str,
    values: Iterable[int],
    minimum: int,
    maximum: int,
) -> tuple[int, ...]:
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


def _axis_pass(grid: list[list[int]], axis: str) -> list[list[int]]:
    source = prototype._validate_grid(grid)
    output = copy.deepcopy(source)
    height, width = len(source), len(source[0])
    if axis == "horizontal":
        for row in range(height):
            for col in range(width - 2):
                color = source[row][col]
                if color and color == source[row][col + 2] and source[row][col + 1] == 0:
                    output[row][col + 1] = color
    elif axis == "vertical":
        for row in range(height - 2):
            for col in range(width):
                color = source[row][col]
                if color and color == source[row + 2][col] and source[row + 1][col] == 0:
                    output[row + 1][col] = color
    else:  # pragma: no cover
        raise ValueError(axis)
    return output


def _axis_only(grid: list[list[int]], axis: str, passes: int) -> list[list[int]]:
    result = prototype._validate_grid(grid)
    for _ in range(passes):
        result = _axis_pass(result, axis)
    return result


def _horizontal_precedence_pass(grid: list[list[int]]) -> list[list[int]]:
    source = prototype._validate_grid(grid)
    output = copy.deepcopy(source)
    height, width = len(source), len(source[0])
    for row in range(height - 2):
        for col in range(width):
            color = source[row][col]
            if color and color == source[row + 2][col] and source[row + 1][col] == 0:
                output[row + 1][col] = color
    for row in range(height):
        for col in range(width - 2):
            color = source[row][col]
            if color and color == source[row][col + 2] and source[row][col + 1] == 0:
                output[row][col + 1] = color
    return output


def _horizontal_precedence(grid: list[list[int]], passes: int) -> list[list[int]]:
    result = prototype._validate_grid(grid)
    for _ in range(passes):
        result = _horizontal_precedence_pass(result)
    return result


def _any_gap(grid: list[list[int]]) -> list[list[int]]:
    source = prototype._validate_grid(grid)
    output = copy.deepcopy(source)
    height, width = len(source), len(source[0])
    for row in range(height):
        for left in range(width):
            color = source[row][left]
            if color == 0:
                continue
            for right in range(left + 2, width):
                if source[row][right] == color and all(source[row][col] == 0 for col in range(left + 1, right)):
                    for col in range(left + 1, right):
                        output[row][col] = color
    for col in range(width):
        for top in range(height):
            color = source[top][col]
            if color == 0:
                continue
            for bottom in range(top + 2, height):
                if source[bottom][col] == color and all(source[row][col] == 0 for row in range(top + 1, bottom)):
                    for row in range(top + 1, bottom):
                        output[row][col] = color
    return output


def _diagonal_midpoints(grid: list[list[int]]) -> list[list[int]]:
    source = prototype._validate_grid(grid)
    output = prototype._apply_one_pass(source)
    height, width = len(source), len(source[0])
    for row in range(height - 2):
        for col in range(width - 2):
            color = source[row][col]
            if color and color == source[row + 2][col + 2] and source[row + 1][col + 1] == 0:
                output[row + 1][col + 1] = color
            color = source[row][col + 2]
            if color and color == source[row + 2][col] and source[row + 1][col + 1] == 0:
                output[row + 1][col + 1] = color
    return output


def _overwrite_blocked(grid: list[list[int]]) -> list[list[int]]:
    source = prototype._validate_grid(grid)
    output = prototype._apply_one_pass(source)
    height, width = len(source), len(source[0])
    for row in range(height):
        for col in range(width - 2):
            color = source[row][col]
            if color and color == source[row][col + 2]:
                output[row][col + 1] = color
    for row in range(height - 2):
        for col in range(width):
            color = source[row][col]
            if color and color == source[row + 2][col]:
                output[row + 1][col] = color
    return output


def _fixed_color(grid: list[list[int]], passes: int, color: int = 1) -> list[list[int]]:
    result = prototype._validate_grid(grid)
    for _ in range(passes):
        source = result
        result = prototype._apply_one_pass(source)
        for row in range(len(source)):
            for col in range(len(source[0])):
                if source[row][col] == 0 and result[row][col] != 0:
                    result[row][col] = color
    return result


def _first_pair_only(grid: list[list[int]]) -> list[list[int]]:
    source = prototype._validate_grid(grid)
    output = copy.deepcopy(source)
    height, width = len(source), len(source[0])
    for row in range(height):
        for col in range(width - 2):
            color = source[row][col]
            if color and color == source[row][col + 2] and source[row][col + 1] == 0:
                output[row][col + 1] = color
                return output
    for row in range(height - 2):
        for col in range(width):
            color = source[row][col]
            if color and color == source[row + 2][col] and source[row + 1][col] == 0:
                output[row + 1][col] = color
                return output
    return output


def _candidate_names() -> tuple[str, ...]:
    return (
        "passes:1",
        "passes:2",
        "copy",
        "closure",
        "horizontal-only:1",
        "horizontal-only:2",
        "vertical-only:1",
        "vertical-only:2",
        "horizontal-precedence:1",
        "horizontal-precedence:2",
        "any-gap",
        "diagonal-midpoints",
        "overwrite-blocked",
        "fixed-color:1",
        "fixed-color:2",
        "first-pair-only",
    )


def _predict(candidate: str, grid: list[list[int]]) -> list[list[int]]:
    if candidate.startswith("passes:"):
        return prototype.apply_passes(grid, int(candidate.rsplit(":", 1)[1]))
    if candidate == "copy":
        return prototype._validate_grid(grid)
    if candidate == "closure":
        return prototype.apply_until_stable(grid)
    if candidate.startswith("horizontal-only:"):
        return _axis_only(grid, "horizontal", int(candidate.rsplit(":", 1)[1]))
    if candidate.startswith("vertical-only:"):
        return _axis_only(grid, "vertical", int(candidate.rsplit(":", 1)[1]))
    if candidate.startswith("horizontal-precedence:"):
        return _horizontal_precedence(grid, int(candidate.rsplit(":", 1)[1]))
    if candidate == "any-gap":
        return _any_gap(grid)
    if candidate == "diagonal-midpoints":
        return _diagonal_midpoints(grid)
    if candidate == "overwrite-blocked":
        return _overwrite_blocked(grid)
    if candidate.startswith("fixed-color:"):
        return _fixed_color(grid, int(candidate.rsplit(":", 1)[1]))
    if candidate == "first-pair-only":
        return _first_pair_only(grid)
    raise ValueError(f"unknown audit candidate: {candidate}")


def _audit_case(seed: int, demos: int, queries: int, passes: int) -> dict:
    episode = prototype.generate_episode(seed, passes, demos, queries)
    candidates = _candidate_names()
    selected = f"passes:{passes}"
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
        "settings": {"fill_passes": passes},
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
        _audit_case(seed, demos, queries, passes)
        for seed in checked_seeds
        for demos in checked_demos
        for passes in prototype.PASS_OPTIONS
    ]
    passed = all(
        case["demo_survivors"]
        == [f"passes:{case['settings']['fill_passes']}"]
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
            "The selected setting is the sole survivor among the enumerated demonstration-only rivals. "
            "This finite audit is not a universal uniqueness proof."
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
