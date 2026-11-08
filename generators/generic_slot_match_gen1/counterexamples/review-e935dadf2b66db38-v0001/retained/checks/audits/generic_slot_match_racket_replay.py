#!/usr/bin/env python3
"""Execute one generic-slot PROGRAM on a retained generated input in Racket."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "repo/generators/generic_slot_match_gen1/generator.py"
CASE = ROOT / "checks/audits/generic_slot_match_gen1"


def sha_json(value) -> str:
    payload = json.dumps(value, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def program_body(program: str) -> str:
    marker = "(lambda (g)"
    start = program.index(marker) + len(marker)
    depth = 1
    end = start
    while end < len(program) and depth:
        if program[end] == "(":
            depth += 1
        elif program[end] == ")":
            depth -= 1
        end += 1
    if depth:
        raise ValueError("unbalanced PROGRAM")
    return program[start:end - 1].strip()


def main() -> int:
    spec = importlib.util.spec_from_file_location("slot_match_racket_replay", GENERATOR)
    assert spec is not None and spec.loader is not None
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    grid = json.loads((CASE / "input.json").read_text())
    official = json.loads((CASE / "official_output.json").read_text())
    rival = json.loads((CASE / "rival_output.json").read_text())
    body = program_body(gen.PROGRAM)

    bridge = RacketBridge()
    bridge.define_grid("g", grid)
    actual = bridge.eval_text(body)
    differing = [
        [row, col, official[row][col], rival[row][col]]
        for row in range(len(official))
        for col in range(len(official[0]))
        if official[row][col] != rival[row][col]
    ]
    report = {
        "schema": "generic-slot-match-racket-replay-v1",
        "task_id": gen.TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "program_sha256": hashlib.sha256(gen.PROGRAM.encode()).hexdigest(),
        "provenance": {
            "seed": 46,
            "difficulty": "easy",
            "pair": "test[1]",
            "belongs_to_generated_domain": True,
            "separate_input_validator": False,
        },
        "command": [
            "python3", "run_with_racket.py", "python3",
            "../checks/audits/generic_slot_match_racket_replay.py",
        ],
        "cwd": "packet_root",
        "input_sha256": sha_json(grid),
        "racket_output_sha256": sha_json(actual),
        "official_output_sha256": sha_json(official),
        "rival_output_sha256": sha_json(rival),
        "racket_matches_official": actual == official,
        "racket_matches_rival": actual == rival,
        "official_rival_differences": differing,
        "input": grid,
        "racket_output": actual,
        "rival_output": rival,
    }
    (CASE / "racket.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in (
        "generator_sha256", "program_sha256", "racket_matches_official",
        "racket_matches_rival", "official_rival_differences")}, indent=2))
    return 0 if actual == official and actual != rival else 1


if __name__ == "__main__":
    raise SystemExit(main())
