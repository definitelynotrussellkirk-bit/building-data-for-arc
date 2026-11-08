#!/usr/bin/env python3
"""Source-bound shortcut and cyclic-lesson probe for task 195dfcc5b541.

This reviewer tool discovers rivals from the generator's live declarations.  It
checks their fit on the canonical demonstrations, retains exact generated
counterexamples, and holds out every position in each deterministic four-pair
lesson window.  Its independent Python geometry oracle is diagnostic; pass
``--racket`` to require parity with the selected Racket authority on every
materialized generated input.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import inspect
import json
import os
from pathlib import Path
from typing import Any, Iterable

from reference_probe import (
    canonical_pairs,
    changed_cells,
    geometry_output,
    load_generator,
    racket_outputs,
)

TASK_ID = "195dfcc5b541"


def _sha256_file(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _declared_rules(gen: Any, attribute: str) -> dict[str, Any]:
    value = getattr(gen, attribute, {})
    if not isinstance(value, dict):
        raise TypeError(f"{attribute} must be a dict, found {type(value).__name__}")
    result: dict[str, Any] = {}
    for name, solver in value.items():
        if not isinstance(name, str) or not name:
            raise TypeError(f"{attribute} contains a non-string or empty name: {name!r}")
        if not callable(solver):
            raise TypeError(f"{attribute}[{name!r}] is not callable")
        result[name] = solver
    return result


def _call_solver(solver: Any, grid: list[list[int]]) -> list[list[int]]:
    caller_copy = deepcopy(grid)
    first_input = deepcopy(grid)
    first = solver(first_input)
    second = solver(deepcopy(grid))
    if caller_copy != grid:
        raise AssertionError("probe mutated its caller-owned input")
    if first_input != grid:
        raise AssertionError("declared solver mutated its input")
    if first != second:
        raise AssertionError("declared solver is non-deterministic")
    if not isinstance(first, list):
        raise TypeError(f"declared solver returned {type(first).__name__}, expected a grid")
    return first


def _band_name(band: str | None) -> str:
    return "default" if band is None else band


def _counterexample_record(
    *,
    band: str | None,
    seed: int,
    sample_index: int,
    grid: list[list[int]],
    expected: list[list[int]],
    rival: list[list[int]],
) -> dict[str, Any]:
    return {
        "band": _band_name(band),
        "seed": seed,
        "sample_index": sample_index,
        "input_sha256": _grid_sha256(grid),
        "input": grid,
        "intended_output": expected,
        "rival_output": rival,
        "differing_cells": [
            {
                "row": row,
                "col": col,
                "intended": expected[row][col],
                "rival": rival[row][col],
            }
            for row, col in changed_cells(rival, expected)
        ],
    }


def build_report(
    gen: Any,
    *,
    seeds: Iterable[int],
    starts: Iterable[int],
    bands: Iterable[str | None],
    verify_racket: bool,
) -> dict[str, Any]:
    """Build a JSON-serializable source-bound rival and lesson report."""
    seed_values = list(seeds)
    start_values = list(starts)
    band_values = list(bands)
    if not seed_values or not start_values or not band_values:
        raise ValueError("seeds, starts, and bands must all be non-empty")
    if any(type(value) is not int or value < 0 for value in seed_values + start_values):
        raise ValueError("seeds and starts must be non-negative integers")

    shortcuts = _declared_rules(gen, "CANONICAL_SHORTCUTS")
    competitors = _declared_rules(gen, "LESSON_COMPETITORS")
    rivals = dict(shortcuts)
    rivals.update(competitors)
    if not rivals:
        raise ValueError("generator declares no canonical shortcuts or lesson competitors")

    examples_needed = getattr(gen, "EXAMPLES_NEEDED", None)
    if type(examples_needed) is not int or examples_needed < 1:
        raise ValueError("EXAMPLES_NEEDED must be a positive integer")
    window_size = examples_needed + 1

    source = inspect.getsourcefile(gen)
    source_path = Path(source).resolve() if source else None
    report: dict[str, Any] = {
        "schema": "195dfcc5b541-shortcut-probe-v1",
        "task_id": getattr(gen, "TASK_ID", None),
        "generator_version": getattr(gen, "VERSION", None),
        "generator_sha256": _sha256_file(source_path),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "label_authority": (
            "independent visible-geometry Python oracle; when racket.enabled is true, "
            "every generated oracle output was also matched to the selected Racket authority"
        ),
        "settings": {
            "seeds": seed_values,
            "starts": start_values,
            "bands": [_band_name(band) for band in band_values],
            "examples_needed": examples_needed,
            "window_size": window_size,
            "query_policy": "hold out every pair position once per deterministic window",
        },
        "declarations": {
            "CANONICAL_SHORTCUTS": sorted(shortcuts),
            "LESSON_COMPETITORS": sorted(competitors),
        },
        "canonical_shortcuts": {},
        "generated": {
            "samples": 0,
            "unique_inputs": 0,
            "counterexamples": {name: 0 for name in sorted(rivals)},
            "first_counterexample": {},
            "failures": [],
        },
        "lessons": {
            "windows": 0,
            "query_rotations": 0,
            "ambiguous_rotations": [],
            "hook_disagreements": [],
        },
        "racket": {"enabled": bool(verify_racket), "cases": 0, "matches": None},
        "limits": [
            "Finite evidence against declared rivals, not proof against every conceivable rule.",
            "Windows use direct deterministic generator draws; the public lesson census separately covers production materialization and rejection handling.",
        ],
        "errors": [],
        "status": "pending",
    }

    canonical = canonical_pairs()
    training = [pair for pair in canonical if pair.get("split") == "train"]
    for name, shortcut in sorted(shortcuts.items()):
        training_fits = sum(
            _call_solver(shortcut, pair["input"]) == pair["output"] for pair in training
        )
        all_fits = sum(
            _call_solver(shortcut, pair["input"]) == pair["output"] for pair in canonical
        )
        report["canonical_shortcuts"][name] = {
            "training": {"fits": training_fits, "pairs": len(training)},
            "all_labeled": {"fits": all_fits, "pairs": len(canonical)},
        }
        if training_fits != len(training):
            report["errors"].append(
                f"declared canonical shortcut {name!r} does not fit every training demonstration"
            )

    samples: dict[tuple[str | None, int, int], dict[str, Any]] = {}
    windows: list[dict[str, Any]] = []
    for band in band_values:
        for seed in seed_values:
            for start in start_values:
                keys = []
                for sample_index in range(start, start + window_size):
                    key = (band, seed, sample_index)
                    keys.append(key)
                    if key in samples:
                        continue
                    try:
                        grid = gen.generate(seed, sample_index, difficulty=band)
                        check_errors = list(gen.self_check(deepcopy(grid)) or [])
                        if check_errors:
                            raise ValueError("self_check: " + "; ".join(check_errors))
                        expected = geometry_output(grid)
                        if expected == grid:
                            raise ValueError("intended rule is identity on generated input")
                        samples[key] = {
                            "input": grid,
                            "output": expected,
                            "input_sha256": _grid_sha256(grid),
                        }
                    except Exception as exc:
                        report["generated"]["failures"].append(
                            {
                                "band": _band_name(band),
                                "seed": seed,
                                "sample_index": sample_index,
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )
                windows.append({"band": band, "seed": seed, "start": start, "keys": keys})

    report["generated"]["samples"] = len(samples)
    report["generated"]["unique_inputs"] = len(
        {sample["input_sha256"] for sample in samples.values()}
    )

    if verify_racket and samples:
        ordered_keys = sorted(samples, key=lambda key: (_band_name(key[0]), key[1], key[2]))
        grids = [samples[key]["input"] for key in ordered_keys]
        try:
            actual = racket_outputs(grids)
            expected = [samples[key]["output"] for key in ordered_keys]
            report["racket"].update(
                {"cases": len(grids), "matches": actual == expected}
            )
            if actual != expected:
                for key, oracle_output, racket_output in zip(ordered_keys, expected, actual):
                    if oracle_output != racket_output:
                        report["errors"].append(
                            "Racket parity mismatch at "
                            f"band={_band_name(key[0])} seed={key[1]} sample_index={key[2]}"
                        )
                        break
        except Exception as exc:
            report["racket"].update(
                {"cases": len(grids), "matches": False, "error": f"{type(exc).__name__}: {exc}"}
            )
            report["errors"].append("Racket parity execution failed")

    for key, sample in samples.items():
        band, seed, sample_index = key
        for name, rival_solver in sorted(rivals.items()):
            try:
                rival = _call_solver(rival_solver, sample["input"])
            except Exception as exc:
                report["errors"].append(
                    f"rival {name!r} failed at {_band_name(band)}/{seed}/{sample_index}: "
                    f"{type(exc).__name__}: {exc}"
                )
                continue
            if rival != sample["output"]:
                report["generated"]["counterexamples"][name] += 1
                report["generated"]["first_counterexample"].setdefault(
                    name,
                    _counterexample_record(
                        band=band,
                        seed=seed,
                        sample_index=sample_index,
                        grid=sample["input"],
                        expected=sample["output"],
                        rival=rival,
                    ),
                )

    for window in windows:
        if any(key not in samples for key in window["keys"]):
            continue
        pairs = [samples[key] for key in window["keys"]]
        report["lessons"]["windows"] += 1
        for query_index in range(len(pairs)):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            report["lessons"]["query_rotations"] += 1
            direct_reasons = []
            for name, rival_solver in sorted(rivals.items()):
                fits_demos = all(
                    _call_solver(rival_solver, pair["input"]) == pair["output"]
                    for pair in demos
                )
                changes_query = (
                    _call_solver(rival_solver, query["input"]) != query["output"]
                )
                if fits_demos and changes_query:
                    direct_reasons.append(name)
            if direct_reasons:
                report["lessons"]["ambiguous_rotations"].append(
                    {
                        "band": _band_name(window["band"]),
                        "seed": window["seed"],
                        "start": window["start"],
                        "query_index": query_index,
                        "rivals": direct_reasons,
                        "query_input_sha256": query["input_sha256"],
                    }
                )
            hook = getattr(gen, "lesson_identifiable", None)
            if callable(hook):
                hook_reasons = list(
                    hook(
                        [
                            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                            for pair in demos
                        ],
                        {"input": deepcopy(query["input"]), "output": deepcopy(query["output"])},
                    )
                    or []
                )
                if bool(hook_reasons) != bool(direct_reasons):
                    report["lessons"]["hook_disagreements"].append(
                        {
                            "band": _band_name(window["band"]),
                            "seed": window["seed"],
                            "start": window["start"],
                            "query_index": query_index,
                            "direct_rivals": direct_reasons,
                            "hook_reasons": hook_reasons,
                        }
                    )

    for name, count in report["generated"]["counterexamples"].items():
        if count == 0:
            report["errors"].append(f"no generated counterexample found for rival {name!r}")
    if report["generated"]["failures"]:
        report["errors"].append("one or more generated samples failed validation")
    if report["lessons"]["ambiguous_rotations"]:
        report["errors"].append("a declared rival survives at least one rotated lesson")
    if report["lessons"]["hook_disagreements"]:
        report["errors"].append("lesson_identifiable disagrees with direct rival scoring")
    if verify_racket and report["racket"]["matches"] is not True:
        report["errors"].append("Racket parity was required but did not pass")

    report["status"] = "pass" if not report["errors"] else "fail"
    return report


def _parse_band(value: str) -> str | None:
    return None if value == "default" else value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--start", type=int, action="append", dest="starts")
    parser.add_argument(
        "--band",
        action="append",
        choices=("default", "easy", "medium", "hard"),
        dest="bands",
    )
    parser.add_argument("--racket", action="store_true", help="require selected-authority parity")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    generator_path = args.generator or os.environ.get("GENERATOR_UNDER_TEST")
    gen = load_generator(generator_path)
    report = build_report(
        gen,
        seeds=args.seeds or [195, 991],
        starts=args.starts or list(range(12)),
        bands=[_parse_band(value) for value in (args.bands or ["default", "easy", "medium", "hard"])],
        verify_racket=args.racket,
    )
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(serialized, encoding="utf-8")
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "out": str(args.out),
                    "samples": report["generated"]["samples"],
                    "windows": report["lessons"]["windows"],
                    "query_rotations": report["lessons"]["query_rotations"],
                },
                sort_keys=True,
            )
        )
    else:
        print(serialized, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
