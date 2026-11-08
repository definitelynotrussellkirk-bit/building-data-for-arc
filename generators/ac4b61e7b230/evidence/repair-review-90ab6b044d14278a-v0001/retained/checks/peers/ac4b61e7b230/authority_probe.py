#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "ac4b61e7b230"
EXPECTED_SOURCE = "7472decbbed2b49988fa904d58283f5cafb85897b6e131000f6fcd2fd7a9270e"
BASE_RELATIVE = Path("base/solutions/training/05f2a901__ac4b61e7b230.json")


def execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def main() -> int:
    root = find_root(__file__)
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    if source_sha != EXPECTED_SOURCE:
        raise ValueError(f"peer source drift: {source_sha}")
    canonical_row = next(
        json.loads(line)
        for line in canonical_path(root).read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line).get("task_id") == TASK_ID
    )
    canonical = canonical_row["program_solution"]
    data_root = canonical_path(root).parents[1]
    base = json.loads((data_root / BASE_RELATIVE).read_text(encoding="utf-8"))["racket_target"]
    sources = {
        "canonical": canonical,
        "base_raw": base["raw_code"],
        "base_target": base["target_code"],
    }
    normalized = {name: " ".join(text.split()) for name, text in sources.items()}
    grids = [pair["input"] for split in ("train", "test") for pair in canonical_row[split]]
    grids.extend(
        generator.generate(37, index, difficulty="hard", scene_profile=profile)
        for index, profile in enumerate(generator.GENERAL_PROFILES)
    )
    expected = [generator.rule_mirror(grid) for grid in grids]
    evaluations = {}
    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=64) as bridge:
        for name, text in sources.items():
            evaluations[name] = [execute(bridge, text, grid) for grid in grids]
    parity = {name: outputs == expected for name, outputs in evaluations.items()}
    report = {
        "schema": "ac4b61e7b230-authority-probe-v1",
        "task_id": TASK_ID,
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha,
        "cases": len(grids),
        "protected_racket_evaluations": len(grids) * len(sources),
        "byte_sha256": {name: hashlib.sha256(text.encode()).hexdigest() for name, text in sources.items()},
        "exact_groups": len(set(sources.values())),
        "normalized_groups": len(set(normalized.values())),
        "base_raw_exact_canonical": base["raw_code"] == canonical,
        "base_target_exact_canonical": base["target_code"] == canonical,
        "base_raw_normalized_canonical": normalized["base_raw"] == normalized["canonical"],
        "base_target_normalized_canonical": normalized["base_target"] == normalized["canonical"],
        "racket_parity": parity,
        "status": "blocked_exact_authority" if not base["target_code"] == canonical and all(parity.values()) else "unexpected",
        "scope": "Current selected generator plus 4 canonical and 8 generated relation-profile inputs; exact source policy remains owner-side.",
    }
    out = Path(__file__).with_name("authority-summary.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "blocked_exact_authority" else 1


if __name__ == "__main__":
    raise SystemExit(main())
