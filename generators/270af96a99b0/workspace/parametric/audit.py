"""Bounded matched-input and finite-rival audit for the native family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

_HERE = Path(__file__).resolve().parent
_SETTINGS = ("source_position", "smaller_area")


def _load(filename: str):
    path = _HERE / filename
    name = "_audit_270af96a99b0_" + filename.replace(".", "_") + hashlib.sha256(str(path).encode()).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def run(*, seeds: Iterable[int] = range(32), demo_counts: Iterable[int] = (2, 3, 6)) -> dict:
    adapter = _load("adapter.py")
    rivals = _load("rivals.py").RIVALS
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    survivors = []
    matched = []
    prefixes = []
    large = []
    episodes = 0
    pairs = 0
    setting_disagreements = 0

    for seed in seeds:
        full_by_setting = {
            setting: adapter.generate(seed, {"tie_break": setting}, 6, 4)
            for setting in _SETTINGS
        }
        if (
            _inputs(full_by_setting[_SETTINGS[0]], "train")
            != _inputs(full_by_setting[_SETTINGS[1]], "train")
            or _inputs(full_by_setting[_SETTINGS[0]], "test")
            != _inputs(full_by_setting[_SETTINGS[1]], "test")
        ):
            matched.append({"seed": seed, "reason": "settings changed inputs"})
        for setting in _SETTINGS:
            full = full_by_setting[setting]
            large_inputs = [grid for grid in _inputs(full, "test") if len(grid) == 30 and len(grid[0]) == 30]
            if len(large_inputs) != 1:
                large.append({"seed": seed, "setting": setting, "count": len(large_inputs)})
            for demos in demo_counts:
                episode = adapter.generate(seed, {"tie_break": setting}, demos, 4)
                episodes += 1
                pairs += demos + 4
                if _inputs(episode, "train") != _inputs(full, "train")[:demos] or _inputs(episode, "test") != _inputs(full, "test"):
                    prefixes.append({"seed": seed, "setting": setting, "demos": demos})
                for name, rival in rivals.items():
                    if name == setting:
                        continue
                    fits = all(rival(pair["input"]) == pair["output"] for pair in episode["train"])
                    changed = [
                        index
                        for index, pair in enumerate(episode["test"])
                        if rival(pair["input"]) != pair["output"]
                    ]
                    if fits and changed:
                        survivors.append(
                            {
                                "seed": seed,
                                "demos": demos,
                                "setting": setting,
                                "rival": name,
                                "changed_queries": changed,
                            }
                        )
                other = _SETTINGS[1] if setting == _SETTINGS[0] else _SETTINGS[0]
                if all(
                    rivals[other](pair["input"]) != pair["output"]
                    for pair in episode["train"]
                ):
                    setting_disagreements += 1
    result = {
        "schema": "arcpuzzles-parametric-finite-audit-v1",
        "task_id": "270af96a99b0",
        "status": "passed" if not any((survivors, matched, prefixes, large)) else "failed",
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "settings": list(_SETTINGS),
        "episodes": episodes,
        "pairs": pairs,
        "finite_rivals": sorted(rivals),
        "query_changing_survivors": survivors,
        "matched_input_failures": matched,
        "prefix_failures": prefixes,
        "large_query_failures": large,
        "setting_disagreement_episodes": setting_disagreements,
        "limits": "Finite Python mirror audit only; protected Racket qualification remains authoritative.",
    }
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--seeds", type=int, default=32)
    args = parser.parse_args(argv)
    result = run(seeds=range(args.seeds))
    text = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
