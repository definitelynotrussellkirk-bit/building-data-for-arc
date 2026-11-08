"""Reusable bounded self-audit for the 75ff4423494a parametric family."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import public_challenge_bytes, public_challenge_id

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_audit_target_75ff4423494a", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)

SHORTCUTS = (
    "first_anchor",
    "last_anchor",
    "fixed_rank_2",
    "fixed_rank_4",
    "reverse_rank",
    "signal_row_count",
    "signal_component_count",
    "ranked_without_origin",
)


def rival_output(grid: list[list[int]], rival: str) -> list[list[int]]:
    if rival in prototype.MODES:
        return prototype.apply_mode(grid, rival)
    info = prototype.analyze(grid)
    external = info["external_anchors"]
    signal = prototype.signal_intermediate(grid)
    if rival == "first_anchor":
        return prototype.apply_ranked(grid, 1)
    if rival == "last_anchor":
        return prototype.apply_ranked(grid, len(external))
    if rival == "fixed_rank_2":
        return prototype.apply_ranked(grid, 2)
    if rival == "fixed_rank_4":
        return prototype.apply_ranked(grid, 4)
    if rival == "reverse_rank":
        return prototype.apply_ranked(grid, len(external) - signal["rank"] + 1)
    if rival in {"signal_row_count", "signal_component_count"}:
        return prototype.apply_ranked(grid, 1)
    if rival == "ranked_without_origin":
        selected = external[signal["rank"] - 1]
        return prototype._overlay(grid, [selected])
    raise ValueError(f"unknown rival: {rival}")


def _public_projection(episode: dict[str, Any], settings: dict[str, Any]) -> list[str]:
    private = copy.deepcopy(episode)
    private["settings"] = copy.deepcopy(settings)
    private["private_note"] = "hidden"
    visible = public_challenge_bytes(private)
    altered = copy.deepcopy(private)
    altered["settings"] = {prototype.PARAMETER_NAME: prototype.MODES[0]}
    altered["program_solution"] = "(rule! g)"
    altered["private_note"] = "changed"
    for pair in altered["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]
    failures: list[str] = []
    if public_challenge_bytes(altered) != visible:
        failures.append("private metadata or labels changed public bytes")
    first = {"train": private["train"], "test": private["test"][:1]}
    if public_challenge_bytes(first) != public_challenge_bytes(copy.deepcopy(first)):
        failures.append("first-turn projection is unstable")
    parsed = json.loads(public_challenge_bytes(first))
    if len(parsed.get("test", [])) != 1 or "output" in parsed["test"][0]:
        failures.append("first-turn projection leaks future queries or answer")
    if not isinstance(public_challenge_id(private), str):
        failures.append("public identifier is not a string")
    return failures


def build_report(
    *,
    seeds: Iterable[int] = range(64),
    demo_counts: tuple[int, ...] = (2, 3, 6),
) -> dict[str, Any]:
    rows = []
    harmful = []
    projection_failures = []
    exact_30 = 0
    setting_differences = 0
    for seed in seeds:
        for demos in demo_counts:
            matched = {
                mode: prototype.generate(seed, {prototype.PARAMETER_NAME: mode}, demos, 4)
                for mode in prototype.MODES
            }
            left, right = (matched[mode] for mode in prototype.MODES)
            for a, b in zip(left["train"] + left["test"], right["train"] + right["test"]):
                if a["input"] != b["input"]:
                    raise AssertionError("settings changed sampled inputs")
                setting_differences += a["output"] != b["output"]
            for mode, episode in matched.items():
                declared = [
                    candidate
                    for candidate in prototype.MODES
                    if all(
                        prototype.apply_mode(pair["input"], candidate) == pair["output"]
                        for pair in episode["train"]
                    )
                ]
                shortcut_rows = {}
                for rival in SHORTCUTS:
                    fits = all(
                        rival_output(pair["input"], rival) == pair["output"]
                        for pair in episode["train"]
                    )
                    disagreements = sum(
                        rival_output(pair["input"], rival) != pair["output"]
                        for pair in episode["test"]
                    )
                    shortcut_rows[rival] = {
                        "fits_all_demos": fits,
                        "query_disagreements": disagreements,
                    }
                    if fits and disagreements:
                        harmful.append({
                            "seed": seed,
                            "demos": demos,
                            "mode": mode,
                            "rival": rival,
                            "query_disagreements": disagreements,
                        })
                public_failures = _public_projection(
                    episode, {prototype.PARAMETER_NAME: mode}
                )
                projection_failures.extend(
                    {"seed": seed, "demos": demos, "mode": mode, "failure": failure}
                    for failure in public_failures
                )
                exact_30 += sum(
                    len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                    for pair in episode["test"]
                )
                rows.append({
                    "seed": seed,
                    "demos": demos,
                    "mode": mode,
                    "declared_survivors": declared,
                    "shortcuts": shortcut_rows,
                })
    status = "passed" if (
        all(row["declared_survivors"] == [row["mode"]] for row in rows)
        and not harmful
        and not projection_failures
        and setting_differences > 0
    ) else "failed"
    return {
        "schema": "75ff4423494a-parametric-self-audit-v1",
        "status": status,
        "episodes": len(rows),
        "harmful_survivors": len(harmful),
        "harmful_survivor_rows": harmful,
        "public_projection_failures": projection_failures,
        "exact_30x30_pairs": exact_30,
        "setting_dependent_answer_differences": setting_differences,
        "declared_shortcuts": list(SHORTCUTS),
        "rows": rows,
        "limits": "Finite declared settings and eight named shortcuts; no universal uniqueness or model-learning claim.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if type(args.seeds) is not int or not 1 <= args.seeds <= 512:
        raise ValueError("--seeds must be in 1..512")
    report = build_report(seeds=range(args.seeds))
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "status": report["status"],
        "episodes": report["episodes"],
        "harmful_survivors": report["harmful_survivors"],
        "exact_30x30_pairs": report["exact_30x30_pairs"],
        "out": str(destination),
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
