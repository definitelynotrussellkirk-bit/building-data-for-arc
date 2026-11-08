#!/usr/bin/env python3
"""Bounded adversarial and protected-Racket probe for a1ece4864521.

This is intentionally task-local and reusable by later reviewers.  It checks
minimum-lesson identifiability, declared semantic rivals, count/prefix behavior,
Racket parity, crossed controls, size boundaries, and negative episode
validation without mutating catalog approval state.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent
RACKET_RESTART_INTERVAL = 32


def minimum_tile_diversity(*, seed_count: int) -> int:
    """Scale the diversity floor for both one-seed smoke and full campaigns."""
    if isinstance(seed_count, bool) or not isinstance(seed_count, int) or seed_count < 1:
        raise ValueError("seed_count must be a positive integer")
    return min(8, max(2, seed_count * 2))

SPEC = importlib.util.spec_from_file_location("_a1ece4864521_probe_prototype", HERE / "prototype.py")
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


class ProtectedEvaluator:
    def __init__(self) -> None:
        self.bridge = RacketBridge(max_calls_before_restart=RACKET_RESTART_INTERVAL)
        identity = self.bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("probe requires protected Racket")
        self.identity = {
            key: identity[key]
            for key in (
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            )
            if key in identity
        }
        self._wrapped: dict[str, str] = {}
        self._result_cache: dict[tuple[str, str], list[list[int]]] = {}
        self.evaluations = 0
        self.cache_hits = 0
        self.restarts = 0

    def apply(self, program: str, grid: list[list[int]]) -> list[list[int]]:
        program_key = hashlib.sha256(program.encode("utf-8")).hexdigest()
        grid_key = hashlib.sha256(
            json.dumps(grid, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        key = (program_key, grid_key)
        cached = self._result_cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            return copy.deepcopy(cached)
        if program not in self._wrapped:
            self._wrapped[program] = wrap_rule(program)
        self.evaluations += 1
        value = self.bridge.eval_text(f"({self._wrapped[program]} {_literal(grid)})")
        prototype._grid(value, "Racket output")
        self._result_cache[key] = copy.deepcopy(value)
        return value

    def close(self) -> None:
        self.restarts = int(getattr(self.bridge, "_restarts", 0))
        self.bridge.close()


def _phase_flip_control(grid: list[list[int]]) -> tuple[list[list[int]], dict[str, Any]]:
    """Flip one colored anomaly's latent source residue while fixing positions/colors."""
    facts = prototype.analyze_scene(grid)
    chosen = next(
        (a for a in facts["anomalies"] if a[2] not in (0, 8) and a[3] == 0),
        None,
    )
    if chosen is None:
        raise AssertionError("control needs one colored inferred-zero anomaly")
    row, col, _value, old_phase = chosen
    tile = [line[:] for line in facts["tile"]]
    tile[row % 5][col % 5] = 8
    clean = prototype.base._clean_grid(tile, facts["height"], facts["width"])
    controlled = [line[:] for line in clean]
    for ar, ac, value, _expected in facts["anomalies"]:
        controlled[ar][ac] = value
    new = prototype.analyze_scene(controlled)
    if new["errors"]:
        raise AssertionError("phase control is invalid: " + "; ".join(new["errors"]))
    counterpart = next(a for a in new["anomalies"] if a[0] == row and a[1] == col)
    if counterpart[3] != 8:
        raise AssertionError("phase control did not change the intended intermediate")
    if [(a[0], a[1], a[2]) for a in new["anomalies"]] != [
        (a[0], a[1], a[2]) for a in facts["anomalies"]
    ]:
        raise AssertionError("phase control changed anomaly positions or values")
    return controlled, {
        "position": [row, col],
        "old_phase": old_phase,
        "new_phase": counterpart[3],
        "dimensions_fixed": [facts["height"], facts["width"]],
        "anomaly_positions_and_values_fixed": True,
    }


