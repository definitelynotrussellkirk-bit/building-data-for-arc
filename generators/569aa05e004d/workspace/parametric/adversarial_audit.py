#!/usr/bin/env python3
"""Bounded adversarial audit for the 569aa05e004d parametric family.

This is intentionally reusable by later reviewers.  It attacks the declared
minimum lesson, sampler determinism/settings independence, partial and wrong
intermediates, exact-two count semantics, fixed color/rank/location shortcuts,
certificate forgery, boundary profiles, and (optionally) protected-Racket parity.
Finite success is evidence, not a uniqueness proof.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proto = _load("_569aa05e004d_parametric_audit_impl", HERE / "prototype.py")


def _smallest_color_only(grid: list[list[int]]) -> list[list[int]]:
    first = proto.stage_rows(grid)
    relations = proto._vertical_targets(first)
    if not relations:
        return first
    chosen = min(color for _column, color, _top, _bottom in relations)
    out = [row[:] for row in first]
    for column, color, top, bottom in relations:
        if color == chosen:
            for row in range(top, bottom + 1):
                if out[row][column] == 0:
                    out[row][column] = color
    return out


def _leftmost_relation_per_color(grid: list[list[int]]) -> list[list[int]]:
    first = proto.stage_rows(grid)
    relations = proto._vertical_targets(first)
    selected: dict[int, tuple[int, int, int, int]] = {}
    for relation in relations:
        column, color, _top, _bottom = relation
        if color not in selected or column < selected[color][0]:
            selected[color] = relation
    out = [row[:] for row in first]
    for column, color, top, bottom in selected.values():
        for row in range(top, bottom + 1):
            if out[row][column] == 0:
                out[row][column] = color
    return out


def _middle_third_only(grid: list[list[int]]) -> list[list[int]]:
    first = proto.stage_rows(grid)
    width = len(first[0])
    low, high = width // 3, (2 * width + 2) // 3
    out = [row[:] for row in first]
    for column, color, top, bottom in proto._vertical_targets(first):
        if low <= column < high:
            for row in range(top, bottom + 1):
                if out[row][column] == 0:
                    out[row][column] = color
    return out


def _first_vertical_relation_only(grid: list[list[int]]) -> list[list[int]]:
    first = proto.stage_rows(grid)
    relations = proto._vertical_targets(first)
    out = [row[:] for row in first]
    if relations:
        column, color, top, bottom = relations[0]
        for row in range(top, bottom + 1):
            if out[row][column] == 0:
                out[row][column] = color
    return out


EXTRA_SEQUENTIAL_ATTACKS = {
    "smallest_color_only": _smallest_color_only,
    "leftmost_relation_per_color": _leftmost_relation_per_color,
    "middle_third_only": _middle_third_only,
    "first_vertical_relation_only": _first_vertical_relation_only,
}


def _expect_certificate_failure(episode: dict[str, Any], mutator, contains: str | None = None) -> bool:
    candidate = copy.deepcopy(episode)
    mutator(candidate)
    try:
        proto.certify(candidate)
    except (TypeError, ValueError) as exc:
        return contains is None or contains in str(exc)
    return False


def _racket_evaluator():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        bridge.close()
        raise RuntimeError(f"unprotected Racket backend: {identity}")
    wrapped: dict[str, str] = {}

    def apply(program: str, grid: list[list[int]]) -> list[list[int]]:
        if program not in wrapped:
            wrapped[program] = wrap_rule(program)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrapped[program]} {literal})")

    return bridge, apply, {
        key: identity[key]
        for key in ("schema", "backend", "protected", "binary_sha256", "prelude_sha256")
        if key in identity
    }


def _crossed_controls_report() -> dict[str, Any]:
    controls = proto.crossed_controls()
    varying = controls["different_intermediate_same_profile"]
    nuisance = controls["same_intermediate_different_raw_nuisance"]
    if len({tuple(case["analysis"]["shape"]) for case in varying}) != 1:
        raise AssertionError("crossed intermediate control changed dimensions")
    if len({proto.digest(proto.stage_rows(case["input"])) for case in varying}) != len(varying):
        raise AssertionError("crossed intermediate control did not vary Stage A")
    if len({case["analysis"]["stage_b_changed_cells"] for case in varying}) < 2:
        raise AssertionError("crossed intermediate control did not vary Stage B")
    if nuisance[0]["input"] == nuisance[1]["input"]:
        raise AssertionError("nuisance controls must differ in raw input")
    if nuisance[0]["intermediate"] != nuisance[1]["intermediate"]:
        raise AssertionError("nuisance controls must preserve the intermediate")
    if nuisance[0]["output"] != nuisance[1]["output"]:
        raise AssertionError("nuisance controls must preserve the final output")
    return {
        "different_intermediate_same_profile": [case["analysis"] for case in varying],
        "same_intermediate_different_raw_nuisance": [case["analysis"] for case in nuisance],
    }


def run_base_sampler_audit(*, seeds: Iterable[int] = range(8)) -> dict[str, Any]:
    """Exercise every declared production-axis combination on a bounded seed set."""
    generator = _load("_569aa05e004d_base_audit", HERE.parents[1] / "generator.py")
    difficulties = (None, "easy", "medium", "hard")
    checks = 0
    max_shape = [0, 0]
    for difficulty in difficulties:
        for seed in seeds:
            for layout in generator._LAYOUTS:
                for texture in generator._TEXTURES:
                    for edge_profile in generator._EDGE_PROFILES:
                        for color_reuse in (False, True):
                            grid = generator.generate(
                                seed,
                                checks % 17,
                                difficulty=difficulty,
                                layout=layout,
                                texture=texture,
                                edge_profile=edge_profile,
                                color_reuse=color_reuse,
                            )
                            expected = {
                                "layout": layout,
                                "texture": texture,
                                "edge_profile": edge_profile,
                                "color_reuse": color_reuse,
                            }
                            observed = generator.observe_overrides(grid)
                            if observed != expected:
                                raise AssertionError((difficulty, seed, expected, observed))
                            errors = generator.self_check(grid)
                            if errors:
                                raise AssertionError((difficulty, seed, expected, errors))
                            if generator.rule_mirror(grid) == grid:
                                raise AssertionError("production draw was a no-op")
                            max_shape = max(max_shape, [len(grid), len(grid[0])])
                            checks += 1
    return {"status": "pass", "draws_checked": checks, "max_shape": max_shape}


def run_audit(
    *,
    seeds: Iterable[int] = range(32),
    demo_counts: Iterable[int] = (2, 3, 6),
    use_racket: bool = True,
) -> dict[str, Any]:
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    episodes_checked = 0
    pairs_checked = 0
    setting_counts = {setting[proto.PARAMETER]: 0 for setting in proto.SETTINGS}
    shortcut_failures: dict[str, list[dict[str, Any]]] = {}
    max_shape = [0, 0]
    max_stage_b_changed = 0
    min_stage_b_changed: int | None = None
    raw_decoy_lessons = 0
    negative_certificate_checks = 0
    foreground_preservation_checks = 0
    racket_evaluations = 0
    bridge = apply = racket_identity = None
    if use_racket:
        bridge, apply, racket_identity = _racket_evaluator()

    try:
        for seed in seeds:
            for demos in demo_counts:
                baseline_inputs: list[list[list[int]]] | None = None
                for setting in proto.SETTINGS:
                    episode = proto.generate(seed, setting, demos, 4)
                    episodes_checked += 1
                    setting_counts[setting[proto.PARAMETER]] += 1
                    pairs = episode["train"] + episode["test"]
                    pairs_checked += len(pairs)
                    inputs = [pair["input"] for pair in pairs]
                    if baseline_inputs is None:
                        baseline_inputs = copy.deepcopy(inputs)
                    elif inputs != baseline_inputs:
                        raise AssertionError((seed, demos, "inputs depend on hidden setting"))
                    if len({proto.digest(grid) for grid in inputs}) != len(inputs):
                        raise AssertionError((seed, demos, "duplicate episode input"))
                    if episode["certificate"]["shortcut_survivors"]:
                        raise AssertionError((seed, demos, setting, episode["certificate"]))

                    analyses = [proto.analyze_scene(grid) for grid in inputs]
                    for grid, analysis in zip(inputs, analyses):
                        first = proto.stage_rows(grid)
                        final = proto.stage_columns(first)
                        if any(
                            before != 0 and after != before
                            for first_row, final_row in zip(first, final)
                            for before, after in zip(first_row, final_row)
                        ):
                            raise AssertionError((seed, demos, setting, "Stage B overwrote Stage-A foreground"))
                        foreground_preservation_checks += 1
                        max_shape = max(max_shape, analysis["shape"])
                        changed = analysis["stage_b_changed_cells"]
                        max_stage_b_changed = max(max_stage_b_changed, changed)
                        min_stage_b_changed = changed if min_stage_b_changed is None else min(min_stage_b_changed, changed)
                    if any(
                        proto.stage_columns(pair["input"]) != proto.stage_columns(proto.stage_rows(pair["input"]))
                        for pair in episode["train"]
                    ):
                        raw_decoy_lessons += 1

                    attacks = dict(proto._SHORTCUTS[setting[proto.PARAMETER]])
                    if setting[proto.PARAMETER] == "rows_then_columns":
                        attacks.update(EXTRA_SEQUENTIAL_ATTACKS)
                    for name, attack in attacks.items():
                        disagreements = [
                            index for index, pair in enumerate(episode["train"])
                            if attack(pair["input"]) != pair["output"]
                        ]
                        if not disagreements:
                            shortcut_failures.setdefault(name, []).append({
                                "seed": seed,
                                "demos": demos,
                                "settings": setting,
                            })

                    if use_racket and seed in seeds[: min(4, len(seeds))] and demos in demo_counts[:1]:
                        for pair in pairs:
                            got = apply(proto.program(setting), pair["input"])
                            racket_evaluations += 1
                            if got != pair["output"]:
                                raise AssertionError((seed, setting, "Racket/Python mismatch"))

                # Count-independence: shorter prefixes and all queries are stable.
                short = proto.generate(seed, proto.DEFAULT, 2, 4)
                long = proto.generate(seed, proto.DEFAULT, 6, 4)
                if short["train"] != long["train"][:2] or short["test"] != long["test"]:
                    raise AssertionError((seed, "demo-count dependence"))

        forgery_episode = proto.generate(17, {proto.PARAMETER: "rows_then_columns"}, 2, 4)
        mutations = [
            (lambda e: e["test"][0].__setitem__("input", copy.deepcopy(e["train"][0]["input"])), "distinct"),
            (lambda e: e["test"][0].__setitem__("output", copy.deepcopy(e["test"][1]["output"])), "query label"),
            (lambda e: e.__setitem__("program_solution", "(rule! g)"), "program_solution"),
            (lambda e: e.__setitem__("settings", {proto.PARAMETER: "invalid"}), None),
            (lambda e: e["train"][0]["input"][0].__setitem__(0, True), None),
            (lambda e: e["train"][0].pop("output"), None),
        ]
        for mutator, contains in mutations:
            if not _expect_certificate_failure(forgery_episode, mutator, contains):
                raise AssertionError(f"certificate accepted forged mutation containing {contains!r}")
            negative_certificate_checks += 1

        crossed = _crossed_controls_report()
        if shortcut_failures:
            raise AssertionError(f"shortcut survivors: {shortcut_failures}")
        if raw_decoy_lessons != len(seeds) * len(demo_counts) * len(proto.SETTINGS):
            raise AssertionError("a minimum lesson lacked a wrong-intermediate decoy")
        if max_shape != [30, 30]:
            raise AssertionError(f"30x30 profile was not exercised: {max_shape}")
        return {
            "schema": "arcpuzzles-569aa05e004d-adversarial-audit-v1",
            "status": "pass",
            "seeds": list(seeds),
            "demo_counts": list(demo_counts),
            "episodes_checked": episodes_checked,
            "pairs_checked": pairs_checked,
            "setting_counts": setting_counts,
            "shortcut_failures": shortcut_failures,
            "raw_decoy_lessons": raw_decoy_lessons,
            "negative_certificate_checks": negative_certificate_checks,
            "foreground_preservation_checks": foreground_preservation_checks,
            "max_shape": max_shape,
            "min_stage_b_changed_cells": min_stage_b_changed,
            "max_stage_b_changed_cells": max_stage_b_changed,
            "crossed_controls": crossed,
            "racket": racket_identity,
            "racket_evaluations": racket_evaluations,
            "limits": [
                "bounded generated scenes and declared attacks do not prove universal uniqueness",
                "owner qualification and exact-source acceptance remain separate",
            ],
        }
    finally:
        if bridge is not None:
            bridge.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--demo-counts", default="2,3,6")
    parser.add_argument("--no-racket", action="store_true")
    parser.add_argument("--base-seeds", type=int, default=0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    demo_counts = tuple(int(value) for value in args.demo_counts.split(",") if value)
    report = run_audit(
        seeds=range(args.seeds),
        demo_counts=demo_counts,
        use_racket=not args.no_racket,
    )
    if args.base_seeds:
        report["base_sampler"] = run_base_sampler_audit(seeds=range(args.base_seeds))
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
