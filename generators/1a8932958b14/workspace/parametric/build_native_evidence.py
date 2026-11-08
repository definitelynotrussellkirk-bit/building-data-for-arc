#!/usr/bin/env python3
"""Build compact protected-Racket evidence for the native parametric family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from arcpuzzles.review_witness import build_witness
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "1a8932958b14"
HERE = Path(__file__).resolve().parent


def _load_family():
    path = HERE / "family.py"
    name = "_task_1a8932958b14_native_evidence_family"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _apply_factory(bridge: RacketBridge):
    wrapped: dict[str, str] = {}

    def apply(program: str, grid: list[list[int]]) -> list[list[int]]:
        if program not in wrapped:
            wrapped[program] = wrap_rule(program)
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        return bridge.eval_text(f"({wrapped[program]} {literal})")

    return apply


def _program_sha(program: str) -> str:
    return hashlib.sha256(program.encode("utf-8")).hexdigest()


def _pair_rows(episode: dict[str, Any]) -> list[dict[str, Any]]:
    return [*episode["train"], *episode["test"]]


def _admission_recipe(execution: dict[str, Any], family: Any) -> dict[str, Any]:
    """Select a qualified case and author a wrong-intermediate witness recipe.

    The official review_witness builder supplies the exact qualification source
    binding, executes both programs through protected Racket, and replays the
    resulting labels. This helper only chooses a qualified pair and records the
    causal interpretation.
    """
    episodes = execution.get("episodes")
    if not isinstance(episodes, list):
        raise ValueError("qualification execution lacks episodes")
    for episode_index, episode in enumerate(episodes):
        if episode.get("settings") != {"translation_policy": "payload_axis_gate"}:
            continue
        for split in ("train", "test"):
            pairs = episode.get(split)
            if not isinstance(pairs, list):
                continue
            for pair_index, pair in enumerate(pairs):
                grid = pair.get("input") if isinstance(pair, dict) else None
                output = pair.get("output") if isinstance(pair, dict) else None
                if not isinstance(grid, list) or not isinstance(output, list):
                    continue
                trace = family.sequential_trace(grid, "payload_axis_gate")
                axis = trace["intermediate"]
                wrong_axis = "tall" if axis == "wide" else "wide"
                if family.transform_with_axis(grid, wrong_axis) == output:
                    continue
                return {
                    "step_a": "classify payload bounding-box axis",
                    "intermediate": "payload_axis in {wide, tall}",
                    "step_b": "choose marker-vector multiplier from payload axis, then translate",
                    "why_b_depends_on_a": (
                        "Step B uses multiplier +2 for a wide payload and -1 for a tall payload; "
                        "the selected translation cannot be known until Step A classifies the input payload."
                    ),
                    "cases": [
                        {
                            "episode_index": episode_index,
                            "split": split,
                            "pair_index": pair_index,
                            "counterfactual_program": family.forced_axis_program(wrong_axis),
                            "intermediate_value": axis,
                            "ablation": "wrong_intermediate",
                        }
                    ],
                }
    raise ValueError("qualification has no payload-axis case with a harmful wrong intermediate")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--qualification", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    if not out.is_absolute():
        out = (Path.cwd() / out).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"refusing nonempty output directory: {out}")
    out.mkdir(parents=True, exist_ok=True)

    qualification = Path(args.qualification)
    if not qualification.is_absolute():
        qualification = (Path.cwd() / qualification).resolve()
    if not qualification.is_file() or not qualification.with_name("execution.json").is_file():
        raise ValueError("qualification and sibling execution.json are required")

    root = find_root(__file__)
    family = _load_family()
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)

    settings = (
        {"translation_policy": "marker_vector"},
        {"translation_policy": "payload_axis_gate"},
    )
    programs = {setting["translation_policy"]: family.program(setting) for setting in settings}
    forced_programs = {
        "force_wide": family.forced_axis_program("wide"),
        "force_tall": family.forced_axis_program("tall"),
    }

    jobs = []
    public_rows = []
    public_dir = out / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    with RacketBridge(timeout=30.0) as bridge:
        runtime = bridge.runtime_identity
        if runtime.get("backend") != "racket" or runtime.get("protected") is not True:
            raise RuntimeError("evidence requires the protected Racket runtime")
        apply = _apply_factory(bridge)

        for seed in (0, 17):
            for setting in settings:
                selected = setting["translation_policy"]
                episode = family.generate(seed, setting, demos=2, queries=4)
                pairs = _pair_rows(episode)
                actual = [apply(programs[selected], pair["input"]) for pair in pairs]
                if actual != [pair["output"] for pair in pairs]:
                    raise AssertionError(f"Racket labels disagree for {selected=} {seed=}")
                if any(generator.self_check(pair["input"]) for pair in pairs):
                    raise AssertionError("family emitted an input outside canonical grammar")

                other = next(name for name in programs if name != selected)
                other_demo_outputs = [
                    apply(programs[other], pair["input"]) for pair in episode["train"]
                ]
                other_mismatches = [
                    index
                    for index, (predicted, pair) in enumerate(
                        zip(other_demo_outputs, episode["train"])
                    )
                    if predicted != pair["output"]
                ]
                if not other_mismatches:
                    raise AssertionError("other declared setting survived the demonstrations")

                forced_rows = []
                for name, source in forced_programs.items():
                    predicted = [apply(source, pair["input"]) for pair in episode["train"]]
                    mismatches = [
                        index
                        for index, (output, pair) in enumerate(zip(predicted, episode["train"]))
                        if output != pair["output"]
                    ]
                    if not mismatches:
                        raise AssertionError(f"forced-axis rival survived: {name} {selected=} {seed=}")
                    forced_rows.append(
                        {
                            "name": name,
                            "program_sha256": _program_sha(source),
                            "mismatching_demo_indices": mismatches,
                            "refuted": True,
                        }
                    )

                python_audit = family.audit_shortcuts(episode["train"], selected=selected)
                if not all(row["refuted"] for row in python_audit):
                    raise AssertionError("a declared Python shortcut survived the minimum lesson")

                jobs.append(
                    {
                        "seed": seed,
                        "settings": copy.deepcopy(setting),
                        "counts": {"demos": 2, "queries": 4},
                        "selected_program_sha256": _program_sha(programs[selected]),
                        "stored_labels_match_protected_racket": True,
                        "other_declared_setting": other,
                        "other_setting_mismatching_demo_indices": other_mismatches,
                        "forced_axis_rivals": forced_rows,
                        "python_shortcut_audit": python_audit,
                        "scene_facts": family.episode_summary(episode),
                        "harmful_survivors": [],
                    }
                )

                if seed == 0:
                    public = family.public_challenge(episode)
                    public_id = public_challenge_id(public)
                    public_bytes = public_challenge_bytes(public)
                    if public_id != hashlib.sha256(public_bytes).hexdigest():
                        raise AssertionError("public challenge ID is not the exact visible-byte hash")
                    mutated = copy.deepcopy(episode)
                    mutated["test"][0]["output"][0][0] = (
                        mutated["test"][0]["output"][0][0] + 1
                    ) % 10
                    if public_challenge_bytes(family.public_challenge(mutated)) != public_bytes:
                        raise AssertionError("private query answers changed visible bytes")
                    public_path = public_dir / f"{public_id}.json"
                    public_path.write_bytes(public_bytes)
                    public_rows.append(
                        {
                            "settings": copy.deepcopy(setting),
                            "path": str(public_path.relative_to(out)),
                            "public_id": public_id,
                            "sha256": _sha256_bytes(public_bytes),
                            "query_answer_invariance": True,
                        }
                    )

    source_paths = [
        HERE / "adapter.py",
        HERE / "family.py",
        HERE / "canonical.rkt",
        HERE / "promotion.json",
        HERE / "build_native_evidence.py",
        root
        / "generators"
        / TASK_ID
        / "tests"
        / "test_parametric_adapter_1a8932958b14.py",
    ]
    inventory = {
        "schema": "task-parametric-source-inventory-v1",
        "task_id": TASK_ID,
        "canonical_generator": {
            "path": str(generator_path.relative_to(root)),
            "sha256": generator_sha,
            "changed": False,
        },
        "files": [
            {
                "path": str(path.relative_to(root)),
                "sha256": _sha256_bytes(path.read_bytes()),
                "bytes": path.stat().st_size,
            }
            for path in source_paths
        ],
        "programs": {
            name: {"sha256": _program_sha(source), "bytes": len(source.encode("utf-8"))}
            for name, source in {**programs, **forced_programs}.items()
        },
    }

    self_review = {
        "schema": "arcpuzzles-parametric-self-review-v1",
        "task_id": TASK_ID,
        "question": (
            "Can a tested plausible wrong rule fit every visible minimum lesson "
            "demonstration yet disagree on a query?"
        ),
        "result": "no_harmful_survivor_in_finite_set",
        "scope": {
            "seeds": [0, 17],
            "settings": [copy.deepcopy(setting) for setting in settings],
            "demos": 2,
            "queries": 4,
            "protected_racket_rivals": [
                "other declared setting",
                "force wide intermediate",
                "force tall intermediate",
            ],
            "python_rivals": [
                "always_double",
                "always_reverse",
                "axis_gate_swapped",
                "vector_orientation_gate",
                "palette_parity_gate",
            ],
        },
        "jobs": jobs,
        "limitations": [
            "This is finite rival evidence, not a proof of unique induction.",
            "The Python-only rivals are checked against deterministic claim labels; native qualification independently replays declared settings through protected Racket.",
        ],
    }

    execution = json.loads(qualification.with_name("execution.json").read_text(encoding="utf-8"))
    witness_recipe = _admission_recipe(execution, family)
    _json(out / "witness-recipe.json", witness_recipe)
    witness_result = build_witness(
        root, qualification, witness_recipe, out / "causal", timeout=30
    )

    summary = {
        "schema": "arcpuzzles-parametric-native-evidence-v1",
        "task_id": TASK_ID,
        "status": "pass",
        "settings": [copy.deepcopy(setting) for setting in settings],
        "minimum_lesson_jobs": len(jobs),
        "all_stored_labels_match_protected_racket": True,
        "finite_self_review": "no_harmful_survivor_in_tested_set",
        "causal_witness": "causal/witness.json",
        "causal_replay": "causal/replay.json",
        "witness_recipe": "witness-recipe.json",
        "self_review": "self-review.json",
        "source_inventory": "source-inventory.json",
        "public_exports": public_rows,
        "stress_case": jobs[0]["scene_facts"]["test"][-1],
        "racket_runtime": runtime,
        "source": {
            "canonical_generator_path": str(generator_path.relative_to(root)),
            "canonical_generator_sha256": generator_sha,
            "canonical_authority_changed": False,
        },
        "limitations": [
            "Evidence covers two seeds and the declared finite rivals, not every seed or every possible alternative rule.",
            "Reviewer-ready is not owner acceptance or training admission.",
        ],
    }

    _json(out / "self-review.json", self_review)
    _json(out / "source-inventory.json", inventory)
    _json(out / "summary.json", summary)
    print(
        json.dumps(
            {
                "status": "pass",
                "out": str(out),
                "jobs": len(jobs),
                "public_exports": len(public_rows),
                "witness_outputs_differ": True,
                "witness_status": witness_result["status"],
                "source_inventory_sha256": _sha256_json(inventory),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
