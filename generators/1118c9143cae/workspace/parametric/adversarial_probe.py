#!/usr/bin/env python3
"""Bounded adversarial probe for the 1118c9143cae echo-scope family.

The probe targets rule-specific bypasses rather than a generic volume sweep:
fixed color/count/rank selectors, first/last/min/max selectors, geometry-only
echoes, partial-intermediate rules, matched-input drift, count/size boundaries,
and malformed or forged private episode material.  Optional protected-Racket
replay checks representative complete four-query episodes.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = HERE / "prototype.py"
_SPEC = importlib.util.spec_from_file_location(
    "_1118c9143cae_adversarial_prototype_"
    + hashlib.sha256(str(_PROTOTYPE_PATH).encode()).hexdigest(),
    _PROTOTYPE_PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_PROTOTYPE_PATH}")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)

SCHEMA = "arcpuzzles-1118-parametric-adversarial-v1"


def _key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _source_signature(grid: list[list[int]]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    )


def _intermediate(grid: list[list[int]]) -> dict[str, Any]:
    color = prototype.rarest_color(grid)
    counts = prototype.color_counts(grid)
    return {
        "color": color,
        "count": counts[color],
        "rank": sorted(counts).index(color),
        "dimensions": [len(grid), len(grid[0])],
        "source_signature": _source_signature(grid),
    }


def _expect_rejected(callable_, *, contains: str | None = None) -> str | None:
    try:
        callable_()
    except (TypeError, ValueError) as exc:
        if contains is not None and contains not in str(exc):
            return f"wrong rejection message {exc!s}; expected substring {contains!r}"
        return None
    except Exception as exc:  # pragma: no cover - retained in report if reached
        return f"wrong exception type {type(exc).__name__}: {exc}"
    return "request was accepted"


def _validator_attacks(seed: int) -> tuple[list[str], list[dict[str, Any]]]:
    settings = {"echo_scope": "rarest_color"}
    episode = prototype.generate(seed, settings, 3, 4)
    attacks: list[tuple[str, dict[str, Any], tuple[str, ...]]] = []

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    attacks.append(("duplicate_input", duplicate, ("duplicate", "distinct")))

    stale = copy.deepcopy(episode)
    stale["program_solution"] = prototype.program({"echo_scope": "all"})
    attacks.append(("stale_program", stale, ("program",)))

    forged = copy.deepcopy(episode)
    forged["test"][1]["output"][0][0] = (
        9 if forged["test"][1]["output"][0][0] != 9 else 8
    )
    attacks.append(("forged_label", forged, ("label", "output")))

    malformed = copy.deepcopy(episode)
    malformed["train"][0]["input"][0][0] = True
    attacks.append(("bool_cell", malformed, ("integer", "cell")))

    ragged = copy.deepcopy(episode)
    ragged["train"][0]["input"][1] = ragged["train"][0]["input"][1][:-1]
    attacks.append(("ragged_grid", ragged, ("rectangular",)))

    wrong_demos = copy.deepcopy(episode)
    wrong_demos["train"] = wrong_demos["train"][:1]
    attacks.append(("wrong_demo_count", wrong_demos, ("demo", "2..6")))

    wrong_queries = copy.deepcopy(episode)
    wrong_queries["test"] = wrong_queries["test"][:3]
    attacks.append(("wrong_query_count", wrong_queries, ("four", "quer")))

    extra_private = copy.deepcopy(episode)
    extra_private["settings"] = settings
    attacks.append(("unexpected_private_field", extra_private, ("exactly",)))

    failures: list[dict[str, Any]] = []
    for name, candidate, expected_words in attacks:
        errors = prototype.validate_episode(candidate, settings)
        lowered = " ".join(errors).lower()
        if not errors or not any(word.lower() in lowered for word in expected_words):
            failures.append({"attack": name, "errors": errors})
    return [name for name, _, _ in attacks], failures


def _request_attacks() -> list[dict[str, str]]:
    attacks = (
        ("missing_setting", lambda: prototype.program({}), "exactly echo_scope"),
        (
            "extra_setting",
            lambda: prototype.program({"echo_scope": "all", "extra": 1}),
            "echo_scope",
        ),
        (
            "unknown_setting",
            lambda: prototype.generate(1, {"echo_scope": "unknown"}, 3, 4),
            "echo_scope",
        ),
        (
            "bool_seed",
            lambda: prototype.generate(True, {"echo_scope": "all"}, 3, 4),
            "seed",
        ),
        (
            "too_few_demos",
            lambda: prototype.generate(1, {"echo_scope": "all"}, 1, 4),
            "demos",
        ),
        (
            "too_many_demos",
            lambda: prototype.generate(1, {"echo_scope": "all"}, 7, 4),
            "demos",
        ),
        (
            "bool_demos",
            lambda: prototype.generate(1, {"echo_scope": "all"}, True, 4),
            "demos",
        ),
        (
            "wrong_queries",
            lambda: prototype.generate(1, {"echo_scope": "all"}, 3, 3),
            "queries",
        ),
        (
            "bool_queries",
            lambda: prototype.generate(1, {"echo_scope": "all"}, 3, True),
            "queries",
        ),
        (
            "tied_rarest",
            lambda: prototype.rarest_color([[1, 2], [0, 0]]),
            "unique rarest",
        ),
    )
    failures: list[dict[str, str]] = []
    for name, call, contains in attacks:
        problem = _expect_rejected(call, contains=contains)
        if problem is not None:
            failures.append({"attack": name, "problem": problem})
    return failures


def _racket_replay(
    seeds: list[int],
    episodes_by_seed: dict[int, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    selected = []
    if seeds:
        selected.append(seeds[0])
    if len(seeds) > 1 and seeds[-1] != seeds[0]:
        selected.append(seeds[-1])
    bridge = RacketBridge()
    cases: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            failures.append({"kind": "runtime_identity", "identity": identity})
        for seed in selected:
            for scope in prototype.ECHO_SCOPES:
                episode = episodes_by_seed[seed][scope]
                wrapped = wrap_rule(episode["program_solution"])
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        bridge.define_grid("g", pair["input"])
                        actual = bridge.eval_text(f"({wrapped} g)")
                        matched = actual == pair["output"]
                        cases.append(
                            {
                                "seed": seed,
                                "scope": scope,
                                "split": split,
                                "index": index,
                                "dimensions": [len(pair["input"]), len(pair["input"][0])],
                                "matched": matched,
                            }
                        )
                        if not matched:
                            failures.append(cases[-1])
    finally:
        bridge.shutdown()
    return {
        "requested": True,
        "runtime": identity,
        "selected_seeds": selected,
        "cases": cases,
        "failures": failures,
    }


def run_probe(
    *,
    out: str | Path | None = None,
    seeds: Iterable[int] = range(24),
    racket: bool = False,
) -> dict[str, Any]:
    seed_list = list(seeds)
    if not seed_list or any(type(seed) is not int for seed in seed_list):
        raise ValueError("seeds must be a nonempty iterable of exact integers")
    if len(set(seed_list)) != len(seed_list):
        raise ValueError("seeds must be distinct")

    ambiguous_lessons: list[dict[str, Any]] = []
    matched_input_failures: list[dict[str, Any]] = []
    boundary_failures: list[dict[str, Any]] = []
    deterministic_failures: list[dict[str, Any]] = []
    episodes_by_seed: dict[int, dict[str, dict[str, Any]]] = {}

    fixed_geometry_colors: set[int] = set()
    fixed_geometry_counts: set[int] = set()
    fixed_geometry_ranks: set[int] = set()
    nuisance_by_intermediate: dict[tuple[int, int], set[tuple[tuple[int, int], ...]]] = {}
    total_pairs = 0

    global_state = random.getstate()
    for seed in seed_list:
        episodes = {
            scope: prototype.generate(seed, {"echo_scope": scope}, 2, 4)
            for scope in prototype.ECHO_SCOPES
        }
        episodes_by_seed[seed] = episodes
        if random.getstate() != global_state:
            deterministic_failures.append({"seed": seed, "kind": "global_random_state_changed"})
            global_state = random.getstate()

        repeated = prototype.generate(seed, {"echo_scope": "all"}, 2, 4)
        if repeated != episodes["all"]:
            deterministic_failures.append({"seed": seed, "kind": "repeat_mismatch"})

        all_inputs = [
            pair["input"]
            for pair in episodes["all"]["train"] + episodes["all"]["test"]
        ]
        rare_inputs = [
            pair["input"]
            for pair in episodes["rarest_color"]["train"]
            + episodes["rarest_color"]["test"]
        ]
        if all_inputs != rare_inputs:
            matched_input_failures.append({"seed": seed, "kind": "settings_input_drift"})
        if len({_key(grid) for grid in all_inputs}) != len(all_inputs):
            matched_input_failures.append({"seed": seed, "kind": "duplicate_input"})

        for scope, episode in episodes.items():
            validation = prototype.validate_episode(episode, {"echo_scope": scope})
            if validation:
                boundary_failures.append(
                    {"seed": seed, "scope": scope, "kind": "episode_validation", "errors": validation}
                )
            total_pairs += len(episode["train"]) + len(episode["test"])
            for name, rival in prototype.SHORTCUTS.items():
                survives = all(
                    rival(pair["input"]) == pair["output"]
                    for pair in episode["train"]
                )
                changed_queries = [
                    index
                    for index, pair in enumerate(episode["test"])
                    if rival(pair["input"]) != pair["output"]
                ]
                if survives and changed_queries:
                    ambiguous_lessons.append(
                        {
                            "seed": seed,
                            "scope": scope,
                            "shortcut": name,
                            "changed_queries": changed_queries,
                        }
                    )

        demo_intermediates = [_intermediate(grid) for grid in rare_inputs[:2]]
        if demo_intermediates[0]["color"] == demo_intermediates[1]["color"]:
            ambiguous_lessons.append({"seed": seed, "kind": "fixed_color_core"})
        if demo_intermediates[0]["count"] == demo_intermediates[1]["count"]:
            ambiguous_lessons.append({"seed": seed, "kind": "fixed_count_core"})
        for info in demo_intermediates:
            fixed_geometry_colors.add(info["color"])
            fixed_geometry_counts.add(info["count"])
            fixed_geometry_ranks.add(info["rank"])
            nuisance_by_intermediate.setdefault((info["color"], info["count"]), set()).add(
                info["source_signature"]
            )

        large = rare_inputs[-1]
        sources = [
            (row, col, value)
            for row, values in enumerate(large)
            for col, value in enumerate(values)
            if value != 0
        ]
        rows = {row for row, _, _ in sources}
        cols = {col for _, col, _ in sources}
        boundary = sum(
            row in (0, 29) or col in (0, 29) for row, col, _ in sources
        )
        if (
            (len(large), len(large[0])) != (30, 30)
            or len(sources) != 40
            or len(rows) < 10
            or len(cols) < 10
            or boundary < 4
        ):
            boundary_failures.append(
                {
                    "seed": seed,
                    "kind": "substantive_30x30",
                    "dimensions": [len(large), len(large[0])],
                    "sources": len(sources),
                    "row_spread": len(rows),
                    "col_spread": len(cols),
                    "boundary_sources": boundary,
                }
            )
        if prototype.apply_python(large, "all") == prototype.apply_python(
            large, "rarest_color"
        ):
            boundary_failures.append({"seed": seed, "kind": "30x30_setting_collapse"})

    request_attack_failures = _request_attacks()
    validator_attacks_checked, validator_attack_failures = _validator_attacks(seed_list[0])

    crossed_control_failures: list[dict[str, Any]] = []
    if len(fixed_geometry_colors) < min(6, len(seed_list)):
        crossed_control_failures.append(
            {"kind": "insufficient_color_variation", "observed": sorted(fixed_geometry_colors)}
        )
    if fixed_geometry_counts != {2, 3}:
        crossed_control_failures.append(
            {"kind": "insufficient_count_variation", "observed": sorted(fixed_geometry_counts)}
        )
    if len(fixed_geometry_ranks) < 2:
        crossed_control_failures.append(
            {"kind": "insufficient_color_rank_variation", "observed": sorted(fixed_geometry_ranks)}
        )
    same_intermediate_variants = max(
        (len(signatures) for signatures in nuisance_by_intermediate.values()),
        default=0,
    )
    if same_intermediate_variants < 2:
        crossed_control_failures.append(
            {"kind": "no_nuisance_variation_at_fixed_intermediate"}
        )

    racket_report = (
        _racket_replay(seed_list, episodes_by_seed)
        if racket
        else {"requested": False, "cases": [], "failures": []}
    )
    all_failure_groups = (
        ambiguous_lessons,
        matched_input_failures,
        boundary_failures,
        deterministic_failures,
        request_attack_failures,
        validator_attack_failures,
        crossed_control_failures,
        racket_report["failures"],
    )
    status = "passed" if not any(all_failure_groups) else "failed"
    report = {
        "schema": SCHEMA,
        "status": status,
        "scope": (
            "bounded seeds; all declared settings; two-demo minimum; four queries; "
            "declared rule-specific shortcuts; crossed color/count/rank controls; "
            "malformed requests and private-episode corruption"
        ),
        "seeds": seed_list,
        "settings": list(prototype.ECHO_SCOPES),
        "episodes_checked": len(seed_list) * len(prototype.ECHO_SCOPES),
        "pairs_checked": total_pairs,
        "shortcuts_checked": list(prototype.SHORTCUTS),
        "ambiguous_lessons": ambiguous_lessons,
        "matched_input_failures": matched_input_failures,
        "boundary_failures": boundary_failures,
        "deterministic_failures": deterministic_failures,
        "request_attack_failures": request_attack_failures,
        "validator_attacks_checked": validator_attacks_checked,
        "validator_attack_failures": validator_attack_failures,
        "crossed_controls": {
            "fixed_geometry_colors": sorted(fixed_geometry_colors),
            "fixed_geometry_counts": sorted(fixed_geometry_counts),
            "fixed_geometry_color_ranks": sorted(fixed_geometry_ranks),
            "max_geometry_variants_at_same_color_count": same_intermediate_variants,
            "failures": crossed_control_failures,
        },
        "racket": racket_report,
        "findings_repaired_before_final_probe": [
            {
                "finding": "the initial sampler always made color 7 rarest",
                "repair": "vary the non-minimum rare color and reject fixed-color survivors in the two-demo core",
            },
            {
                "finding": "the initial sampler always used rare count 2",
                "repair": "cross counts 2 and 3 in the first two demonstrations and reject fixed-count survivors",
            },
            {
                "finding": "the initial prototype had no strict private-episode validator",
                "repair": "add source-program, label, type, count, distinct-input, and ambiguity validation",
            },
            {
                "finding": "rival probing continued after structural rejection and crashed on a ragged grid",
                "repair": "skip semantic ambiguity probes after any structural error and retain a ragged-grid attack",
            },
        ],
        "finite_limit": (
            "No bounded shortcut set proves universal rule uniqueness; owner source review, "
            "fresh native qualification, and downstream learning evaluation remain required."
        ),
    }
    if out is not None:
        destination = Path(out)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-count", type=int, default=24)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.seed_count <= 256:
        parser.error("--seed-count must be in 1..256")
    report = run_probe(out=args.out, seeds=range(args.seed_count), racket=args.racket)
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes_checked": report["episodes_checked"],
                "pairs_checked": report["pairs_checked"],
                "racket_cases": len(report["racket"]["cases"]),
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
