#!/usr/bin/env python3
"""Reusable bounded audit for the 165ab20d8b6b native neighborhood family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "165ab20d8b6b"
HERE = Path(__file__).resolve().parent


def load_prototype():
    path = HERE / "prototype.py"
    name = "_audit_165ab_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def episode_inputs(episode: dict[str, Any]) -> list[Any]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def run(out: Path) -> dict[str, Any]:
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    root = find_root(__file__)
    module = load_prototype()
    contract = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
    jobs = [
        {"seed": seed, "settings": setting, "demos": demos, "queries": 4}
        for setting in module.SETTINGS
        for seed in (0, 17)
        for demos in (2, 6)
    ]
    racket = evaluate_contract(root, TASK_ID, contract, jobs)

    prefix_checks = 0
    matched_input_checks = 0
    self_reviews = []
    stress_rows = []
    for seed in range(64):
        by_setting = {}
        for setting in module.SETTINGS:
            short = module.generate(seed, setting, 2, 1)
            long = module.generate(seed, setting, 6, 4)
            if short["train"] != long["train"][:2] or short["test"] != long["test"][:1]:
                raise AssertionError("count prefix instability")
            prefix_checks += 1
            review = module.self_review(module.generate(seed, setting, 2, 4))
            if review["harmful_survivors"] or review["intended_survivors"] != [setting["neighborhood"]]:
                raise AssertionError(review)
            self_reviews.append(review)
            by_setting[setting["neighborhood"]] = long
            grid = long["test"][3]["input"]
            output = long["test"][3]["output"]
            foreground = sum(cell != 0 for row in grid for cell in row)
            output_cells = sum(cell != 0 for row in output for cell in row)
            if (len(grid), len(grid[0])) != (30, 30) or foreground < 100 or output_cells < 70:
                raise AssertionError("substantive 30x30 stress floor failed")
            if not module.has_enclosed_shell_cell(grid):
                raise AssertionError("30x30 scene lost enclosed-shell topology")
            stress_rows.append(
                {
                    "seed": seed,
                    "setting": setting,
                    "shape": [len(grid), len(grid[0])],
                    "foreground_cells": foreground,
                    "output_cells": output_cells,
                    "colors": sorted({cell for row in grid for cell in row if cell}),
                    "boundary_contacts": {
                        "top": any(grid[0][column] != 0 for column in range(len(grid[0]))),
                        "bottom": any(grid[-1][column] != 0 for column in range(len(grid[0]))),
                        "left": any(row[0] != 0 for row in grid),
                        "right": any(row[-1] != 0 for row in grid),
                    },
                }
            )
        if episode_inputs(by_setting["cardinal"]) != episode_inputs(by_setting["moore"]):
            raise AssertionError("settings changed generated inputs")
        matched_input_checks += 1

    public_rows = []
    public_dir = out / "public"
    public_dir.mkdir()
    for setting in module.SETTINGS:
        for seed in (0, 17):
            episode = module.generate(seed, setting, 2, 4)
            for query_index in range(4):
                challenge = module.public_challenge(episode, query_index)
                body = public_challenge_bytes(challenge)
                identifier = public_challenge_id(challenge)
                path = public_dir / f"{identifier}.json"
                if path.exists() and path.read_bytes() != body:
                    raise AssertionError("public identifier collision")
                path.write_bytes(body)
                public_rows.append(
                    {
                        "id": identifier,
                        "path": path.relative_to(out).as_posix(),
                        "seed": seed,
                        "settings": setting,
                        "query_index": query_index,
                    }
                )
    if len({row["id"] for row in public_rows}) != len(public_rows):
        raise AssertionError("duplicate public challenge bytes")

    report = {
        "schema": "165ab20d8b6b-parametric-self-audit-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "jobs": jobs,
        "racket": racket["racket"],
        "racket_evaluations": racket["racket_evaluations"],
        "qualification_like_checks": racket["checks"],
        "python_stress": {
            "seeds": 64,
            "episodes": 128,
            "prefix_checks": prefix_checks,
            "matched_input_checks": matched_input_checks,
            "finite_candidate_reviews": len(self_reviews),
            "harmful_survivors": 0,
        },
        "stress_30x30": stress_rows,
        "public_exports": public_rows,
        "limits": "Finite declared candidates and seeds only; not universal identifiability or measured model gain.",
    }
    write_json(out / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.out.resolve())
    print(
        json.dumps(
            {
                "status": report["status"],
                "racket_evaluations": report["racket_evaluations"],
                "stress_episodes": report["python_stress"]["episodes"],
                "public_exports": len(report["public_exports"]),
                "report": str(args.out.resolve() / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
