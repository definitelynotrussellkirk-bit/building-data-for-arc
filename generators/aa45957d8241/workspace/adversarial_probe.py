#!/usr/bin/env python3
"""Bounded adversarial probe for aa45957d8241's repaired contract."""
from __future__ import annotations

import importlib.util
import itertools
import json
import sys
import time
from pathlib import Path

TASK = "aa45957d8241"
SOURCE = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("aa45957d8241_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


def fail(message: str, **context):
    raise AssertionError(json.dumps({"message": message, **context}, sort_keys=True))


def boundary_probe() -> dict:
    draws = 0
    started = time.perf_counter()
    for band, height, width, codes, distractors, residue, seed in itertools.product(
        ("easy", "medium", "hard"),
        (8, 18),
        (11, 24),
        (2, 3),
        (0, 2),
        range(GEN.LESSON_SCHEDULE_PERIOD),
        (0, 19),
    ):
        sample_index = residue
        overrides = {
            "grid_h": height,
            "grid_w": width,
            "n_codes": codes,
            "n_distractors": distractors,
        }
        grid = GEN.generate(seed, sample_index, difficulty=band, **overrides)
        draws += 1
        errors = GEN.self_check(grid)
        if errors:
            fail("self_check rejected boundary draw", band=band, seed=seed,
                 sample_index=sample_index, overrides=overrides, errors=errors)
        observed = GEN.observe_overrides(grid)
        if observed != overrides:
            fail("boundary override mismatch", band=band, seed=seed,
                 sample_index=sample_index, requested=overrides, observed=observed)
        replay = GEN.generate(seed, sample_index, difficulty=band, **overrides)
        if replay != grid:
            fail("boundary draw was not deterministic", band=band, seed=seed,
                 sample_index=sample_index, overrides=overrides)
    return {
        "surface": "sampler_boundaries_and_retry_schedule",
        "draws": draws,
        "findings": 0,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }


def lesson_probe() -> dict:
    windows = rotations = 0
    rival_refutations = {name: 0 for name in GEN.LESSON_COMPETITORS}
    started = time.perf_counter()
    for band, seed, start in itertools.product(
        ("easy", "medium", "hard"), range(30), range(GEN.LESSON_SCHEDULE_PERIOD)
    ):
        grids = [GEN.generate(seed, start + offset, difficulty=band) for offset in range(4)]
        labelled = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
        windows += 1
        for query_index, query in enumerate(labelled):
            demos = [pair for index, pair in enumerate(labelled) if index != query_index]
            reasons = GEN.lesson_identifiable(demos, query)
            if reasons:
                fail("rotated lesson remained ambiguous", band=band, seed=seed,
                     start=start, query_index=query_index, reasons=reasons)
            rotations += 1
            for name, rival in GEN.LESSON_COMPETITORS.items():
                if any(rival(pair["input"]) != pair["output"] for pair in demos):
                    rival_refutations[name] += 1
                else:
                    fail("declared rival survived demonstrations", band=band,
                         seed=seed, start=start, query_index=query_index, rival=name)
    return {
        "surface": "lesson_certificate_rivals",
        "windows": windows,
        "rotations": rotations,
        "rival_refutations": rival_refutations,
        "findings": 0,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    report = {
        "schema": "aa45957d8241-adversarial-probe-v1",
        "task_id": TASK,
        "generator_version": GEN.VERSION,
        "generator_sha256": __import__("hashlib").sha256(SOURCE.read_bytes()).hexdigest(),
        "results": [boundary_probe(), lesson_probe()],
        "status": "pass",
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