def _dimension_control(grid: list[list[int]]) -> tuple[list[list[int]], dict[str, Any]]:
    """Extend bottom/right by one period while fixing tile, anomalies and routes."""
    facts = prototype.analyze_scene(grid)
    new_h = facts["height"] + 5
    new_w = facts["width"] + 5
    if new_h > 30 or new_w > 30:
        raise AssertionError("dimension control needs room for one full period")
    clean = prototype.base._clean_grid(facts["tile"], new_h, new_w)
    controlled = [line[:] for line in clean]
    for row, col, value, _expected in facts["anomalies"]:
        controlled[row][col] = value
    new = prototype.analyze_scene(controlled)
    if new["errors"]:
        raise AssertionError("dimension control is invalid: " + "; ".join(new["errors"]))
    old_roles = [(r, c, expected) for r, c, _v, expected in facts["anomalies"]]
    new_roles = [(r, c, expected) for r, c, _v, expected in new["anomalies"]]
    if old_roles != new_roles:
        raise AssertionError("dimension control changed anomaly phases")
    return controlled, {
        "old_dimensions": [facts["height"], facts["width"]],
        "new_dimensions": [new_h, new_w],
        "tile_fixed": True,
        "anomaly_positions_values_and_phases_fixed": True,
    }


def _expect_rejected(episode: dict[str, Any], settings: dict[str, str], kind: str) -> str:
    tampered = copy.deepcopy(episode)
    if kind == "forged_label":
        tampered["test"][0]["output"][0][0] = (tampered["test"][0]["output"][0][0] + 1) % 10
    elif kind == "duplicate_input":
        tampered["test"][0]["input"] = copy.deepcopy(tampered["train"][0]["input"])
    elif kind == "boolean_cell":
        tampered["train"][0]["input"][0][0] = True
    elif kind == "wrong_program":
        tampered["program_solution"] = "(rule! (lambda (g) g))"
    elif kind == "wrong_count":
        tampered["test"].pop()
    else:
        raise AssertionError(kind)
    try:
        prototype.validate_episode(tampered, settings=settings, demos=2, queries=4)
    except ValueError as exc:
        return str(exc)
    raise AssertionError(f"validator accepted {kind}")


