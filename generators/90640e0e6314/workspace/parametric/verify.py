#!/usr/bin/env python3
"""Racket-verify and materialize the 90640e0e6314 identity-corner prototype."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import tempfile
import types
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)


HERE = Path(__file__).resolve().parent


def _install_packet_scripts_namespace(root: Path) -> None:
    """Expose the packet parser imported lazily by the shared rule wrapper."""
    qualified = "scripts.comment_solutions"
    if qualified in sys.modules:
        return
    source = root / "shared" / "tools" / "comment_solutions.py"
    if not source.is_file():
        raise FileNotFoundError(f"missing packet parser source: {source}")
    package = sys.modules.get("scripts")
    if package is None:
        package = types.ModuleType("scripts")
        package.__path__ = [str(source.parent)]
        sys.modules["scripts"] = package
    spec = importlib.util.spec_from_file_location(qualified, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load packet parser source: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    spec.loader.exec_module(module)


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        "90640e0e6314_identity_corner_verify", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_json(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_program(task_id: str, root: Path) -> str:
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row["program_solution"]
    raise RuntimeError(f"canonical program missing for {task_id}")


def _write_json_exclusive(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _assert_public_redacted(challenge: dict[str, Any], prototype: Any) -> None:
    if set(challenge) != {"train", "test"}:
        raise AssertionError("public challenge must contain only train/test")
    if not challenge["train"] or not challenge["test"]:
        raise AssertionError("public challenge must retain demos and queries")
    if any(set(pair) != {"input", "output"} for pair in challenge["train"]):
        raise AssertionError("public demonstrations have unexpected fields")
    if any(set(pair) != {"input"} for pair in challenge["test"]):
        raise AssertionError("public queries must contain input only")

    serialized = json.dumps(challenge, sort_keys=True)
    forbidden = (
        prototype.PARAMETER_NAME,
        *prototype.ALLOWED_SETTINGS,
        "rule!",
        "sampling",
        "program",
        "parameter",
        "seed",
    )
    leaked = [token for token in forbidden if token in serialized]
    if leaked:
        raise AssertionError(f"public challenge leaks hidden metadata: {leaked}")


def _episode_entries(
    *, prototype: Any, episodes: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Preflight visible IDs and redaction before creating any output directory."""
    entries: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for setting in prototype.ALLOWED_SETTINGS:
        episode = episodes[setting]
        challenge = prototype.public_challenge(episode)
        _assert_public_redacted(challenge, prototype)
        identifier = prototype.public_identifier(challenge)
        if identifier in identifiers:
            raise AssertionError("visible-derived public identifier collision")
        identifiers.add(identifier)
        digest = identifier.removeprefix("challenge-").removesuffix(".json")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise AssertionError(f"invalid visible-derived public identifier: {identifier}")
        entries.append(
            {
                "setting": setting,
                "episode": episode,
                "challenge": challenge,
                "identifier": identifier,
                "directory": f"episode-{digest}",
            }
        )
    return sorted(entries, key=lambda entry: entry["directory"])


