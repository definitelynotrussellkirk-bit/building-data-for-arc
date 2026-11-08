#!/usr/bin/env python3
"""Compatibility CLI and bounded evidence builder for the native alignment family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent
PROTOTYPE_PATH = HERE / "prototype.py"
_NAME = "parametric_659980b6f715_compat_source"


def _load():
    module = sys.modules.get(_NAME)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(_NAME, PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[_NAME] = module
    spec.loader.exec_module(module)
    return module


P = _load()
TASK_ID = P.TASK_ID
VERSION = "1.0.0-native"
ALIGNMENTS = P.ALIGNMENTS
DEFAULT_ALIGNMENT = P.DEFAULT_ALIGNMENT


def materialize_program(alignment=DEFAULT_ALIGNMENT, *, root=None) -> str:
    return P.program_for(alignment)


def choose_alignment(seed, selection="seeded") -> str:
    return P.choose_alignment(seed, selection)


def _racket_outputs(bridge: RacketBridge, grids: list[list[list[int]]]) -> dict[str, list[list[list[int]]]]:
    wrapped = {name: wrap_rule(P.program_for(name)) for name in P.ALIGNMENTS}
    outputs = {name: [] for name in P.ALIGNMENTS}
    for grid in grids:
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        for name in P.ALIGNMENTS:
            outputs[name].append(bridge.eval_text(f"({wrapped[name]} {literal})"))
    return outputs


def generate_episode(seed, *, alignment="seeded", root=None, bridge=None) -> dict[str, Any]:
    selected = choose_alignment(seed, alignment)
    native = P.generate_episode(seed, selected, demos=3, queries=1)
    pairs = native["train"] + native["test"]
    grids = [pair["input"] for pair in pairs]
    if bridge is not None:
        predictions = _racket_outputs(bridge, grids)
        for name in P.ALIGNMENTS:
            for grid, output in zip(grids, predictions[name]):
                if output != P.solve(grid, name):
                    raise AssertionError(f"protected Racket disagrees for {name}")
    else:
        predictions = {name: [P.solve(grid, name) for grid in grids] for name in P.ALIGNMENTS}
    chosen = predictions[selected]
    rivals = {
        name: {
            "demo_refutations": [i for i in range(3) if predictions[name][i] != chosen[i]],
            "query_differs": predictions[name][3] != chosen[3],
        }
        for name in P.ALIGNMENTS
    }
    return {
        "schema": "normalized-overlap-parametric-episode-v2",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "seed": seed,
        "parameter": {P.PARAMETER_NAME: selected},
        "program": P.program_for(selected),
        "program_sha256": hashlib.sha256(P.program_for(selected).encode()).hexdigest(),
        "train": deepcopy(native["train"]),
        "test": deepcopy(native["test"]),
        "all_setting_outputs": predictions,
        "assessment": {
            "identified": all(rivals[name]["demo_refutations"] for name in P.ALIGNMENTS if name != selected),
            "query_separates_settings": all(rivals[name]["query_differs"] for name in P.ALIGNMENTS if name != selected),
            "rivals": rivals,
        },
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_evidence(seed, out_dir, *, root=None) -> dict[str, Any]:
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty evidence directory: {out}")
    out.mkdir(parents=True, exist_ok=True)
    with RacketBridge(timeout=30, max_calls_before_restart=64) as bridge:
        episodes = [
            generate_episode(seed + i, alignment=name, bridge=bridge)
            for i, name in enumerate(P.ALIGNMENTS)
        ]
    for name in P.ALIGNMENTS:
        path = out / "private" / "rules" / f"{name}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(P.program_for(name), encoding="utf-8")
    for i, episode in enumerate(episodes):
        _write_json(out / "private" / f"episode-{i:03d}.json", episode)
        _write_json(out / "public" / f"episode-{i:03d}.json", P.public_view({
            "train": episode["train"], "test": episode["test"]
        }, 0))
    witness_grid = episodes[1]["test"][0]["input"]
    witness = {
        "input": witness_grid,
        "intermediate": P.intermediate_for(witness_grid, "bottom_right"),
        "outputs": {name: P.solve(witness_grid, name) for name in P.ALIGNMENTS},
    }
    _write_json(out / "private" / "differing-witness.json", witness)
    report = {
        "schema": "normalized-overlap-parametric-evidence-v2",
        "status": "pass" if all(e["assessment"]["identified"] for e in episodes) else "fail",
        "task_id": TASK_ID,
        "episodes_identified": sum(bool(e["assessment"]["identified"]) for e in episodes),
        "episodes_total": len(episodes),
        "query_separation_count": sum(bool(e["assessment"]["query_separates_settings"]) for e in episodes),
        "runtime": racket_runtime_status(),
        "limitations": "Finite two-setting evidence; no universal identifiability or owner acceptance.",
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("evidence", "episode"))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--alignment", default="seeded", choices=("seeded",) + P.ALIGNMENTS)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if args.command == "evidence":
        payload = build_evidence(args.seed, args.out)
    else:
        payload = generate_episode(args.seed, alignment=args.alignment)
        _write_json(Path(args.out), payload)
    print(json.dumps(payload if args.command == "evidence" else payload["assessment"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
