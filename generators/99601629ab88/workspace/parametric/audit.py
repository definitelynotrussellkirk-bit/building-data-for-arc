"""Bounded authoring audit for the native 99601629ab88 family.

This tool is intentionally finite. It checks the two declared settings on two
qualification seeds, fits the retained shortcut bank to demonstrations before
query comparison, verifies matched/prefix-stable inputs and public projection,
and records the substantive 30x30 query. Racket authority comes from native
qualification, not from this Python audit.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
ADAPTER = HOME / "adapter.py"


def _load():
    name = "_audit_99601629ab88_adapter_" + hashlib.sha256(str(ADAPTER).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, ADAPTER)
    if spec is None or spec.loader is None:
        raise ImportError(ADAPTER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build() -> dict:
    adapter = _load()
    settings = [
        {"matrix_orientation": "mirror_left_right"},
        {"matrix_orientation": "largest_block_to_top_left"},
    ]
    rows = []
    for seed in (0, 17):
        episodes = [adapter.generate(seed, setting, 2, 4) for setting in settings]
        assert [p["input"] for p in episodes[0]["train"]] == [p["input"] for p in episodes[1]["train"]]
        assert [p["input"] for p in episodes[0]["test"]] == [p["input"] for p in episodes[1]["test"]]
        for setting, episode in zip(settings, episodes):
            certificate = adapter.lesson_certificate(
                episode["train"], [pair["input"] for pair in episode["test"]]
            )
            assert certificate["surviving_settings"] == [setting]
            assert certificate["ambiguous_rivals"] == []
            one = adapter.generate(seed, setting, 2, 1)
            assert adapter.public_turn(one, 0) == adapter.public_turn(episode, 0)
            stress = episode["test"][3]["input"]
            analysis = adapter.analyze(stress)
            assert (len(stress), len(stress[0])) == (30, 30)
            rows.append(
                {
                    "seed": seed,
                    "settings": setting,
                    "minimum_demos": 2,
                    "queries": 4,
                    "surviving_settings": certificate["surviving_settings"],
                    "surviving_rivals": certificate["surviving_rivals"],
                    "ambiguous_rivals": certificate["ambiguous_rivals"],
                    "query_corners": [adapter.analyze(pair["input"])["largest_corner"] for pair in episode["test"]],
                    "stress": {
                        "shape": [30, 30],
                        "matrix_shape": [len(analysis["matrix"]), len(analysis["matrix"][0])],
                        "largest_corner": analysis["largest_corner"],
                        "nonzero_cells": sum(cell != 0 for row in stress for cell in row),
                    },
                }
            )
    return {
        "schema": "arcpuzzles-99601629ab88-self-audit-v1",
        "scope": "2 seeds x 2 settings; 2 demonstrations; 4 queries; two declared settings and ten finite rivals; Python claims only",
        "jobs": rows,
        "job_count": len(rows),
        "ambiguous_job_count": sum(bool(row["ambiguous_rivals"]) for row in rows),
        "training_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"jobs": report["job_count"], "ambiguous": report["ambiguous_job_count"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
