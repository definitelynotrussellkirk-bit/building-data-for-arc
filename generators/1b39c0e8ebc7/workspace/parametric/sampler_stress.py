#!/usr/bin/env python3
"""Bounded deterministic sampler/domain stress for future reviewers."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_vector_direction_stress_impl", _HOME / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
p = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = p
_SPEC.loader.exec_module(p)


def run_stress(seed_count: int = 64) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 512:
        raise ValueError("seed_count must be an exact integer in 1..512")
    episodes = scenes = 0
    unique = set()
    vectors = set()
    shapes = set()
    minimum_quadrant = 10**9
    for seed in range(seed_count):
        for setting in p.SETTINGS:
            for demos in (2, 3, 6):
                episode = p.generate(seed, {p.PARAMETER: setting}, demos, 4)
                episodes += 1
                assert len(episode["train"]) == demos and len(episode["test"]) == 4
                local = []
                for split in ("train", "test"):
                    for pair in episode[split]:
                        scenes += 1
                        key = json.dumps(pair["input"], separators=(",", ":"))
                        local.append(key)
                        unique.add(key)
                        info = p.analyze_scene(pair["input"])
                        assert info["errors"] == []
                        assert info["forward_targets"] and info["reverse_targets"]
                        assert info["unmatched_sources"] and info["unmatched_targets"]
                        assert pair["output"] == p.apply_rule(pair["input"], setting)
                        vectors.add(tuple(info["vector"]))
                        shapes.add((info["height"], info["width"]))
                        if (info["height"], info["width"]) == (30, 30):
                            occupied = {
                                (r, c)
                                for r, row in enumerate(pair["input"])
                                for c, value in enumerate(row)
                                if value
                            }
                            counts = [
                                sum((r >= 15) * 2 + (c >= 15) == q for r, c in occupied)
                                for q in range(4)
                            ]
                            minimum_quadrant = min(minimum_quadrant, *counts)
                            assert {0, 29} <= {r for r, _ in occupied}
                            assert {0, 29} <= {c for _, c in occupied}
                assert len(local) == len(set(local))
    return {
        "schema": "arcpuzzles-vector-direction-sampler-stress-v1",
        "task_id": p.TASK_ID,
        "seed_count": seed_count,
        "episodes": episodes,
        "scenes_checked": scenes,
        "unique_scenes": len(unique),
        "vectors_observed": [list(v) for v in sorted(vectors)],
        "shapes_observed": [list(s) for s in sorted(shapes)],
        "minimum_30x30_quadrant_occupancy": minimum_quadrant,
        "status": "passed",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run_stress(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "episodes", "scenes_checked", "unique_scenes")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
