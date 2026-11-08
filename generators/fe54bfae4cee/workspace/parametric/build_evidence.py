#!/usr/bin/env python3
"""Build source-bound causal, shortcut-audit, and public-export evidence.

Run only after native qualification.  The tool reuses the exact adjacent
prototype, executes both admitted setting programs through protected Racket,
and writes private evidence separately from hash-named public challenges.
"""
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

TASK_ID = "fe54bfae4cee"
STEP_A = "Apply the canonical exact-gap midpoint rule once to the episode input."
INTERMEDIATE = "The complete grid after pass 1, including newly created colored midpoints."
STEP_B = "Apply the same canonical midpoint rule to that intermediate grid, allowing newly created midpoints to serve as endpoints."
WHY_B_DEPENDS_ON_A = "Second-generation midpoint candidates do not exist in the original input; their endpoint is created by step A, so skipping or corrupting A changes step B's final grid."

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "fe54bfae4cee_evidence_prototype",
    _HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load exact-pass midpoint prototype")
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
    """Write exact visible bytes under their full SHA-256 content identity."""
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
        "limits": "Two bounded authored cascades. Protected Racket labels prove the counterfactual outputs, not universal algorithmic depth.",
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


def _programs(qualification: dict):
    programs = {passes: prototype.program_for(passes) for passes in (1, 2)}
    reported = qualification.get("programs")
    if not isinstance(reported, dict):
        raise ValueError("qualification lacks program map")
    for passes, source in programs.items():
        key = _setting_key({"passes": passes})
        if reported.get(key) != hashlib.sha256(source.encode()).hexdigest():
            raise ValueError(f"qualified program hash differs for passes={passes}")
    return programs


def _audit_episodes(execution: dict) -> list[dict]:
    audits = []
    for episode in execution["episodes"]:
        audit = prototype.audit_episode(episode)
        if audit["survivors"] != [audit["chosen"]] or audit["ambiguous_query_changers"]:
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
        # Two complementary scenes are enough to demonstrate both H→V and V→H
        # newly-created endpoint paths.  Each scene itself contains both paths.
        for seed, slot in ((0, 0), (17, 1)):
            grid = prototype.build_input(seed, slot)
            intermediate = apply(programs[1], grid)
            final = apply(programs[2], grid)
            if intermediate != prototype.apply_passes(grid, 1):
                raise ValueError("Racket/Python pass-1 parity failed")
            if final != prototype.apply_passes(grid, 2):
                raise ValueError("Racket/Python pass-2 parity failed")
            if intermediate == final:
                raise ValueError("causal ablation did not change final output")
            cases.append(
                {
                    "input": grid,
                    "settings": {"passes": 2},
                    "intermediate_value": intermediate,
                    "program": programs[2],
                    "output": final,
                    "ablation": "skip_a",
                    "counterfactual_program": programs[1],
                    "counterfactual_output": intermediate,
                }
            )

        seen_seeds = set()
        for episode in execution["episodes"]:
            seed = episode["seed"]
            if seed in seen_seeds:
                continue
            seen_seeds.add(seed)
            grid = episode["train"][0]["input"]
            one = apply(programs[1], grid)
            two = apply(programs[2], grid)
            if one == two:
                raise ValueError("declared setting programs do not contrast on a demonstration")
            contrasts.append(
                {
                    "seed": seed,
                    "input": grid,
                    "passes_1_output": one,
                    "passes_2_output": two,
                    "different_cells": sum(
                        left != right
                        for one_row, two_row in zip(one, two)
                        for left, right in zip(one_row, two_row)
                    ),
                }
            )

    witness = witness_document(qualification["source_binding"], cases)
    witness_path = _write_json(output / "sequential-witness.json", witness)
    self_review = {
        "schema": "fe54bfae4cee-parametric-self-review-v1",
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
        "finding": "No tested rival survived the visible demonstrations while changing a query; exact pass count remains finitely established, not universally unique.",
        "limits": "Finite rivals: identity, one pass, two passes, unbounded closure, horizontal-only and vertical-only, on the native qualification episodes.",
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
        "schema": "fe54bfae4cee-evidence-build-v1",
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
