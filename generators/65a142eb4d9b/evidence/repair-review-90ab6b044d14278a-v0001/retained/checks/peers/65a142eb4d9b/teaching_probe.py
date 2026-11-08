#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "65a142eb4d9b"
EXPECTED_SOURCE = "813bbc9e683f528b5d7039cca54f528a0706f2d6e4236edd3bb47470c5f99959"
BANDS = ("easy", "medium", "hard")


def execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def main() -> int:
    root = find_root(__file__)
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    if source_sha != EXPECTED_SOURCE:
        raise ValueError(f"peer source drift: {source_sha}")
    canonical_rows = [
        json.loads(line)
        for line in canonical_path(root).read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line).get("task_id") == TASK_ID
    ]
    if len(canonical_rows) != 1:
        raise ValueError(f"expected one canonical row, found {len(canonical_rows)}")
    program = canonical_rows[0]["program_solution"]

    failures: list[dict] = []
    grids: list[list[list[int]]] = []
    witness_profiles: dict[str, dict[str, list[str]]] = {}
    lesson_windows = 0
    for band in BANDS:
        band_grids = [generator.generate(61, index, difficulty=band) for index in range(6)]
        grids.extend(band_grids)
        witness_profiles[band] = {}
        for index, grid in enumerate(band_grids):
            profile = generator.schedule_profile(61, index, difficulty=band)
            if profile != generator.SCHEDULE_PROFILES[index]:
                failures.append({"kind": "profile", "band": band, "index": index, "profile": profile})
            errors = generator.self_check(grid)
            if errors:
                failures.append({"kind": "grammar", "band": band, "index": index, "errors": errors})
            if grid != generator.generate(61, index, difficulty=band):
                failures.append({"kind": "determinism", "band": band, "index": index})
        for name, predicate in generator.SEMANTIC_WITNESSES.items():
            profiles = [
                generator.SCHEDULE_PROFILES[index]
                for index, grid in enumerate(band_grids)
                if predicate(grid)
            ]
            witness_profiles[band][name] = profiles
            if not profiles:
                failures.append({"kind": "missing_witness", "band": band, "witness": name})
        for start in range(6):
            pairs = []
            for offset in range(4):
                grid = generator.generate(900 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
            lesson_windows += 1
            reasons = generator.lesson_identifiable(pairs[:3], pairs[3])
            if reasons:
                failures.append({"kind": "lesson", "band": band, "start": start, "reasons": reasons})

    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=64) as bridge:
        racket = [execute(bridge, program, grid) for grid in grids]
    mirrors = [generator.rule_mirror(grid) for grid in grids]
    if racket != mirrors:
        failures.append({"kind": "racket_parity"})

    report = {
        "schema": "65a142eb4d9b-bounded-teaching-probe-v1",
        "task_id": TASK_ID,
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "bands": list(BANDS),
        "scheduled_grids": len(grids),
        "cyclic_three_demo_windows": lesson_windows,
        "protected_racket_evaluations": len(grids),
        "witness_profiles": witness_profiles,
        "failures": failures,
        "status": "passed" if not failures else "failed",
        "scope": "One complete six-profile schedule per difficulty band, every cyclic three-demo window, four declared rivals, and protected-Racket parity on the 18 scheduled grids.",
    }
    out = Path(__file__).with_name("teaching-summary.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
