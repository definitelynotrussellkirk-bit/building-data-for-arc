"""Bounded teaching and shortcut audit for the 3194379886a5 prototype."""
from __future__ import annotations

from collections import Counter
import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_audit_3194379886a5_prototype", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rival_output(module, name: str, grid: list[list[int]]) -> list[list[int]]:
    facts = module.analyze(grid)
    if name == "fixed_panel_0":
        selected = 0
    elif name == "fixed_panel_1":
        selected = 1
    elif name == "fixed_panel_2":
        selected = 2
    elif name == "projection_first":
        selected = facts["projection_matches"][0]
    elif name == "cyclic_next":
        selected = (facts["match_index"] + 1) % 3
    elif name == "cyclic_previous":
        selected = (facts["match_index"] - 1) % 3
    else:
        raise ValueError(name)
    return module._paint(
        facts["prototype_cells"][selected],
        facts["panel_size"],
        facts["query_color"],
    )


def run_audit(
    *,
    seeds: Iterable[int] = range(32),
    demo_counts: tuple[int, ...] = (2, 3, 6),
) -> dict[str, Any]:
    module = _load_prototype()
    seed_values = tuple(seeds)
    rivals = (
        "fixed_panel_0",
        "fixed_panel_1",
        "fixed_panel_2",
        "projection_first",
        "cyclic_next",
        "cyclic_previous",
    )
    rival_survivors: Counter[str] = Counter()
    setting_survivors = 0
    projection_shortcut_failures = 0
    pair_count = 0
    max_shape = [0, 0]
    settings = tuple({"selection_rule": rule} for rule in module.SELECTION_RULES)

    for seed in seed_values:
        for demos in demo_counts:
            for selected in settings:
                episode = module.generate(seed, selected, demos=demos, queries=4)
                visible = episode["train"]
                all_pairs = visible + episode["test"]
                pair_count += len(all_pairs)
                for pair in all_pairs:
                    height = len(pair["input"])
                    width = len(pair["input"][0])
                    max_shape = [max(max_shape[0], height), max(max_shape[1], width)]
                    facts = module.analyze(pair["input"])
                    if facts["projection_matches"][0] != facts["match_index"]:
                        projection_shortcut_failures += 1

                finite = [
                    candidate
                    for candidate in settings
                    if all(
                        module.finish_python(pair["input"], candidate) == pair["output"]
                        for pair in visible
                    )
                ]
                if finite == [selected]:
                    setting_survivors += 1

                for rival in rivals:
                    if all(
                        _rival_output(module, rival, pair["input"]) == pair["output"]
                        for pair in visible
                    ):
                        rival_survivors[rival] += 1

    jobs = len(seed_values) * len(demo_counts) * len(settings)
    status = (
        "pass"
        if setting_survivors == jobs and not rival_survivors and max_shape == [6, 27]
        else "fail"
    )
    return {
        "schema": "3194379886a5-bounded-parametric-audit-v1",
        "status": status,
        "scope": "finite declared-setting and shortcut audit; not universal identifiability",
        "seeds": list(seed_values),
        "demo_counts": list(demo_counts),
        "query_count": 4,
        "settings": [setting["selection_rule"] for setting in settings],
        "jobs": jobs,
        "pairs": pair_count,
        "settings_survivors": setting_survivors,
        "declared_rivals": list(rivals),
        "rival_survivors": dict(sorted(rival_survivors.items())),
        "projection_shortcut_failures": projection_shortcut_failures,
        "max_lawful_canvas": max_shape,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=32)
    args = parser.parse_args()
    report = run_audit(seeds=range(args.seeds))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
