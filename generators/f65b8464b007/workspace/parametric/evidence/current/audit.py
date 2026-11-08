"""Run a bounded protected-Racket learnability audit for f65b8464b007."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes


def _load_prototype():
    path = Path(__file__).resolve().parents[2] / "prototype.py"
    spec = importlib.util.spec_from_file_location("_f65_audit_prototype", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _literal(grid):
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, default=107)
    parser.add_argument("--demos", type=int, default=3)
    args = parser.parse_args()

    prototype, source = _load_prototype()
    settings = [
        {"shift_rule": "next"},
        {"shift_rule": "densest_index"},
    ]
    episodes = [
        prototype.generate_episode(
            args.seed,
            shift_rule=setting["shift_rule"],
            demos=args.demos,
            queries=4,
        )
        for setting in settings
    ]
    inputs = [
        pair["input"]
        for split in ("train", "test")
        for pair in episodes[0][split]
    ]
    if inputs != [
        pair["input"]
        for split in ("train", "test")
        for pair in episodes[1][split]
    ]:
        raise AssertionError("settings did not receive matched inputs")

    bridge = RacketBridge()
    wrapped = {
        name: wrap_rule(prototype.rival_program(name))
        for name in prototype.RIVAL_NAMES
    }
    cache = {}
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("audit requires protected Racket")
        for name, rule in wrapped.items():
            for index, grid in enumerate(inputs):
                output = bridge.eval_text(f"({rule} {_literal(grid)})")
                cache[(name, index)] = output
                expected = prototype.transform_rival(grid, name)
                if output != expected:
                    raise AssertionError(f"Racket/Python disagreement for {name} input {index}")
    finally:
        bridge.close()

    reports = []
    for setting, episode in zip(settings, episodes):
        labels = [
            pair["output"]
            for split in ("train", "test")
            for pair in episode[split]
        ]
        survivors = [
            name for name in prototype.RIVAL_NAMES
            if all(cache[(name, index)] == labels[index]
                   for index in range(args.demos))
        ]
        if survivors != [setting["shift_rule"]]:
            raise AssertionError(f"unexpected demo survivors: {survivors}")
        disagreements = {
            name: [
                index - args.demos
                for index in range(args.demos, args.demos + 4)
                if cache[(name, index)] != labels[index]
            ]
            for name in prototype.RIVAL_NAMES
            if name != setting["shift_rule"]
        }
        if not all(disagreements.values()):
            raise AssertionError(f"a rival agrees on all queries: {disagreements}")
        reports.append({
            "settings": setting,
            "demo_survivors": survivors,
            "query_disagreements": disagreements,
            "program_sha256": hashlib.sha256(
                prototype.program(setting).encode()
            ).hexdigest(),
            "label_sha256": hashlib.sha256(
                json.dumps(labels, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        })

    public = {
        "train": episodes[0]["train"],
        "test": [{"input": pair["input"]} for pair in episodes[0]["test"]],
    }
    public_payload = json.loads(public_challenge_bytes(public))
    if any("output" in pair for pair in public_payload["test"]):
        raise AssertionError("query answers leaked into public projection")

    analyses = [prototype.analyze(grid) for grid in inputs]
    result = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": prototype.TASK_ID,
        "seed": args.seed,
        "demos": args.demos,
        "queries": 4,
        "rivals": list(prototype.RIVAL_NAMES),
        "settings": reports,
        "matched_inputs": True,
        "distinct_inputs": len({json.dumps(grid) for grid in inputs}) == len(inputs),
        "query_shapes": [
            [analysis["height"], analysis["width"]]
            for analysis in analyses[args.demos:]
        ],
        "query_densest_indices": [
            analysis["densest_index"] for analysis in analyses[args.demos:]
        ],
        "large_query_nonzero_cells": sum(
            value != 0 for row in inputs[-1] for value in row
        ),
        "exact_30x30_limit": (
            "Impossible under three-row bands with one blank row between bands: "
            "height is 4*b+1. The 29x29 query is the largest square <=30 in "
            "the extended 3x5-section grammar."
        ),
        "public_projection_sha256": hashlib.sha256(
            public_challenge_bytes(public)
        ).hexdigest(),
        "public_projection_query_outputs_omitted": True,
        "racket": {
            key: identity[key]
            for key in (
                "schema", "backend", "protected", "binary_sha256",
                "prelude_sha256", "bridge_sha256", "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            )
            if key in identity
        },
        "racket_evaluations": len(cache),
        "prototype_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "scope": (
            "Finite audit of eight declared rules on one matched 3-demo/4-query "
            "episode per setting; not a universal uniqueness or learning claim."
        ),
    }
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(target),
        "racket_evaluations": result["racket_evaluations"],
        "settings": [row["demo_survivors"] for row in reports],
        "query_shapes": result["query_shapes"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
