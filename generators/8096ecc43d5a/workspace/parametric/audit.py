#!/usr/bin/env python3
"""Bounded native/Racket self-audit for the transform-script order family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
RIVALS = (
    "left_to_right", "right_to_left", "sorted_codes", "deduplicate_codes",
    "collapse_adjacent_codes", "first_only", "last_only", "ignore_script",
)


def _load_native():
    path = HERE / "native.py"
    name = "_audit_native_8096_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_public(native, directory: Path, seed: int) -> list[dict]:
    if directory.exists():
        raise FileExistsError(directory)
    directory.mkdir(parents=True)
    rows = []
    for setting in native.SETTINGS:
        episode = native.generate(seed, {"script_order": setting}, 3, 4)
        for index in range(4):
            visible = native.public_turn(episode, index)
            body = public_challenge_bytes(visible)
            identifier = public_challenge_id(visible)
            path = directory / f"{identifier}.json"
            if path.exists():
                raise ValueError("duplicate visible public challenge")
            path.write_bytes(body)
            rows.append({"public_id": identifier, "bytes": len(body), "sha256": _sha(path)})
    return sorted(rows, key=lambda row: row["public_id"])


def audit(seeds: list[int], demo_counts: list[int], public_dir: Path | None) -> dict:
    native = _load_native()
    bridge = RacketBridge()
    evaluations = 0
    episodes = []
    findings = []
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("protected Racket is required")
        wrapped = {setting: wrap_rule(native.program({"script_order": setting}))
                   for setting in native.SETTINGS}
        for seed in seeds:
            for demos in demo_counts:
                for setting in native.SETTINGS:
                    request = {"script_order": setting}
                    episode = native.generate(seed, request, demos, 4)
                    one_query = native.generate(seed, request, demos, 1)
                    if native.public_turn(episode, 0) != native.public_turn(one_query, 0):
                        findings.append({"seed": seed, "demos": demos, "setting": setting,
                                         "finding": "first-turn projection changed with query count"})
                    for pair in episode["train"] + episode["test"]:
                        got = bridge.eval_text(f"({wrapped[setting]} {_literal(pair['input'])})")
                        evaluations += 1
                        if got != pair["output"]:
                            findings.append({"seed": seed, "demos": demos, "setting": setting,
                                             "finding": "selected Racket label differs from Python claim"})
                    other = next(value for value in native.SETTINGS if value != setting)
                    other_fits = True
                    for pair in episode["train"]:
                        got = bridge.eval_text(f"({wrapped[other]} {_literal(pair['input'])})")
                        evaluations += 1
                        other_fits &= got == pair["output"]
                    if other_fits:
                        findings.append({"seed": seed, "demos": demos, "setting": setting,
                                         "finding": "declared alternate setting survived demonstrations"})
                    survivors = [mode for mode in RIVALS
                                 if all(native.rival_transform(pair["input"], mode) == pair["output"]
                                        for pair in episode["train"])]
                    if survivors != [setting]:
                        findings.append({"seed": seed, "demos": demos, "setting": setting,
                                         "finding": "diagnostic rival survivor mismatch",
                                         "expected": [setting], "observed": survivors})
                    large = episode["test"][-1]["input"]
                    episodes.append({"seed": seed, "demos": demos, "queries": 4,
                                     "setting": setting, "diagnostic_survivors": survivors,
                                     "large_input_shape": [len(large), len(large[0])],
                                     "large_nonzero_body_cells": sum(v != 0 for row in large[2:] for v in row)})
    finally:
        bridge.close()
    public = _write_public(native, public_dir, seeds[0]) if public_dir is not None else []
    sources = []
    for path in sorted(HERE.iterdir()):
        if path.is_file() and path.suffix in {".py", ".rkt", ".json"}:
            sources.append({"path": path.name, "sha256": _sha(path), "bytes": path.stat().st_size})
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": native.TASK_ID,
        "status": "passed" if not findings else "findings",
        "racket": {"backend": "racket", "protected": True},
        "racket_evaluations": evaluations,
        "seeds": seeds,
        "demo_counts": demo_counts,
        "queries": 4,
        "diagnostic_rivals": list(RIVALS),
        "episodes": episodes,
        "public_files": public,
        "findings": findings,
        "sources": sources,
        "limits": "Finite declared-setting Racket replay plus named Python script shortcuts; not universal identifiability or owner acceptance.",
        "training_admitted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--demos", type=int, action="append", dest="demos")
    parser.add_argument("--public-dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    seeds = args.seeds or [0, 17]
    demos = args.demos or [2, 3, 6]
    if args.out.exists():
        raise FileExistsError(args.out)
    result = audit(seeds, demos, args.public_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "episodes": len(result["episodes"]),
                      "racket_evaluations": result["racket_evaluations"],
                      "findings": len(result["findings"]),
                      "public_files": len(result["public_files"])}))
    return 0 if not result["findings"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
