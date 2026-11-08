#!/usr/bin/env python3
"""Produce a source-bound, minimal override-contract counterexample for ca5dcbac0e83."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "ca5dcbac0e83"
RULE_HASH = "901c6a6fb4b5"  # canonical authority index in this packet


def load_generator(path: Path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}_{digest[:12]}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, digest


def colors(grid):
    return sorted({value for row in grid for value in row if value != 0})


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    generator_path = root / "repo" / "generators" / TASK_ID / "generator.py"
    gen, digest = load_generator(generator_path)

    witness = None
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(100):
            for sample_index in range(4):
                grid3 = gen.generate(seed, sample_index, difficulty=difficulty, palette_size=3)
                grid4 = gen.generate(seed, sample_index, difficulty=difficulty, palette_size=4)
                if grid3 == grid4 and len(colors(grid3)) == 4:
                    witness = {
                        "difficulty": difficulty,
                        "seed": seed,
                        "sample_index": sample_index,
                        "palette_size_3_grid": grid3,
                        "palette_size_4_grid": grid4,
                        "realized_endpoint_colors": colors(grid3),
                        "palette_size_3_self_check": gen.self_check(grid3, difficulty=difficulty),
                    }
                    break
            if witness:
                break
        if witness:
            break
    if witness is None:
        raise RuntimeError("did not find the expected ignored palette_size witness")

    unknown_grid = gen.generate(
        witness["seed"],
        witness["sample_index"],
        difficulty=witness["difficulty"],
        __override_contract_unknown_axis__="typo",
    )
    declared_rejection = None
    try:
        gen.generate(0, 0, difficulty="easy", grid_h=7)
    except Exception as exc:  # evidence captures the target's public failure surface
        declared_rejection = {"type": type(exc).__name__, "message": str(exc)}

    output = {
        "schema": "arc-audit-override-counterexample-v1",
        "classification": "reproduced override-contract defect; not a rule-semantic counterexample",
        "task_id": TASK_ID,
        "generator_path": "repo/generators/ca5dcbac0e83/generator.py",
        "generator_sha256": digest,
        "rule_hash": RULE_HASH,
        "command": {
            "cwd": "packet_root",
            "argv": [
                "env",
                "PYTHONPATH=repo/shared/runtime",
                "python3",
                "checks/audit/ca5dcbac0e83/override_probe.py",
            ],
        },
        "palette_size_ignored": {
            **witness,
            "claim": (
                "palette_size=3 and palette_size=4 returned byte-identical grids; "
                "the palette_size=3 result realized four endpoint colors."
            ),
        },
        "unknown_override_accepted": {
            "override": {"__override_contract_unknown_axis__": "typo"},
            "returned_grid": unknown_grid,
            "same_as_unoverridden_witness": unknown_grid
            == gen.generate(
                witness["seed"], witness["sample_index"], difficulty=witness["difficulty"]
            ),
        },
        "declared_domain_rejected": {
            "difficulty": "easy",
            "seed": 0,
            "sample_index": 0,
            "override": {"grid_h": 7},
            "axis_declares": "7..14",
            "exception": declared_rejection,
        },
        "validator_domain": {
            "palette_size_witness_passes_self_check": not witness["palette_size_3_self_check"],
            "note": (
                "The generated witness is otherwise valid under the target validator. "
                "The defect is that accepted exact controls are inert or inconsistent."
            ),
        },
        "racket_output": None,
        "rival_output": None,
        "racket_note": (
            "Not applicable: this is a generator control-contract defect and does not dispute "
            "the selected Racket transformation."
        ),
    }
    out = Path(__file__).with_name("counterexample.json")
    out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(out),
        "generator_sha256": digest,
        "witness": {
            "difficulty": witness["difficulty"],
            "seed": witness["seed"],
            "sample_index": witness["sample_index"],
            "realized_endpoint_colors": witness["realized_endpoint_colors"],
        },
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
