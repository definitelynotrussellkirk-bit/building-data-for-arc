"""Finite demonstration-only shortcut audit for the rotation/scale family.

The candidate set is deliberately bounded.  Passing means that the selected
setting alone fits the visible demonstrations among these enumerated rivals; it
is not a universal uniqueness proof over all ARC programs.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

_HERE = Path(__file__).resolve().parent
_NAME = "arcpuzzles_5e8e4691afde_self_audit_prototype"
_SPEC = importlib.util.spec_from_file_location(_NAME, _HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError("cannot load adjacent prototype.py")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = prototype
_SPEC.loader.exec_module(prototype)

SCHEMA = "arcpuzzles-rotation-scale-self-audit-v1"
CANDIDATE_FAMILY = (
    "declared transforms plus endpoint, center, copy, fill, frame, and diagonal shortcuts"
)


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


def _setting_name(setting) -> str:
    return f"setting:{setting.quarter_turns}:{setting.distance_scale}"


def _candidate_names() -> tuple[str, ...]:
    declared = tuple(_setting_name(setting) for setting in prototype.SETTINGS)
    return declared + (
        "copy-input",
        "solid-center-color",
        "original-center",
        "endpoint-center",
        "indicator-center",
        "canonical-frame-only",
        "canonical-diagonals-only",
        "canonical-retain-background",
    )


def _paint(grid: list[list[int]], target: tuple[int, int], mode: str) -> list[list[int]]:
    info = prototype.scene_info(grid)
    height, width, color = info["height"], info["width"], info["color"]
    center_row, center_col = target
    if mode == "retain":
        output = copy.deepcopy(grid)
    else:
        output = [[color for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            at_center = (row, col) == target
            in_frame = abs(row - center_row) <= 1 and abs(col - center_col) <= 1
            on_diagonal = row - col == center_row - center_col or row + col == center_row + center_col
            if at_center:
                output[row][col] = color
            elif mode in {"full", "retain"} and (in_frame or on_diagonal):
                output[row][col] = 4
            elif mode == "frame" and in_frame:
                output[row][col] = 4
            elif mode == "diagonals" and on_diagonal:
                output[row][col] = 4
    return output


def _predict(candidate: str, grid: list[list[int]]) -> list[list[int]]:
    if candidate.startswith("setting:"):
        _, turns, scale = candidate.split(":")
        return prototype.mirror(grid, prototype.Setting(int(turns), int(scale)))

    info = prototype.scene_info(grid)
    if candidate == "copy-input":
        return copy.deepcopy(grid)
    if candidate == "solid-center-color":
        return [[info["color"] for _ in range(info["width"])] for _ in range(info["height"])]
    if candidate == "original-center":
        return _paint(grid, info["center"], "full")
    if candidate == "endpoint-center":
        return _paint(grid, info["endpoint"], "full")
    if candidate == "indicator-center":
        return _paint(grid, info["indicator"], "full")

    canonical_target = prototype.target_center(info, prototype.DEFAULT)
    if candidate == "canonical-frame-only":
        return _paint(grid, canonical_target, "frame")
    if candidate == "canonical-diagonals-only":
        return _paint(grid, canonical_target, "diagonals")
    if candidate == "canonical-retain-background":
        return _paint(grid, canonical_target, "retain")
    raise ValueError(f"unknown audit candidate: {candidate}")


def _audit_case(seed: int, demos: int, queries: int, setting) -> dict:
    episode = prototype.generate_episode(seed, setting, demos, queries)
    candidates = _candidate_names()
    selected = _setting_name(setting)
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
        "settings": setting.as_dict(),
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
        _audit_case(seed, demos, queries, setting)
        for seed in checked_seeds
        for demos in checked_demos
        for setting in prototype.SETTINGS
    ]
    passed = all(
        case["demo_survivors"]
        == [f"setting:{case['settings']['quarter_turns']}:{case['settings']['distance_scale']}"]
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
