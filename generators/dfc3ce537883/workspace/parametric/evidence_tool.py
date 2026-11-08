#!/usr/bin/env python3
"""Build compact, source-bound author evidence for the dfc3ce537883 prototype.

This tool is intentionally task-local so future reviewers can rerun the same
bounded teaching, parity, public-projection, count-boundary, and shortcut audit
without reconstructing ad-hoc commands.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id

_HOME = Path(__file__).resolve().parent
_PROTO_PATH = _HOME / "prototype.py"
_SPEC = importlib.util.spec_from_file_location("dfc3ce537883_evidence_prototype", _PROTO_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load prototype from {_PROTO_PATH}")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    bridge.define_grid("g", grid)
    return bridge.eval_text(f"({wrap_rule(program)} g)")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _public_episode(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": deepcopy(episode["train"]),
        "test": deepcopy(episode["test"]),
        # Deliberately present private fields; the serializer must exclude them.
        "settings": deepcopy(episode["settings"]),
        "program": episode["program"],
        "seed": episode["seed"],
    }


def first_turn_public_bytes(episode: dict[str, Any]) -> bytes:
    """Project stored four-query controller data to the single visible first turn."""
    if type(episode) is not dict or type(episode.get("test")) is not list or not episode["test"]:
        raise ValueError("episode needs at least one stored query")
    return public_challenge_bytes(
        {
            "train": deepcopy(episode.get("train")),
            "test": [deepcopy(episode["test"][0])],
        }
    )


def run(*, seed: int = 17) -> tuple[dict[str, Any], bytes, str]:
    """Execute the bounded prequalification audit and return report/public bytes."""
    count_cases: list[dict[str, Any]] = []
    teaching: list[dict[str, Any]] = []
    evaluations = 0
    declared = {
        followup: prototype.program_for(followup)
        for followup in prototype.ALLOWED_FOLLOWUPS
    }
    shortcuts = {
        name: prototype.shortcut_program(name)
        for name in prototype.PLAUSIBLE_SHORTCUTS
    }

    with RacketBridge(max_calls_before_restart=256) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise AssertionError("prequalification evidence requires protected Racket")

        for case_seed, demos in ((seed, 2), (seed + 1, 6)):
            for followup in prototype.ALLOWED_FOLLOWUPS:
                episode = prototype.make_episode(
                    case_seed,
                    followup=followup,
                    demos=demos,
                    queries=4,
                )
                pairs = episode["train"] + episode["test"]
                for pair in pairs:
                    actual = _execute(bridge, declared[followup], pair["input"])
                    evaluations += 1
                    if actual != pair["output"]:
                        raise AssertionError(f"Racket/Python parity failed for {followup}")
                survivors: list[str] = []
                for rival, program in declared.items():
                    outputs = [_execute(bridge, program, pair["input"]) for pair in episode["train"]]
                    evaluations += len(outputs)
                    if all(output == pair["output"] for output, pair in zip(outputs, episode["train"])):
                        survivors.append(rival)
                if survivors != [followup]:
                    raise AssertionError(f"demo-only declared survivors for {followup}: {survivors}")
                teaching.append(
                    {
                        "seed": case_seed,
                        "demos": demos,
                        "queries": 4,
                        "chosen": followup,
                        "survivors": survivors,
                    }
                )
                count_cases.append(
                    {
                        "seed": case_seed,
                        "followup": followup,
                        "demos": demos,
                        "queries": 4,
                        "input_count": len(pairs),
                        "distinct_inputs": len({repr(pair["input"]) for pair in pairs}),
                        "query_shapes": [
                            [len(pair["input"]), len(pair["input"][0])]
                            for pair in episode["test"]
                        ],
                    }
                )

        audit_episode = prototype.make_episode(
            seed,
            followup=prototype.ALTERNATE_FOLLOWUP,
            demos=2,
            queries=4,
        )
        self_review: list[dict[str, Any]] = []
        for name, program in shortcuts.items():
            outputs = []
            python_outputs = []
            for pair in audit_episode["train"] + audit_episode["test"]:
                outputs.append(_execute(bridge, program, pair["input"]))
                python_outputs.append(prototype.apply_shortcut_python(pair["input"], name))
                evaluations += 1
            if outputs != python_outputs:
                raise AssertionError(f"Racket/Python shortcut parity failed for {name}")
            demo_count = len(audit_episode["train"])
            demo_matches = [
                output == pair["output"]
                for output, pair in zip(outputs[:demo_count], audit_episode["train"])
            ]
            query_matches = [
                output == pair["output"]
                for output, pair in zip(outputs[demo_count:], audit_episode["test"])
            ]
            if all(demo_matches):
                raise AssertionError(f"plausible shortcut survived every visible demo: {name}")
            first_mismatch = demo_matches.index(False)
            pair = audit_episode["train"][first_mismatch]
            self_review.append(
                {
                    "shortcut": name,
                    "program": program,
                    "program_sha256": _sha256_text(program),
                    "demo_matches": demo_matches,
                    "query_matches": query_matches,
                    "survives_all_demos": False,
                    "refuting_case": {
                        "demo_index": first_mismatch,
                        "input": pair["input"],
                        "expected_output": pair["output"],
                        "shortcut_output": outputs[first_mismatch],
                    },
                }
            )

    public = _public_episode(audit_episode)
    public_bytes = public_challenge_bytes(public)
    public_id = public_challenge_id(public)
    mutated = deepcopy(public)
    mutated["settings"] = {"followup": "private-mutated"}
    mutated["program"] = "private-mutated"
    mutated["seed"] += 999
    mutated["test"][0]["output"][0][0] ^= 1
    if public_challenge_bytes(mutated) != public_bytes or public_challenge_id(mutated) != public_id:
        raise AssertionError("private fields or query labels changed public challenge identity")

    first_turn = first_turn_public_bytes(audit_episode)
    future_mutated = deepcopy(audit_episode)
    for index, pair in enumerate(future_mutated["test"][1:], start=1):
        pair["input"] = [[index]]
        pair["output"] = [[9 - index]]
    future_mutated["total_queries"] = 999
    if first_turn_public_bytes(future_mutated) != first_turn:
        raise AssertionError("future queries or count metadata changed first-turn public bytes")
    visible_first = json.loads(first_turn)
    if set(visible_first) != {"train", "test"} or len(visible_first["test"]) != 1:
        raise AssertionError("first-turn projection must expose exactly one query and no count metadata")

    report = {
        "schema": "arcpuzzles-dfc3ce537883-prequalification-v1",
        "task_id": prototype.TASK_ID,
        "status": "pass",
        "prototype_version": prototype.PROTOTYPE_VERSION,
        "racket": {
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
        },
        "racket_evaluations": evaluations,
        "declared_programs": {
            name: _sha256_text(program) for name, program in declared.items()
        },
        "count_boundaries": count_cases,
        "demo_only_teaching": teaching,
        "self_review": {
            "question": "Can a plausible wrong rule fit every visible demo yet disagree on a query?",
            "tested_rivals": self_review,
            "survivors": [],
            "scope": "Only the three named finite rivals were tested; this is not universal uniqueness.",
        },
        "query_audit": prototype.audit_episode(audit_episode),
        "public_projection": {
            "public_id": public_id,
            "sha256": hashlib.sha256(public_bytes).hexdigest(),
            "bytes": len(public_bytes),
            "private_metadata_and_query_label_invariance": True,
            "queries": 4,
            "demos": len(audit_episode["train"]),
            "first_turn_sha256": hashlib.sha256(first_turn).hexdigest(),
            "first_turn_queries_visible": 1,
            "identical_to_single_query_projection": True,
            "future_queries_and_count_metadata_invariant": True,
        },
        "limits": "Bounded seeds/counts and finite rivals only; qualification remains the native authority.",
        "training_admitted": False,
    }
    return report, public_bytes, public_id



STEP_A = (
    "Mirror every nonzero, non-9 cell left of the full-height color-9 divider "
    "to the equal-distance right cell."
)
INTERMEDIATE = (
    "The mirrored color-2 probe's unique adjacent candidate frame: its color, "
    "perimeter cell count, bounding box, and size-derived fill color."
)
STEP_B = (
    "Fill the selected candidate frame's bounding box with color 1 for an "
    "8-cell 3x3 frame or color 5 for a 12-cell 4x4 frame."
)
WHY_B_DEPENDS_ON_A = (
    "Before A there is no right-side color-2 probe, so B cannot know which of "
    "the color-3/4 frames is selected; replacing A's selected-frame intermediate "
    "with the other frame changes the final grid."
)


def build_sequential_witness(qualification_path: Path, *, seed: int = 17) -> dict[str, Any]:
    """Build and protected-Racket replay one 30x30 wrong-intermediate witness."""
    qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
    if (
        qualification.get("schema") != "arcpuzzles-parametric-qualification-v1"
        or qualification.get("status") != "qualified"
        or qualification.get("task_id") != prototype.TASK_ID
    ):
        raise ValueError("qualification_path is not this task's qualified native receipt")
    episode = prototype.make_episode(
        seed,
        followup=prototype.ALTERNATE_FOLLOWUP,
        demos=3,
        queries=4,
    )
    grid = episode["test"][-1]["input"]
    case = prototype.build_dependency_case(grid)
    setting_key = json.dumps(case["settings"], sort_keys=True, separators=(",", ":"))
    expected_hash = qualification.get("programs", {}).get(setting_key)
    if expected_hash != _sha256_text(case["program"]):
        raise ValueError("witness program is not the qualified alternate setting program")
    with RacketBridge(max_calls_before_restart=32) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise AssertionError("sequential witness requires protected Racket")
        actual = _execute(bridge, case["program"], grid)
        counterfactual = _execute(bridge, case["counterfactual_program"], grid)
    if actual != case["output"] or counterfactual != case["counterfactual_output"]:
        raise AssertionError("protected Racket witness labels differ from Python construction")
    if actual == counterfactual:
        raise AssertionError("wrong-intermediate witness does not change final output")
    case["output"] = actual
    case["counterfactual_output"] = counterfactual
    return {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "source_binding": qualification["source_binding"],
        "racket": {"backend": "racket", "protected": True},
        "step_a": STEP_A,
        "intermediate": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY_B_DEPENDS_ON_A,
        "cases": [case],
        "limits": (
            "One bounded 30x30 wrong-intermediate case; protected execution proves "
            "the reported output change, not universal algorithmic depth."
        ),
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--public-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--qualification", type=Path)
    parser.add_argument("--witness-out", type=Path)
    args = parser.parse_args(argv)
    report, public_bytes, public_id = run(seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.public_dir.mkdir(parents=True, exist_ok=True)
    public_path = args.public_dir / f"challenge-{public_id}.json"
    public_path.write_bytes(public_bytes)
    witness_path = None
    if (args.qualification is None) != (args.witness_out is None):
        raise ValueError("--qualification and --witness-out must be supplied together")
    if args.qualification is not None:
        witness = build_sequential_witness(args.qualification, seed=args.seed)
        args.witness_out.parent.mkdir(parents=True, exist_ok=True)
        args.witness_out.write_text(
            json.dumps(witness, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        witness_path = str(args.witness_out)
    print(
        json.dumps(
            {
                "status": report["status"],
                "out": str(args.out),
                "public": str(public_path),
                "witness": witness_path,
                "racket_evaluations": report["racket_evaluations"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
