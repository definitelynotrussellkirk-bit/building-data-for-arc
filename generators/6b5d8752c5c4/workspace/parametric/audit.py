"""Bounded self-audit for the 6b5d8752c5c4 divider-source family."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


_HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = _HERE / "prototype.py"
_MODULE_NAME = "_6b5d8752c5c4_divider_source_audit_prototype"


def _load_prototype():
    module = sys.modules.get(_MODULE_NAME)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load prototype: {_PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


prototype = _load_prototype()


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [
        pair["input"]
        for split in ("train", "test")
        for pair in episode[split]
    ]


def _public_bytes(episode: dict[str, Any]) -> bytes:
    return json.dumps(
        prototype.public_payload(episode),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _first_turn_expected(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][0]["input"])}],
    }


def build_report(seed_start: int = 0, seed_count: int = 16) -> dict[str, Any]:
    """Audit finite settings, counts, named rivals, and public projections."""
    prototype._literal_int("seed_start", seed_start, 0, prototype.MAX_SEED)
    prototype._literal_int("seed_count", seed_count, 1, 256)
    if seed_start + seed_count - 1 > prototype.MAX_SEED:
        raise ValueError("last audit seed exceeds the supported range")

    failures: list[dict[str, Any]] = []
    episodes_checked = 0
    surface_counts = {"8x8": 0, "30x30": 0}
    setting_neutral = True
    settings_identified = True
    shortcuts_rejected = True
    public_private_invariant = True
    first_turn_exact = True

    for seed in range(seed_start, seed_start + seed_count):
        for demos in range(prototype.MIN_DEMOS, prototype.MAX_DEMOS + 1):
            episodes = {
                source: prototype.generate(
                    seed,
                    {"divider_source": source},
                    demos,
                    prototype.QUERY_COUNT,
                )
                for source in prototype.DIVIDER_SOURCES
            }
            reference_inputs = _inputs(episodes[prototype.DIVIDER_SOURCES[0]])
            for source, episode in episodes.items():
                episodes_checked += 1
                context = {"seed": seed, "demos": demos, "source": source}
                if prototype.generate(
                    seed,
                    {"divider_source": source},
                    demos,
                    prototype.QUERY_COUNT,
                ) != episode:
                    failures.append({**context, "kind": "nondeterministic_episode"})

                if _inputs(episode) != reference_inputs:
                    setting_neutral = False
                    failures.append({**context, "kind": "setting_dependent_inputs"})

                assessment = prototype.assess_demos(episode["train"], source)
                if assessment["declared_survivors"] != [source]:
                    settings_identified = False
                    failures.append(
                        {
                            **context,
                            "kind": "declared_survivor_failure",
                            "survivors": assessment["declared_survivors"],
                        }
                    )
                surviving_shortcuts = [
                    name
                    for name, row in assessment["shortcuts"].items()
                    if row["fits_all_demos"]
                ]
                if surviving_shortcuts:
                    shortcuts_rejected = False
                    failures.append(
                        {
                            **context,
                            "kind": "shortcut_survived",
                            "shortcuts": surviving_shortcuts,
                        }
                    )

                analyses = [prototype.analyze_input(grid) for grid in reference_inputs]
                surface_counts["8x8"] += sum(row["canvas"] == 8 for row in analyses)
                surface_counts["30x30"] += sum(row["canvas"] == 30 for row in analyses)
                if not any(row["canvas"] == 30 for row in analyses):
                    failures.append({**context, "kind": "missing_30x30_surface"})

                visible = _public_bytes(episode)
                altered = copy.deepcopy(episode)
                altered["settings"] = {"divider_source": "private-change"}
                altered["program_solution"] = "(rule! private-change)"
                altered["private_note"] = "must not change public identity"
                for pair in altered["test"]:
                    pair["output"] = [
                        [7 for _ in row] for row in pair["output"]
                    ]
                if _public_bytes(altered) != visible:
                    public_private_invariant = False
                    failures.append({**context, "kind": "private_projection_leak"})

                if prototype.first_turn_payload(episode) != _first_turn_expected(episode):
                    first_turn_exact = False
                    failures.append({**context, "kind": "first_turn_projection_mismatch"})

    retained_episode = prototype.generate(
        seed_start,
        {"divider_source": "bbox_midpoint"},
        2,
        prototype.QUERY_COUNT,
    )
    retained_input = retained_episode["train"][0]["input"]
    correct_output = prototype.apply_setting(retained_input, "bbox_midpoint")
    counterfactual_output = prototype.apply_setting(retained_input, "lane_marker")
    retained_case = {
        "seed": seed_start,
        "split": "train",
        "pair_index": 0,
        "settings": {"divider_source": "bbox_midpoint"},
        "input": retained_input,
        "correct_intermediate": prototype.analyze_input(retained_input)["bars"],
        "wrong_intermediate": "use each lane marker as divider instead of each bounding-box midpoint",
        "output": correct_output,
        "counterfactual_program": prototype.LANE_MARKER_PROGRAM,
        "counterfactual_output": counterfactual_output,
        "ablation": "wrong_intermediate",
        "changes_final_output": correct_output != counterfactual_output,
    }
    if not retained_case["changes_final_output"]:
        failures.append({"kind": "retained_counterfactual_did_not_change_output"})

    return {
        "schema": "6b5d8752c5c4-parametric-self-audit-v1",
        "status": "passed" if not failures else "failed",
        "seed_start": seed_start,
        "seed_count": seed_count,
        "demo_counts": [2, 3, 4, 5, 6],
        "settings": [
            {"divider_source": source}
            for source in prototype.DIVIDER_SOURCES
        ],
        "episodes_checked": episodes_checked,
        "surface_counts": surface_counts,
        "all_inputs_setting_neutral": setting_neutral,
        "all_declared_settings_identified": settings_identified,
        "all_named_shortcuts_rejected": shortcuts_rejected,
        "all_public_projections_private_invariant": public_private_invariant,
        "all_first_turn_views_exact": first_turn_exact,
        "failures": failures,
        "retained_case": retained_case,
        "limits": (
            "Finite deterministic audit over the declared two-setting family, "
            "five demo counts, and four named shortcuts; not a universal "
            "identifiability or model-learning claim."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=16)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    report = build_report(args.seed_start, args.seed_count)
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes_checked": report["episodes_checked"],
                "failures": len(report["failures"]),
                "out": str(destination),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