def run_probe(*, seeds=(0, 1, 2, 3), demo_counts=(2, 3, 6)) -> dict[str, Any]:
    seeds = list(seeds)
    demo_counts = list(demo_counts)
    if not seeds or not demo_counts:
        raise ValueError("seeds and demo_counts must be nonempty")
    evaluator = ProtectedEvaluator()
    episodes = 0
    max_shape = [0, 0]
    tile_hashes: set[str] = set()
    first_source_indices = []
    validator_attacks: dict[str, str] = {}
    try:
        for seed in seeds:
            canonical_full = prototype.generate(seed, {"fill_route": "below_right"}, 2, 4)
            canonical_one = prototype.generate(seed, {"fill_route": "below_right"}, 2, 1)
            if canonical_one["test"][0] != canonical_full["test"][0]:
                raise AssertionError("one-query prefix differs from four-query presentation")
            # Identify the private source role only for the retained reviewer report.
            first_shape = [
                len(canonical_full["test"][0]["input"]),
                len(canonical_full["test"][0]["input"][0]),
            ]
            first_source_indices.append(first_shape)

            for demos in demo_counts:
                for settings in prototype.SETTINGS:
                    episode = prototype.generate(seed, settings, demos, 4)
                    prototype.validate_episode(episode, settings=settings, demos=demos, queries=4)
                    if prototype.setting_survivors(episode["train"]) != [settings]:
                        raise AssertionError("setting survivor drift")
                    survivors = prototype.rival_survivors(episode["train"], settings)
                    if survivors:
                        raise AssertionError(f"shortcut survivors: {survivors}")
                    for pair in episode["train"] + episode["test"]:
                        actual = evaluator.apply(episode["program_solution"], pair["input"])
                        if actual != pair["output"]:
                            raise AssertionError("protected Racket disagrees with stored label")
                        facts = prototype.analyze_scene(pair["input"])
                        tile_hashes.add(
                            hashlib.sha256(
                                json.dumps(facts["tile"], separators=(",", ":")).encode()
                            ).hexdigest()
                        )
                        max_shape[0] = max(max_shape[0], len(pair["input"]))
                        max_shape[1] = max(max_shape[1], len(pair["input"][0]))
                    episodes += 1

        sample = prototype.generate(seeds[0], {"fill_route": "phase_diagonal"}, 2, 4)
        for kind in ("forged_label", "duplicate_input", "boolean_cell", "wrong_program", "wrong_count"):
            validator_attacks[kind] = _expect_rejected(sample, {"fill_route": "phase_diagonal"}, kind)

        base_control = sample["train"][0]["input"]
        phase_control, phase_meta = _phase_flip_control(base_control)
        original_phase = prototype.transform(base_control, {"fill_route": "phase_diagonal"})
        changed_phase = prototype.transform(phase_control, {"fill_route": "phase_diagonal"})
        if original_phase == changed_phase:
            raise AssertionError("phase control failed to change phase-directed output")
        # Execute both control labels with protected Racket.
        phase_program = prototype.program({"fill_route": "phase_diagonal"})
        if evaluator.apply(phase_program, base_control) != original_phase:
            raise AssertionError("Racket failed original phase control")
        if evaluator.apply(phase_program, phase_control) != changed_phase:
            raise AssertionError("Racket failed changed phase control")

        dimension_base = prototype.generate(seeds[0], {"fill_route": "phase_diagonal"}, 3, 4)["train"][0]["input"]
        expanded, dimension_meta = _dimension_control(dimension_base)
        old_out = prototype.transform(dimension_base, {"fill_route": "phase_diagonal"})
        new_out = prototype.transform(expanded, {"fill_route": "phase_diagonal"})
        h, w = len(old_out), len(old_out[0])
        if [row[:w] for row in new_out[:h]] != old_out:
            raise AssertionError("dimension nuisance changed the fixed original region")
        if evaluator.apply(phase_program, expanded) != new_out:
            raise AssertionError("Racket failed dimension control")
    finally:
        evaluator.close()

    if max_shape != [30, 30]:
        raise AssertionError(f"boundary coverage drifted: {max_shape}")
    if len(tile_hashes) < minimum_tile_diversity(seed_count=len(seeds)):
        raise AssertionError("latent tile diversity is unexpectedly low")
    return {
        "schema": "a1ece4864521-adversarial-probe-v1",
        "status": "passed",
        "task_id": prototype.TASK_ID,
        "seeds": seeds,
        "demo_counts": demo_counts,
        "settings": list(prototype.SETTINGS),
        "episodes_checked": episodes,
        "queries_per_episode": 4,
        "declared_rivals": sorted(prototype.RIVALS),
        "shortcut_survivors": 0,
        "distinct_latent_tiles": len(tile_hashes),
        "max_input_shape": max_shape,
        "first_query_shapes": first_source_indices,
        "validator_attacks": validator_attacks,
        "crossed_controls": {
            "vary_intermediate_at_fixed_dimensions_positions_colors": phase_meta,
            "vary_dimensions_at_fixed_tile_positions_phases": dimension_meta,
        },
        "racket": evaluator.identity,
        "racket_evaluations": evaluator.evaluations,
        "racket_cache_hits": evaluator.cache_hits,
        "racket_restart_interval": RACKET_RESTART_INTERVAL,
        "racket_restarts": evaluator.restarts,
        "limits": "Finite declared rivals, seeds and profiles; not a proof against every possible shortcut.",
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3])
    parser.add_argument("--demo-counts", type=int, nargs="+", default=[2, 3, 6])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run_probe(seeds=args.seeds, demo_counts=args.demo_counts)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
