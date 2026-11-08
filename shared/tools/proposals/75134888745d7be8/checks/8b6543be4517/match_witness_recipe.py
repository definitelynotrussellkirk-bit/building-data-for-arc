"""Bind an audited causal case to exact native qualification episode/pair bytes.

This only prepares a recipe. The native review_witness build command must still
validate current source and execute both programs through protected Racket.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def same(a, b):
    return json.dumps(a, sort_keys=True, allow_nan=False) == json.dumps(b, sort_keys=True, allow_nan=False)


def bind(qualification_path, case, template):
    qualification = json.loads(qualification_path.read_text())
    execution_path = qualification_path.parent / "execution.json"
    body = execution_path.read_bytes()
    if hashlib.sha256(body).hexdigest() != qualification["execution"]["sha256"]:
        raise ValueError("execution bytes do not match the qualification receipt")
    if qualification.get("status") != "qualified":
        raise ValueError("native qualification is not qualified")
    if same(case["output"], case["counterfactual_output"]):
        raise ValueError("audited counterfactual does not change the final output")
    execution = json.loads(body)
    for episode_index, episode in enumerate(execution["episodes"]):
        if not (same(episode["settings"], case["settings"]) and episode["program"] == case["program"]):
            continue
        for split in ("train", "test"):
            for pair_index, pair in enumerate(episode[split]):
                if same(pair["input"], case["input"]) and same(pair["output"], case["output"]):
                    recipe = {key: template[key] for key in
                              ("step_a", "intermediate", "step_b", "why_b_depends_on_a")}
                    if not all(type(value) is str and value.strip() for value in recipe.values()):
                        raise ValueError("supply all four causal descriptions in the template")
                    recipe["cases"] = [{"episode_index": episode_index, "split": split,
                                        "pair_index": pair_index,
                                        "intermediate_value": case["intermediate_value"],
                                        "counterfactual_program": case["counterfactual_program"],
                                        "ablation": case["ablation"]}]
                    return recipe
    raise ValueError("audited setting/program/input/output has no exact qualified pair")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", required=True, type=Path)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        recipe = bind(args.qualification, json.loads(args.case.read_text()),
                      json.loads(args.template.read_text()))
        with args.out.open("x", encoding="utf-8") as handle:
            json.dump(recipe, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
    except (OSError, KeyError, ValueError, TypeError) as error:
        parser.exit(1, f"match_witness_recipe: {error}\n")
    case = recipe["cases"][0]
    print(json.dumps({"status": "draft_only", "episode_index": case["episode_index"],
                      "split": case["split"], "pair_index": case["pair_index"], "out": str(args.out)}))


if __name__ == "__main__":
    main()
