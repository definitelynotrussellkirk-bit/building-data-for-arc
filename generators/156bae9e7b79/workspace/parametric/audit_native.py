"""Bounded deterministic self-audit for the adjacent native family.

This deliberately checks the reusable contract surfaces that are easy to lose
between review rounds: stable episode construction, labels, setting separation,
sequential-query projection, the 30x30 boundary and the retained wrong-order
counterfactual.  It is not a universal uniqueness proof.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
TASK_ID = HERE.parents[1].name
_NATIVE_PATH = HERE / "native_family.py"
_SPEC = importlib.util.spec_from_file_location(f"native_audit_target_{TASK_ID}", _NATIVE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {_NATIVE_PATH}")
NATIVE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = NATIVE
_SPEC.loader.exec_module(NATIVE)


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _frozen(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def run_audit(seed_count: int = 32) -> dict[str, Any]:
    """Run a bounded audit and return a deterministic JSON-ready receipt."""
    _exact_int(seed_count, 1, 4096, "seed_count")
    episode_count = 0
    pair_count = 0
    wrong_order_differences = 0
    setting_distinctions = 0
    first_turn_checks = 0
    max_input = [0, 0]

    for seed in range(seed_count):
        for setting in NATIVE.SETTINGS:
            settings = {NATIVE.PARAMETER: setting}
            episode = NATIVE.generate(seed, settings, demos=3, queries=4)
            repeat = NATIVE.generate(seed, settings, demos=3, queries=4)
            if episode != repeat:
                raise AssertionError(f"nondeterministic episode for seed={seed} setting={setting}")
            if len(episode["train"]) != 3 or len(episode["test"]) != 4:
                raise AssertionError("episode count contract changed")
            if episode["program_solution"] != NATIVE.program(settings):
                raise AssertionError("program_solution is not source-bound")
            all_pairs = episode["train"] + episode["test"]
            keys = [_frozen(pair["input"]) for pair in all_pairs]
            if len(keys) != len(set(keys)):
                raise AssertionError(f"duplicate input for seed={seed} setting={setting}")
            for pair in all_pairs:
                if pair["output"] != NATIVE.solve(deepcopy(pair["input"]), setting):
                    raise AssertionError("stored label differs from Python mirror")
                h, w = len(pair["input"]), len(pair["input"][0])
                max_input = [max(max_input[0], h), max(max_input[1], w)]
                if NATIVE.solve_wrong_order(pair["input"]) != NATIVE.solve(
                    pair["input"], "highlight_projected_majority"
                    if TASK_ID == "156bae9e7b79"
                    else "highlight_visible_majority",
                ):
                    wrong_order_differences += 1
            other = next(candidate for candidate in NATIVE.SETTINGS if candidate != setting)
            for pair in episode["train"]:
                if NATIVE.solve(pair["input"], other) == pair["output"]:
                    raise AssertionError("visible demonstration does not distinguish the settings")
                setting_distinctions += 1

            public = NATIVE.public_turn(episode, 0)
            if set(public) != {"train", "test"} or len(public["test"]) != 1:
                raise AssertionError("public projection shape changed")
            if set(public["test"][0]) != {"input"}:
                raise AssertionError("public query leaks a label")
            text = _frozen(public)
            for secret in ("settings", "program_solution", NATIVE.PARAMETER, "rule!"):
                if secret in text:
                    raise AssertionError(f"public projection leaks {secret}")
            single = NATIVE.generate(seed, settings, demos=3, queries=1)
            if public != NATIVE.public_turn(single, 0):
                raise AssertionError("first turn differs between one-query and four-query use")
            first_turn_checks += 1
            last = episode["test"][-1]["input"]
            if (len(last), len(last[0])) != (30, 30):
                raise AssertionError("fourth private query is no longer the 30x30 boundary")
            episode_count += 1
            pair_count += len(all_pairs)

    if wrong_order_differences < seed_count:
        raise AssertionError("wrong-order witness did not diverge often enough")
    return {
        "schema": "arcpuzzles-native-bounded-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "seed_count": seed_count,
        "settings": list(NATIVE.SETTINGS),
        "episode_count": episode_count,
        "pair_count": pair_count,
        "setting_distinctions": setting_distinctions,
        "first_turn_checks": first_turn_checks,
        "wrong_order_differences": wrong_order_differences,
        "maximum_input_shape": max_input,
        "scope_note": "bounded deterministic audit; not a universal uniqueness proof",
    }


def write_receipt(receipt: dict[str, Any], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=32, help="number of consecutive seeds from zero")
    parser.add_argument("--out", type=Path, required=True, help="JSON receipt path")
    args = parser.parse_args(argv)
    receipt = run_audit(args.seeds)
    write_receipt(receipt, args.out)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
