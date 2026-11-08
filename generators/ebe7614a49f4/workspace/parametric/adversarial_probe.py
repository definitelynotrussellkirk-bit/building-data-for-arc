"""Bounded adversarial probe for the ``ebe7614a49f4`` point/ray family.

This is deliberately reusable by later reviewers: pure sampler/certificate/privacy
checks can run without Racket, while the CLI additionally replays a bounded
native contract and a causal counterfactual through protected Racket.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

from reviewer_support import find_root, public_challenge_bytes

TASK_ID = "ebe7614a49f4"
ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "promotion.json"
PROTOTYPE = HERE / "prototype.py"


def _load_prototype():
    name = "_ebe7614a49f4_probe_" + hashlib.sha256(str(PROTOTYPE).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _expect_rejected(call) -> bool:
    try:
        call()
    except (TypeError, ValueError):
        return True
    return False


def _sampler_sweep(prototype, sweep_seeds: Iterable[int]) -> dict:
    seeds = tuple(sweep_seeds)
    episodes = 0
    minimum = 0
    matched_pairs = 0
    input_count = 0
    failures = []
    sizes = set()
    for seed in seeds:
        for demos in (2, 6):
            by_setting = {}
            for setting in prototype.SETTINGS:
                try:
                    episode = prototype.generate(seed, setting, demos=demos, queries=4)
                except Exception as exc:
                    failures.append({
                        "seed": seed,
                        "demos": demos,
                        "settings": setting,
                        "error": type(exc).__name__,
                        "message": str(exc),
                    })
                    continue
                episodes += 1
                minimum += demos == 2
                by_setting[setting["render"]] = episode
                inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
                input_count += len(inputs)
                if len({prototype.digest(grid) for grid in inputs}) != len(inputs):
                    failures.append({"seed": seed, "demos": demos, "settings": setting, "kind": "duplicate_inputs"})
                for grid in inputs:
                    info = prototype.profile(grid)
                    sizes.add(tuple(info["dimensions"]))
                    if not info["sequentially_decisive"]:
                        failures.append({"seed": seed, "demos": demos, "settings": setting, "kind": "selector_bypass"})
                certificate = episode["certificate"]
                if certificate["survivors"] != [setting]:
                    failures.append({"seed": seed, "demos": demos, "settings": setting, "kind": "ambiguous_setting"})
                if any(not rows for rows in certificate["extra_refutations"].values()):
                    failures.append({"seed": seed, "demos": demos, "settings": setting, "kind": "shortcut_survivor"})
            if set(by_setting) == {"points", "rays"}:
                points = by_setting["points"]
                rays = by_setting["rays"]
                left = [pair["input"] for pair in points["train"] + points["test"]]
                right = [pair["input"] for pair in rays["train"] + rays["test"]]
                if left != right:
                    failures.append({"seed": seed, "demos": demos, "kind": "unmatched_inputs"})
                else:
                    matched_pairs += len(left)
                if points["test"] != prototype.generate(seed, {"render": "points"}, 2, 4)["test"]:
                    failures.append({"seed": seed, "demos": demos, "kind": "query_bank_depends_on_demo_count"})
    return {
        "seed_count": len(seeds),
        "episodes": episodes,
        "minimum_demo_episodes": minimum,
        "matched_input_pairs": matched_pairs,
        "input_count": input_count,
        "sizes": [list(size) for size in sorted(sizes)],
        "failures": failures,
    }


def _crossed_controls(prototype) -> dict:
    grid = prototype.generate(31, {"render": "rays"}, demos=2, queries=4)["test"][1]["input"]
    changed_decoy = prototype.change_decoy_codes(grid)
    changed_selected = prototype.change_selected_code(grid)
    original_intermediate = prototype.intersections(grid)
    decoy_preserved = (
        original_intermediate == prototype.intersections(changed_decoy)
        and prototype.transform(grid, {"render": "rays"})
        == prototype.transform(changed_decoy, {"render": "rays"})
    )
    selected_changed = (
        original_intermediate == prototype.intersections(changed_selected)
        and prototype.transform(grid, {"render": "rays"})
        != prototype.transform(changed_selected, {"render": "rays"})
    )
    return {
        "decoy_change_preserved_intermediate": original_intermediate == prototype.intersections(changed_decoy),
        "decoy_change_preserved_output": decoy_preserved,
        "selected_code_preserved_intermediate": original_intermediate == prototype.intersections(changed_selected),
        "selected_code_changed_output": selected_changed,
    }


def _tamper_rejections(prototype) -> dict:
    episode = prototype.generate(7, prototype.DEFAULT, demos=2, queries=4)
    cases = []
    wrong_label = copy.deepcopy(episode)
    wrong_label["train"][0]["output"] = [[9]]
    cases.append(("wrong_label", wrong_label))
    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    cases.append(("duplicate_input", duplicate))
    bool_cell = copy.deepcopy(episode)
    bool_cell["test"][0]["input"][0][0] = True
    cases.append(("bool_cell", bool_cell))
    forged_program = copy.deepcopy(episode)
    forged_program["program_solution"] = prototype.program({"render": "rays"})
    cases.append(("forged_program", forged_program))
    forged_certificate = copy.deepcopy(episode)
    forged_certificate["certificate"]["survivors"] = [prototype.DEFAULT, {"render": "rays"}]
    cases.append(("forged_certificate", forged_certificate))
    results = {name: _expect_rejected(lambda value=value: prototype.certify(value)) for name, value in cases}
    request_results = {
        "bool_seed": _expect_rejected(lambda: prototype.generate(True, prototype.DEFAULT, 2, 4)),
        "one_demo": _expect_rejected(lambda: prototype.generate(0, prototype.DEFAULT, 1, 4)),
        "seven_demos": _expect_rejected(lambda: prototype.generate(0, prototype.DEFAULT, 7, 4)),
        "one_query": _expect_rejected(lambda: prototype.generate(0, prototype.DEFAULT, 2, 1)),
        "five_queries": _expect_rejected(lambda: prototype.generate(0, prototype.DEFAULT, 2, 5)),
        "extra_setting": _expect_rejected(lambda: prototype.generate(0, {"render": "points", "x": 1}, 2, 4)),
    }
    combined = {**results, **request_results}
    return {"cases": combined, "all_rejected": all(combined.values())}


def _public_projection(prototype) -> dict:
    episode = prototype.generate(29, {"render": "rays"}, demos=3, queries=4)
    visible = {"train": episode["train"], "test": [episode["test"][0]]}
    base = public_challenge_bytes(visible)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"render": "points"}
    changed["program_solution"] = "private replacement"
    changed["test"][0]["output"][0][0] = (changed["test"][0]["output"][0][0] + 1) % 10
    changed["test"][1]["input"][0][0] = (changed["test"][1]["input"][0][0] + 1) % 10
    changed["test"][3]["output"][0][0] = (changed["test"][3]["output"][0][0] + 1) % 10
    alternate = public_challenge_bytes({"train": changed["train"], "test": [changed["test"][0]]})
    return {
        "visible_sha256": hashlib.sha256(base).hexdigest(),
        "private_fields_hidden": base == alternate,
        "first_query_answer_hidden": base == alternate,
        "future_queries_hidden": base == alternate,
    }


def _racket_apply(program: str, grid: list[list[int]], bridge):
    from puzzle_generators.rule_wrap import wrap_rule

    wrapped = wrap_rule(program)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrapped} {literal})")




def _racket_case_list(racket_cases):
    return tuple(racket_cases or ()) or ((0, 2), (17, 2), (0, 6), (17, 6))

def _protected_racket(prototype, racket_cases) -> dict:
    from arc_repl.racket_bridge import RacketBridge
    from arcpuzzles.parametric_worker import evaluate_contract

    contract = json.loads(CONTRACT.read_text())
    cases = _racket_case_list(racket_cases)
    jobs = [
        {"seed": seed, "settings": setting, "demos": demos, "queries": 4}
        for seed, demos in cases
        for setting in prototype.SETTINGS
    ]
    native = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    episode = prototype.generate(17, {"render": "rays"}, demos=2, queries=4)
    pair = episode["test"][0]
    with RacketBridge(timeout=60) as bridge:
        intended = _racket_apply(prototype.RAYS_PROGRAM, pair["input"], bridge)
        counterfactual = _racket_apply(prototype.ALL_DIRECTION_TOKENS_PROGRAM, pair["input"], bridge)
        identity = {
            key: bridge.runtime_identity[key]
            for key in ("schema", "backend", "protected", "binary_sha256")
            if key in bridge.runtime_identity
        }
    if intended != pair["output"] or intended == counterfactual:
        raise AssertionError("protected Racket causal counterfactual failed")
    return {
        "status": "passed",
        "job_count": len(jobs),
        "racket": native["racket"],
        "racket_evaluations": native["racket_evaluations"],
        "causal_counterfactual": {
            "ablation": "skip_a",
            "output_changed": intended != counterfactual,
            "racket": identity,
            "counterfactual_program_sha256": hashlib.sha256(
                prototype.ALL_DIRECTION_TOKENS_PROGRAM.encode()
            ).hexdigest(),
        },
    }


def run_probe(*, prototype=None, sweep_seeds=range(64), racket_cases=None, include_racket=True) -> dict:
    prototype = _load_prototype() if prototype is None else prototype
    sweep = _sampler_sweep(prototype, sweep_seeds)
    crossed = _crossed_controls(prototype)
    tamper = _tamper_rejections(prototype)
    public = _public_projection(prototype)
    stress_grid = prototype.generate(41, {"render": "rays"}, demos=2, queries=4)["test"][-1]["input"]
    stress = prototype.profile(stress_grid)
    protected = (
        _protected_racket(prototype, racket_cases)
        if include_racket
        else {"status": "not_run"}
    )
    failures = []
    if sweep["failures"]:
        failures.append("sampler")
    if not all(crossed.values()):
        failures.append("crossed_controls")
    if not tamper["all_rejected"]:
        failures.append("tamper_rejection")
    if not all(public[key] for key in ("private_fields_hidden", "first_query_answer_hidden", "future_queries_hidden")):
        failures.append("public_projection")
    if stress["dimensions"] != (30, 30) or stress["route_cell_count"] < 60 or not stress["touches_all_boundaries"]:
        failures.append("30x30_stress")
    if include_racket and protected.get("status") != "passed":
        failures.append("protected_racket")
    if failures:
        raise AssertionError("adversarial probe failures: " + ", ".join(failures))
    return {
        "schema": "arcpuzzles-ebe7614a49f4-adversarial-probe-v1",
        "status": "passed",
        "settings": [setting["render"] for setting in prototype.SETTINGS],
        "minimum_demo_count": 2,
        "maximum_demo_count": 6,
        "query_count": 4,
        "semantic_shortcuts_tested": list(prototype.RIVAL_NAMES),
        "pure_sampler_sweep": sweep,
        "crossed_controls": crossed,
        "tamper_rejections": tamper,
        "public_projection": public,
        "thirty_square": stress,
        "protected_racket": protected,
        "limits": (
            "Finite authored attacks over the requested seeds, two settings, 2/6-demo corners, "
            "four queries, eight shortcut families and bounded Racket jobs; not universal uniqueness."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--no-racket", action="store_true")
    args = parser.parse_args()
    if type(args.seeds) is not int or not 1 <= args.seeds <= 512:
        raise ValueError("--seeds must be in 1..512")
    report = run_probe(sweep_seeds=range(args.seeds), include_racket=not args.no_racket)
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(args.out),
        "episodes": report["pure_sampler_sweep"]["episodes"],
        "racket_evaluations": report["protected_racket"].get("racket_evaluations", 0),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
