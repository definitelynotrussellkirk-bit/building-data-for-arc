#!/usr/bin/env python3
"""Protected-Racket audit for the native connectivity family.

This is reusable authoring evidence, not acceptance. It checks the declared
finite settings, independent count boundaries, matched inputs, prefix stability,
finite shortcut review, a substantive 30x30 query, and exact one-query public
projection.
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


def _load_prototype():
    name = "_eefadafb2b7b_self_audit_" + hashlib.sha256(
        str(PROTOTYPE_PATH).encode()
    ).hexdigest()
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


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(output: Path, seeds: list[int]) -> dict[str, Any]:
    prototype = _load_prototype()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)

    programs = {
        connectivity: prototype.program({"connectivity": connectivity})
        for connectivity in (8, 4)
    }
    wrapped = {key: wrap_rule(value) for key, value in programs.items()}
    jobs = []
    evaluations = 0

    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("audit requires protected Racket")

        def execute(connectivity: int, grid: list[list[int]]) -> list[list[int]]:
            nonlocal evaluations
            evaluations += 1
            return bridge.eval_text(
                f"({wrapped[connectivity]} {_grid_literal(grid)})"
            )

        for seed in seeds:
            generated: dict[tuple[int, int], dict[str, Any]] = {}
            for demos in (2, 6):
                for connectivity in (8, 4):
                    settings = {"connectivity": connectivity}
                    episode = prototype.generate(seed, settings, demos, 4)
                    generated[(demos, connectivity)] = episode
                    selected_labels = []
                    for pair in episode["train"] + episode["test"]:
                        observed = execute(connectivity, pair["input"])
                        if observed != pair["output"]:
                            raise AssertionError(
                                f"Racket label mismatch seed={seed} demos={demos} "
                                f"connectivity={connectivity}"
                            )
                        selected_labels.append(observed)

                    survivors = []
                    for candidate in (8, 4):
                        candidate_outputs = [
                            execute(candidate, pair["input"])
                            for pair in episode["train"]
                        ]
                        if all(
                            observed == pair["output"]
                            for observed, pair in zip(candidate_outputs, episode["train"])
                        ):
                            survivors.append(candidate)
                    if survivors != [connectivity]:
                        raise AssertionError(
                            f"demo-only survivors differ: {seed=} {demos=} "
                            f"{connectivity=} {survivors=}"
                        )
                    review = prototype.self_review(episode)
                    if review["harmful_survivors"]:
                        raise AssertionError(
                            f"finite harmful survivor: {seed=} {demos=} "
                            f"{connectivity=} {review['harmful_survivors']}"
                        )
                    stress = episode["test"][-1]["input"]
                    stress_nonzero = sum(cell != 0 for row in stress for cell in row)
                    if (len(stress), len(stress[0])) != (30, 30) or stress_nonzero < 90:
                        raise AssertionError("30x30 stress query is not substantive")
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
                                programs[connectivity].encode()
                            ).hexdigest(),
                        }
                    )

                left = generated[(demos, 8)]
                right = generated[(demos, 4)]
                left_inputs = [p["input"] for p in left["train"] + left["test"]]
                right_inputs = [p["input"] for p in right["train"] + right["test"]]
                if left_inputs != right_inputs:
                    raise AssertionError("settings changed the input stream")

            for connectivity in (8, 4):
                short = generated[(2, connectivity)]
                long = generated[(6, connectivity)]
                if short["train"] != long["train"][:2] or short["test"] != long["test"]:
                    raise AssertionError("demo/query streams are not prefix stable")

            # Three demos are the qualification/default teaching count. Save one
            # query per public file, with no future-query or total-count hint.
            for connectivity in (8, 4):
                settings = {"connectivity": connectivity}
                episode = prototype.generate(seed, settings, 3, 4)
                first_only = prototype.generate(seed, settings, 3, 1)
                for index, query in enumerate(episode["test"]):
                    turn = {"train": episode["train"], "test": [query]}
                    body = public_challenge_bytes(turn)
                    identifier = public_challenge_id(turn)
                    path = output / "public" / f"{identifier}.json"
                    if path.exists() and path.read_bytes() != body:
                        raise AssertionError("public ID collision")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(body)
                    if index == 0 and body != public_challenge_bytes(first_only):
                        raise AssertionError(
                            "first sequential turn differs from single-query use"
                        )

    public_files = sorted((output / "public").glob("*.json"))
    report = {
        "schema": "eefadafb2b7b-native-self-audit-v1",
        "status": "passed",
        "scope": (
            "Finite settings {8,4}, seeds 0/17 by default, demo boundaries 2/6, "
            "four queries, protected-Racket labels, finite candidate shortcuts, "
            "matched inputs, prefix stability, public projection, and 30x30 stress."
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
            str(key): hashlib.sha256(value.encode()).hexdigest()
            for key, value in programs.items()
        },
        "public_files": [
            {
                "path": path.relative_to(output).as_posix(),
                "sha256": _hash_file(path),
                "bytes": path.stat().st_size,
            }
            for path in public_files
        ],
        "public_file_count": len(public_files),
        "limits": "Finite tested rivals and seeds only; not a universal uniqueness proof or acceptance.",
    }
    _write(output / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    args = parser.parse_args(argv)
    seeds = [0, 17] if args.seeds is None else args.seeds
    if len(seeds) != len(set(seeds)) or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("seeds must be distinct nonnegative integers")
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
