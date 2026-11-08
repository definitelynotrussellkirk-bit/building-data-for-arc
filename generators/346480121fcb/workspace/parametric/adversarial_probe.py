#!/usr/bin/env python3
"""Bounded adversarial probes for the selector interpretation family.

This is intentionally reusable by later reviewers. It attacks the minimum
(two-demonstration) lesson with simple selection/transform shortcuts, checks
crossed controls, and tries malformed authored episodes/public projections.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_task_346480121fcb_probe_prototype", HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("unable to load adjacent prototype.py")
PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(PROTOTYPE)

SETTINGS = ({"selection_mode": "color"}, {"selection_mode": "area"})


def _render_object(source: list[list[int]], item: dict[str, Any], key: int) -> list[list[int]]:
    crop = PROTOTYPE._crop(source, item["bbox"])
    return PROTOTYPE._crop_to_content(PROTOTYPE._transform(crop, key))


def _selection_rival(policy: Callable[[list[dict[str, Any]]], dict[str, Any]]):
    def apply(source: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
        profile = PROTOTYPE.analyze_input(source)
        return _render_object(source, policy(profile["objects"]), profile["key"])
    return apply


def _correct_item(profile: dict[str, Any], settings: dict[str, str]) -> dict[str, Any]:
    return profile[f"{settings['selection_mode']}_candidate"]


def _ignore_key(source: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    profile = PROTOTYPE.analyze_input(source)
    item = _correct_item(profile, settings)
    return PROTOTYPE._crop_to_content(PROTOTYPE._crop(source, item["bbox"]))


def _fixed_key(source: list[list[int]], settings: dict[str, str], key: int = 2) -> list[list[int]]:
    profile = PROTOTYPE.analyze_input(source)
    item = _correct_item(profile, settings)
    return _render_object(source, item, key)


RIVALS = {
    "first_object": _selection_rival(lambda objects: objects[0]),
    "last_object": _selection_rival(lambda objects: objects[-1]),
    "topmost_object": _selection_rival(lambda objects: min(objects, key=lambda item: (item["bbox"][0], item["bbox"][1]))),
    "leftmost_object": _selection_rival(lambda objects: min(objects, key=lambda item: (item["bbox"][1], item["bbox"][0]))),
    "largest_object": _selection_rival(lambda objects: max(objects, key=lambda item: (item["size"], -item["index"]))),
    "smallest_object": _selection_rival(lambda objects: min(objects, key=lambda item: (item["size"], item["index"]))),
    "lowest_color": _selection_rival(lambda objects: min(objects, key=lambda item: (item["color"], item["index"]))),
    "highest_color": _selection_rival(lambda objects: max(objects, key=lambda item: (item["color"], -item["index"]))),
    "ignore_transform_key": _ignore_key,
    "always_transform_key_2": _fixed_key,
}


def _fits_lesson(episode: dict[str, Any], rival: Callable) -> bool:
    settings = episode["settings"]
    try:
        return all(rival(pair["input"], settings) == pair["output"] for pair in episode["train"])
    except Exception:
        return False


def _certificate_attacks() -> dict[str, bool]:
    episode = PROTOTYPE.generate_episode(991, {"selection_mode": "color"}, demos=2, queries=4)

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])

    short = copy.deepcopy(episode)
    short["train"] = short["train"][:1]

    boolean = copy.deepcopy(episode)
    boolean["train"][0]["input"][1][1] = True

    boolean_output = copy.deepcopy(episode)
    replaced = False
    for row in boolean_output["train"][0]["output"]:
        for index, value in enumerate(row):
            if value == 0:
                row[index] = False
                replaced = True
                break
        if replaced:
            break
    if not replaced:
        raise AssertionError("probe fixture needs an output zero for the bool-equality attack")

    stale_program = copy.deepcopy(episode)
    stale_program["program"] += "\n"

    wrong_output = copy.deepcopy(episode)
    wrong_output["train"][0]["output"] = [[9]]

    forged_settings = copy.deepcopy(episode)
    forged_settings["settings"] = {"selection_mode": "rank"}

    one = PROTOTYPE.generate_episode(71, {"selection_mode": "area"}, demos=2, queries=1)
    four = PROTOTYPE.generate_episode(71, {"selection_mode": "area"}, demos=2, queries=4)
    visible_one = PROTOTYPE.public_turn(one, 0)
    visible_four = PROTOTYPE.public_turn(four, 0)
    raw = json.dumps(visible_four, sort_keys=True, separators=(",", ":")).encode()

    return {
        "duplicate_input_rejected": any("duplicates" in error for error in PROTOTYPE.episode_errors(duplicate)),
        "one_demo_rejected": any("2..6" in error for error in PROTOTYPE.episode_errors(short)),
        "boolean_cell_rejected": any("exact integer" in error for error in PROTOTYPE.episode_errors(boolean)),
        "boolean_output_rejected": any(
            "output" in error and "exact integer" in error
            for error in PROTOTYPE.episode_errors(boolean_output)
        ),
        "stale_program_rejected": any("program" in error for error in PROTOTYPE.episode_errors(stale_program)),
        "forged_output_rejected": any("output" in error for error in PROTOTYPE.episode_errors(wrong_output)),
        "undeclared_setting_rejected": bool(PROTOTYPE.episode_errors(forged_settings)),
        "first_turn_prefix_stable": visible_one == visible_four,
        "future_private_fields_absent": all(
            token not in raw
            for token in (b"selection_mode", b"program", b"answer", b"query_count", b"source_index")
        ),
    }


def run(*, seed_start: int = 0, seed_count: int = 32) -> dict[str, Any]:
    if type(seed_start) is not int or seed_start < 0:
        raise ValueError("seed_start must be a nonnegative exact integer")
    if type(seed_count) is not int or not 1 <= seed_count <= 4096:
        raise ValueError("seed_count must be an exact integer in 1..4096")

    survivals = {name: 0 for name in RIVALS}
    order_relations: set[str] = set()
    size_relations: set[str] = set()
    color_relations: set[str] = set()
    episodes_checked = 0
    query_disagreements = {name: 0 for name in RIVALS}

    for seed in range(seed_start, seed_start + seed_count):
        for settings in SETTINGS:
            episode = PROTOTYPE.generate_episode(seed, settings, demos=2, queries=4)
            episodes_checked += 1
            for pair in episode["train"]:
                profile = PROTOTYPE.analyze_input(pair["input"])
                color = profile["color_candidate"]
                area = profile["area_candidate"]
                order_relations.add("color_first" if color["index"] < area["index"] else "area_first")
                size_relations.add("color_larger" if color["size"] > area["size"] else "color_smaller")
                color_relations.add("color_higher" if color["color"] > area["color"] else "color_lower")
            for name, rival in RIVALS.items():
                if _fits_lesson(episode, rival):
                    survivals[name] += 1
                try:
                    if any(rival(pair["input"], settings) != pair["output"] for pair in episode["test"]):
                        query_disagreements[name] += 1
                except Exception:
                    query_disagreements[name] += 1

    certificate_attacks = _certificate_attacks()
    crossed = {
        "candidate_scan_order_both_directions": order_relations == {"color_first", "area_first"},
        "candidate_size_relation_both_directions": size_relations == {"color_larger", "color_smaller"},
        "candidate_color_rank_both_directions": color_relations == {"color_higher", "color_lower"},
    }
    passed = (
        all(value == 0 for value in survivals.values())
        and all(value > 0 for value in query_disagreements.values())
        and all(certificate_attacks.values())
        and all(crossed.values())
    )
    return {
        "schema": "346480121fcb-adversarial-probe-v1",
        "status": "passed" if passed else "failed",
        "seed_start": seed_start,
        "seed_count": seed_count,
        "episodes_checked": episodes_checked,
        "minimum_demo_count": 2,
        "queries_per_episode": 4,
        "rival_full_lesson_survivals": survivals,
        "rival_query_disagreements": query_disagreements,
        "certificate_attacks": certificate_attacks,
        "crossed_controls": crossed,
        "finite_limit": "These bounded rivals and seeds do not prove universal uniqueness.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=32)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run(seed_start=args.seed_start, seed_count=args.seed_count)
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
