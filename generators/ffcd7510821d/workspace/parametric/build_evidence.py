#!/usr/bin/env python3
"""Build protected-Racket causal, shortcut-audit, and public evidence."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes

TASK_ID = "ffcd7510821d"
STEP_A = (
    "Count maroon (9) cells on row 0 modulo four, clear only those marker cells, "
    "and crop the remaining nonzero scene tightly."
)
INTERMEDIATE = (
    "The input-dependent pair (turns modulo four, complete cropped object after "
    "row-0 marker removal)."
)
STEP_B = (
    "Use the private episode direction and the intermediate turn value to choose "
    "and apply the corresponding whole-object quarter-turn rotation."
)
WHY_B_DEPENDS_ON_A = (
    "The rotation branch and its object are not available until the marker count "
    "and crop are computed; forcing a different turn on the same asymmetric crop "
    "changes the protected-Racket final output."
)

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "ffcd7510821d_evidence_prototype",
    _HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load direction-parametric marker rotation prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = prototype
_SPEC.loader.exec_module(prototype)


def _json_bytes(value) -> bytes:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _write_json(path: Path, value) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = _json_bytes(value)
    if path.exists() and path.read_bytes() != raw:
        raise FileExistsError(f"refusing to replace differing evidence: {path}")
    path.write_bytes(raw)
    return path


def write_public_episode(episode: dict, directory: Path) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    public = prototype.public_challenge(episode)
    raw = public_challenge_bytes(public)
    digest = hashlib.sha256(raw).hexdigest()
    path = directory / f"challenge-{digest}.json"
    if path.exists() and path.read_bytes() != raw:
        raise FileExistsError(f"public content identity collision: {path}")
    path.write_bytes(raw)
    return path


def witness_document(source_binding: dict, cases: list[dict]) -> dict:
    if not isinstance(source_binding, dict) or not source_binding:
        raise ValueError("source_binding must be a nonempty object")
    if not isinstance(cases, list) or not 1 <= len(cases) <= 16:
        raise ValueError("witness requires 1..16 cases")
    return {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "source_binding": copy.deepcopy(source_binding),
        "racket": {"backend": "racket", "protected": True},
        "step_a": STEP_A,
        "intermediate": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY_B_DEPENDS_ON_A,
        "cases": copy.deepcopy(cases),
        "limits": (
            "Two bounded qualification-derived cases. Protected Racket proves "
            "the wrong-turn counterfactual on those inputs, not universal uniqueness."
        ),
    }


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _executor(bridge: RacketBridge):
    wrapped: dict[str, str] = {}

    def apply(program: str, grid: list[list[int]]) -> list[list[int]]:
        if program not in wrapped:
            wrapped[program] = wrap_rule(program)
        result = bridge.eval_text(f"({wrapped[program]} {_grid_literal(grid)})")
        return [[int(cell) for cell in row] for row in result]

    return apply


def _setting_key(settings: dict) -> str:
    return json.dumps(
        settings,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _load_qualification(path: Path):
    path = Path(path).resolve()
    qualification = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(qualification, dict)
        or qualification.get("schema") != "arcpuzzles-parametric-qualification-v1"
        or qualification.get("status") != "qualified"
        or qualification.get("task_id") != TASK_ID
        or not isinstance(qualification.get("source_binding"), dict)
    ):
        raise ValueError("expected a qualified source-bound receipt for this task")
    execution_meta = qualification.get("execution")
    if not isinstance(execution_meta, dict) or execution_meta.get("path") != "execution.json":
        raise ValueError("qualification must cite sibling execution.json")
    execution_path = path.parent / "execution.json"
    raw = execution_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != execution_meta.get("sha256"):
        raise ValueError("qualification execution hash differs")
    execution = json.loads(raw)
    if (
        execution.get("racket", {}).get("backend") != "racket"
        or execution.get("racket", {}).get("protected") is not True
        or not isinstance(execution.get("episodes"), list)
    ):
        raise ValueError("qualification lacks protected Racket episodes")
    return qualification, execution


def _programs(qualification: dict) -> dict[str, str]:
    programs = {direction: prototype.program_for(direction) for direction in prototype.DIRECTIONS}
    reported = qualification.get("programs")
    if not isinstance(reported, dict):
        raise ValueError("qualification lacks program map")
    for direction, source in programs.items():
        key = _setting_key({"direction": direction})
        if reported.get(key) != hashlib.sha256(source.encode()).hexdigest():
            raise ValueError(f"qualified program hash differs for direction={direction}")
    return programs


def _audit_episodes(execution: dict) -> list[dict]:
    audits = []
    for episode in execution["episodes"]:
        audit = prototype.audit_episode(episode)
        if (
            audit["setting_survivors"] != [audit["chosen"]]
            or audit["ambiguous_query_changers"]
            or audit["surviving_equivalent_rivals"]
        ):
            raise ValueError(f"finite shortcut audit failed: {audit}")
        audits.append(
            {
                "seed": episode["seed"],
                "settings": episode["settings"],
                "audit": audit,
            }
        )
    return audits


def build(qualification_path: Path, output: Path) -> dict:
    qualification, execution = _load_qualification(qualification_path)
    programs = _programs(qualification)
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.mkdir(parents=True)

    identity = None
    cases = []
    contrasts = []
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("protected Racket backend is required")
        apply = _executor(bridge)

        # One case per direction, both derived from qualified episode bytes.
        emitted = set()
        for episode in execution["episodes"]:
            direction = episode["settings"]["direction"]
            if direction in emitted:
                continue
            emitted.add(direction)
            pair = episode["train"][0]
            grid = pair["input"]
            turns = prototype.marker_turns(grid)
            if turns != 1:
                raise ValueError("first demonstration must expose marker turn one")
            correct_program = programs[direction]
            wrong_turn = 2
            wrong_program = prototype.fixed_turn_program(direction, wrong_turn)
            correct = apply(correct_program, grid)
            wrong = apply(wrong_program, grid)
            if correct != pair["output"] or correct != prototype.apply_rule(grid, direction):
                raise ValueError("qualification/Racket/Python chosen output differs")
            if wrong != prototype.apply_with_forced_turns(grid, direction, wrong_turn):
                raise ValueError("Racket/Python wrong-turn counterfactual differs")
            if correct == wrong:
                raise ValueError("wrong marker-count intermediate did not change output")
            cases.append(
                {
                    "input": grid,
                    "settings": {"direction": direction},
                    "intermediate_value": {
                        "marker_count": grid[0].count(9),
                        "turns_mod4": turns,
                        "cropped_object": prototype.content_crop(grid),
                    },
                    "program": correct_program,
                    "output": correct,
                    "ablation": "wrong_intermediate",
                    "counterfactual_intermediate": {
                        "turns_mod4": wrong_turn,
                        "cropped_object": prototype.content_crop(grid),
                    },
                    "counterfactual_program": wrong_program,
                    "counterfactual_output": wrong,
                }
            )

        seen_seeds = set()
        for episode in execution["episodes"]:
            seed = episode["seed"]
            if seed in seen_seeds:
                continue
            seen_seeds.add(seed)
            grid = episode["train"][0]["input"]
            clockwise = apply(programs["clockwise"], grid)
            counterclockwise = apply(programs["counterclockwise"], grid)
            if clockwise == counterclockwise:
                raise ValueError("declared directions do not contrast on a demonstration")
            contrasts.append(
                {
                    "seed": seed,
                    "input": grid,
                    "clockwise_output": clockwise,
                    "counterclockwise_output": counterclockwise,
                    "different_cells": sum(
                        left != right
                        for left_row, right_row in zip(clockwise, counterclockwise)
                        for left, right in zip(left_row, right_row)
                    ),
                }
            )

    witness_path = _write_json(
        output / "sequential-witness.json",
        witness_document(qualification["source_binding"], cases),
    )
    self_review = {
        "schema": "ffcd7510821d-direction-parametric-self-review-v1",
        "task_id": TASK_ID,
        "source_binding": qualification["source_binding"],
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
        "episode_audits": _audit_episodes(execution),
        "racket_setting_contrasts": contrasts,
        "status": "passed",
        "finding": (
            "No tested rival survived the visible demonstrations while changing "
            "a query; direction remains finitely established, not universally unique."
        ),
        "limits": (
            "Finite rivals: both declared directions, crop-only, three fixed turns, "
            "content-color count, marker-count-plus-one, largest-only, uncropped "
            "rotation, and post-rotation mirror, on native qualification episodes."
        ),
    }
    self_review_path = _write_json(output / "self-review.json", self_review)

    public_paths = []
    emitted_settings = set()
    for episode in execution["episodes"]:
        key = _setting_key(episode["settings"])
        if key in emitted_settings:
            continue
        emitted_settings.add(key)
        public_paths.append(write_public_episode(episode, output / "public"))

    receipt = {
        "schema": "ffcd7510821d-direction-evidence-build-v1",
        "task_id": TASK_ID,
        "qualification_sha256": hashlib.sha256(Path(qualification_path).read_bytes()).hexdigest(),
        "source_binding": qualification["source_binding"],
        "outputs": [
            {
                "path": path.relative_to(output).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            for path in [witness_path, self_review_path, *public_paths]
        ],
        "racket_evaluations": 2 * len(cases) + 2 * len(contrasts),
        "status": "passed",
    }
    receipt_path = _write_json(output / "evidence-build.json", receipt)
    return {
        "status": "passed",
        "witness": str(witness_path),
        "self_review": str(self_review_path),
        "public": [str(path) for path in public_paths],
        "receipt": str(receipt_path),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    options = parser.parse_args(argv)
    try:
        result = build(options.qualification, options.out)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": type(exc).__name__, "message": str(exc)}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
