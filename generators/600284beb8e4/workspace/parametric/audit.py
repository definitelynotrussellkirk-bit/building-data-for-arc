#!/usr/bin/env python3
"""Bounded adversarial audit for the 600284beb8e4 parametric family.

This is intentionally task-local and reusable by later reviewers.  It attacks
minimum lessons with finite plausible rivals, checks matched inputs/count edges,
stresses the substantive 30x30 query, and can replay a small min/max matrix
through the checkout's protected Racket runtime.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def _load_adapter():
    spec = importlib.util.spec_from_file_location("audit_adapter_600284beb8e4", HERE / "adapter.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def run_python(seed_count: int) -> dict:
    adapter = _load_adapter()
    episodes = 0
    named_attacks = 0
    wrong_setting_checks = 0
    matched_input_checks = 0
    stress_checks = 0
    crossed_by_profile: dict[tuple[int, int, str], set[str]] = {}
    crossed_by_side: dict[tuple[int, int, str], set[str]] = {}

    for seed in range(seed_count):
        baseline_inputs = None
        for demos in (2, 6):
            generated = {
                setting: adapter.generate(seed, {"edge_policy": setting}, demos, 4)
                for setting in adapter.EDGE_POLICIES
            }
            episodes += len(generated)

            inputs = [pair["input"] for pair in generated["full"]["train"] + generated["full"]["test"]]
            if baseline_inputs is None:
                baseline_inputs = inputs
            for setting, episode in generated.items():
                current_inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
                assert current_inputs == inputs
                assert len({_freeze(grid) for grid in current_inputs}) == demos + 4
                matched_input_checks += 1

                survivors = [
                    candidate
                    for candidate in adapter.EDGE_POLICIES
                    if all(
                        adapter.rule_mirror(pair["input"], candidate) == pair["output"]
                        for pair in episode["train"]
                    )
                ]
                assert survivors == [setting], (seed, demos, setting, survivors)
                wrong_setting_checks += len(adapter.EDGE_POLICIES) - 1

                q4 = episode["test"][3]["input"]
                scene4 = adapter.inspect_scene(q4)
                assert (len(q4), len(q4[0])) == (30, 30)
                assert scene4["overlap_height"] >= 8 and scene4["overlap_width"] >= 8
                assert sum(cell != 0 for row in q4 for cell in row) >= 100
                stress_checks += 1

                if setting in {"near_cue", "far_cue"}:
                    train = episode["train"]
                    rivals: dict[str, Callable] = {
                        **{f"fixed_{side}": (lambda grid, side=side: adapter.fixed_edge_rival(grid, side))
                           for side in adapter.CUE_SIDES},
                        "color2_near": adapter.color2_near_rival,
                        "color2_far": adapter.color2_far_rival,
                        "full_overlap": lambda grid: adapter.rule_mirror(grid, "full"),
                        "opposite_cue_policy": lambda grid, setting=setting: adapter.rule_mirror(
                            grid, "far_cue" if setting == "near_cue" else "near_cue"
                        ),
                    }
                    first_side = adapter.inspect_scene(train[0]["input"])["cue_side"]
                    rivals["freeze_first_demo_side"] = (
                        lambda grid, side=first_side, setting=setting: adapter.fixed_edge_rival(
                            grid, side if setting == "near_cue" else adapter._opposite(side)
                        )
                    )
                    for name, rival in rivals.items():
                        assert any(rival(pair["input"]) != pair["output"] for pair in train), (
                            seed, demos, setting, name
                        )
                        named_attacks += 1

            # Matched inputs must actually expose all three rule settings.
            for index in range(demos + 4):
                outputs = {
                    _freeze((generated[setting]["train"] + generated[setting]["test"])[index]["output"])
                    for setting in adapter.EDGE_POLICIES
                }
                assert len(outputs) == 3

        # Cross controls over fixed query dimensions: gather profile/side pairs.
        episode = adapter.generate(seed, {"edge_policy": "near_cue"}, 2, 4)
        for pair in episode["test"]:
            grid = pair["input"]
            scene = adapter.inspect_scene(grid)
            h, w = len(grid), len(grid[0])
            b2, b3 = scene["bbox2"], scene["bbox3"]
            profile_signature = json.dumps([b2[2]-b2[0], b2[3]-b2[1], b3[2]-b3[0], b3[3]-b3[1]])
            side = scene["cue_side"]
            crossed_by_profile.setdefault((h, w, profile_signature), set()).add(side)
            crossed_by_side.setdefault((h, w, side), set()).add(profile_signature)

    assert any(len(sides) >= 2 for sides in crossed_by_profile.values())
    assert any(len(profiles) >= 2 for profiles in crossed_by_side.values())

    # Strict API/certificate-adjacent malformed requests.
    adapter = _load_adapter()
    bad_calls = [
        lambda: adapter.generate(True, {"edge_policy": "full"}, 2, 4),
        lambda: adapter.generate(0, {"edge_policy": "full"}, 1, 4),
        lambda: adapter.generate(0, {"edge_policy": "full"}, 7, 4),
        lambda: adapter.generate(0, {"edge_policy": "full"}, 2, 0),
        lambda: adapter.generate(0, {"edge_policy": "full"}, 2, 5),
        lambda: adapter.generate(0, {"edge_policy": "near"}, 2, 4),
        lambda: adapter.generate(0, {"edge_policy": "full", "extra": 1}, 2, 4),
    ]
    rejected = 0
    for call in bad_calls:
        try:
            call()
        except (TypeError, ValueError):
            rejected += 1
        else:
            raise AssertionError("malformed request was accepted")

    return {
        "status": "passed",
        "scope": "finite adversarial Python audit; not universal uniqueness proof",
        "seed_count": seed_count,
        "episodes": episodes,
        "named_shortcut_attacks": named_attacks,
        "wrong_setting_checks": wrong_setting_checks,
        "matched_input_checks": matched_input_checks,
        "substantive_30x30_checks": stress_checks,
        "malformed_requests_rejected": rejected,
        "crossed_control_profile_groups": sum(len(v) >= 2 for v in crossed_by_profile.values()),
        "crossed_control_side_groups": sum(len(v) >= 2 for v in crossed_by_side.values()),
    }


def run_racket() -> dict:
    from arcpuzzles.parametric_worker import evaluate_contract

    contract = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
    jobs = [
        {"seed": 801 + i * 17 + demos, "settings": {"edge_policy": setting}, "demos": demos, "queries": 4}
        for i, setting in enumerate(("full", "near_cue", "far_cue"))
        for demos in (2, 6)
    ]
    result = evaluate_contract(REPO, "600284beb8e4", contract, jobs)
    return {
        "status": "passed",
        "jobs": len(jobs),
        "settings": 3,
        "demo_counts": [2, 6],
        "queries_per_job": 4,
        "racket_evaluations": result["racket_evaluations"],
        "racket": result["racket"],
        "sole_survivor_checks": len(result["checks"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=96)
    parser.add_argument("--protected-racket", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        raise SystemExit("--seeds must be positive")
    report = {"python": run_python(args.seeds)}
    if args.protected_racket:
        report["protected_racket"] = run_racket()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
