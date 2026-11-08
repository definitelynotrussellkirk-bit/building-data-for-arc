"""Bounded adversarial audit for the a44e3443619f cascade prototype.

The audit is deliberately task-specific.  It attacks the minimum two-demo
lesson, several plausible partial/intermediate bypasses, sampler boundaries,
strict certificate rejection, crossed controls, settings-independent inputs,
and protected-Racket parity.  It writes a compact source-bound JSON receipt for
future reviewers; it does not grant owner acceptance or training admission.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
REPO = HERE.parents[3]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prototype = _load("_a44_parametric_audit_impl", HERE / "prototype.py")
base_generator = _load("_a44_base_audit_impl", TASK_HOME / "generator.py")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_binding() -> dict[str, str]:
    paths = {
        "generator.py": TASK_HOME / "generator.py",
        "prototype.py": HERE / "prototype.py",
        "adapter.py": HERE / "adapter.py",
        "promotion.json": HERE / "promotion.json",
        "cascade.rkt": HERE / "cascade.rkt",
        "skip_stage_one.rkt": HERE / "skip_stage_one.rkt",
        "tests/test_parametric_cascade.py": TASK_HOME / "tests/test_parametric_cascade.py",
    }
    return {name: _sha256(path) for name, path in paths.items()}


def _racket_runner():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        bridge.close()
        raise RuntimeError("audit requires protected Racket")
    cache: dict[str, str] = {}

    def execute(program: str, grid: list[list[int]]) -> list[list[int]]:
        wrapped = cache.setdefault(program, wrap_rule(program))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrapped} {literal})")

    return bridge, execute, {
        key: identity[key]
        for key in (
            "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
            "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256",
        )
        if key in identity
    }


def _assert_base_sampler() -> dict[str, object]:
    hist: dict[str, int] = {"2": 0, "3": 0}
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(128):
            grid = base_generator.generate(seed, seed % 7, difficulty=difficulty)
            centres = base_generator._x_centers(grid)
            if len(centres) not in (2, 3):
                raise AssertionError((difficulty, seed, centres))
            if base_generator.self_check(grid):
                raise AssertionError((difficulty, seed, base_generator.self_check(grid)))
            hist[str(len(centres))] += 1
    for count in (2, 3):
        for seed in range(32):
            grid = base_generator.generate(seed, 5, n_quads=count)
            if len(base_generator._x_centers(grid)) != count:
                raise AssertionError(("override", count, seed))
    return {"draws": 4 * 128 + 2 * 32, "effective_x_histogram": hist}


def _negative_certificate_checks() -> int:
    checked = 0
    episode = prototype.generate(41, {"completion_depth": "cascade"}, 2, 4)

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    try:
        prototype.certify(duplicate)
    except ValueError as exc:
        if "distinct" not in str(exc):
            raise
        checked += 1
    else:
        raise AssertionError("duplicate input certificate forgery was accepted")

    wrong_program = copy.deepcopy(episode)
    wrong_program["program_solution"] = prototype.program({"completion_depth": "single"})
    try:
        prototype.certify(wrong_program)
    except ValueError as exc:
        if "program" not in str(exc):
            raise
        checked += 1
    else:
        raise AssertionError("wrong program certificate forgery was accepted")

    wrong_query = copy.deepcopy(episode)
    wrong_query["test"][0]["output"] = copy.deepcopy(wrong_query["test"][1]["output"])
    try:
        prototype.certify(wrong_query)
    except ValueError as exc:
        if "query label" not in str(exc):
            raise
        checked += 1
    else:
        raise AssertionError("wrong query label was accepted")

    wrong_setting = copy.deepcopy(episode)
    wrong_setting["settings"] = {"completion_depth": "single"}
    try:
        prototype.certify(wrong_setting)
    except ValueError:
        checked += 1
    else:
        raise AssertionError("mismatched private setting was accepted")

    too_few = copy.deepcopy(episode)
    too_few["train"] = too_few["train"][:1]
    try:
        prototype.certify(too_few)
    except ValueError as exc:
        if "2..6" not in str(exc):
            raise
        checked += 1
    else:
        raise AssertionError("one-demo forged certificate was accepted")

    malformed = copy.deepcopy(episode)
    malformed["test"][0]["input"][0][0] = True
    try:
        prototype.certify(malformed)
    except ValueError as exc:
        if "exact integer" not in str(exc):
            raise
        checked += 1
    else:
        raise AssertionError("bool-valued grid was accepted")
    return checked


def _check_controls(execute=None) -> dict[str, object]:
    controls = prototype.crossed_controls()
    varying = controls["different_intermediate_same_profile"]
    if {tuple(case["analysis"]["shape"]) for case in varying} != {(13, 13)}:
        raise AssertionError("crossed profile dimensions drifted")
    if len({case["analysis"]["cascade_targets"] for case in varying}) != 2:
        raise AssertionError("intended intermediate did not vary at fixed profile")

    nuisance = controls["same_targets_different_nuisance"]
    if len({tuple(map(tuple, case["analysis"]["target_cells"])) for case in nuisance}) != 1:
        raise AssertionError("nuisance change moved causal targets")
    if nuisance[0]["input"] == nuisance[1]["input"]:
        raise AssertionError("nuisance controls are identical")

    racket_cases = 0
    if execute is not None:
        for group in controls.values():
            for case in group:
                grid = case["input"]
                for setting in prototype.SETTINGS:
                    got = execute(prototype.program(setting), grid)
                    expected = prototype.transform(grid, setting)
                    if got != expected:
                        raise AssertionError(("control Racket mismatch", setting))
                    racket_cases += 1
    return {
        "different_intermediate_same_profile": [case["analysis"] for case in varying],
        "same_targets_different_nuisance": [case["analysis"] for case in nuisance],
        "protected_racket_cases": racket_cases,
    }


def run_audit(
    *,
    seeds: Iterable[int] = range(16),
    demo_counts: Iterable[int] = (2, 3, 6),
    use_racket: bool = True,
) -> dict[str, object]:
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    if not seeds or not demo_counts:
        raise ValueError("audit requires nonempty seeds and demo counts")
    for seed in seeds:
        prototype._strict_int("seed", seed, 0, prototype.MAX_SEED)
    for count in demo_counts:
        prototype._strict_int("demos", count, prototype.MIN_DEMOS, prototype.MAX_DEMOS)

    bridge = None
    execute = None
    racket_identity = {"backend": "not_run", "protected": False}
    if use_racket:
        bridge, execute, racket_identity = _racket_runner()

    episodes_checked = 0
    pairs_checked = 0
    racket_evaluations = 0
    max_shape = [0, 0]
    target_histogram: dict[str, int] = {}
    shortcut_disagreements: dict[str, int] = {name: 0 for name in prototype.SHORTCUTS}
    query_role_counts = {"thin_wide": 0, "thin_tall": 0, "large": 0, "30x30": 0}

    try:
        for seed in seeds:
            for demos in demo_counts:
                episodes = {
                    setting["completion_depth"]: prototype.generate(seed, setting, demos, 4)
                    for setting in prototype.SETTINGS
                }
                visible_inputs = {
                    key: [pair["input"] for pair in episode["train"] + episode["test"]]
                    for key, episode in episodes.items()
                }
                if visible_inputs["single"] != visible_inputs["cascade"]:
                    raise AssertionError(("setting leaked into input grammar", seed, demos))

                for setting in prototype.SETTINGS:
                    episode = episodes[setting["completion_depth"]]
                    certificate = prototype.certify(episode, execute=execute)
                    episodes_checked += 1
                    pairs_checked += len(episode["train"]) + len(episode["test"])
                    if execute is not None:
                        # certify executes every setting on demonstrations and the
                        # selected program on all queries.
                        racket_evaluations += len(prototype.SETTINGS) * demos + 4
                    if certificate["shortcut_survivors"]:
                        raise AssertionError((seed, demos, setting, certificate["shortcut_survivors"]))
                    for name, disagreements in certificate["shortcut_disagreements"].items():
                        shortcut_disagreements[name] += len(disagreements)
                    for pair in episode["train"] + episode["test"]:
                        if any(cell not in (0, 2) for row in pair["input"] for cell in row):
                            raise AssertionError("input grammar leaked output/distractor colours")
                        analysis = prototype.analyze_scene(pair["input"])
                        if analysis["cascade_targets"] < 1:
                            raise AssertionError(("scene without causal target", seed, demos, setting))
                        key = str(analysis["cascade_targets"])
                        target_histogram[key] = target_histogram.get(key, 0) + 1
                        shape = analysis["shape"]
                        max_shape[0] = max(max_shape[0], shape[0])
                        max_shape[1] = max(max_shape[1], shape[1])
                    shapes = [prototype.analyze_scene(pair["input"])["shape"] for pair in episode["test"]]
                    query_role_counts["thin_wide"] += int(shapes[0][0] < shapes[0][1])
                    query_role_counts["thin_tall"] += int(shapes[1][0] > shapes[1][1])
                    query_role_counts["large"] += int(shapes[2][0] >= 20 and shapes[2][1] >= 20)
                    query_role_counts["30x30"] += int(shapes[3] == [30, 30])

        controls = _check_controls(execute)
        if execute is not None:
            racket_evaluations += controls["protected_racket_cases"]
        negatives = _negative_certificate_checks()
        base = _assert_base_sampler()
    finally:
        if bridge is not None:
            bridge.close()

    if any(count == 0 for count in shortcut_disagreements.values()):
        raise AssertionError(("unexercised shortcut", shortcut_disagreements))
    if max_shape != [30, 30]:
        raise AssertionError(("missing 30x30 stress", max_shape))

    return {
        "schema": "a44e3443619f-adversarial-audit-v1",
        "status": "pass",
        "task_id": prototype.TASK_ID,
        "settings": [dict(setting) for setting in prototype.SETTINGS],
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "episodes_checked": episodes_checked,
        "pairs_checked": pairs_checked,
        "racket_evaluations": racket_evaluations,
        "racket": racket_identity,
        "shortcut_demo_disagreements": shortcut_disagreements,
        "target_count_histogram": target_histogram,
        "query_role_counts": query_role_counts,
        "crossed_controls": controls,
        "negative_certificate_checks": negatives,
        "base_sampler": base,
        "max_shape": max_shape,
        "source_sha256": _source_binding(),
        "limits": (
            "Finite named-rival, crossed-control, sampler, certificate and Racket checks; "
            "not a proof of universal identifiability or owner acceptance."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-count", type=int, default=16)
    parser.add_argument("--demo-counts", type=int, nargs="+", default=[2, 3, 6])
    parser.add_argument("--no-racket", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if type(args.seed_count) is not int or not 1 <= args.seed_count <= 256:
        raise ValueError("seed-count must be in 1..256")
    report = run_audit(
        seeds=range(args.seed_count),
        demo_counts=args.demo_counts,
        use_racket=not args.no_racket,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
