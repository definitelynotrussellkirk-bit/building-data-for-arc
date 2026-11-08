#!/usr/bin/env python3
"""Rotate each three-pair window through every query position.

The shared lesson census uses the production sampler but does not rotate all
pairs into the query slot.  This task-local probe closes that narrow gap while
iterating the generator's live LESSON_COMPETITORS declaration.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = HOME / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("cyclic_probe_e4c4a1290088", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seed(band: str, start: int, offset: int) -> int:
    payload = f"e4c4a1290088:cyclic:v1:{band}:{start}:{offset}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def _grid_hash(grid) -> str:
    packed = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(packed).hexdigest()


def run(per_band: int = 100) -> dict:
    gen = _load_generator()
    competitors = dict(gen.LESSON_COMPETITORS)
    failures = []
    unique_inputs = set()
    rotations = 0
    per_band_stats = {}
    for band in ("easy", "medium", "hard"):
        band_failures = 0
        rival_refutations = {name: 0 for name in competitors}
        for start in range(per_band):
            pairs = []
            for offset in range(3):
                sample_index = start + offset
                grid = gen.generate(_seed(band, start, offset), sample_index, difficulty=band)
                unique_inputs.add(_grid_hash(grid))
                pairs.append({"input": grid, "output": gen.oracle_output(grid)})
            for query_index in range(3):
                query = pairs[query_index]
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                rotations += 1
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    band_failures += 1
                    failures.append({
                        "band": band,
                        "start": start,
                        "query_index": query_index,
                        "reasons": reasons,
                    })
                for name, competitor in competitors.items():
                    if any(competitor(pair["input"]) != pair["output"] for pair in demos):
                        rival_refutations[name] += 1
                    else:
                        band_failures += 1
                        failures.append({
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "surviving_rival": name,
                        })
        per_band_stats[band] = {
            "windows": per_band,
            "rotations": per_band * 3,
            "failures": band_failures,
            "rival_refutations": rival_refutations,
        }
    return {
        "schema": "e4c4a1290088-cyclic-lesson-probe-v1",
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "per_band_requested": per_band,
        "rotations": rotations,
        "unique_inputs": len(unique_inputs),
        "competitors": sorted(competitors),
        "per_band": per_band_stats,
        "failures": failures,
        "status": "pass" if not failures else "fail",
        "limits": [
            "Finite declared-rival probe, not proof of universal identifiability.",
            "Uses deterministic task-local consecutive windows, not the shared production lesson materializer.",
        ],
    }


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cyclic-lesson-probe.json")
    report = run()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "rotations", "unique_inputs")}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
