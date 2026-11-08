#!/usr/bin/env python3
"""Cheap semantic shortcut sweep for the 70abd9105769 family.

The sweep intentionally avoids Racket.  It independently recomputes native
setting identification and tests every task-local Python rival against the
minimum demonstration set.  Run this before the protected-Racket probe so
sampler teaching holes are found cheaply and reproducibly.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_70abd9105769_semantic_prototype", HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _exact_int(value: Any, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer; bool is forbidden")
    return value


def run(seeds: Iterable[int], *, demos: int = 2) -> dict[str, Any]:
    seed_list = list(seeds)
    if not seed_list:
        raise ValueError("seeds must be nonempty")
    for seed in seed_list:
        _exact_int(seed, "seed")
    _exact_int(demos, "demos")
    if not 2 <= demos <= 6:
        raise ValueError("demos must be in 2..6")

    survivor_counts: Counter[str] = Counter()
    survivor_examples: dict[str, dict[str, Any]] = {}
    ambiguous = 0
    episodes = 0
    observations: dict[str, set[Any]] = defaultdict(set)
    rival_names_by_mode: dict[str, set[str]] = defaultdict(set)

    for seed in seed_list:
        for setting in prototype.SETTINGS:
            mode = setting["mode"]
            episode = prototype.generate(seed, setting, demos=demos, queries=4)
            episodes += 1
            train = episode["train"]

            episode_survivors: list[str] = []
            native_survivors = [
                candidate["mode"]
                for candidate in prototype.SETTINGS
                if all(
                    prototype.transform(pair["input"], candidate) == pair["output"]
                    for pair in train
                )
            ]
            if native_survivors != [mode]:
                episode_survivors.extend(
                    f"native:{candidate}"
                    for candidate in native_survivors
                    if candidate != mode
                )

            first_rivals = prototype.shortcut_outputs(train[0]["input"], setting)
            rival_names_by_mode[mode].update(first_rivals)
            for name in sorted(first_rivals):
                if all(
                    prototype.shortcut_outputs(pair["input"], setting)[name]
                    == pair["output"]
                    for pair in train
                ):
                    key = f"{mode}:{name}"
                    episode_survivors.append(key)
                    survivor_counts[key] += 1
                    survivor_examples.setdefault(
                        key,
                        {
                            "seed": seed,
                            "mode": mode,
                            "input_sha256": prototype.grid_sha256(train[0]["input"]),
                        },
                    )

            if episode_survivors:
                ambiguous += 1

            for pair in train:
                facts = prototype.scene_facts(pair["input"])
                observations["target_colors"].add(facts["object_majority_color"])
                observations["pixel_decoy_colors"].add(facts["pixel_majority_color"])
                observations["target_center_bboxes"].add(tuple(facts["target_center_bbox"]))
                observations["all_center_bboxes"].add(tuple(facts["all_center_bbox"]))
                observations["object_count_profiles"].add(
                    tuple(sorted(facts["object_counts"].items()))
                )
                observations["pixel_count_profiles"].add(
                    tuple(sorted(facts["pixel_counts"].items()))
                )
                observations["square_size_profiles"].add(tuple(facts["square_sizes"]))
                observations["grid_shapes"].add(
                    (len(pair["input"]), len(pair["input"][0]))
                )
                observations["target_object_counts"].add(
                    facts["object_counts"][facts["object_majority_color"]]
                )
                observations["target_pixel_counts"].add(
                    facts["pixel_counts"][facts["object_majority_color"]]
                )

    status = "pass" if ambiguous == 0 and not survivor_counts else "fail"
    return {
        "status": status,
        "task_id": prototype.TASK_ID,
        "seeds": seed_list,
        "demos": demos,
        "episodes": episodes,
        "ambiguous_episodes": ambiguous,
        "surviving_rivals": dict(sorted(survivor_counts.items())),
        "survivor_examples": survivor_examples,
        "rival_names": {
            mode: sorted(names) for mode, names in sorted(rival_names_by_mode.items())
        },
        "crossed_controls": {
            name: len(values) for name, values in sorted(observations.items())
        },
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(100)))
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run(args.seeds, demos=args.demos)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
