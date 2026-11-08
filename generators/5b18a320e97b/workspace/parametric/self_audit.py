#!/usr/bin/env python3
"""Protected-Racket audit for the native 5b18a320e97b read-direction family.

The audit exercises both settings, minimum/maximum demo counts, all four query
slots, matched inputs, prefix stability, finite authored rivals, the substantive
30x30 query, and one-query public projections.  It is finite evidence rather
than a universal identifiability claim.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
PROTOTYPE_PATH = HERE / "prototype.py"
DIRECTIONS = ("forward", "reverse")


def _load_prototype():
    name = "_audit_5b18a320e97b_" + hashlib.sha256(
        str(PROTOTYPE_PATH).encode()
    ).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def audit(output: Path, seeds: list[int]) -> dict[str, Any]:
    """Run the bounded audit and write a source-readable evidence directory."""
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    if (
        type(seeds) is not list
        or not seeds
        or len(seeds) != len(set(seeds))
        or any(type(seed) is not int or seed < 0 for seed in seeds)
    ):
        raise ValueError("seeds must be a nonempty list of distinct nonnegative integers")
    output.mkdir(parents=True)

    prototype = _load_prototype()
    programs = {
        direction: prototype.program({"read_direction": direction})
        for direction in DIRECTIONS
    }
    wrapped = {direction: wrap_rule(source) for direction, source in programs.items()}
    jobs: list[dict[str, Any]] = []
    public_rows: dict[str, bytes] = {}
    evaluations = 0

    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("self-audit requires protected Racket")

        def execute(direction: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal evaluations
            evaluations += 1
            return bridge.eval_text(
                f"({wrapped[direction]} {_grid_literal(grid)})"
            )

        for seed in seeds:
            generated: dict[tuple[int, str], dict[str, Any]] = {}
            for demos in (2, 6):
                for direction in DIRECTIONS:
                    settings = {"read_direction": direction}
                    episode = prototype.generate(seed, settings, demos, 4)
                    generated[(demos, direction)] = episode
                    for pair in episode["train"] + episode["test"]:
                        if execute(direction, pair["input"]) != pair["output"]:
                            raise AssertionError(
                                f"Racket label mismatch: {seed=} {demos=} {direction=}"
                            )
                    survivors = []
                    for candidate in DIRECTIONS:
                        predictions = [
                            execute(candidate, pair["input"])
                            for pair in episode["train"]
                        ]
                        if all(
                            prediction == pair["output"]
                            for prediction, pair in zip(
                                predictions, episode["train"], strict=True
                            )
                        ):
                            survivors.append(candidate)
                    if survivors != [direction]:
                        raise AssertionError(
                            f"demo-only finite survivors differ: {seed=} {demos=} "
                            f"{direction=} {survivors=}"
                        )
                    review = prototype.self_review(episode)
                    if review["survivors"] != [f"intended_{direction}"]:
                        raise AssertionError(
                            f"finite wrong-rule survivor: {seed=} {demos=} "
                            f"{direction=} {review=}"
                        )
                    stress = episode["test"][-1]["input"]
                    stress_nonzero = sum(cell != 0 for row in stress for cell in row)
                    if (len(stress), len(stress[0])) != (30, 30) or stress_nonzero < 120:
                        raise AssertionError("fourth query is not substantive 30x30 stress")
                    jobs.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "queries": 4,
                            "settings": settings,
                            "survivors": survivors,
                            "finite_self_review": review,
                            "stress_nonzero_cells": stress_nonzero,
                            "program_sha256": hashlib.sha256(
                                programs[direction].encode()
                            ).hexdigest(),
                        }
                    )

                if _inputs(generated[(demos, "forward")]) != _inputs(
                    generated[(demos, "reverse")]
                ):
                    raise AssertionError("settings changed the input stream")

            for direction in DIRECTIONS:
                short = generated[(2, direction)]
                long = generated[(6, direction)]
                one_query = prototype.generate(
                    seed, {"read_direction": direction}, 2, 1
                )
                if short["train"] != long["train"][:2]:
                    raise AssertionError("demonstration stream is not prefix stable")
                if short["test"] != long["test"]:
                    raise AssertionError("query stream changed with demo count")
                if one_query["test"] != short["test"][:1]:
                    raise AssertionError("query stream is not prefix stable")

                full = prototype.generate(
                    seed, {"read_direction": direction}, 3, 4
                )
                single = prototype.generate(
                    seed, {"read_direction": direction}, 3, 1
                )
                if prototype.public_view(full, 0) != prototype.public_view(single, 0):
                    raise AssertionError("first sequential turn differs from single-query use")
                for query_index in range(4):
                    visible = prototype.public_view(full, query_index)
                    body = public_challenge_bytes(visible)
                    identifier = public_challenge_id(visible)
                    previous = public_rows.setdefault(identifier, body)
                    if previous != body:
                        raise AssertionError("public content ID collision")

    public_files = []
    for identifier, body in sorted(public_rows.items()):
        path = output / "public" / f"{identifier}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        public_files.append(
            {
                "path": path.relative_to(output).as_posix(),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
        )

    report = {
        "schema": "arcpuzzles-5b18a320e97b-native-self-audit-v1",
        "status": "passed",
        "task_id": "5b18a320e97b",
        "scope": (
            "Finite settings forward/reverse; supplied seeds; demo boundaries 2/6; "
            "four queries; protected-Racket labels; finite authored wrong rules; "
            "matched inputs; prefix stability; one-query public projection; 30x30 stress."
        ),
        "jobs": jobs,
        "job_count": len(jobs),
        "racket_evaluations": evaluations,
        "racket": {
            key: identity[key]
            for key in (
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            )
            if key in identity
        },
        "programs": {
            direction: hashlib.sha256(source.encode()).hexdigest()
            for direction, source in programs.items()
        },
        "public_files": public_files,
        "public_file_count": len(public_files),
        "limits": (
            "Finite seeds and authored candidates only; no universal uniqueness, "
            "acceptance, measured-learning, or training-admission claim."
        ),
    }
    _write_json(output / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    args = parser.parse_args(argv)
    seeds = [0, 17] if args.seeds is None else args.seeds
    report = audit(args.out, seeds)
    print(
        json.dumps(
            {
                "status": report["status"],
                "jobs": report["job_count"],
                "racket_evaluations": report["racket_evaluations"],
                "public_files": report["public_file_count"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
