#!/usr/bin/env python3
"""Portable finite qualification probe for f505996a2fdc.

This complements the Racket-backed lesson census with an inexpensive exhaustive
check of every cyclic six-pair window, every leave-one-out query position, and
every rival declared by the selected generator.  It intentionally imports the
selected Python authority mirror, so it is a schedule/regression probe rather
than independent label evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

for ancestor in Path(__file__).resolve().parents:
    packet_runtime = ancestor / "shared" / "runtime"
    if (packet_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(packet_runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "f505996a2fdc"


def load_generator(path: str | None = None):
    root = find_root(__file__)
    default = root / "generators" / TASK_ID / "generator.py"
    if not default.is_file():
        default = root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    selected = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or default).resolve()
    spec = importlib.util.spec_from_file_location(f"qualification_{TASK_ID}", selected)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {selected}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, selected, root


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def pair(gen, grid):
    return {"input": copy.deepcopy(grid), "output": gen._authority_output(grid)}


def run(*, seeds: int, starts: int, source: str | None = None) -> dict[str, Any]:
    gen, selected, root = load_generator(source)
    rivals = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    report: dict[str, Any] = {
        "schema": "f505996a2fdc-qualification-v1",
        "task_id": TASK_ID,
        "generator": str(selected),
        "generator_sha256": hashlib.sha256(selected.read_bytes()).hexdigest(),
        "seeds": seeds,
        "starts_per_seed": starts,
        "bands": ["easy", "medium", "hard"],
        "rivals": sorted(rivals),
        "canonical_shortcuts": {},
        "windows": 0,
        "rotations": 0,
        "errors": [],
        "command_histogram": Counter(),
        "unique_inputs": set(),
        "limits": [
            "Uses the generator's Python authority mirror; Racket-backed evidence is separate.",
            "Checks only declared rivals and finite sampled seed families.",
            "Does not prove uniqueness against every possible inferred rule.",
        ],
    }

    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    for name, shortcut in shortcuts.items():
        fits = sum(shortcut(copy.deepcopy(item["input"])) == item["output"] for item in canonical)
        report["canonical_shortcuts"][name] = {"fits": fits, "pairs": len(canonical)}
        if fits != len(canonical):
            report["errors"].append(
                f"canonical shortcut {name!r} fits {fits}/{len(canonical)} pairs"
            )

    for band in report["bands"]:
        for seed_offset in range(seeds):
            seed = 10_000 + seed_offset
            for start in range(starts):
                pairs = [
                    pair(gen, gen.generate(seed, start + offset, difficulty=band))
                    for offset in range(gen.EXAMPLES_NEEDED + 1)
                ]
                report["windows"] += 1
                for item in pairs:
                    analysis = gen._analysis(item["input"])
                    report["command_histogram"][str(analysis["cmd"])] += 1
                    report["unique_inputs"].add(digest(item["input"]))
                    findings = gen.self_check(item["input"])
                    if findings:
                        report["errors"].append(
                            f"self_check {band=} {seed=} {start=}: {findings}"
                        )
                if {gen._analysis(item["input"])["cmd"] for item in pairs} != set(range(1, 7)):
                    report["errors"].append(
                        f"command cycle incomplete at {band=} {seed=} {start=}"
                    )
                for query_index, query in enumerate(pairs):
                    demos = [item for index, item in enumerate(pairs) if index != query_index]
                    report["rotations"] += 1
                    reasons = gen.lesson_identifiable(demos, query)
                    if reasons:
                        report["errors"].append(
                            f"hook warning at {band=} {seed=} {start=} {query_index=}: {reasons}"
                        )
                    for name, rival in rivals.items():
                        if all(rival(copy.deepcopy(demo["input"])) == demo["output"] for demo in demos):
                            report["errors"].append(
                                f"rival {name!r} survived at {band=} {seed=} {start=} {query_index=}"
                            )

    report["command_histogram"] = dict(sorted(report["command_histogram"].items()))
    report["unique_inputs"] = len(report["unique_inputs"])
    report["status"] = "pass" if not report["errors"] else "fail"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--starts", type=int, default=12)
    parser.add_argument("--generator")
    parser.add_argument("--out")
    args = parser.parse_args()
    report = run(seeds=args.seeds, starts=args.starts, source=args.generator)
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
