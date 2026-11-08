"""Bounded protected-Racket learnability and public-projection audit.

This utility is intentionally task-local. It executes the two declared programs
and six plausible rivals against matched episodes, verifies demonstration-only
identification, and writes hash-named public challenges separately from private
settings and answers.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import public_challenge_bytes, public_challenge_id

_HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    path = _HERE / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prototype = _load("_e99db71ae23d_audit_prototype", "prototype.py")
adapter = _load("_e99db71ae23d_audit_adapter", "adapter.py")


def program_map() -> dict[str, str]:
    result = {
        policy: prototype.program_for(policy)
        for policy in prototype.DIRECTION_POLICIES
    }
    result.update({name: prototype.rival_program(name) for name in prototype.RIVAL_NAMES})
    return result


def public_projection(episode: dict) -> dict:
    return {
        "train": episode["train"],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def _raw(value) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def run_audit(output: Path) -> dict:
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)

    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    programs = program_map()
    wrapped = {name: wrap_rule(program) for name, program in programs.items()}
    bridge = RacketBridge()
    evaluations = 0

    def execute(name: str, grid: list[list[int]]) -> list[list[int]]:
        nonlocal evaluations
        evaluations += 1
        return bridge.eval_text(f"({wrapped[name]} {_grid_literal(grid)})")

    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("audit requires the protected Racket backend")
        jobs = []
        samples = []
        for seed, demos in ((0, 2), (17, 3), (41, 6)):
            for policy in prototype.DIRECTION_POLICIES:
                setting = {"direction_policy": policy}
                episode = adapter.generate(seed, setting, demos, 4)
                certificate = prototype.lesson_certificate(episode)
                if not certificate["identifiable"]:
                    raise AssertionError((seed, demos, policy, certificate))

                survivors = []
                for name in programs:
                    labels = [execute(name, pair["input"]) for pair in episode["train"]]
                    if all(label == pair["output"] for label, pair in zip(labels, episode["train"])):
                        survivors.append(name)
                if survivors != [policy]:
                    raise AssertionError((seed, demos, policy, survivors))

                for pair in episode["test"]:
                    if execute(policy, pair["input"]) != pair["output"]:
                        raise AssertionError((seed, demos, policy, "query label mismatch"))

                query_disagreements = {
                    name: sum(
                        execute(name, pair["input"]) != pair["output"]
                        for pair in episode["test"]
                    )
                    for name in programs
                    if name != policy
                }
                jobs.append(
                    {
                        "seed": seed,
                        "demos": demos,
                        "queries": 4,
                        "setting": setting,
                        "survivors": survivors,
                        "query_disagreements": query_disagreements,
                        "scene_checks": [
                            prototype.analyze_scene(pair["input"])
                            for pair in episode["test"]
                        ],
                    }
                )
                if seed == 17 and demos == 3:
                    public = public_projection(episode)
                    visible_id = public_challenge_id(public)
                    samples.append(
                        {
                            "public_id": visible_id,
                            "setting": setting,
                            "program_sha256": hashlib.sha256(
                                episode["program_solution"].encode()
                            ).hexdigest(),
                            "query_answers": [pair["output"] for pair in episode["test"]],
                            "public": public,
                        }
                    )

        output.mkdir(parents=True, exist_ok=False)
        public_dir = output / "public"
        private_dir = output / "private"
        public_dir.mkdir()
        private_dir.mkdir()
        for sample in samples:
            payload = public_challenge_bytes(sample["public"])
            (public_dir / f"challenge-{sample['public_id']}.json").write_bytes(payload)
        private_rows = [
            {key: value for key, value in sample.items() if key != "public"}
            for sample in samples
        ]
        (private_dir / "samples.json").write_bytes(_raw(private_rows))
        report = {
            "schema": "e99db71ae23d-parametric-audit-v1",
            "status": "passed",
            "task_id": prototype.TASK_ID,
            "programs": {
                name: hashlib.sha256(program.encode()).hexdigest()
                for name, program in programs.items()
            },
            "jobs": jobs,
            "public_ids": sorted(sample["public_id"] for sample in samples),
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
            "limits": (
                "Finite audit of two declared settings and six authored rivals on "
                "three seeds/demo counts; not universal uniqueness or measured learning gain."
            ),
        }
        (output / "audit.json").write_bytes(_raw(report))
        return report
    finally:
        bridge.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run_audit(args.out)
    print(json.dumps({
        "status": report["status"],
        "jobs": len(report["jobs"]),
        "racket_evaluations": report["racket_evaluations"],
        "public_ids": report["public_ids"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
