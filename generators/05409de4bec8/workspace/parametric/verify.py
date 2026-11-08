#!/usr/bin/env python3
"""Build source-bound Racket evidence for the rectangle-policy prototype."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import public_challenge_bytes, public_challenge_id

import prototype


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def seed_for(setting: str, start: int) -> int:
    seed = start
    while prototype.choose_setting(seed) != setting:
        seed += 1
    return seed


def callable_rule(program: str) -> str:
    """Materialize the implicit ``g/h/w`` bindings used by ``rule!``.

    The packet's general ``wrap_rule`` helper depends on an authoring-only
    parser that is intentionally absent from this retained review bundle.
    Both prototype programs are body-form rules with no shorthand forms, so
    the exact runtime contract is the explicit lambda below.
    """
    body = strip_rule_wrapper(program)
    return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))"


def execute(program: str, inputs: list[list[list[int]]]) -> list[list[list[int]]]:
    bridge = RacketBridge()
    try:
        bridge.eval_text(f"(define __parametric_rule {callable_rule(program)})")
        outputs = []
        for index, grid in enumerate(inputs):
            name = f"__parametric_input_{index}"
            bridge.define_grid(name, grid)
            outputs.append(bridge.eval_text(f"(__parametric_rule {name})"))
        return outputs
    finally:
        bridge.shutdown()


def plan_public_batch(
    items: list[tuple[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Return a visible-content-only, ID-sorted public write plan.

    ``private_key`` is carried only so the private report can recover its
    setting-to-path map. It never participates in the public bytes, ID, name,
    or ordering. Duplicate visible challenges are rejected before any write.
    """
    plan: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    for private_key, episode in items:
        payload = public_challenge_bytes(episode)
        public_id = public_challenge_id(episode)
        if sha256_bytes(payload) != public_id:
            raise AssertionError("public challenge ID does not hash exact written bytes")
        previous = seen.get(public_id)
        if previous is not None:
            raise ValueError(
                "duplicate visible public payload for "
                f"{previous!r} and {private_key!r}: {public_id}"
            )
        seen[public_id] = private_key
        plan.append(
            {
                "private_key": private_key,
                "public_id": public_id,
                "filename": f"episode-{public_id}.json",
                "payload": payload,
            }
        )
    plan.sort(key=lambda row: row["public_id"])
    return plan


def write_public_batch(
    public_dir: Path, items: list[tuple[str, dict[str, Any]]]
) -> list[dict[str, Any]]:
    """Write exact visible bytes in public-ID order and return that order."""
    plan = plan_public_batch(items)
    public_dir.mkdir(parents=True, exist_ok=True)
    occupied = [public_dir / row["filename"] for row in plan
                if (public_dir / row["filename"]).exists()]
    if occupied:
        raise FileExistsError(
            "refusing to overwrite public batch path(s): "
            + ", ".join(str(path) for path in occupied)
        )
    for row in plan:
        (public_dir / row["filename"]).write_bytes(row["payload"])
    return plan


