"""Bounded self-review for the f2e717c7c250 crop-then-rotate family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("f2_dominant_rotate_audit_prototype", HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent prototype")
P = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = P
_SPEC.loader.exec_module(P)


def rival_outputs(grid):
    facts = P.analyze(grid)
    crop = facts["crop"]
    first_is_smaller = facts["keys"][0] < facts["keys"][1]
    return {
        "crop_only": crop,
        "always_cw": P.rotate_cw(crop),
        "always_ccw": P.rotate_ccw(crop),
        "always_180": P.rotate_180(crop),
        "smaller_key_cw": P.rotate_cw(crop) if first_is_smaller else P.rotate_ccw(crop),
        "larger_key_cw": P.rotate_ccw(crop) if first_is_smaller else P.rotate_cw(crop),
        "wrong_dominant_direction": P.apply_wrong_direction(grid),
    }


def python_audit(*, seeds=(0, 17), demo_counts=range(2, 7)):
    ambiguities = []
    stress = 0
    episodes = 0
    rival_names = set()
    for seed in seeds:
        for demos in demo_counts:
            episode = P.generate_episode(seed, postprocess="dominant_key_rotate", demos=demos, queries=4)
            episodes += 1
            if (len(episode["test"][3]["input"]), len(episode["test"][3]["input"][0])) == (30, 30):
                stress += 1
            fitting = None
            for pair in episode["train"]:
                outputs = rival_outputs(pair["input"])
                rival_names.update(outputs)
                here = {name for name, output in outputs.items() if output == pair["output"]}
                fitting = here if fitting is None else fitting & here
            for query_index, pair in enumerate(episode["test"]):
                outputs = rival_outputs(pair["input"])
                for name in sorted(fitting or ()):
                    if outputs[name] != pair["output"]:
                        ambiguities.append({"seed": seed, "demos": demos, "query_index": query_index, "rival": name})
    return {
        "schema": "f2e717c7c250-dominant-key-rotate-audit-v1",
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
        for mode in P.POSTPROCESSES:
            episode = P.generate_episode(0, postprocess=mode, demos=2, queries=4)
            wrapped = wrap_rule(P.rule_text(mode))
            for pair in episode["train"] + episode["test"]:
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
                actual = bridge.eval_text(f"({wrapped} {literal})")
                if actual != pair["output"]:
                    raise AssertionError((mode, checked))
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
        mode: P.generate_episode(0, postprocess=mode, demos=3, queries=4)
        for mode in P.POSTPROCESSES
    }
    examples["causal_case"] = case
    examples_dir = args.out / "examples"
    examples_dir.mkdir(exist_ok=True)
    (examples_dir / "private.json").write_text(json.dumps(examples, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "audit": str(args.out / "audit.json")}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
