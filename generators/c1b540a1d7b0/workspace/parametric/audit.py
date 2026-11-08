"""Replayable bounded self-audit for c1b540a1d7b0."""
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_arc_c1b540a1d7b0_audit_family", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = family
_SPEC.loader.exec_module(family)


def _racket_apply(program: str, grid: list[list[int]], bridge: Any) -> list[list[int]]:
    from puzzle_generators.rule_wrap import wrap_rule
    wrapped = wrap_rule(program)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrapped} {literal})")


def _racket_case() -> dict[str, Any]:
    from arc_repl.racket_bridge import RacketBridge
    settings = {"component_scope": "largest_component"}
    episode = family.generate(0, settings, 2, 4)
    pair = episode["train"][0]
    correct_program = family.program(settings)
    wrong_program = family.counterfactual_program()
    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        correct = _racket_apply(correct_program, pair["input"], bridge)
        wrong = _racket_apply(wrong_program, pair["input"], bridge)
    finally:
        bridge.close()
    intermediate = family.largest_component_intermediate(pair["input"])
    comps = family.components5(pair["input"])
    smallest = min(comps, key=len)
    return {
        "settings": settings,
        "input": pair["input"],
        "program": correct_program,
        "output": correct,
        "counterfactual_program": wrong_program,
        "counterfactual_output": wrong,
        "intermediate_value": intermediate,
        "wrong_intermediate": {
            "selected_size": len(smallest),
            "selected_bbox": list(family._bbox(smallest)),
            "source": "smallest gray component",
        },
        "ablation": "wrong_intermediate",
        "changes_final_output": correct != wrong,
        "racket": {k: identity.get(k) for k in ("schema", "backend", "protected", "binary_sha256", "prelude_sha256") if k in identity},
    }


def build_report(*, seeds=(0, 17, 2718), demo_counts=(2, 3, 6), include_racket=True) -> dict[str, Any]:
    settings_space = [
        {"component_scope": "all_components"},
        {"component_scope": "largest_component"},
    ]
    cases = []
    matched_all = True
    unique_all = True
    shortcuts_all = True
    private_all = True
    for seed in seeds:
        for demos in demo_counts:
            episodes = {s["component_scope"]: family.generate(seed, s, demos, 4) for s in settings_space}
            matched = all(
                [p["input"] for p in episodes["all_components"][split]]
                == [p["input"] for p in episodes["largest_component"][split]]
                for split in ("train", "test")
            )
            matched_all &= matched
            for settings in settings_space:
                episode = episodes[settings["component_scope"]]
                cert = family.lesson_certificate(episode["train"], [p["input"] for p in episode["test"]])
                unique = cert["surviving_settings"] == [settings]
                no_shortcuts = cert["surviving_shortcuts"] == []
                unique_all &= unique
                shortcuts_all &= no_shortcuts
                private = {**copy.deepcopy(episode), "settings": settings, "seed": seed}
                visible = family.public_bytes(private)
                changed = copy.deepcopy(private)
                changed["program_solution"] = "private"
                changed["settings"] = settings_space[1 if settings == settings_space[0] else 0]
                for pair in changed["test"]:
                    pair["output"] = [[9 for _ in row] for row in pair["output"]]
                invariant = family.public_bytes(changed) == visible
                private_all &= invariant
                cases.append({
                    "seed": seed,
                    "demos": demos,
                    "settings": settings,
                    "matched_inputs": matched,
                    "unique_setting": unique,
                    "shortcuts_rejected": no_shortcuts,
                    "public_private_invariant": invariant,
                    "query_shapes": [[len(p["input"]), len(p["input"][0])] for p in episode["test"]],
                    "component_sizes": [family.largest_component_intermediate(p["input"])["component_sizes"] for p in episode["test"]],
                })
    report = {
        "schema": "c1b540a1d7b0-parametric-self-audit-v1",
        "task_id": family.TASK_ID,
        "status": "passed" if matched_all and unique_all and shortcuts_all and private_all else "failed",
        "summary": {
            "cases": len(cases),
            "all_lessons_unique": unique_all,
            "all_shortcuts_rejected": shortcuts_all,
            "all_inputs_setting_independent": matched_all,
            "all_public_projections_private_invariant": private_all,
            "query_outputs_consulted": False,
        },
        "cases": cases,
        "racket_case": _racket_case() if include_racket else None,
    }
    if include_racket and not report["racket_case"]["changes_final_output"]:
        report["status"] = "failed"
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--no-racket", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(include_racket=not args.no_racket)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))
    return 0 if report["status"] == "passed" else 1

if __name__ == "__main__":
    raise SystemExit(main())
