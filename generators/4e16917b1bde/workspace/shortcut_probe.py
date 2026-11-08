#!/usr/bin/env python3
"""Reproduce the canonical-fitting rare-color shortcut counterexample."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "4e16917b1bde"
RIVAL_NAME = "mirror only colors within one count of the modal color"
TASK_DIR = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def _load_generator():
    """Load the selected source directly in both repo and copied runtimes."""
    source = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"task_generator_{TASK_ID}", source
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _generator_path() -> Path:
    candidates = (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("generator.py not found under portable root")


def _read_grid() -> list[list[int]]:
    payload = json.loads(
        (TASK_DIR / "counterexamples" / "rare-color-input.json").read_text()
    )
    return payload["input"]


def _read_racket_output() -> tuple[list[list[int]], dict]:
    receipt = json.loads(
        (TASK_DIR / "counterexamples" / "rare-color-racket.json").read_text()
    )
    return receipt["results"][0]["output"], receipt


def build_report() -> dict:
    grid = _read_grid()
    intended, receipt = _read_racket_output()
    rival = GEN.SEMANTIC_RIVALS[RIVAL_NAME]
    rival_output = rival(grid)
    python_output = GEN.rule_mirror(grid)
    canonical = canonical_pairs(TASK_ID, root=ROOT)
    canonical_fit = [rival(pair["input"]) == pair["output"] for pair in canonical]
    differing_cells = [
        [row, col]
        for row in range(len(intended))
        for col in range(len(intended[0]))
        if intended[row][col] != rival_output[row][col]
    ]

    assert GEN.self_check(grid) == []
    assert receipt["executed_rule_hash"] == GEN.RULE_HASH
    assert python_output == intended
    assert all(canonical_fit)
    assert differing_cells
    assert GEN.SEMANTIC_WITNESSES["strong_color_frequency_skew"](grid)

    generator_path = _generator_path()
    return {
        "schema": "arcpuzzles-task-shortcut-counterexample-v1",
        "task_id": TASK_ID,
        "generator_version": GEN.VERSION,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_hash": GEN.RULE_HASH,
        "rival": RIVAL_NAME,
        "canonical_pairs_fit": sum(canonical_fit),
        "canonical_pairs_total": len(canonical_fit),
        "input_is_generator_lawful": True,
        "generated_witness": "strong_color_frequency_skew",
        "input": grid,
        "intended_racket_output": intended,
        "rival_output": rival_output,
        "differing_cells_zero_based": differing_cells,
        "racket_receipt": "counterexamples/rare-color-racket.json",
        "reproduce": {
            "cwd": "repo",
            "argv": [
                "python3",
                "generators/4e16917b1bde/workspace/shortcut_probe.py",
                "--out",
                "generators/4e16917b1bde/counterexamples/rare-color-shortcut.json",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report()
    rendered = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
