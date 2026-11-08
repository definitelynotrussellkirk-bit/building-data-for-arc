"""Replayable finite self-audit for the 959992fc8fa9 parametric family."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_arc_959992fc8fa9_parametric_audit_family", _PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = family
_SPEC.loader.exec_module(family)


def _racket_apply(program: str, grid: list[list[int]], bridge: Any) -> list[list[int]]:
    from puzzle_generators.rule_wrap import wrap_rule

    wrapped = wrap_rule(program)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    return bridge.eval_text(f"({wrapped} {literal})")


def _public_invariant(episode: dict[str, Any]) -> bool:
    private = {
        **copy.deepcopy(episode),
        "settings": {"intersection_policy": "repeated_color_priority"},
        "seed": 0,
        "private_note": "original",
    }
    visible = family.public_bytes(private)
    changed = copy.deepcopy(private)
    changed["settings"] = {"intersection_policy": "different_red"}
    changed["program_solution"] = "private replacement"
    changed["private_note"] = "changed"
    for pair in changed["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]
    return family.public_bytes(changed) == visible


def _racket_case() -> dict[str, Any]:
    from arc_repl.racket_bridge import RacketBridge

    settings = {"intersection_policy": "repeated_color_priority"}
    episode = family.generate(0, settings, demos=2, queries=4)
    pair = episode["train"][0]
    correct_program = family.program(settings)
    wrong_program = family.counterfactual_program("first_source")
    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        correct = _racket_apply(correct_program, pair["input"], bridge)
        wrong = _racket_apply(wrong_program, pair["input"], bridge)
    finally:
        bridge.close()
    pixels = family.source_pixels(pair["input"])
    return {
        "settings": settings,
        "input": pair["input"],
        "program": correct_program,
        "output": correct,
        "counterfactual_program": wrong_program,
        "counterfactual_output": wrong,
        "intermediate": family.repeated_color_intermediate(pair["input"]),
        "wrong_intermediate": {
            "priority_color": pixels[0][2],
            "source": "first source in reading order",
        },
        "ablation": "wrong_intermediate",
        "changes_final_output": correct != wrong,
        "racket": {
            key: identity.get(key)
            for key in ("schema", "backend", "protected", "binary_sha256", "prelude_sha256")
            if key in identity
        },
    }


def build_report(
    *,
    seeds: list[int] | tuple[int, ...] = (0, 17, 2718),
    demo_counts: list[int] | tuple[int, ...] = (2, 3, 6),
    include_racket: bool = True,
) -> dict[str, Any]:
    settings_space = [
        {"intersection_policy": "different_red"},
        {"intersection_policy": "repeated_color_priority"},
    ]
    cases: list[dict[str, Any]] = []
    all_inputs_setting_independent = True
    for seed in seeds:
        for demos in demo_counts:
            episodes = {
                setting["intersection_policy"]: family.generate(
                    seed, setting, demos=demos, queries=4
                )
                for setting in settings_space
            }
            canonical_inputs = {
                split: [pair["input"] for pair in episodes["different_red"][split]]
                for split in ("train", "test")
            }
            matched = all(
                canonical_inputs[split]
                == [
                    pair["input"]
                    for pair in episodes["repeated_color_priority"][split]
                ]
                for split in ("train", "test")
            )
            all_inputs_setting_independent &= matched
            for setting in settings_space:
                episode = episodes[setting["intersection_policy"]]
                certificate = family.lesson_certificate(
                    episode["train"], [pair["input"] for pair in episode["test"]]
                )
                cases.append(
                    {
                        "seed": seed,
                        "demos": demos,
                        "settings": setting,
                        "surviving_settings": certificate["surviving_settings"],
                        "surviving_shortcuts": certificate["surviving_shortcuts"],
                        "shortcuts": certificate["shortcuts"],
                        "query_outputs_consulted": certificate["query_outputs_consulted"],
                        "inputs_setting_independent": matched,
                        "public_projection_private_invariant": _public_invariant(episode),
                        "query_shapes": [
                            [len(pair["input"]), len(pair["input"][0])]
                            for pair in episode["test"]
                        ],
                    }
                )

    racket_case = _racket_case() if include_racket else None
    summary = {
        "cases": len(cases),
        "all_lessons_unique": all(
            case["surviving_settings"] == [case["settings"]] for case in cases
        ),
        "all_shortcuts_rejected": all(
            case["surviving_shortcuts"] == [] for case in cases
        ),
        "all_inputs_setting_independent": all_inputs_setting_independent,
        "all_public_projections_private_invariant": all(
            case["public_projection_private_invariant"] for case in cases
        ),
        "query_outputs_consulted": any(
            case["query_outputs_consulted"] for case in cases
        ),
    }
    passed = (
        summary["all_lessons_unique"]
        and summary["all_shortcuts_rejected"]
        and summary["all_inputs_setting_independent"]
        and summary["all_public_projections_private_invariant"]
        and not summary["query_outputs_consulted"]
        and (racket_case is None or racket_case["changes_final_output"])
    )
    return {
        "schema": "959992fc8fa9-parametric-self-audit-v1",
        "task_id": family.TASK_ID,
        "status": "passed" if passed else "failed",
        "summary": summary,
        "cases": cases,
        "racket_case": racket_case,
        "limits": (
            "Finite two-setting and six-shortcut audit over the listed seeds/counts; "
            "not universal uniqueness or a model-learning claim."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--no-racket", action="store_true")
    options = parser.parse_args(argv)
    report = build_report(include_racket=not options.no_racket)
    destination = Path(options.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "cases": report["summary"]["cases"],
                "racket": report["racket_case"] is not None,
                "out": str(destination),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
