"""Bounded teaching and shortcut audit for the bdb419bbf286 prototype."""
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
    spec = importlib.util.spec_from_file_location("_audit_bdb419bbf286_prototype", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_audit(
    *,
    seeds: Iterable[int] = range(32),
    demo_counts: tuple[int, ...] = (2, 3, 6),
) -> dict[str, Any]:
    module = _load_prototype()
    seed_values = tuple(seeds)
    rivals = (
        "fixed_one",
        "fixed_two",
        "fixed_four",
        "fixed_five",
        "fixed_six",
        "last_marker_fixed_three",
        "last_marker_to_boundary",
    )
    settings = tuple({"repeat_rule": rule} for rule in module.REPEAT_RULES)
    rival_survivors: Counter[str] = Counter()
    setting_survivors = 0
    last_marker_failures = 0
    pair_count = 0
    thirty_by_thirty_pairs = 0
    max_shape = [0, 0]

    for seed in seed_values:
        for demos in demo_counts:
            for selected in settings:
                episode = module.generate(seed, selected, demos=demos, queries=4)
                visible = episode["train"]
                all_pairs = visible + episode["test"]
                pair_count += len(all_pairs)
                corresponding_last_rule = (
                    "last_marker_fixed_three"
                    if selected["repeat_rule"] == "fixed_three"
                    else "last_marker_to_boundary"
                )
                for pair in all_pairs:
                    height = len(pair["input"])
                    width = len(pair["input"][0])
                    max_shape = [max(max_shape[0], height), max(max_shape[1], width)]
                    thirty_by_thirty_pairs += (height, width) == (30, 30)
                    if module.finish_python(
                        pair["input"], {"repeat_rule": corresponding_last_rule}
                    ) != pair["output"]:
                        last_marker_failures += 1

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
                        module.finish_python(pair["input"], {"repeat_rule": rival})
                        == pair["output"]
                        for pair in visible
                    ):
                        rival_survivors[rival] += 1

    jobs = len(seed_values) * len(demo_counts) * len(settings)
    status = (
        "pass"
        if setting_survivors == jobs
        and not rival_survivors
        and last_marker_failures == pair_count
        and max_shape == [30, 30]
        else "fail"
    )
    return {
        "schema": "bdb419bbf286-bounded-parametric-audit-v1",
        "status": status,
        "scope": "finite declared-setting and shortcut audit; not universal identifiability",
        "seeds": list(seed_values),
        "demo_counts": list(demo_counts),
        "query_count": 4,
        "settings": [setting["repeat_rule"] for setting in settings],
        "jobs": jobs,
        "pairs": pair_count,
        "settings_survivors": setting_survivors,
        "declared_rivals": list(rivals),
        "rival_survivors": dict(sorted(rival_survivors.items())),
        "last_marker_failures": last_marker_failures,
        "thirty_by_thirty_pairs": thirty_by_thirty_pairs,
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
