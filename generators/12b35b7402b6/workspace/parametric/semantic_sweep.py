#!/usr/bin/env python3
"""Bounded semantic shortcut sweep for the 12b35b7402b6 family.

This is intentionally Racket-free so future authoring agents can run hundreds of
seeds cheaply before spending protected-runtime evaluations.  It independently
checks two-demo identification, every declared task-local rival, and whether the
sampler crosses the controls that make rank/position/count shortcuts visible.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_12b35b7402b6_semantic_prototype", HERE / "prototype.py"
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

            # Recompute selection ambiguity independently of the episode's own
            # certificate.  The other native setting is itself a strong rival.
            native_survivors = [
                candidate["mode"]
                for candidate in prototype.SETTINGS
                if all(
                    prototype.transform(pair["input"], candidate) == pair["output"]
                    for pair in train
                )
            ]
            episode_survivors: list[str] = []
            if native_survivors != [mode]:
                for candidate in native_survivors:
                    if candidate != mode:
                        episode_survivors.append(f"native:{candidate}")

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
                observations["marker_spans"].add(facts["marker_span"])
                observations["marker_counts"].add(facts["marker_count"])
                observations["true_payload_ranks"].add(
                    facts["true_payload_position_rank"]
                )
                observations["true_key_sizes"].add(
                    facts["post_stage_largest_red_size"]
                )
                observations["skip_key_sizes"].add(
                    facts["pre_stage_largest_red_size"]
                )
                observations["skip_deltas"].add(
                    facts["post_stage_largest_red_size"]
                    - facts["pre_stage_largest_red_size"]
                )
                observations["connectivity_deltas"].add(
                    facts["post_stage_largest_red8_size"]
                    - facts["post_stage_largest_red_size"]
                )
                observations["touching_red_component_counts"].add(
                    len(facts["touching_red_component_sizes"])
                )
                observations["touching_red_partitions"].add(
                    tuple(facts["touching_red_component_sizes"])
                )
                observations["grid_shapes"].add(
                    (len(pair["input"]), len(pair["input"][0]))
                )

    crossed = {name: len(values) for name, values in sorted(observations.items())}
    return {
        "status": "pass" if ambiguous == 0 else "fail",
        "task_id": prototype.TASK_ID,
        "seeds": seed_list,
        "demos": demos,
        "episodes": episodes,
        "ambiguous_episodes": ambiguous,
        "surviving_rivals": dict(sorted(survivor_counts.items())),
        "survivor_examples": survivor_examples,
        "rivals_attacked": {
            mode: sorted(names) for mode, names in sorted(rival_names_by_mode.items())
        },
        "crossed_controls": crossed,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.count <= 0:
        raise ValueError("count must be positive")
    report = run(range(args.start, args.start + args.count), demos=args.demos)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