def build_evidence(
    out: Path,
    *,
    start_seed: int,
    demo_count: int,
    query_count: int,
) -> dict[str, Any]:
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    private = out / "private"
    public_dir = out / "public"
    rules_dir = private / "rules"

    if prototype.program_for(prototype.DEFAULT_SETTING) != prototype.canonical_program():
        raise AssertionError("default setting is not the exact canonical authority")

    programs = {
        setting: prototype.program_for(setting)
        for setting in prototype.ALLOWED_SETTINGS
    }
    seeds = {
        setting: seed_for(setting, start_seed)
        for setting in prototype.ALLOWED_SETTINGS
    }
    reports = []
    verified_episodes: dict[str, dict[str, Any]] = {}
    public_items: list[tuple[str, dict[str, Any]]] = []

    for setting in prototype.ALLOWED_SETTINGS:
        program = programs[setting]
        rule_path = rules_dir / f"rule-{setting}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(program + "\n", encoding="utf-8")

        episode = prototype.build_episode(
            seeds[setting], demo_count=demo_count, query_count=query_count
        )
        pairs = episode["train"] + episode["test"]
        inputs = [pair["input"] for pair in pairs]
        actual = execute(program, inputs)
        expected = [prototype.apply_python(grid, setting) for grid in inputs]
        if actual != expected:
            raise AssertionError(f"Python/Racket mismatch for {setting}")
        for pair, output in zip(pairs, actual):
            pair["output"] = output

        other = next(v for v in prototype.ALLOWED_SETTINGS if v != setting)
        rival_outputs = execute(programs[other], inputs)
        demo_disagreements = [
            index
            for index in range(demo_count)
            if rival_outputs[index] != actual[index]
        ]
        query_disagreements = [
            index - demo_count
            for index in range(demo_count, len(inputs))
            if rival_outputs[index] != actual[index]
        ]
        if not demo_disagreements:
            raise AssertionError(f"demos do not identify {setting}")
        if query_disagreements != list(range(query_count)):
            raise AssertionError(f"not every query distinguishes {setting}")

        private_path = private / f"episode-{setting}.json"
        write_json(private_path, episode)
        public_items.append((setting, episode))
        verified_episodes[setting] = episode
        reports.append(
            {
                "setting": setting,
                "seed": seeds[setting],
                "program_sha256": sha256_bytes(program.encode()),
                "private_episode": str(private_path.relative_to(out)),
                "demo_rival_disagreement_indices": demo_disagreements,
                "query_rival_disagreement_indices": query_disagreements,
                "all_labels_executed_by_racket": True,
            }
        )

    public_plan = write_public_batch(public_dir, public_items)
    public_by_setting = {row["private_key"]: row for row in public_plan}
    for episode_report in reports:
        public_row = public_by_setting[episode_report["setting"]]
        episode_report["public_id"] = public_row["public_id"]
        episode_report["public_challenge"] = str(
            (public_dir / public_row["filename"]).relative_to(out)
        )

    witness_input = verified_episodes["longer"]["test"][0]["input"]
    witness = {
        "input": witness_input,
        "is_rectangle": prototype.is_rectangle(witness_input),
        "outputs": {
            setting: execute(programs[setting], [witness_input])[0]
            for setting in prototype.ALLOWED_SETTINGS
        },
    }
    if witness["outputs"]["longer"] == witness["outputs"]["both"]:
        raise AssertionError("same-input setting witness does not disagree")
    write_json(private / "same-input-disagreement.json", witness)

    report = {
        "schema": "05409de4bec8-parametric-rectangle-policy-v2",
        "status": "passed_bounded_prototype_evidence",
        "prototype_status": "proposed_unapproved",
        "parameter": {
            "name": prototype.PARAMETER_NAME,
            "allowed": list(prototype.ALLOWED_SETTINGS),
            "default": prototype.DEFAULT_SETTING,
            "selected_once_per_episode": True,
        },
        "counts": {"demonstrations": demo_count, "queries": query_count},
        "production_generator_sha256": sha256_file(prototype.GENERATOR_PATH),
        "prototype_sha256": sha256_file(Path(prototype.__file__)),
        "verifier_sha256": sha256_file(Path(__file__)),
        "racket_runtime": racket_runtime_status(),
        "public_write_order": [row["public_id"] for row in public_plan],
        "episodes": reports,
        "limitations": [
            "finite evidence for two retained seeds and the declared rival only",
            "prototype is separate from the selected canonical generator and catalog",
            "four rectangle queries test the parameter boundary but not every lawful input",
        ],
    }
    write_json(out / "report.json", report)

    files = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            files.append(
                {
                    "path": str(path.relative_to(out)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    manifest = {
        "schema": "parametric-evidence-manifest-v1",
        "report_sha256": sha256_file(out / "report.json"),
        "files": files,
    }
    write_json(out / "manifest.json", manifest)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--start-seed", type=int, default=20261023)
    parser.add_argument("--demo-count", type=int, default=5)
    parser.add_argument("--query-count", type=int, default=4)
    args = parser.parse_args()
    report = build_evidence(
        args.out,
        start_seed=args.start_seed,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
