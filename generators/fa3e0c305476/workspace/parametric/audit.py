"""Bounded self-review for the fa3e0c305476 anchor-hole relay family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("fa_anchor_hole_audit_prototype", HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent prototype")
P = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = P
_SPEC.loader.exec_module(P)


def _paint(grid, predicate, *, first_only=False):
    info = P.analyze(grid)
    out = [row[:] for row in grid]
    used = False
    for index, obj in enumerate(info["objects"]):
        count = obj["hole_count"]
        selected = bool(predicate(index, obj, info)) and (not first_only or not used)
        if selected:
            used = True
        color = P.COLOR_BY_COUNT.get(count, 8) if selected else 8
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def rival_outputs(grid):
    return {
        "all_objects": P.apply_scope(grid, "all_objects"),
        "anchor_only": _paint(grid, lambda index, _obj, _info: index == 0),
        "first_match_only": _paint(
            grid,
            lambda _index, obj, info: obj["hole_count"] == info["anchor_hole_count"],
            first_only=True,
        ),
        "fixed_count_1": _paint(grid, lambda _i, obj, _info: obj["hole_count"] == 1),
        "fixed_count_2": _paint(grid, lambda _i, obj, _info: obj["hole_count"] == 2),
        "fixed_count_3": _paint(grid, lambda _i, obj, _info: obj["hole_count"] == 3),
        "fixed_count_4": _paint(grid, lambda _i, obj, _info: obj["hole_count"] == 4),
        "second_object_anchor": P.apply_second_anchor(grid),
    }


def python_audit(*, seeds=(0, 17), demo_counts=range(2, 7)):
    ambiguities = []
    stress = 0
    episodes = 0
    rival_names = set()
    for seed in seeds:
        for demos in demo_counts:
            episode = P.generate_episode(
                seed,
                recolor_scope="anchor_hole_matches",
                demos=demos,
                queries=4,
            )
            episodes += 1
            if (len(episode["test"][3]["input"]), len(episode["test"][3]["input"][0])) == (30, 30):
                stress += 1
            demo_rivals = None
            for pair in episode["train"]:
                outputs = rival_outputs(pair["input"])
                rival_names.update(outputs)
                fitting = {name for name, output in outputs.items() if output == pair["output"]}
                demo_rivals = fitting if demo_rivals is None else demo_rivals & fitting
            for query_index, pair in enumerate(episode["test"]):
                outputs = rival_outputs(pair["input"])
                for name in sorted(demo_rivals or ()):
                    if outputs[name] != pair["output"]:
                        ambiguities.append({
                            "seed": seed,
                            "demos": demos,
                            "query_index": query_index,
                            "rival": name,
                        })
    return {
        "schema": "fa3e0c305476-anchor-hole-audit-v1",
        "status": "passed" if not ambiguities else "failed",
        "episodes": episodes,
        "stress_30x30": stress,
        "rivals": sorted(rival_names),
        "ambiguities": ambiguities,
        "limits": "Finite declared rivals over seeds 0 and 17; not universal uniqueness.",
    }


def _racket_check():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    checked = 0
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        for scope in P.SCOPES:
            episode = P.generate_episode(0, recolor_scope=scope, demos=2, queries=4)
            wrapped = wrap_rule(P.rule_text(scope))
            for pair in episode["train"] + episode["test"]:
                literal = "'(" + " ".join(
                    "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
                ) + ")"
                actual = bridge.eval_text(f"({wrapped} {literal})")
                if actual != pair["output"]:
                    raise AssertionError((scope, checked))
                checked += 1
    return {"backend": "racket", "protected": True, "labels_checked": checked}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    report = python_audit()
    report["racket"] = _racket_check()
    case = P.causal_case(0)
    report["causal_case"] = {
        "settings": case["settings"],
        "input_sha256": hashlib.sha256(json.dumps(case["input"], separators=(",", ":")).encode()).hexdigest(),
        "output_differs": case["output"] != case["counterfactual_output"],
        "ablation": case["ablation"],
        "intermediate_value": case["intermediate_value"],
    }
    (args.out / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    examples = {
        scope: P.generate_episode(0, recolor_scope=scope, demos=3, queries=4)
        for scope in P.SCOPES
    }
    examples["causal_case"] = case
    examples_dir = args.out / "examples"
    examples_dir.mkdir(exist_ok=True)
    (examples_dir / "private.json").write_text(json.dumps(examples, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "audit": str(args.out / "audit.json")}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