def _materialize(
    *,
    artifact_dir: Path,
    seed: int,
    prototype: Any,
    programs: dict[str, str],
    episodes: dict[str, dict[str, Any]],
    generator_sha256: str,
) -> dict[str, Any]:
    entries = _episode_entries(prototype=prototype, episodes=episodes)
    artifact_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{artifact_dir.name}.tmp-{os.getpid()}-",
            dir=artifact_dir.parent,
        )
    )
    file_records: dict[str, dict[str, Any]] = {}
    public_name_to_setting: dict[str, str] = {}

    def retain_bytes(relative: str, data: bytes, *, kind: str, setting: str) -> None:
        path = temp_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        file_records[relative] = {
            "sha256": _sha256_bytes(data),
            "bytes": len(data),
            "kind": kind,
            "setting": setting,
        }

    try:
        for setting in prototype.ALLOWED_SETTINGS:
            retain_bytes(
                f"programs/{setting}.rkt",
                (programs[setting] + "\n").encode("utf-8"),
                kind="private_exact_racket_program",
                setting=setting,
            )

        for entry in entries:
            setting = entry["setting"]
            relative_root = f"episodes/{entry['directory']}"
            public_data = prototype.public_bytes(entry["challenge"])
            private_data = (
                json.dumps(entry["episode"], indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
            retain_bytes(
                f"{relative_root}/public/challenge.json",
                public_data,
                kind="public_answer_free_challenge",
                setting=setting,
            )
            retain_bytes(
                f"{relative_root}/private/episode.json",
                private_data,
                kind="private_complete_episode",
                setting=setting,
            )
            public_name_to_setting[entry["identifier"]] = setting

        manifest = {
            "schema": "90640e0e6314-parametric-materialization-v1",
            "status": "passed",
            "scope": "proposed task-local prototype; canonical production unchanged",
            "task_id": prototype.TASK_ID,
            "seed": seed,
            "generator_sha256": generator_sha256,
            "private_parameter": {
                "name": prototype.PARAMETER_NAME,
                "allowed_settings": list(prototype.ALLOWED_SETTINGS),
                "chosen_once_per_episode": True,
            },
            "public_directory_policy": (
                "episode-<sha256 exact visible challenge bytes>; independent of "
                "private seed metadata and query answers"
            ),
            "private_public_name_map": public_name_to_setting,
            "files": file_records,
        }
        _write_json(temp_dir / "private" / "manifest.json", manifest)
        summary = {
            "status": "passed",
            "episodes": len(entries),
            "programs": len(programs),
            "public_identifiers": sorted(public_name_to_setting),
        }
        _write_json(temp_dir / "private" / "summary.json", summary)
        temp_dir.rename(artifact_dir)
    except BaseException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

    return {
        "artifact_dir": str(artifact_dir),
        "manifest": manifest,
        "episode_directories": [entry["directory"] for entry in entries],
    }


def _validate_destination(path: Path, *, kind: str) -> Path:
    resolved = Path(path)
    if resolved.exists():
        raise FileExistsError(f"{kind} already exists: {resolved}")
    return resolved


def verify(*, seed: int, out_path: Path, artifact_dir: Path) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    out_path = _validate_destination(Path(out_path), kind="verification output")
    artifact_dir = _validate_destination(Path(artifact_dir), kind="artifact directory")

    prototype = _load_prototype()
    root = find_root(__file__)
    _install_packet_scripts_namespace(root)
    generator, generator_path, generator_sha256 = load_selected_generator(
        prototype.TASK_ID, root=root
    )

    canonical_program = _canonical_program(prototype.TASK_ID, root)
    programs = {
        setting: prototype.program_for(setting)
        for setting in prototype.ALLOWED_SETTINGS
    }
    if programs[prototype.DEFAULT_SETTING] != canonical_program:
        raise AssertionError("default prototype program is not exact canonical text")
    if _normalized_rule_hash(canonical_program) != prototype.CANONICAL_RULE_HASH:
        raise AssertionError("canonical rule hash drift")
    if generator.RULE_HASH != prototype.CANONICAL_RULE_HASH:
        raise AssertionError("selected generator rule pin disagrees with prototype")

    episodes = {
        setting: prototype.build_episode(
            seed,
            setting=setting,
            n_train=prototype.DEFAULT_N_TRAIN,
            n_test=prototype.DEFAULT_N_TEST,
        )
        for setting in prototype.ALLOWED_SETTINGS
    }
    reference_episode = episodes[prototype.DEFAULT_SETTING]
    reference_pairs = [
        (split, index, pair["input"])
        for split in ("train", "test")
        for index, pair in enumerate(reference_episode[split])
    ]
    reference_inputs = [grid for _, _, grid in reference_pairs]
    for setting, episode in episodes.items():
        errors = prototype.episode_errors(episode)
        if errors:
            raise AssertionError(f"invalid {setting} episode: {errors}")
        inputs = [
            pair["input"]
            for split in ("train", "test")
            for pair in episode[split]
        ]
        if inputs != reference_inputs:
            raise AssertionError(f"input drift across settings for {setting}")
        if episode["generator_sha256"] != generator_sha256:
            raise AssertionError(f"generator source drift in {setting} episode")

    canonical_examples = canonical_pairs(
        prototype.TASK_ID, root=root, labeled_only=True
    )
    bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
    checks: list[dict[str, Any]] = []
    canonical_checks: list[dict[str, Any]] = []
    try:
        runtime_identity = bridge.runtime_identity
        rule_names: dict[str, str] = {}
        for index, setting in enumerate(prototype.ALLOWED_SETTINGS):
            name = f"__identity_corner_rule_{index}"
            bridge.eval_text(f"(define {name} {wrap_rule(programs[setting])})")
            rule_names[setting] = name

        for pair_index, (split, split_index, grid) in enumerate(reference_pairs):
            grid_name = f"__identity_corner_input_{pair_index}"
            bridge.define_grid(grid_name, grid)
            candidate_outputs: dict[str, list[list[int]]] = {}
            for setting in prototype.ALLOWED_SETTINGS:
                racket_output = bridge.eval_text(
                    f"({rule_names[setting]} {grid_name})"
                )
                python_output = prototype.solve_setting(grid, setting)
                if racket_output != python_output:
                    raise AssertionError(
                        f"Racket/Python mismatch for {setting} pair {pair_index}"
                    )
                candidate_outputs[setting] = racket_output
            output_hashes = {
                setting: _sha256_json(output)
                for setting, output in candidate_outputs.items()
            }
            all_distinct = len(set(output_hashes.values())) == len(programs)
            if not all_distinct:
                raise AssertionError(f"pair {pair_index} is not four-setting sensitive")
            checks.append(
                {
                    "pair_index": pair_index,
                    "split": split,
                    "split_index": split_index,
                    "input_sha256": _sha256_json(grid),
                    "outputs": {
                        setting: {
                            "sha256": output_hashes[setting],
                            "racket_python_exact": True,
                        }
                        for setting in prototype.ALLOWED_SETTINGS
                    },
                    "all_settings_distinct": True,
                }
            )

        default_rule_name = rule_names[prototype.DEFAULT_SETTING]
        for canonical_index, pair in enumerate(canonical_examples):
            grid_name = f"__canonical_input_{canonical_index}"
            bridge.define_grid(grid_name, pair["input"])
            actual = bridge.eval_text(f"({default_rule_name} {grid_name})")
            if actual != pair["output"]:
                raise AssertionError(
                    "default program failed canonical pair "
                    f"variant={pair['variant']} split={pair['split']} "
                    f"pair={pair['pair_index']}"
                )
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": _sha256_json(pair["input"]),
                    "output_sha256": _sha256_json(actual),
                    "exact": True,
                }
            )
    finally:
        bridge.shutdown()

    for setting, episode in episodes.items():
        expected_outputs = [
            pair["output"]
            for split in ("train", "test")
            for pair in episode[split]
        ]
        verified_hashes = [row["outputs"][setting]["sha256"] for row in checks]
        if verified_hashes != [_sha256_json(output) for output in expected_outputs]:
            raise AssertionError(f"retained labels do not match Racket for {setting}")

    materialization = _materialize(
        artifact_dir=artifact_dir,
        seed=seed,
        prototype=prototype,
        programs=programs,
        episodes=episodes,
        generator_sha256=generator_sha256,
    )
    source_files = [
        HERE / "prototype.py",
        HERE / "verify.py",
        HERE / "README.md",
        HERE / "manifest.json",
    ]
    every_demo_distinct = all(
        row["all_settings_distinct"] for row in checks if row["split"] == "train"
    )
    every_query_distinct = all(
        row["all_settings_distinct"] for row in checks if row["split"] == "test"
    )
    report = {
        "schema": "90640e0e6314-parametric-verification-v1",
        "status": "passed",
        "scope": "proposed task-local prototype; not catalog approval",
        "task_id": prototype.TASK_ID,
        "seed": seed,
        "parameter": {
            "name": prototype.PARAMETER_NAME,
            "allowed_values": list(prototype.ALLOWED_SETTINGS),
            "original_default": prototype.DEFAULT_SETTING,
            "selection_scope": "once per complete episode",
            "fixed_across_episode": True,
            "sampling_independent_of_setting": True,
        },
        "counts": {
            "episodes": len(episodes),
            "demonstrations_per_episode": prototype.DEFAULT_N_TRAIN,
            "queries_per_episode": prototype.DEFAULT_N_TEST,
            "distinct_shared_inputs": len(reference_inputs),
            "racket_setting_calls": len(checks) * len(programs),
            "canonical_pairs_checked": len(canonical_checks),
        },
        "canonical_binding": {
            "generator_path": str(generator_path.relative_to(root)),
            "generator_sha256": generator_sha256,
            "rule_hash": prototype.CANONICAL_RULE_HASH,
            "default_program_exact_canonical": True,
            "canonical_pairs": canonical_checks,
        },
        "programs": {
            setting: {
                "text": program,
                "sha256": _sha256_bytes(program.encode("utf-8")),
                "normalized_rule_hash": _normalized_rule_hash(program),
            }
            for setting, program in programs.items()
        },
        "episodes": episodes,
        "checks": checks,
        "teaching": {
            "every_demo_refutes_all_rivals": every_demo_distinct,
            "every_query_distinguishes_all_settings": every_query_distinct,
            "query_answers_used_to_choose_demos": False,
        },
        "racket_runtime": runtime_identity,
        "materialization": materialization,
        "prototype_sources": {
            path.name: _sha256_file(path) for path in source_files
        },
        "command": shlex.join(
            [
                "python3",
                "review.py",
                "run",
                "python3",
                "generators/90640e0e6314/workspace/parametric/verify.py",
                "--seed",
                str(seed),
                "--out",
                str(out_path),
                "--artifact-dir",
                str(artifact_dir),
            ]
        ),
        "limitations": [
            "The finite four-setting corner family is not an exhaustive hypothesis class.",
            "The production generator and canonical selected authority are unchanged.",
            "This prototype is proposed and is not catalog-approved or runtime-integrated.",
        ],
    }
    try:
        _write_json_exclusive(out_path, report)
    except BaseException:
        # Keep evidence all-or-nothing when the report destination races with us.
        shutil.rmtree(artifact_dir, ignore_errors=True)
        raise
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    report = verify(
        seed=args.seed,
        out_path=args.out,
        artifact_dir=args.artifact_dir,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "counts": report["counts"],
                "evidence": str(args.out),
                "artifact_dir": str(args.artifact_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
