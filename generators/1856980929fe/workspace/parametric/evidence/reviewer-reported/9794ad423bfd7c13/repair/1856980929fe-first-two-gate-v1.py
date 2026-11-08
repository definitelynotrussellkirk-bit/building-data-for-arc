#!/usr/bin/env python3
"""Replay the large raw-lesson probe and prove the declared gate catches each shortcut."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path.cwd()
TASK = "1856980929fe"
PROBE_PATH = ROOT / "generators" / TASK / "workspace" / "review_probe.py"
GENERATOR_PATH = ROOT / "generators" / TASK / "generator.py"
OUT = ROOT.parent / "checks" / "repair" / "1856980929fe-first-two-gate-v1.json"
LESSONS_PER_BAND = 100
DEMOS = 5


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if OUT.exists():
        raise FileExistsError(OUT)
    probe = load_module("gate_probe_1856980929fe", PROBE_PATH)
    gen = probe.gen
    vulnerable = []
    missed = []
    caught_by_rival = {name: 0 for name in gen.LESSON_COMPETITORS}

    for band in probe.BANDS:
        for lesson_index in range(LESSONS_PER_BAND):
            seed = probe._lesson_seed(band, lesson_index)
            start = lesson_index * probe.LESSON_STRIDE
            grids = [
                gen.generate(seed, start + offset, difficulty=band)
                for offset in range(DEMOS + 1)
            ]
            outputs = [gen.rule_mirror(grid) for grid in grids]
            demos = [
                {"input": grid, "output": output}
                for grid, output in zip(grids[:-1], outputs[:-1])
            ]
            query = {"input": grids[-1]}
            reasons = gen.lesson_identifiable(demos, query)
            for name, rival in gen.LESSON_COMPETITORS.items():
                survives = all(
                    rival(grid) == expected
                    for grid, expected in zip(grids[:-1], outputs[:-1])
                )
                changes_query = rival(grids[-1]) != outputs[-1]
                if not (survives and changes_query):
                    continue
                expected_reason = f"{name} fits every demo but changes the query answer"
                row = {
                    "band": band,
                    "lesson_index": lesson_index,
                    "seed": seed,
                    "start_sample_index": start,
                    "rival": name,
                    "expected_reason": expected_reason,
                    "gate_reasons": reasons,
                }
                vulnerable.append(row)
                if expected_reason in reasons:
                    caught_by_rival[name] += 1
                else:
                    missed.append(row)

    assert len(vulnerable) == 7, len(vulnerable)
    assert caught_by_rival == {
        "shared_first_size": 0,
        "single_fan_level": 0,
        "first_two_seeds_only": 7,
    }
    assert not missed

    retained_seed = 2
    retained_start = 11
    retained_grids = [
        gen.generate(retained_seed, retained_start + offset, difficulty="easy")
        for offset in range(6)
    ]
    retained_outputs = [gen.rule_mirror(grid) for grid in retained_grids]
    retained_reasons = gen.lesson_identifiable(
        [
            {"input": grid, "output": output}
            for grid, output in zip(retained_grids[:-1], retained_outputs[:-1])
        ],
        {"input": retained_grids[-1]},
    )
    assert retained_reasons == [
        "first_two_seeds_only fits every demo but changes the query answer"
    ]

    report = {
        "schema": "arcpuzzles-semantic-gate-replay-v1",
        "task_id": TASK,
        "generator_sha256": sha256_file(GENERATOR_PATH),
        "probe_sha256": sha256_file(PROBE_PATH),
        "scope": {
            "bands": list(probe.BANDS),
            "lessons_per_band": LESSONS_PER_BAND,
            "demos": DEMOS,
            "query_count_per_lesson": 1,
            "lesson_stride": probe.LESSON_STRIDE,
        },
        "raw_query_discriminating_survivors": len(vulnerable),
        "caught_by_gate": len(vulnerable) - len(missed),
        "missed_by_gate": len(missed),
        "caught_by_rival": caught_by_rival,
        "vulnerable_lessons": vulnerable,
        "retained_regression": {
            "seed": retained_seed,
            "difficulty": "easy",
            "sample_indices": list(range(retained_start, retained_start + 6)),
            "seed_counts": [len(gen._rectangles(grid)) for grid in retained_grids],
            "gate_reasons": retained_reasons,
        },
        "limitations": [
            "Finite replay of the source-bound shared-seed consecutive-index assembler only.",
            "Authority outputs use the Python mirror; task tests and parametric evidence separately execute Racket.",
        ],
        "status": "pass",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({
        "status": "pass",
        "raw_survivors": len(vulnerable),
        "caught": len(vulnerable) - len(missed),
        "out": str(OUT),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
