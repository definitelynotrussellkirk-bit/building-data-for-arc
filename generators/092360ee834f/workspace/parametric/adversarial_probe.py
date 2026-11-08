#!/usr/bin/env python3
"""Bounded adversarial review for 092360ee834f's scan-order family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time
from typing import Any, Callable

from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "092360ee834f"
HERE = Path(__file__).resolve().parent


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_adversarial_092360ee834f", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _blank(grid):
    return [[0] * len(grid[0]) for _ in grid]


def _paint(grid, cells):
    out = _blank(grid)
    if cells:
        for r, c in cells:
            out[r][c] = 8
    return out


def _choose(items, order):
    if not items:
        return None
    return items[0] if order == "first" else items[-1]


def _wrong_models(proto) -> dict[str, Callable[[list[list[int]], dict[str, str]], list[list[int]]]]:
    def green(grid, connectivity=4):
        return proto._components(grid, color=3, connectivity=connectivity)

    def target_row(grid):
        return sum(value == 1 for value in grid[0])

    def fixed_first_green(grid, setting):
        return _paint(grid, _choose(green(grid), setting["match_order"]))

    def count_all_ones(grid, setting):
        target = sum(value == 1 for row in grid for value in row)
        return _paint(grid, _choose([c for c in green(grid) if len(c) == target], setting["match_order"]))

    def count_nonzero_header(grid, setting):
        target = sum(value != 0 for value in grid[0])
        return _paint(grid, _choose([c for c in green(grid) if len(c) == target], setting["match_order"]))

    def eight_connected(grid, setting):
        target = target_row(grid)
        components = green(grid, connectivity=8)
        return _paint(grid, _choose([c for c in components if len(c) == target], setting["match_order"]))

    def any_color_component(grid, setting):
        target = target_row(grid)
        components = proto._components(grid, color=None, connectivity=4)
        return _paint(grid, _choose([c for c in components if len(c) == target], setting["match_order"]))

    def fixed_target_four(grid, setting):
        return _paint(grid, _choose([c for c in green(grid) if len(c) == 4], setting["match_order"]))

    def largest_green(grid, setting):
        components = green(grid)
        if not components:
            return _blank(grid)
        size = max(map(len, components))
        return _paint(grid, _choose([c for c in components if len(c) == size], setting["match_order"]))

    def leftmost_match(grid, setting):
        target = target_row(grid)
        matches = [c for c in green(grid) if len(c) == target]
        chosen = min(matches, key=lambda cells: min(c for _, c in cells)) if matches else None
        return _paint(grid, chosen)

    def rightmost_match(grid, setting):
        target = target_row(grid)
        matches = [c for c in green(grid) if len(c) == target]
        chosen = max(matches, key=lambda cells: max(c for _, c in cells)) if matches else None
        return _paint(grid, chosen)

    return {
        "ignore_area_choose_ordered_green": fixed_first_green,
        "count_all_ones": count_all_ones,
        "count_nonzero_header": count_nonzero_header,
        "eight_connected_green": eight_connected,
        "ignore_color_component": any_color_component,
        "fixed_target_four": fixed_target_four,
        "largest_green": largest_green,
        "leftmost_match": leftmost_match,
        "rightmost_match": rightmost_match,
    }


def _expect_value_error(fn, label: str) -> str:
    try:
        fn()
    except ValueError as exc:
        return f"{label}: {exc}"
    raise AssertionError(f"{label} unexpectedly succeeded")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    proto = _load()
    started = time.monotonic()
    models = _wrong_models(proto)

    episodes_checked = 0
    input_pairs_checked = 0
    shortcut_checks = 0
    shortcut_rejections: dict[str, int] = {name: 0 for name in models}
    ambiguous: list[dict[str, Any]] = []
    stress_profiles: list[dict[str, Any]] = []

    # Smallest promised lesson first, then count corners and fresh seeds.
    for seed in range(8):
        for demos in (2, 3, 6):
            settings_episodes = [
                proto.generate(seed, setting, demos=demos, queries=4)
                for setting in proto.SETTINGS
            ]
            first_inputs = [pair["input"] for pair in settings_episodes[0]["train"] + settings_episodes[0]["test"]]
            last_inputs = [pair["input"] for pair in settings_episodes[1]["train"] + settings_episodes[1]["test"]]
            assert first_inputs == last_inputs
            input_pairs_checked += len(first_inputs)
            for episode in settings_episodes:
                episodes_checked += 1
                setting = episode["settings"]
                assert episode["certificate"]["survivors"] == [setting]
                for name, predict in models.items():
                    fits = all(predict(pair["input"], setting) == pair["output"] for pair in episode["train"])
                    changes_query = any(predict(pair["input"], setting) != pair["output"] for pair in episode["test"])
                    shortcut_checks += 1
                    if fits and changes_query:
                        ambiguous.append(
                            {
                                "seed": seed,
                                "demos": demos,
                                "settings": setting,
                                "model": name,
                            }
                        )
                    if not fits:
                        shortcut_rejections[name] += 1
                stress_profiles.append(proto.analyze_scene(episode["test"][3]["input"]))

    if ambiguous:
        raise AssertionError(f"wrong rules fit all demos and change a query: {ambiguous[:5]}")
    if any(count == 0 for count in shortcut_rejections.values()):
        raise AssertionError(f"never rejected shortcut: {shortcut_rejections}")

    # Query-prefix and independent count corners.
    prefix_checks = 0
    for seed in range(4):
        for setting in proto.SETTINGS:
            one = proto.generate(seed + 100, setting, demos=2, queries=1)
            eight = proto.generate(seed + 100, setting, demos=6, queries=8)
            assert one["test"] == eight["test"][:1]
            prefix_checks += 1

    # Crossed controls: change k at fixed dimensions/profile and vary nuisance
    # geometry at fixed k. Both must change the selected intermediate/output.
    crossed = []
    for target_a, target_b in ((3, 6), (4, 7)):
        a = proto.sample_input(211, "query", 0, target_size=target_a)
        b = proto.sample_input(211, "query", 0, target_size=target_b)
        pa, pb = proto.analyze_scene(a), proto.analyze_scene(b)
        assert (pa["grid_h"], pa["grid_w"]) == (pb["grid_h"], pb["grid_w"])
        assert pa["target_size"] == target_a and pb["target_size"] == target_b
        assert proto.transform(a, {"match_order": "first"}) != proto.transform(
            b, {"match_order": "first"}
        )
        crossed.append({"fixed_dims": [pa["grid_h"], pa["grid_w"]], "targets": [target_a, target_b]})
    fixed_target_ids = {
        proto.digest(proto.sample_input(seed, "query", 0, target_size=4))
        for seed in range(220, 226)
    }
    assert len(fixed_target_ids) == 6

    # Public/private projection and adversarial verifier mutations.
    base = proto.generate(307, {"match_order": "first"}, demos=2, queries=4)
    public_before = public_challenge_bytes(base)
    private_mutation = copy.deepcopy(base)
    private_mutation["settings"] = {"match_order": "last"}
    private_mutation["program_solution"] = "forged private program"
    private_mutation["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(private_mutation) == public_before
    assert public_challenge_id(private_mutation) == public_challenge_id(base)
    visible_mutation = copy.deepcopy(base)
    visible_mutation["train"][0]["output"] = [[9]]
    assert public_challenge_id(visible_mutation) != public_challenge_id(base)

    corrupt_label = copy.deepcopy(base)
    corrupt_label["train"][0]["output"] = [[0]]
    duplicate = copy.deepcopy(base)
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    forged_program = copy.deepcopy(base)
    forged_program["program_solution"] = proto.program({"match_order": "last"})
    forged_certificate = copy.deepcopy(base)
    forged_certificate["certificate"] = {"survivors": [{"match_order": "last"}]}
    assert proto.certify(forged_certificate)["survivors"] == [{"match_order": "first"}]
    rejections = [
        _expect_value_error(lambda: proto.certify(corrupt_label), "corrupt label"),
        _expect_value_error(lambda: proto.certify(duplicate), "duplicate input"),
        _expect_value_error(lambda: proto.certify(forged_program), "forged program"),
        _expect_value_error(lambda: proto.generate(0, {"match_order": "first"}, True, 4), "boolean demos"),
        _expect_value_error(lambda: proto.transform([[0.0]], {"match_order": "first"}), "float grid"),
    ]

    # Protected Racket replay on both settings, including the 30x30 query.
    racket_rows = []
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=60, max_calls_before_restart=256) as bridge:
        for setting in proto.SETTINGS:
            episode = proto.generate(401, setting, demos=2, queries=4)
            cert = proto.certify(
                episode,
                execute=lambda source, grid: proto.execute_rule(source, grid, bridge=bridge),
            )
            racket_rows.append({"settings": setting, "survivors": cert["survivors"]})
        runtime = bridge.runtime_identity

    # Summarize only compact profile extrema; the actual inputs remain reproducible.
    stress = [row for row in stress_profiles if row["grid_h"] == 30]
    result = {
        "schema": "arcpuzzles-parametric-adversarial-v1",
        "task_id": TASK_ID,
        "status": "pass",
        "attempted_surfaces": [
            "minimum two-demo lessons and 3/6-demo boundaries across eight seeds",
            "nine wrong-rule families: area/count/color/connectivity/position shortcuts",
            "crossed target-vs-geometry controls, query-prefix independence, and 30x30 spread",
            "corrupt labels, duplicate inputs, forged programs/certificates, numeric types, and public/private leakage",
            "protected Racket replay for both episode settings",
        ],
        "episodes_checked": episodes_checked,
        "input_pairs_checked": input_pairs_checked,
        "shortcut_checks": shortcut_checks,
        "shortcut_rejections": shortcut_rejections,
        "ambiguous_wrong_rules": ambiguous,
        "prefix_checks": prefix_checks,
        "crossed_controls": crossed,
        "stress_summary": {
            "count": len(stress),
            "min_body_nonzero": min(row["body_nonzero_count"] for row in stress),
            "min_bbox_height": min(row["body_bbox_height"] for row in stress),
            "min_bbox_width": min(row["body_bbox_width"] for row in stress),
            "min_green_components": min(row["green_component_count"] for row in stress),
        },
        "rejections": rejections,
        "racket": racket_rows,
        "runtime": runtime,
        "finite_limits": (
            "Bounded probes disprove the listed rivals on sampled lessons; they do not prove "
            "universal semantic uniqueness for every conceivable wrong rule."
        ),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "source_sha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ("prototype.py", "adapter.py", "promotion.json")
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "episodes_checked": episodes_checked,
                "shortcut_checks": shortcut_checks,
                "ambiguous_wrong_rules": len(ambiguous),
                "stress_summary": result["stress_summary"],
                "elapsed_seconds": result["elapsed_seconds"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
