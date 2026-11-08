#!/usr/bin/env python3
"""Replay a generic lesson generator's stored outputs through its Racket rule."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import purity_body, rule_application


GENERIC_ROOT = ROOT / "puzzle_generators" / "generic" / "concepts"


def _generic_path(task_id: str) -> Path:
    if not task_id.startswith("generic_"):
        raise ValueError(f"not a generic task id: {task_id}")
    family, separator, generator = task_id[len("generic_"):].rpartition("_")
    if (
        not separator
        or not family
        or not generator.startswith("gen")
    ):
        raise ValueError(
            "generic task id must look like generic_<family>_genN: "
            f"{task_id}"
        )
    return GENERIC_ROOT / family / f"{generator}.py"


def _load(task_id: str):
    path = _generic_path(task_id)
    if not path.exists():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(
        f"generic_parity_{task_id}", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid(value: Any) -> bool:
    return bool(
        isinstance(value, list)
        and value
        and all(
            isinstance(row, list)
            and row
            and all(
                isinstance(cell, int)
                and not isinstance(cell, bool)
                and 0 <= cell <= 9
                for cell in row
            )
            for row in value
        )
        and len({len(row) for row in value}) == 1
    )


def _rule_source(program: str) -> str:
    """Normalize the two generic program schemas to an executable rule."""
    stripped = program.strip()
    if stripped.startswith("(rule!"):
        return stripped
    return f"(rule! (lambda (g) {stripped}))"


def check_task(
    task_id: str,
    *,
    seeds: int = 10,
    bands: tuple[str, ...] = ("easy", "medium", "hard"),
) -> tuple[bool, str]:
    module = _load(task_id)
    generate_task = getattr(module, "generate_task", None)
    if not callable(generate_task):
        return False, "missing generate_task(seed, *, difficulty=...)"

    bridge = RacketBridge(max_calls_before_restart=48)
    total = 0
    exact = 0
    programs: set[str] = set()
    first_failure = ""
    probes: dict[
        str,
        tuple[list[list[int]], list[list[int]]],
    ] = {}
    purity_checked: set[str] = set()
    try:
        for band in bands:
            for seed in range(seeds):
                try:
                    task = generate_task(seed, difficulty=band)
                except Exception as exc:
                    return (
                        False,
                        f"generate_task crashed at {band}/{seed}: "
                        f"{type(exc).__name__}: {exc}",
                    )
                if not isinstance(task, dict):
                    return False, f"{band}/{seed}: task is not a dict"
                program = task.get("program")
                if not isinstance(program, str) or not program.strip():
                    return False, f"{band}/{seed}: missing Racket program"
                rule = _rule_source(program)
                programs.add(rule)
                pairs = list(task.get("train") or []) + list(
                    task.get("test") or []
                )
                if not pairs:
                    return False, f"{band}/{seed}: lesson has no pairs"
                for pair_index, pair in enumerate(pairs):
                    if not isinstance(pair, dict):
                        return (
                            False,
                            f"{band}/{seed}/{pair_index}: pair is not a dict",
                        )
                    input_grid = pair.get("input")
                    expected = pair.get("output")
                    if not _grid(input_grid) or not _grid(expected):
                        return (
                            False,
                            f"{band}/{seed}/{pair_index}: invalid input/output "
                            "grid",
                        )
                    total += 1
                    try:
                        actual = bridge.eval_text(
                            rule_application(rule, input_grid)
                        )
                    except Exception as exc:
                        return (
                            False,
                            f"Racket crash at {band}/{seed}/{pair_index}: "
                            f"{type(exc).__name__}: {exc}",
                        )
                    if actual == expected:
                        exact += 1
                    elif not first_failure:
                        first_failure = (
                            f"{band}/{seed}/{pair_index}: stored output differs"
                        )

                    if rule not in probes:
                        probes[rule] = (
                            copy.deepcopy(input_grid),
                            copy.deepcopy(expected),
                        )
                    elif (
                        rule not in purity_checked
                        and input_grid != probes[rule][0]
                    ):
                        probe_input, probe_output = probes[rule]
                        try:
                            result = bridge.eval_text(
                                purity_body(rule, probe_input, input_grid)
                            )
                        except Exception as exc:
                            return (
                                False,
                                "Racket A→B→A probe crashed: "
                                f"{type(exc).__name__}: {exc}",
                            )
                        if not isinstance(result, list) or len(result) != 3:
                            return False, "Racket A→B→A probe returned bad shape"
                        first, replay, input_after = result
                        if input_after != probe_input:
                            return False, "INPUT_MUTATION in generic Racket rule"
                        if first != probe_output or replay != probe_output:
                            return False, "STATEFUL generic Racket rule"
                        purity_checked.add(rule)
    finally:
        bridge.shutdown()

    unchecked = programs - purity_checked
    if unchecked:
        return (
            False,
            "could not obtain two distinct inputs for A→B→A probe on "
            f"{len(unchecked)}/{len(programs)} sampled program variants",
        )
    if exact != total:
        return (
            False,
            f"PARITY FAIL {exact}/{total} exact; first {first_failure}",
        )
    return (
        True,
        f"PARITY PASS {exact}/{total} exact across {len(programs)} program "
        "variant(s); A→B→A/input purity PASS",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--bands", default="easy,medium,hard")
    args = parser.parse_args()
    bands = tuple(
        band.strip() for band in args.bands.split(",") if band.strip()
    )
    if args.seeds < 1 or not bands:
        parser.error("--seeds must be positive and --bands must be nonempty")
    try:
        passed, detail = check_task(
            args.task_id,
            seeds=args.seeds,
            bands=bands,
        )
    except Exception as exc:
        passed = False
        detail = f"{type(exc).__name__}: {exc}"
    print(f"{args.task_id}: {detail}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
