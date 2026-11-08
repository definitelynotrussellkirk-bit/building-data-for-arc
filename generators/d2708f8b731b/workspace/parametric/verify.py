#!/usr/bin/env python3
"""Protected-Racket verification for the proposed prototype-rotation family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

import prototype

HERE = Path(__file__).resolve().parent


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _execute(programs: dict[str, str], inputs: list[list[list[int]]]):
    with RacketBridge() as bridge:
        rules = {}
        for index, (name, source) in enumerate(programs.items()):
            symbol = f"__prototype_rotation_rule_{index}"
            bridge.eval_text(f"(define {symbol} {wrap_rule(source)})")
            rules[name] = symbol
        grids = []
        for index, grid in enumerate(inputs):
            symbol = f"__prototype_rotation_input_{index}"
            bridge.define_grid(symbol, grid)
            grids.append(symbol)
        return {
            name: [bridge.eval_text(f"({symbol} {grid})") for grid in grids]
            for name, symbol in rules.items()
        }


def verify(out_dir: Path, seed: int = 20261024) -> dict[str, Any]:
    if out_dir.exists():
        raise FileExistsError(out_dir)
    settings = [{prototype.PARAMETER_NAME: value} for value in prototype.SETTINGS]
    episodes = [prototype.generate(seed, setting, 3, 4) for setting in settings]
    inputs = [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]]
    if [pair["input"] for pair in episodes[1]["train"] + episodes[1]["test"]] != inputs:
        raise AssertionError("input sampling depends on hidden prototype_transform")
    programs = prototype.rival_programs(settings[0])
    matrix = _execute(programs, inputs)
    python_matrix = {
        name: [prototype.rival_outputs(grid)[name] for grid in inputs]
        for name in programs
    }
    for name in programs:
        if matrix[name] != python_matrix[name]:
            raise AssertionError(f"Racket/Python mismatch for {name}")

    public_payloads: dict[str, bytes] = {}
    records = []
    for episode in episodes:
        selected = episode["settings"][prototype.PARAMETER_NAME]
        expected = [pair["output"] for pair in episode["train"] + episode["test"]]
        if matrix[selected] != expected:
            raise AssertionError(f"selected Racket labels disagree for {selected}")
        rivals = {}
        for name in programs:
            if name == selected:
                continue
            demo_disagreements = [i for i in range(3) if matrix[name][i] != expected[i]]
            query_disagreements = [i for i in range(4) if matrix[name][3 + i] != expected[3 + i]]
            if not demo_disagreements or len(query_disagreements) != 4:
                raise AssertionError(f"retained lesson does not reject {name}")
            rivals[name] = {
                "demo_disagreement_indices": demo_disagreements,
                "query_disagreement_indices": query_disagreements,
            }
        reveal_ids = []
        for index in range(4):
            payload = prototype.visible_turn(episode, index)
            identifier = hashlib.sha256(payload).hexdigest()
            public_payloads[identifier] = payload
            reveal_ids.append(identifier)
        records.append({
            "settings": episode["settings"],
            "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest(),
            "certificate": episode["certificate"],
            "reveal_ids": reveal_ids,
            "rivals": rivals,
            "labels": expected,
        })

    adversarial = {}
    malformed = lambda: prototype.generate(seed, {prototype.PARAMETER_NAME: "mirror"}, 3, 4)
    tampered = copy.deepcopy(episodes[0])
    tampered["test"][0]["output"][0][0] = 9
    duplicate = copy.deepcopy(episodes[0])
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    for name, action in {
        "malformed_setting": malformed,
        "tampered_label": lambda: prototype.verify_episode(tampered),
        "duplicate_input": lambda: prototype.verify_episode(duplicate),
    }.items():
        try:
            action()
        except ValueError as error:
            adversarial[name] = {"rejected": True, "error": str(error)}
        else:
            raise AssertionError(f"adversarial case accepted: {name}")
    one = prototype.generate(seed, {prototype.PARAMETER_NAME: "identity"}, 3, 1)
    four = prototype.generate(seed, {prototype.PARAMETER_NAME: "identity"}, 3, 4)
    if prototype.visible_turn(one, 0) != prototype.visible_turn(four, 0):
        raise AssertionError("first public turn changes with query count")
    adversarial["query_prefix"] = {"identical": True}

    public_dir = out_dir / "public"
    public_dir.mkdir(parents=True)
    for identifier, payload in sorted(public_payloads.items()):
        if any(secret in payload for secret in (b"settings", b"program", b"prototype_transform")):
            raise AssertionError("public turn leaks private fields")
        (public_dir / f"{identifier}.json").write_bytes(payload)

    stress_grid = inputs[-1]
    stress = prototype.features(stress_grid)
    nonzero = {
        (r, c)
        for r, row in enumerate(stress_grid)
        for c, value in enumerate(row)
        if value != 0
    }
    neutral = {
        (r, c)
        for r, row in enumerate(stress_grid)
        for c, value in enumerate(row)
        if value == 1
    }
    private = {
        "schema": f"{prototype.TASK_ID}-prototype-rotation-parametric-racket-v1",
        "status": "passed",
        "reference": "proposed_parametric",
        "training_admitted": False,
        "seed": seed,
        "racket": {
            "backend": "RacketBridge",
            "protected": True,
            "programs": len(programs),
            "inputs": len(inputs),
            "evaluations": len(programs) * len(inputs),
        },
        "episodes": records,
        "adversarial": adversarial,
        "stress": {
            "shape": [len(stress_grid), len(stress_grid[0])],
            "prototypes": stress["n_prototypes"],
            "targets": stress["n_targets"],
            "neutral_cells": len(neutral),
            "nonzero_cells": len(nonzero),
            "touches_all_boundaries": all((
                any(r == 0 for r, _ in nonzero),
                any(r == 29 for r, _ in nonzero),
                any(c == 0 for _, c in nonzero),
                any(c == 29 for _, c in nonzero),
            )),
        },
        "source_sha256": {
            path.name: _sha(path)
            for path in (
                HERE / "prototype.py",
                HERE / "adapter.py",
                HERE / "promotion.json",
                HERE / "canonical.rkt",
                HERE / "quarter_turn.rkt",
            )
        },
        "limitations": [
            "Evidence covers two settings and three declared finite shortcuts at one retained seed.",
            "The complete four-orientation orbit is a bounded proposal grammar, not all possible legend shapes.",
            "The 30x30 grammar extends the separate proposal; canonical production remains 12..20 by 16..24.",
            "No variant is training-admitted by this receipt.",
        ],
    }
    _write_json(out_dir / "private-report.json", private)
    manifest = {
        "schema": f"{prototype.TASK_ID}-prototype-rotation-evidence-v1",
        "status": "passed",
        "public_files": len(public_payloads),
        "private_report": "private-report.json",
        "files": {
            path.relative_to(out_dir).as_posix(): {
                "sha256": _sha(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(out_dir.rglob("*"))
            if path.is_file()
        },
    }
    _write_json(out_dir / "manifest.json", manifest)
    return private


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE / "evidence" / "current")
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    report = verify(args.out, args.seed)
    print(json.dumps({
        "status": report["status"],
        "episodes": len(report["episodes"]),
        "racket_evaluations": report["racket"]["evaluations"],
        "evidence": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
