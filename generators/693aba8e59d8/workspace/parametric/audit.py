#!/usr/bin/env python3
"""Bounded protected-Racket audit for the bounding-box-area rotation family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

import prototype

HERE = Path(__file__).resolve().parent


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _grid_sha(grid: list[list[int]]) -> str:
    return _sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def _execute(programs: dict[str, str], grids: list[list[list[int]]]) -> tuple[dict[str, list], dict]:
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise AssertionError("audit requires protected Racket")
        symbols = {}
        for index, (name, source) in enumerate(programs.items()):
            symbol = f"__bbox_area_rule_{index}"
            bridge.eval_text(f"(define {symbol} {wrap_rule(source)})")
            symbols[name] = symbol
        inputs = []
        for index, grid in enumerate(grids):
            symbol = f"__bbox_area_input_{index}"
            bridge.define_grid(symbol, grid)
            inputs.append(symbol)
        matrix = {
            name: [bridge.eval_text(f"({symbol} {grid_symbol})") for grid_symbol in inputs]
            for name, symbol in symbols.items()
        }
    return matrix, identity


def audit(out_dir: Path, seeds: list[int]) -> dict[str, Any]:
    if out_dir.exists():
        raise FileExistsError(out_dir)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be a nonempty distinct list")

    settings = [{prototype.PARAMETER_NAME: value} for value in prototype.SETTINGS]
    programs = prototype.rival_programs()
    public_payloads: dict[str, bytes] = {}
    records = []
    evaluations = 0

    for seed in seeds:
        episodes = [prototype.generate(seed, setting, 2, 4) for setting in settings]
        grids = [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]]
        other_grids = [pair["input"] for pair in episodes[1]["train"] + episodes[1]["test"]]
        if grids != other_grids:
            raise AssertionError("input sampling depends on the private setting")

        racket_matrix, identity = _execute(programs, grids)
        evaluations += len(programs) * len(grids)
        python_matrix = {
            name: [prototype.rival_outputs(grid)[name] for grid in grids]
            for name in programs
        }
        if racket_matrix != python_matrix:
            mismatches = [name for name in programs if racket_matrix[name] != python_matrix[name]]
            raise AssertionError(f"Racket/Python mismatch for {mismatches}")

        for episode in episodes:
            chosen = episode["settings"][prototype.PARAMETER_NAME]
            expected = [pair["output"] for pair in episode["train"] + episode["test"]]
            if racket_matrix[chosen] != expected:
                raise AssertionError(f"selected Racket labels differ for {chosen}")
            rival_rows = {}
            survivors = []
            for name in programs:
                demo_disagreements = [
                    index for index in range(2) if racket_matrix[name][index] != expected[index]
                ]
                query_disagreements = [
                    index for index in range(4)
                    if racket_matrix[name][2 + index] != expected[2 + index]
                ]
                if not demo_disagreements:
                    survivors.append(name)
                rival_rows[name] = {
                    "demo_disagreement_indices": demo_disagreements,
                    "query_disagreement_indices": query_disagreements,
                }
            if survivors != [chosen]:
                raise AssertionError(f"demonstrations leave survivors {survivors}, wanted {chosen}")

            reveal_ids = []
            for index in range(4):
                payload = prototype.visible_turn(episode, index)
                visible = json.loads(payload)
                if visible["test"] != [{"input": episode["test"][index]["input"]}]:
                    raise AssertionError("public turn contains a future query or answer")
                if any(secret in payload for secret in (b"settings", b"program_solution", b"rotation_rule")):
                    raise AssertionError("public turn leaks private metadata")
                identifier = _sha_bytes(payload)
                previous = public_payloads.setdefault(identifier, payload)
                if previous != payload:
                    raise AssertionError("public identifier collision")
                reveal_ids.append(identifier)

            records.append({
                "seed": seed,
                "settings": episode["settings"],
                "program_sha256": _sha_bytes(episode["program_solution"].encode()),
                "certificate": episode["certificate"],
                "survivors": survivors,
                "rivals": rival_rows,
                "input_sha256": [_grid_sha(grid) for grid in grids],
                "output_sha256": [_grid_sha(grid) for grid in expected],
                "public_ids": reveal_ids,
            })

    # Exercise every declared count while checking that the first public turn is
    # invariant to the private total query count.
    count_checks = 0
    for seed in seeds:
        full = prototype.generate(seed, settings[0], 6, 4)
        for demos in range(2, 7):
            for queries in range(1, 5):
                episode = prototype.generate(seed, settings[0], demos, queries)
                if episode["train"] != full["train"][:demos] or episode["test"] != full["test"][:queries]:
                    raise AssertionError("requested counts are not prefix stable")
                count_checks += 1
        one = prototype.generate(seed, settings[0], 2, 1)
        four = prototype.generate(seed, settings[0], 2, 4)
        if prototype.visible_turn(one, 0) != prototype.visible_turn(four, 0):
            raise AssertionError("first public turn leaks the total query count")

    # Verifier rejection paths.
    bad_setting = {prototype.PARAMETER_NAME: "unknown"}
    tampered = prototype.generate(seeds[0], settings[0], 2, 4)
    tampered["test"][0]["output"][0][0] = 7
    duplicate = prototype.generate(seeds[0], settings[0], 2, 4)
    duplicate["test"][0] = deepcopy(duplicate["train"][0])
    rejected = {}
    for name, action in {
        "unknown_setting": lambda: prototype.generate(seeds[0], bad_setting, 2, 4),
        "tampered_label": lambda: prototype.verify_episode(tampered),
        "duplicate_input": lambda: prototype.verify_episode(duplicate),
    }.items():
        try:
            action()
        except ValueError as error:
            rejected[name] = str(error)
        else:
            raise AssertionError(f"verifier accepted {name}")

    public_dir = out_dir / "public"
    public_dir.mkdir(parents=True)
    for identifier, payload in sorted(public_payloads.items()):
        (public_dir / f"{identifier}.json").write_bytes(payload)

    stress_episode = prototype.generate(seeds[-1], settings[1], 2, 4)
    stress_grid = stress_episode["test"][3]["input"]
    stress_facts = prototype.features(stress_grid)
    stress_nonzero = sum(value != 0 for row in stress_grid for value in row)
    report = {
        "schema": f"{prototype.TASK_ID}-bbox-area-parametric-audit-v1",
        "status": "passed",
        "reference": "proposed_parametric",
        "training_admitted": False,
        "seeds": seeds,
        "settings": settings,
        "programs": {
            name: _sha_bytes(source.encode()) for name, source in programs.items()
        },
        "racket": {
            "identity": identity,
            "programs": len(programs),
            "inputs_per_seed": 6,
            "evaluations": evaluations,
        },
        "records": records,
        "count_checks": count_checks,
        "rejected_inputs": rejected,
        "stress": {
            "shape": [len(stress_grid), len(stress_grid[0])],
            "nonzero_cells": stress_nonzero,
            "base_cell_count": stress_facts["base_cell_count"],
            "bbox_area": stress_facts["bbox_area"],
            "bbox_area_offset": stress_facts["bbox_area_offset"],
            "touches_all_boundaries": all((
                any(stress_grid[0]),
                any(stress_grid[-1]),
                any(row[0] for row in stress_grid),
                any(row[-1] for row in stress_grid),
            )),
            "input_sha256": _grid_sha(stress_grid),
            "output_sha256": _grid_sha(stress_episode["test"][3]["output"]),
        },
        "public_files": len(public_payloads),
        "source_sha256": {
            path.name: _sha_file(path)
            for path in (
                HERE / "prototype.py",
                HERE / "adapter.py",
                HERE / "promotion.json",
                HERE / "canonical.rkt",
                HERE / "bbox_area_offset.rkt",
                HERE / "audit.py",
            )
        },
        "limits": [
            "Finite audit of two admitted settings and eight declared shortcut programs.",
            "Protected Racket coverage uses two retained seeds, two demonstrations, and four queries.",
            "No universal uniqueness, owner acceptance, or training admission is claimed.",
        ],
    }
    _write(out_dir / "audit.json", report)
    _write(out_dir / "manifest.json", {
        "schema": f"{prototype.TASK_ID}-bbox-area-parametric-evidence-v1",
        "status": "passed",
        "report": "audit.json",
        "public_files": len(public_payloads),
        "files": {
            path.relative_to(out_dir).as_posix(): {
                "sha256": _sha_file(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(out_dir.rglob("*")) if path.is_file()
        },
    })
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    args = parser.parse_args()
    report = audit(args.out, args.seeds or [0, 17])
    print(json.dumps({
        "status": report["status"],
        "racket_evaluations": report["racket"]["evaluations"],
        "records": len(report["records"]),
        "public_files": report["public_files"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
