#!/usr/bin/env python3
"""Reusable finite probe for the d3c9fc4479d8 four-slot lesson schedule.

It checks every requested cyclic start, all four possible query rotations, the
declared competitors, and the assertion that each canonical shortcut really
fits every public canonical pair.  It is authoring evidence, not a proof over
all possible rules.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

HOME = Path(__file__).resolve().parents[1]
LIBRARY = HOME.parents[1]
sys.path.insert(0, str(LIBRARY / "shared/runtime"))

from reviewer_support import canonical_pairs, find_root

TASK_ID = "d3c9fc4479d8"


def _episode(gen, grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def run_probe(gen, *, starts: Iterable[int] = range(8), bands=("easy", "medium", "hard")):
    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))
    shortcut_failures = []
    for name, rival in sorted(gen.CANONICAL_SHORTCUTS.items()):
        for index, pair in enumerate(canonical):
            if rival(pair["input"]) != pair["output"]:
                shortcut_failures.append({"rival": name, "canonical_pair": index})

    ambiguous = []
    witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    starts = list(starts)
    for band_index, band in enumerate(bands):
        seed = 41_000 + band_index
        for start in starts:
            pairs = [
                _episode(gen, gen.generate(seed, start + offset, difficulty=band))
                for offset in range(4)
            ]
            for pair in pairs:
                for name, witness in gen.SEMANTIC_WITNESSES.items():
                    witness_hits[name] += int(bool(witness(pair["input"])))
            for query_index in range(4):
                demos = pairs[:query_index] + pairs[query_index + 1 :]
                reasons = gen.lesson_identifiable(demos, pairs[query_index])
                if reasons:
                    ambiguous.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                        }
                    )

    missing_witnesses = sorted(name for name, count in witness_hits.items() if count == 0)
    status = "pass" if not (shortcut_failures or ambiguous or missing_witnesses) else "fail"
    return {
        "schema": "d3c9fc4479d8-lesson-probe-v1",
        "task_id": TASK_ID,
        "status": status,
        "bands": list(bands),
        "starts": starts,
        "rotations_checked": len(starts) * len(tuple(bands)) * 4,
        "canonical_pairs": len(canonical),
        "canonical_shortcut_failures": shortcut_failures,
        "ambiguous_windows": ambiguous,
        "witness_hits": witness_hits,
        "missing_witnesses": missing_witnesses,
        "limits": [
            "Finite declared-rival probe, not a proof of universal identifiability.",
            "Uses the Python rule mirror; the full battery and lesson census retain Racket-backed evidence.",
        ],
    }


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("d3c9fc4479d8_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--starts", type=int, default=16)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(_load_generator(args.generator), starts=range(args.starts))
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
