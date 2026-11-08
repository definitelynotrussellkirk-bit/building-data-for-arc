#!/usr/bin/env python3
"""Bounded, reproducible self-audit for the length-ranked rod family."""
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
ROOT = HOME.parents[1]


def load(name: str, path: Path):
    key = f"_sticks_audit_{name}_{hashlib.sha256(str(path).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(key, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


adapter = load("adapter", BASE / "adapter.py")
engine = load("engine", BASE / "engine.py")


def _wrong_global_longest(grid):
    info = engine.analyze(grid)
    out = engine.solve(grid, "rank_only")
    winner = max(info["rods"], key=lambda r: (r["length"], -r["top"], -r["col"]))
    for r in range(winner["top"], winner["bottom"] + 1):
        out[r][winner["col"]] = 9
    return out



def _paint_selection(grid, selected, *, highlight=None):
    out = [row[:] for row in grid]
    for rod in selected:
        for r in range(rod["top"] + 1, rod["bottom"]):
            out[r][rod["col"]] = rod["endpoint"]
    if highlight is not None:
        rod = selected[highlight]
        for r in range(rod["top"], rod["bottom"] + 1):
            out[r][rod["col"]] = 9
    return out


def _rivals(grid):
    info = engine.analyze(grid)
    colors = sorted(info["key_counts"])
    selections = {}
    for mode in ("longest", "shortest", "ascending_rank", "reading_order"):
        chosen = []
        for color in colors:
            rank = info["key_counts"][color]
            candidates = [dict(r) for r in info["by_color"][color]]
            if mode == "longest":
                pick = candidates[0]
            elif mode == "shortest":
                pick = candidates[-1]
            elif mode == "ascending_rank":
                pick = sorted(candidates, key=lambda r: (r["length"], r["top"], r["col"]))[rank - 1]
            else:
                pick = sorted(candidates, key=lambda r: (r["top"], r["col"]))[rank - 1]
            chosen.append(pick)
        selections[mode] = chosen
    all_rods = [dict(r) for r in info["rods"]]
    selected = [dict(r) for r in info["selected"]]
    canonical = engine.solve(grid, "rank_only")
    shortest_index = min(range(len(selected)), key=lambda i: selected[i]["length"])
    first_index = min(range(len(selected)), key=lambda i: (selected[i]["endpoint"], selected[i]["top"], selected[i]["col"]))
    return {
        "canonical": canonical,
        "alternate": engine.solve(grid, "highlight_longest_selected"),
        "identity": [row[:] for row in grid],
        "always_longest_per_color": _paint_selection(grid, selections["longest"]),
        "always_shortest_per_color": _paint_selection(grid, selections["shortest"]),
        "ascending_length_rank": _paint_selection(grid, selections["ascending_rank"]),
        "reading_order_rank": _paint_selection(grid, selections["reading_order"]),
        "recolor_every_rod": _paint_selection(grid, all_rods),
        "highlight_global_longest_raw": _wrong_global_longest(grid),
        "highlight_shortest_selected": _paint_selection(grid, selected, highlight=shortest_index),
        "highlight_first_color_selected": _paint_selection(grid, selected, highlight=first_index),
    }

def audit() -> dict:
    settings = [dict(row) for row in adapter.SETTINGS]
    jobs = []
    causal = None
    matched = {}
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
                expected_name = "canonical" if setting["finish"] == "rank_only" else "alternate"
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
                selected_lengths = [r["length"] for r in info["selected"]]
                if len(set(selected_lengths)) != len(selected_lengths):
                    raise AssertionError("selected lengths are not unique")
                if max(selected_lengths) >= max(r["length"] for r in info["rods"]):
                    raise AssertionError("global-longest counterfactual is not separated")
                view = adapter.public_view(episode, turn=0, presentation_seed=seed + 11)
                if set(view) != {"train", "test"} or len(view["test"]) != 1 or set(view["test"][0]) != {"input"}:
                    raise AssertionError("public projection leaked private fields")
                if setting["finish"] == "highlight_longest_selected" and causal is None:
                    wrong = _wrong_global_longest(stress["input"])
                    if wrong == stress["output"]:
                        raise AssertionError("counterfactual failed to change output")
                    causal = {
                        "input": stress["input"],
                        "settings": setting,
                        "intermediate_value": {
                            "selected_lengths": selected_lengths,
                            "global_longest_length": max(r["length"] for r in info["rods"]),
                        },
                        "output": stress["output"],
                        "counterfactual_output": wrong,
                        "ablation": "wrong_intermediate",
                    }
                jobs.append({
                    "seed": seed,
                    "demos": demos,
                    "settings": setting,
                    "pairs": demos + 4,
                    "selected_lengths": selected_lengths,
                    "survivors": survivors,
                })
    assert causal is not None
    return {
        "schema": "arcpuzzles-bounded-authoring-audit-v1",
        "status": "passed",
        "task_id": "public_eval_97d7923e",
        "jobs": jobs,
        "job_count": len(jobs),
        "episode_count": len(jobs),
        "pair_claims": sum(j["pairs"] for j in jobs),
        "declared_rivals": [
            "identity", "always_longest_per_color", "always_shortest_per_color",
            "ascending_length_rank", "reading_order_rank", "recolor_every_rod",
            "other_finish", "highlight_global_longest_raw",
            "highlight_shortest_selected", "highlight_first_color_selected"
        ],
        "causal_case": causal,
        "limits": "Finite settings, seeds, counts and constructive grammar; no universal uniqueness claim.",
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
