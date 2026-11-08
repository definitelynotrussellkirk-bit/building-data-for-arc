"""Bounded adversarial and protected-Racket probe for 8e52225f35b8.

This is intentionally reusable by future reviewers: it attacks the minimum
lesson, independent count corners, semantic rivals, public projection, malformed
contracts, full-size content, and exact Racket labels on source-bound bytes.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
ROOT = TASK_HOME.parents[1]


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_probe_8e52225f35b8", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expect_error(name, fn, attacks):
    try:
        fn()
    except (TypeError, ValueError):
        attacks.append(name)
        return
    raise AssertionError(f"negative attack unexpectedly succeeded: {name}")


def _mirror_local_panels(proto, grid):
    parsed, bounds, _cells = proto._split_panels(grid)
    result = copy.deepcopy(parsed)
    for left, right in bounds:
        for row in range(len(result)):
            original = parsed[row][left:right]
            result[row][left:right] = list(reversed(original))
    return result


def _mirror_output(grid):
    return [list(reversed(row)) for row in grid]


def run_probe():
    proto = _load()
    settings = [
        {"closure_order": "row_then_column"},
        {"closure_order": "column_then_row"},
    ]
    seeds = [0, 1, 2, 17, 37, 2**31 - 1]
    counts = [2, 6]
    episodes = 0
    scene_digests = set()
    metrics = []
    negative_attacks = []
    public_projection_checks = 0
    crossed_controls = 0

    generated = {}
    for seed in seeds:
        for setting in settings:
            for demos in counts:
                episode = proto.generate(seed, setting, demos=demos, queries=4)
                assert episode["certificate"]["survivors"] == [setting]
                assert set(episode["certificate"]["extra_refutations"]) == set(proto.RIVAL_NAMES)
                assert len(episode["train"]) == demos and len(episode["test"]) == 4
                assert proto.certify(episode)["survivors"] == [setting]
                generated[(seed, setting["closure_order"], demos)] = episode
                episodes += 1

        for demos in counts:
            left = generated[(seed, settings[0]["closure_order"], demos)]
            right = generated[(seed, settings[1]["closure_order"], demos)]
            assert [p["input"] for p in left["train"] + left["test"]] == [
                p["input"] for p in right["train"] + right["test"]
            ]

        for setting in settings:
            small = generated[(seed, setting["closure_order"], 2)]
            large = generated[(seed, setting["closure_order"], 6)]
            assert small["train"] == large["train"][:2]
            assert small["test"] == large["test"]
            all_pairs = large["train"] + large["test"]
            assert len({proto.digest(pair["input"]) for pair in all_pairs}) == 10
            scene_digests.update(proto.digest(pair["input"]) for pair in all_pairs)
            metrics.extend(proto.analyze_scene(pair["input"]) for pair in all_pairs)

            # Fixed input/dimensions/profiles, changed semantic intermediate.
            for pair in small["train"]:
                other = settings[1] if setting == settings[0] else settings[0]
                assert proto.intermediate(pair["input"], setting) != proto.intermediate(
                    pair["input"], other
                )
                assert proto.transform(pair["input"], setting) != proto.transform(
                    pair["input"], other
                )
                crossed_controls += 1

            # Changed nuisance orientation, same semantic roles and mirrored answer.
            control_input = small["test"][0]["input"]
            mirrored = _mirror_local_panels(proto, control_input)
            assert proto.transform(mirrored, setting) == _mirror_output(
                proto.transform(control_input, setting)
            )
            crossed_controls += 1

            # Public first turn is invariant to private fields, answer labels, and future inputs.
            first = proto.public_turn(small, 0)
            baseline_bytes = public_challenge_bytes(first)
            baseline_id = public_challenge_id(first)
            changed = copy.deepcopy(small)
            changed["settings"] = settings[1] if setting == settings[0] else settings[0]
            changed["program_solution"] = "forged private program"
            changed["test"][0]["output"] = [[9]]
            changed["test"][1]["input"] = [[7]]
            assert public_challenge_bytes(proto.public_turn(changed, 0)) == baseline_bytes
            assert public_challenge_id(proto.public_turn(changed, 0)) == baseline_id
            visible = copy.deepcopy(small)
            visible["test"][0]["input"][0][0] = 7
            assert public_challenge_id(proto.public_turn(visible, 0)) != baseline_id
            public_projection_checks += 1

    # Minimum lessons must distinguish both settings on every fresh seed.
    for seed in seeds:
        a = generated[(seed, settings[0]["closure_order"], 2)]
        b = generated[(seed, settings[1]["closure_order"], 2)]
        assert any(x["output"] != y["output"] for x, y in zip(a["train"], b["train"]))
        assert all(
            proto.transform(pair["input"], settings[0])
            != proto.transform(pair["input"], settings[1])
            for pair in a["train"] + a["test"]
        )

    sample = copy.deepcopy(generated[(17, settings[0]["closure_order"], 2)])
    _expect_error("demos_below_minimum", lambda: proto.generate(0, settings[0], 1, 4), negative_attacks)
    _expect_error("demos_above_maximum", lambda: proto.generate(0, settings[0], 7, 4), negative_attacks)
    _expect_error("wrong_query_count", lambda: proto.generate(0, settings[0], 2, 3), negative_attacks)
    _expect_error("bool_count", lambda: proto.generate(0, settings[0], True, 4), negative_attacks)
    _expect_error("undeclared_setting", lambda: proto.generate(0, {"closure_order": "bbox"}, 2, 4), negative_attacks)
    _expect_error("bool_grid_cell", lambda: proto.transform([[True]], settings[0]), negative_attacks)
    _expect_error("missing_separator", lambda: proto.transform([[2, 0], [0, 2]], settings[0]), negative_attacks)

    duplicate = copy.deepcopy(sample)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    _expect_error("duplicate_private_input", lambda: proto.certify(duplicate), negative_attacks)
    corrupt = copy.deepcopy(sample)
    corrupt["train"][0]["output"] = [[0]]
    _expect_error("corrupt_label", lambda: proto.certify(corrupt), negative_attacks)
    stale = copy.deepcopy(sample)
    stale["program_solution"] = proto.program(settings[1])
    _expect_error("stale_program", lambda: proto.certify(stale), negative_attacks)
    forged = copy.deepcopy(sample)
    forged["certificate"] = {"survivors": [settings[1]], "racket_checked": True}
    recomputed = proto.certify(forged)
    assert recomputed["survivors"] == [settings[0]] and recomputed["racket_checked"] is False
    negative_attacks.append("forged_certificate_ignored_and_recomputed")

    racket_calls = 0
    cache = {}
    with RacketBridge(timeout=60) as bridge:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket" and identity["protected"] is True

        def execute(source, grid):
            nonlocal racket_calls
            key = (proto.digest(source), proto.digest(grid))
            if key not in cache:
                cache[key] = proto.execute_rule(source, grid, bridge=bridge)
                racket_calls += 1
            return copy.deepcopy(cache[key])

        for seed in seeds:
            for setting in settings:
                episode = generated[(seed, setting["closure_order"], 6)]
                for pair in episode["train"] + episode["test"]:
                    assert execute(episode["program_solution"], pair["input"]) == pair["output"]
                survivors = []
                for candidate in settings:
                    source = proto.program(candidate)
                    if all(
                        execute(source, pair["input"]) == pair["output"]
                        for pair in episode["train"][:2]
                    ):
                        survivors.append(candidate)
                assert survivors == [setting]

    stress = [metric for metric in metrics if metric["height"] == 30 and metric["width"] == 30]
    assert len(stress) == len(seeds) * len(settings)
    assert min(metric["mark_count"] for metric in stress) >= 27
    assert min(metric["occupied_rows"] for metric in stress) == 30
    assert min(metric["occupied_columns"] for metric in stress) >= 24
    assert min(metric["order_disagreement_cells"] for metric in metrics) >= 4
    assert min(metric["row_then_column_exactly_two"] for metric in metrics) >= 1
    assert min(metric["column_then_row_exactly_two"] for metric in metrics) >= 1

    identity_keep = {
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
    sources = [
        TASK_HOME / "generator.py",
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "canonical.rkt",
        TASK_HOME / "tests/test_parametric_closure_order.py",
    ]
    return {
        "schema": "arcpuzzles-parametric-adversarial-probe-v1",
        "task_id": proto.TASK_ID,
        "status": "pass_finite_bounded",
        "settings": settings,
        "seeds": seeds,
        "demo_counts": counts,
        "query_count": 4,
        "episodes_checked": episodes,
        "distinct_generated_scenes": len(scene_digests),
        "minimum_demo_survivor_count": 1,
        "semantic_rivals_refuted": list(proto.RIVAL_NAMES),
        "crossed_control_checks": crossed_controls,
        "public_projection_checks": public_projection_checks,
        "negative_attacks": negative_attacks,
        "protected_racket_evaluations": racket_calls,
        "racket": identity_keep,
        "metrics": {
            "scene_count_with_matched_setting_duplicates": len(metrics),
            "minimum_order_disagreement_cells": min(m["order_disagreement_cells"] for m in metrics),
            "maximum_height": max(m["height"] for m in metrics),
            "maximum_width": max(m["width"] for m in metrics),
            "stress_30x30_count": len(stress),
            "stress_minimum_marks": min(m["mark_count"] for m in stress),
            "stress_minimum_occupied_rows": min(m["occupied_rows"] for m in stress),
            "stress_minimum_occupied_columns": min(m["occupied_columns"] for m in stress),
        },
        "findings_repaired": [
            {
                "finding": "ordinary easy generation used two panels, so all-panel intersection matched majority",
                "repair": "ordinary base now emits three or four panels with guaranteed exactly-two and three-way closure overlap",
            },
            {
                "finding": "first 30x30 parametric stress draft used only 22 of 27 panel columns",
                "repair": "added an output-neutral incomplete shelf so final scenes use at least 25 panel columns without changing either rule label",
            },
        ],
        "finite_limit": "Six fixed adversarial seeds and the declared 2/6 demonstration corners do not prove universal uniqueness; native owner acceptance remains separate.",
        "source_sha256": {path.relative_to(ROOT).as_posix(): _sha(path) for path in sources},
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    report = run_probe()
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "episodes": report["episodes_checked"],
        "racket_evaluations": report["protected_racket_evaluations"],
        "out": str(output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
