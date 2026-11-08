"""Bounded, deterministic self-audit for the connectivity family.

This checks the Python claim surface and semantic scene roles while retaining a
small replay receipt.  Native qualification separately executes every label
through protected Racket.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

HOME = Path(__file__).resolve().parent


def _load_impl():
    path = HOME / "prototype.py"
    spec = importlib.util.spec_from_file_location("_d784_self_audit_impl", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run(
    *,
    seeds: Iterable[int] = (0, 17, 41, 97),
    demo_counts: Iterable[int] = (3, 6),
) -> dict[str, Any]:
    impl = _load_impl()
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    results: list[dict[str, Any]] = []

    for seed in seeds:
        for demos in demo_counts:
            episodes = [impl.generate(seed, settings, demos, 4) for settings in impl.SETTING_OBJECTS]
            input_banks = [
                [pair["input"] for split in ("train", "test") for pair in episode[split]]
                for episode in episodes
            ]
            if any(bank != input_banks[0] for bank in input_banks[1:]):
                raise AssertionError("inputs changed with the hidden setting")
            if demos == min(demo_counts):
                long = impl.generate(seed, impl.DEFAULT, max(demo_counts), 4)
                if episodes[0]["train"] != long["train"][:demos] or episodes[0]["test"] != long["test"]:
                    raise AssertionError("demo prefixes or query bank are unstable")

            for settings, episode, inputs in zip(impl.SETTING_OBJECTS, episodes, input_banks):
                replay = impl.generate(seed, settings, demos, 4)
                if replay != episode:
                    raise AssertionError("generation is not deterministic")
                if episode["certificate"]["survivors"] != [settings]:
                    raise AssertionError("selected setting is not uniquely identified")
                if episode["certificate"]["shortcut_survivors"]:
                    raise AssertionError("declared shortcut survived demonstrations")
                if len({_digest(grid) for grid in inputs}) != len(inputs):
                    raise AssertionError("episode contains duplicate inputs")
                for split in ("train", "test"):
                    for pair in episode[split]:
                        roles = impl.analyze(pair["input"])
                        if not all(
                            roles[name]
                            for name in (
                                "isolated_both",
                                "diagonal_only_groups",
                                "cardinal_components",
                                "non_red_distractors",
                            )
                        ):
                            raise AssertionError("input is missing a semantic role")
                        if pair["output"] != impl.apply_rule(pair["input"], settings):
                            raise AssertionError("claim label disagrees with Python rule")
                stress = episode["test"][-1]
                stress_roles = impl.analyze(stress["input"])
                results.append(
                    {
                        "seed": seed,
                        "demos": demos,
                        "settings": settings,
                        "query_count": len(episode["test"]),
                        "input_count": len(inputs),
                        "unique_input_count": len({_digest(grid) for grid in inputs}),
                        "certificate_ok": True,
                        "stress_dimensions": [len(stress["input"]), len(stress["input"][0])],
                        "stress_red_cells": sum(value == 2 for row in stress["input"] for value in row),
                        "stress_distractors": len(stress_roles["non_red_distractors"]),
                        "stress_diagonal_groups": len(stress_roles["diagonal_only_groups"]),
                        "stress_cardinal_components": len(stress_roles["cardinal_components"]),
                        "program_sha256": hashlib.sha256(
                            episode["program_solution"].encode("utf-8")
                        ).hexdigest(),
                        "episode_sha256": _digest(episode),
                    }
                )

    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": impl.TASK_ID,
        "passed": True,
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "settings": list(impl.SETTING_OBJECTS),
        "jobs": len(results),
        "results": results,
        "limits": {
            "python_claims_only": True,
            "protected_racket_replay": False,
            "note": "Native qualification is required for protected Racket replay.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--demos", action="append", type=int, dest="demo_counts")
    args = parser.parse_args()
    receipt = run(
        seeds=tuple(args.seeds) if args.seeds else (0, 17, 41, 97),
        demo_counts=tuple(args.demo_counts) if args.demo_counts else (3, 6),
    )
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
