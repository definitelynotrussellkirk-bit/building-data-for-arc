#!/usr/bin/env python3
"""Execute both proposed Racket settings and retain source-bound evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import prototype  # noqa: E402


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_program(root: Path) -> str:
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == prototype.TASK_ID:
            return row["program_solution"]
    raise RuntimeError("canonical program missing")


def _racket_callable(source: str) -> str:
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("prototype program must use one `(rule! EXPR)` form")
    expression = stripped[len("(rule!") : -1].strip()
    if not expression.startswith("(lambda"):
        raise ValueError("prototype rule expression must be a lambda")
    return expression


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"'({rows})"


def _application(source: str, grid: list[list[int]]) -> str:
    return f"({_racket_callable(source)} {_grid_literal(grid)})"


def _json_body(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json_body(payload), encoding="utf-8")


def _body_record(body: str | bytes) -> dict[str, Any]:
    encoded = body.encode("utf-8") if isinstance(body, str) else body
    return {"sha256": _sha256_bytes(encoded), "bytes": len(encoded)}


def materialize_artifacts(
    artifact_dir: Path | str,
    *,
    episodes: dict[int, dict[str, Any]],
    programs: dict[int, str],
    seed: int,
    generator_sha: str,
) -> dict[str, Any]:
    """Write private evidence and opaque public challenges into separate trees."""
    artifact_dir = Path(artifact_dir)
    public_dir = artifact_dir / "public"
    private_dir = artifact_dir / "private"
    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "schema": "a631936f7715-parametric-materialization-v2",
        "seed": seed,
        "generator_sha256": generator_sha,
        "public_files": {},
        "private_settings": {},
    }

    prepared: list[tuple[str, int, dict[str, Any], bytes]] = []
    seen_public_ids: dict[str, int] = {}
    for connectivity, episode in episodes.items():
        errors = prototype.episode_errors(episode)
        if errors:
            raise ValueError(f"connectivity {connectivity} episode invalid: {errors}")
        if connectivity not in programs:
            raise ValueError(f"missing program for connectivity {connectivity}")
        selected = episode.get("parameters", {}).get("component_connectivity")
        if selected != connectivity:
            raise ValueError(
                f"episode key {connectivity} does not match private setting {selected}"
            )
        if episode.get("program") != programs[connectivity]:
            raise ValueError(f"episode/program mismatch for connectivity {connectivity}")

        visible = prototype.public_challenge(episode)
        public_id = public_challenge_id(visible)
        public_body = public_challenge_bytes(visible)
        expected_name = f"challenge-{public_id}.json"
        if prototype.public_artifact_name(episode) != expected_name:
            raise RuntimeError("prototype public name differs from shared public-byte contract")
        previous = seen_public_ids.get(public_id)
        if previous is not None:
            raise ValueError(
                f"duplicate visible public challenge for settings {previous} and {connectivity}"
            )
        seen_public_ids[public_id] = connectivity
        prepared.append((public_id, connectivity, episode, public_body))

    for public_id, connectivity, episode, public_body in sorted(prepared):
        public_name = f"challenge-{public_id}.json"
        public_path = public_dir / public_name
        if public_path.exists() and public_path.read_bytes() != public_body:
            raise RuntimeError(f"public identifier collision for {public_name}")
        public_path.write_bytes(public_body)
        manifest["public_files"][public_name] = _body_record(public_body)

        program_name = f"connectivity-{connectivity}.rkt"
        episode_name = f"connectivity-{connectivity}-episode.json"
        program_body = programs[connectivity] + "\n"
        episode_body = _json_body(episode)
        (private_dir / program_name).write_text(program_body, encoding="utf-8")
        (private_dir / episode_name).write_text(episode_body, encoding="utf-8")
        manifest["private_settings"][str(connectivity)] = {
            "program_file": f"private/{program_name}",
            "program_sha256": _body_record(program_body)["sha256"],
            "episode_file": f"private/{episode_name}",
            "episode_sha256": _body_record(episode_body)["sha256"],
            "public_file": f"public/{public_name}",
        }

    _write_json(artifact_dir / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--n-test", type=int, default=4)
    parser.add_argument("--out", required=True)
    parser.add_argument("--artifact-dir")
    args = parser.parse_args()

    root = find_root(__file__)
    canonical = _canonical_program(root)
    programs = {
        connectivity: prototype.program_for(connectivity)
        for connectivity in prototype.ALLOWED_CONNECTIVITIES
    }
    if programs[prototype.DEFAULT_CONNECTIVITY] != canonical:
        raise SystemExit("default setting no longer exactly matches canonical authority")
    if len({_sha256_bytes(source.encode()) for source in programs.values()}) != len(programs):
        raise SystemExit("declared settings materialize the same Racket program")

    episodes = {
        connectivity: prototype.build_episode(
            args.seed,
            connectivity=connectivity,
            n_train=args.n_train,
            n_test=args.n_test,
        )
        for connectivity in prototype.ALLOWED_CONNECTIVITIES
    }
    for connectivity, episode in episodes.items():
        errors = prototype.episode_errors(episode)
        if errors:
            raise SystemExit(f"connectivity {connectivity} episode invalid: {errors}")

    checks: list[dict[str, Any]] = []
    bridge = RacketBridge(timeout=30, max_calls_before_restart=64)
    try:
        runtime_identity = bridge.runtime_identity
        for selected, episode in episodes.items():
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    outputs: dict[str, Any] = {}
                    for candidate, source in programs.items():
                        racket_output = bridge.eval_text(_application(source, pair["input"]))
                        python_output = prototype.apply_python(pair["input"], candidate)
                        if racket_output != python_output:
                            raise SystemExit(
                                f"Racket/Python mismatch for selected={selected} "
                                f"{split}[{index}] candidate={candidate}"
                            )
                        outputs[str(candidate)] = racket_output
                    if outputs[str(selected)] != pair["output"]:
                        raise SystemExit(
                            f"selected label mismatch for connectivity {selected} {split}[{index}]"
                        )
                    checks.append(
                        {
                            "episode_connectivity": selected,
                            "split": split,
                            "pair_index": index,
                            "sampling": pair["sampling"],
                            "input": pair["input"],
                            "outputs": outputs,
                            "settings_disagree": outputs["4"] != outputs["8"],
                        }
                    )
    finally:
        bridge.shutdown()

    if not checks or not all(row["settings_disagree"] for row in checks):
        raise SystemExit("a retained pair does not distinguish the declared settings")

    generator_sha = next(iter(episodes.values()))["generator_sha256"]
    if any(episode["generator_sha256"] != generator_sha for episode in episodes.values()):
        raise SystemExit("episodes used different selected generator bytes")

    consistent_candidates_from_train: dict[str, list[int]] = {}
    for selected, episode in episodes.items():
        train_rows = [
            row
            for row in checks
            if row["episode_connectivity"] == selected and row["split"] == "train"
        ]
        consistent = [
            candidate
            for candidate in programs
            if all(
                row["outputs"][str(candidate)]
                == episode["train"][row["pair_index"]]["output"]
                for row in train_rows
            )
        ]
        if consistent != [selected]:
            raise SystemExit(
                f"demonstrations do not identify connectivity {selected}: {consistent}"
            )
        consistent_candidates_from_train[str(selected)] = consistent

    first = checks[0]
    report = {
        "schema": "a631936f7715-parametric-verification-v2",
        "status": "passed",
        "scope": "proposed prototype; not selected canonical execution",
        "task_id": prototype.TASK_ID,
        "seed": args.seed,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "parameter": {
            "name": "component_connectivity",
            "allowed_values": list(prototype.ALLOWED_CONNECTIVITIES),
            "default": prototype.DEFAULT_CONNECTIVITY,
            "chosen_once_per_episode": True,
            "meaning": (
                "segment magenta source cells with orthogonal or eight-neighbor connectivity; "
                "label lookup remains orthogonal"
            ),
            "input_constraints": (
                "each retained pair has a diagonal-only contact between two 4-components and "
                "one label across that pair, avoiding multi-label order ambiguity"
            ),
        },
        "programs": {
            str(connectivity): {
                "source": source,
                "sha256": _sha256_bytes(source.encode()),
            }
            for connectivity, source in programs.items()
        },
        "canonical_program_sha256": _sha256_bytes(canonical.encode()),
        "generator_sha256": generator_sha,
        "prototype_source_sha256": {
            name: _sha256_bytes((HERE / name).read_bytes())
            for name in ("prototype.py", "verify.py", "README.md")
        },
        "racket_runtime": runtime_identity,
        "episode_errors": {
            str(connectivity): prototype.episode_errors(episode)
            for connectivity, episode in episodes.items()
        },
        "identifiability_from_demonstrations": {
            "consistent_candidates": consistent_candidates_from_train,
            "query_answers_used_to_select_setting": False,
        },
        "public_artifact_names": {
            str(connectivity): prototype.public_artifact_name(episode)
            for connectivity, episode in episodes.items()
        },
        "counts": {
            "settings": len(episodes),
            "train_pairs_per_setting": args.n_train,
            "test_pairs_per_setting": args.n_test,
            "episode_pairs": len(checks),
            "query_pairs": len(episodes) * args.n_test,
            "racket_executions": len(checks) * len(programs),
            "distinguishing_pairs": sum(row["settings_disagree"] for row in checks),
        },
        "exact_disagreement": {
            "input": first["input"],
            "connectivity_4_output": first["outputs"]["4"],
            "connectivity_8_output": first["outputs"]["8"],
        },
        "checks": checks,
        "limitations": [
            "This is a task-local prototype and is not wired into production generation or approval metadata.",
            (
                "The witness builder has exact finite support of "
                f"{prototype.MAX_UNIQUE_INPUTS} inputs (210 ordered color triples times 8 dihedral transforms); "
                "larger requests fail instead of cloning pairs."
            ),
            (
                "Evidence covers two complete episodes at one retained seed with "
                f"{args.n_train} demonstrations and {args.n_test} queries per setting, "
                "not every possible lawful input."
            ),
            "Demonstrations eliminate the one declared parameter rival, not every imaginable transformation.",
        ],
    }
    if args.artifact_dir:
        manifest = materialize_artifacts(
            args.artifact_dir,
            episodes=episodes,
            programs=programs,
            seed=args.seed,
            generator_sha=generator_sha,
        )
        report["materialization"] = {
            "artifact_dir": args.artifact_dir,
            "manifest": manifest,
        }
    else:
        report["materialization"] = None

    out_path = Path(args.out)
    _write_json(out_path, report)
    print(json.dumps({"status": "passed", "out": str(out_path), "counts": report["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
