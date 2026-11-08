#!/usr/bin/env python3
"""Bounded protected-Racket teaching audit and public-example writer."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent


def _load(filename: str) -> ModuleType:
    path = (HERE / filename).resolve()
    name = "_audit_78806e443729_" + path.stem + "_" + hashlib.sha256(str(path).encode()).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


adapter = _load("adapter.py")
family = _load("family.py")


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _apply(bridge: RacketBridge, source: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(f"({wrap_rule(source)} {_literal(grid)})")


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def audit(seed: int = 0, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    rival_sources = {
        "shortest_relay": family.rival_program("shortest_relay"),
        "smallest_color_relay": family.rival_program("smallest_color_relay"),
        "largest_color_relay": family.rival_program("largest_color_relay"),
        "first_seed_relay": family.rival_program("first_seed_relay"),
    }
    rows = []
    with RacketBridge(timeout=20) as bridge:
        identity = bridge.runtime_identity
        for chosen in family.BEAM_MODES:
            episode = adapter.generate(seed, {"beam_mode": chosen}, demos, queries)
            selected_program = adapter.program({"beam_mode": chosen})
            other = next(mode for mode in family.BEAM_MODES if mode != chosen)
            candidates = {"other_setting": adapter.program({"beam_mode": other}), **rival_sources}
            chosen_match = all(
                _apply(bridge, selected_program, pair["input"]) == pair["output"]
                for pair in [*episode["train"], *episode["test"]]
            )
            rival_rows = {}
            for name, source in candidates.items():
                demo_outputs = [_apply(bridge, source, pair["input"]) for pair in episode["train"]]
                query_outputs = [_apply(bridge, source, pair["input"]) for pair in episode["test"]]
                rival_rows[name] = {
                    "program_sha256": hashlib.sha256(source.encode()).hexdigest(),
                    "fits_demonstrations": all(
                        output == pair["output"]
                        for output, pair in zip(demo_outputs, episode["train"], strict=True)
                    ),
                    "query_differs": any(
                        output != pair["output"]
                        for output, pair in zip(query_outputs, episode["test"], strict=True)
                    ),
                    "query_prediction_sha256": [_digest(output) for output in query_outputs],
                }
            rows.append(
                {
                    "settings": {"beam_mode": chosen},
                    "chosen_program_sha256": hashlib.sha256(selected_program.encode()).hexdigest(),
                    "chosen_labels_match_racket": chosen_match,
                    "public_filename": family.public_filename(episode),
                    "rivals": rival_rows,
                }
            )
    passed = all(
        row["chosen_labels_match_racket"]
        and all(not rival["fits_demonstrations"] and rival["query_differs"] for rival in row["rivals"].values())
        for row in rows
    )
    return {
        "schema": "arcpuzzles-78806e443729-teaching-audit-v1",
        "status": "pass" if passed else "fail",
        "scope": {"seed": seed, "demos": demos, "queries": queries, "settings": 2, "rivals": 5},
        "racket": {
            key: identity[key]
            for key in ("schema", "backend", "protected", "binary_sha256", "prelude_sha256", "bridge_sha256")
            if key in identity
        },
        "settings": rows,
        "limits": "Finite authored settings and five executable rivals only; not universal uniqueness.",
    }



def stress(seed_count: int = 50) -> dict[str, Any]:
    """Pure-Python reliability sweep over all supported demo counts and settings."""
    if type(seed_count) is not int or not 1 <= seed_count <= 500:
        raise ValueError("seed_count must be an integer in 1..500; bool is forbidden")
    failures: list[dict[str, Any]] = []
    episodes = visible_pairs = matched = turns = 0
    for seed in range(seed_count):
        for demos in range(2, 7):
            generated = {
                mode: adapter.generate(seed, {"beam_mode": mode}, demos, 4)
                for mode in family.BEAM_MODES
            }
            matched += 1
            left_inputs = [pair["input"] for pair in [*generated["horizontal_only"]["train"], *generated["horizontal_only"]["test"]]]
            right_inputs = [pair["input"] for pair in [*generated["dominant_relay"]["train"], *generated["dominant_relay"]["test"]]]
            if left_inputs != right_inputs:
                failures.append({"seed": seed, "demos": demos, "code": "setting_dependent_inputs"})
            for mode, episode in generated.items():
                episodes += 1
                pairs = [*episode["train"], *episode["test"]]
                visible_pairs += len(pairs)
                keys = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
                if len(keys) != len(set(keys)):
                    failures.append({"seed": seed, "demos": demos, "beam_mode": mode, "code": "duplicate_inputs"})
                for index, pair in enumerate(pairs):
                    if pair["output"] != family.output_for(pair["input"], mode):
                        failures.append({"seed": seed, "demos": demos, "beam_mode": mode, "pair": index, "code": "label_mismatch"})
                for query_index in range(4):
                    turns += 1
                    turn = family.public_turn(episode, query_index)
                    if len(turn.get("test", [])) != 1 or turn["test"][0].get("input") != episode["test"][query_index]["input"]:
                        failures.append({"seed": seed, "demos": demos, "beam_mode": mode, "query": query_index, "code": "sequential_projection"})
                single = adapter.generate(seed, {"beam_mode": mode}, demos, 1)
                if family.public_turn(single, 0) != family.public_turn(episode, 0):
                    failures.append({"seed": seed, "demos": demos, "beam_mode": mode, "code": "first_query_instability"})
    return {
        "schema": "arcpuzzles-78806e443729-stress-v1",
        "status": "pass" if not failures else "fail",
        "counts": {
            "seeds": seed_count,
            "episodes": episodes,
            "visible_pairs": visible_pairs,
            "matched_input_comparisons": matched,
            "sequential_turns": turns,
        },
        "failures": failures,
        "limits": "Constructive Python-side reliability and projection sweep; protected Racket is covered separately by audit and native qualification.",
    }

def write_examples(seed: int, demos: int, queries: int, directory: Path) -> list[dict[str, str]]:
    directory.mkdir(parents=True, exist_ok=True)
    rows = []
    for mode in family.BEAM_MODES:
        episode = adapter.generate(seed, {"beam_mode": mode}, demos, queries)
        public = family.public_challenge(episode)
        filename = family.public_filename(episode)
        public_path = directory / filename
        public_path.write_bytes(family.public_challenge_bytes(public))
        rows.append({"beam_mode": mode, "path": public_path.name, "sha256": hashlib.sha256(public_path.read_bytes()).hexdigest()})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--public-dir", type=Path)
    parser.add_argument("--stress-seeds", type=int, default=0)
    args = parser.parse_args()
    report = audit(args.seed, args.demos, args.queries)
    if args.stress_seeds:
        report["stress"] = stress(args.stress_seeds)
        if report["stress"]["status"] != "pass":
            report["status"] = "fail"
    if args.public_dir is not None:
        report["public_examples"] = write_examples(args.seed, args.demos, args.queries, args.public_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "out": str(args.out), "scope": report["scope"]}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
