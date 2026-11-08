#!/usr/bin/env python3
"""Bounded, reproducible self-audit for the cropped spiral family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
HOME = BASE.parents[1]


def load(name: str, path: Path):
    key = f"_spiral_audit_{name}_{hashlib.sha256(str(path).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(key, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


adapter = load("adapter", BASE / "adapter.py")
engine = load("engine", BASE / "engine.py")


def _wrong_fixed_north(grid):
    info = engine.analyze(grid)
    visible = [set(branch) for branch in info["visible_branches"]]
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for i, branch in enumerate(visible):
        for r, c in branch:
            out[r][c] = 9 if i == 0 else 8
    return out



def _render(info, highlighted=None):
    h, w = len(info["grid"]), len(info["grid"][0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    highlights = set() if highlighted is None else set(highlighted)
    for i, branch in enumerate(info["visible_branches"]):
        for r, c in branch:
            out[r][c] = 9 if i in highlights else 8
    return out


def _rivals(grid):
    info = engine.analyze(grid)
    counts = info["visible_counts"]
    max_i = counts.index(max(counts))
    min_i = counts.index(min(counts))
    return {
        "canonical": _render(info),
        "alternate": _render(info, [max_i]),
        "identity": [row[:] for row in grid],
        "fixed_north": _render(info, [0]),
        "fixed_east": _render(info, [1]),
        "fixed_south": _render(info, [2]),
        "fixed_west": _render(info, [3]),
        "highlight_least_visible": _render(info, [min_i]),
        "highlight_every_branch": _render(info, [0, 1, 2, 3]),
    }

def audit() -> dict:
    settings = [dict(row) for row in adapter.SETTINGS]
    jobs = []
    causal = None
    matched = {}
    winner_classes = set()
    for seed in (0, 17, 43, 97):
        for demos in (2, 3, 6):
            for setting in settings:
                episode = adapter.generate(seed, setting, demos, 4)
                inputs = [p["input"] for p in episode["train"] + episode["test"]]
                digests = [hashlib.sha256(json.dumps(g, separators=(",", ":")).encode()).hexdigest() for g in inputs]
                if len(set(digests)) != len(digests):
                    raise AssertionError("duplicate lesson input")
                key = (seed, demos)
                if key in matched and matched[key] != inputs:
                    raise AssertionError("settings changed input stream")
                matched[key] = copy.deepcopy(inputs)
                expected_name = "canonical" if setting["finish"] == "spiral_only" else "alternate"
                rival_names = list(_rivals(episode["train"][0]["input"]))
                survivors = [
                    name for name in rival_names
                    if all(_rivals(pair["input"])[name] == pair["output"] for pair in episode["train"])
                ]
                if survivors != [expected_name]:
                    raise AssertionError(f"finite rivals not identified: {survivors}")
                stress = episode["test"][-1]
                if (len(stress["input"]), len(stress["input"][0])) != (30, 30):
                    raise AssertionError("missing exact 30x30 stress query")
                info = engine.analyze(stress["input"])
                counts = info["visible_counts"]
                if len(set(counts)) != 4:
                    raise AssertionError("visible branch counts must be unique")
                winner = counts.index(max(counts))
                winner_classes.add(winner)
                if not any(r < 0 or c < 0 or r >= 30 or c >= 30 for b in info["relative_branches"] for r, c in b):
                    raise AssertionError("spiral did not extend beyond canvas")
                view = adapter.public_view(episode, turn=0, presentation_seed=seed + 13)
                if set(view) != {"train", "test"} or len(view["test"]) != 1 or set(view["test"][0]) != {"input"}:
                    raise AssertionError("public projection leaked private fields")
                if setting["finish"] == "highlight_most_visible" and winner != 0 and causal is None:
                    wrong = _wrong_fixed_north(stress["input"])
                    if wrong == stress["output"]:
                        raise AssertionError("counterfactual failed to change output")
                    causal = {
                        "input": stress["input"],
                        "settings": setting,
                        "intermediate_value": {"visible_counts": counts, "winner": winner},
                        "output": stress["output"],
                        "counterfactual_output": wrong,
                        "ablation": "wrong_intermediate",
                    }
                jobs.append({
                    "seed": seed,
                    "demos": demos,
                    "settings": setting,
                    "pairs": demos + 4,
                    "visible_counts": counts,
                    "winner": winner,
                    "survivors": survivors,
                })
    if causal is None:
        # Deterministically search the audited jobs' generated bank for a non-north winner.
        for seed in range(128):
            ep = adapter.generate(seed, {"finish": "highlight_most_visible"}, 2, 4)
            for pair in ep["train"] + ep["test"]:
                info = engine.analyze(pair["input"])
                winner = info["visible_counts"].index(max(info["visible_counts"]))
                if winner != 0:
                    wrong = _wrong_fixed_north(pair["input"])
                    causal = {
                        "input": pair["input"],
                        "settings": {"finish": "highlight_most_visible"},
                        "intermediate_value": {"visible_counts": info["visible_counts"], "winner": winner},
                        "output": pair["output"],
                        "counterfactual_output": wrong,
                        "ablation": "wrong_intermediate",
                    }
                    break
            if causal is not None:
                break
    assert causal is not None
    return {
        "schema": "arcpuzzles-bounded-authoring-audit-v1",
        "status": "passed",
        "task_id": "public_eval_da515329",
        "jobs": jobs,
        "job_count": len(jobs),
        "episode_count": len(jobs),
        "pair_claims": sum(j["pairs"] for j in jobs),
        "winner_classes": sorted(winner_classes),
        "declared_rivals": [
            "identity", "fixed_north", "fixed_east", "fixed_south", "fixed_west",
            "highlight_least_visible", "highlight_every_branch", "other_finish"
        ],
        "causal_case": causal,
        "limits": "Finite settings, seeds, counts and sampled placements; no universal uniqueness claim.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit()
    text = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
