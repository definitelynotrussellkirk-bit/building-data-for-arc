#!/usr/bin/env python3
"""Racket-verify and materialize the task-local bridge-axis prototype."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import types
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
TEST_PATH = HERE.parents[1] / "tests" / "test_parametric_bridge_axes.py"


def _install_packet_scripts_namespace(root: Path) -> None:
    """Expose packet tools under the staged runtime ``scripts`` package."""
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
        "parametric_bridge_axes_7515881f2786_verify", path
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
    return _sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    )


def _normalized_rule_hash(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]


def _canonical_program(task_id: str, root: Path) -> str:
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row["program_solution"]
    raise RuntimeError(f"canonical program missing for {task_id}")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _assert_public_redacted(challenge: dict[str, Any], prototype: Any) -> None:
    serialized = json.dumps(challenge, sort_keys=True)
    forbidden = (
        prototype.PARAMETER_NAME,
        *prototype.ALLOWED_SETTINGS,
        "rule!",
        "sampling",
        "program",
        "parameter",
    )
    leaked = [token for token in forbidden if token in serialized]
    if leaked:
        raise AssertionError(f"public challenge leaks hidden metadata: {leaked}")
    if any("output" in pair for pair in challenge.get("test", [])):
        raise AssertionError("public challenge leaks a query output")


def _materialize(
    *,
    artifact_dir: Path,
    seed: int,
    prototype: Any,
    programs: dict[str, str],
    episodes: dict[str, dict[str, Any]],
    generator_sha256: str,
) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, Any]] = {}
    opaque_public_names = {
        setting: f"challenge-{index:02d}.json"
        for index, setting in enumerate(prototype.ALLOWED_SETTINGS, start=1)
    }

    def retain(relative: str, body: str, *, kind: str, setting: str) -> None:
        path = artifact_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        data = body.encode("utf-8")
        files[relative] = {
            "sha256": _sha256_bytes(data),
            "bytes": len(data),
            "kind": kind,
            "setting": setting,
        }

    for setting in prototype.ALLOWED_SETTINGS:
        episode = episodes[setting]
        challenge = prototype.public_challenge(episode)
        _assert_public_redacted(challenge, prototype)
        retain(
            f"private/rules/{setting}.rkt",
            programs[setting] + "\n",
            kind="private_rule",
            setting=setting,
        )
        retain(
            f"private/episodes/{setting}.json",
            json.dumps(episode, indent=2, sort_keys=True) + "\n",
            kind="private_complete_episode",
            setting=setting,
        )
        retain(
            f"public/challenges/{opaque_public_names[setting]}",
            json.dumps(challenge, indent=2, sort_keys=True) + "\n",
            kind="public_answer_free_challenge",
            setting=setting,
        )

    manifest = {
        "schema": "7515881f2786-parametric-materialization-v1",
        "status": "passed",
        "scope": "proposed task-local prototype; canonical production unchanged",
        "task_id": prototype.TASK_ID,
        "seed": seed,
        "generator_sha256": generator_sha256,
        "parameter": {
            "name": prototype.PARAMETER_NAME,
            "allowed_settings": list(prototype.ALLOWED_SETTINGS),
            "chosen_once_per_episode": True,
        },
        "public_filename_policy": "opaque filenames; no setting or query label",
        "files": files,
    }
    _write_json(artifact_dir / "manifest.json", manifest)
    return manifest


def verify(*, seed: int, out_path: Path, artifact_dir: Path) -> dict[str, Any]:
    """Execute every selected/rival Racket program and retain bounded evidence."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    out_path = Path(out_path)
    artifact_dir = Path(artifact_dir)
    prototype = _load_prototype()
    root = find_root(__file__)
    _install_packet_scripts_namespace(root)

    generator, generator_path, generator_sha256 = load_selected_generator(
        prototype.TASK_ID,
        root=root,
    )
    canonical_program = _canonical_program(prototype.TASK_ID, root)
    programs = {
        setting: prototype.program_for(setting)
        for setting in prototype.ALLOWED_SETTINGS
    }
    canonical_exact = programs[prototype.DEFAULT_SETTING] == canonical_program
    canonical_hash = _normalized_rule_hash(programs[prototype.DEFAULT_SETTING])
    if not canonical_exact:
        raise AssertionError("default prototype program is not exact canonical text")
    if canonical_hash != prototype.CANONICAL_RULE_HASH:
        raise AssertionError(
            f"canonical rule hash drift: {canonical_hash} != {prototype.CANONICAL_RULE_HASH}"
        )
    if generator.RULE_HASH != prototype.CANONICAL_RULE_HASH:
        raise AssertionError("selected generator RULE_HASH disagrees with prototype")

    episodes = {
        setting: prototype.build_episode(
            seed,
            setting=setting,
            n_train=4,
            n_test=1,
        )
        for setting in prototype.ALLOWED_SETTINGS
    }
    for setting, episode in episodes.items():
        errors = prototype.episode_errors(episode)
        if errors:
            raise AssertionError(f"invalid {setting} episode: {errors}")
        if episode["generator_sha256"] != generator_sha256:
            raise AssertionError(f"{setting} episode used different generator bytes")

    # Using the same retained source draws for every setting makes each rule
    # disagreement directly attributable to the hidden episode parameter.
    reference_inputs = [
        pair["input"]
        for split in ("train", "test")
        for pair in episodes[prototype.DEFAULT_SETTING][split]
    ]
    for setting, episode in episodes.items():
        setting_inputs = [
            pair["input"]
            for split in ("train", "test")
            for pair in episode[split]
        ]
        if setting_inputs != reference_inputs:
            raise AssertionError(f"input drift across settings for {setting}")

    bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
    checks: list[dict[str, Any]] = []
    try:
        runtime_identity = bridge.runtime_identity
        rule_names: dict[str, str] = {}
        for setting, program in programs.items():
            name = f"__bridge_axes_{setting}"
            bridge.eval_text(f"(define {name} {wrap_rule(program)})")
            rule_names[setting] = name

        for selected_setting, episode in episodes.items():
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    grid_name = (
                        f"__bridge_axes_input_{selected_setting}_{split}_{pair_index}"
                    )
                    bridge.define_grid(grid_name, pair["input"])
                    candidate_checks: dict[str, Any] = {}
                    for candidate_setting in prototype.ALLOWED_SETTINGS:
                        racket_output = bridge.eval_text(
                            f"({rule_names[candidate_setting]} {grid_name})"
                        )
                        python_output = prototype.apply_python(
                            pair["input"], candidate_setting
                        )
                        racket_python_exact = racket_output == python_output
                        matches_selected = racket_output == pair["output"]
                        if not racket_python_exact:
                            raise AssertionError(
                                "Racket/Python mismatch for "
                                f"selected={selected_setting} candidate={candidate_setting} "
                                f"{split}[{pair_index}]"
                            )
                        if candidate_setting == selected_setting and not matches_selected:
                            raise AssertionError(
                                f"selected Racket output mismatch for {selected_setting} "
                                f"{split}[{pair_index}]"
                            )
                        if candidate_setting != selected_setting and matches_selected:
                            raise AssertionError(
                                f"rival {candidate_setting} agrees with selected "
                                f"{selected_setting} on {split}[{pair_index}]"
                            )
                        candidate_checks[candidate_setting] = {
                            "racket_output_sha256": _sha256_json(racket_output),
                            "python_output_sha256": _sha256_json(python_output),
                            "racket_python_exact": racket_python_exact,
                            "matches_selected_output": matches_selected,
                            "disagrees_with_selected_output": not matches_selected,
                        }
                    checks.append(
                        {
                            "selected_setting": selected_setting,
                            "split": split,
                            "pair_index": pair_index,
                            "sampling": pair["sampling"],
                            "input_sha256": _sha256_json(pair["input"]),
                            "selected_output_sha256": _sha256_json(pair["output"]),
                            "program_checks": candidate_checks,
                        }
                    )
    finally:
        bridge.shutdown()

    all_racket_python_exact = all(
        candidate["racket_python_exact"]
        for row in checks
        for candidate in row["program_checks"].values()
    )
    train_rows = [row for row in checks if row["split"] == "train"]
    test_rows = [row for row in checks if row["split"] == "test"]

    def rival_disagreement_count(rows: list[dict[str, Any]]) -> int:
        return sum(
            candidate["disagrees_with_selected_output"]
            for row in rows
            for setting, candidate in row["program_checks"].items()
            if setting != row["selected_setting"]
        )

    train_rival_disagreements = rival_disagreement_count(train_rows)
    test_rival_disagreements = rival_disagreement_count(test_rows)
    expected_train_disagreements = len(train_rows) * (len(programs) - 1)
    expected_test_disagreements = len(test_rows) * (len(programs) - 1)
    all_demos_refute_every_rival = (
        train_rival_disagreements == expected_train_disagreements
    )
    all_queries_setting_sensitive = (
        test_rival_disagreements == expected_test_disagreements
    )
    if not all_racket_python_exact:
        raise AssertionError("at least one Racket/Python check disagreed")
    if not all_demos_refute_every_rival:
        raise AssertionError("not every demonstration refutes every rival")
    if not all_queries_setting_sensitive:
        raise AssertionError("not every query changes under every rival")

    manifest = _materialize(
        artifact_dir=artifact_dir,
        seed=seed,
        prototype=prototype,
        programs=programs,
        episodes=episodes,
        generator_sha256=generator_sha256,
    )

    source_paths = [
        generator_path,
        HERE / "prototype.py",
        HERE / "verify.py",
        HERE / "README.md",
        TEST_PATH,
    ]
    report = {
        "schema": "7515881f2786-parametric-bridge-axes-verification-v1",
        "status": "passed",
        "scope": "proposed task-local prototype; canonical production unchanged",
        "task_id": prototype.TASK_ID,
        "seed": seed,
        "cwd": os.getcwd(),
        "parameter": {
            "name": prototype.PARAMETER_NAME,
            "allowed_settings": list(prototype.ALLOWED_SETTINGS),
            "canonical_default": prototype.DEFAULT_SETTING,
            "selection_scope": "one hidden setting per complete episode",
            "selection": "explicit retained setting; choose_setting(seed) is deterministic SHA-256",
            "input_constraint": (
                "every production draw has a positive horizontal and vertical bridge, "
                "so every pair distinguishes all three settings"
            ),
        },
        "canonical": {
            "exact_text_match": canonical_exact,
            "normalized_rule_hash": canonical_hash,
            "program_sha256": _sha256_bytes(canonical_program.encode()),
            "selected_generator_rule_hash": generator.RULE_HASH,
        },
        "generator": {
            "path": str(generator_path.relative_to(root)),
            "sha256": generator_sha256,
            "version": generator.VERSION,
        },
        "programs": {
            setting: {
                "sha256": _sha256_bytes(program.encode()),
                "normalized_rule_hash": _normalized_rule_hash(program),
                "exact_canonical": setting == prototype.DEFAULT_SETTING,
            }
            for setting, program in programs.items()
        },
        "episodes": {
            setting: {
                "parameter": episode["parameter"],
                "program_sha256": _sha256_bytes(episode["program"].encode()),
                "train_count": len(episode["train"]),
                "test_count": len(episode["test"]),
                "episode_errors": prototype.episode_errors(episode),
                "input_hashes": [
                    _sha256_json(pair["input"])
                    for split in ("train", "test")
                    for pair in episode[split]
                ],
            }
            for setting, episode in episodes.items()
        },
        "racket_runtime": runtime_identity,
        "counts": {
            "settings": len(programs),
            "episodes": len(episodes),
            "train_pairs_per_episode": len(next(iter(episodes.values()))["train"]),
            "test_pairs_per_episode": len(next(iter(episodes.values()))["test"]),
            "racket_program_pair_checks": sum(
                len(row["program_checks"]) for row in checks
            ),
            "selected_racket_pair_checks": len(checks),
            "rival_racket_pair_checks": len(checks) * (len(programs) - 1),
            "train_rival_disagreements": train_rival_disagreements,
            "test_rival_disagreements": test_rival_disagreements,
        },
        "all_racket_python_exact": all_racket_python_exact,
        "all_demos_refute_every_rival": all_demos_refute_every_rival,
        "all_queries_setting_sensitive": all_queries_setting_sensitive,
        "exact_disagreement": checks[0],
        "checks": checks,
        "materialization": {
            "directory": str(artifact_dir),
            "manifest_sha256": _sha256_file(artifact_dir / "manifest.json"),
            "file_count": len(manifest["files"]),
        },
        "source_hashes": {
            str(path.relative_to(root)): _sha256_file(path)
            for path in source_paths
        },
        "replay": {
            "cwd": "packet_root",
            "command": (
                "python3 review.py run python3 "
                "generators/7515881f2786/workspace/parametric/verify.py "
                f"--seed {seed} --out ../checks/parametric/verification.json "
                "--artifact-dir generators/7515881f2786/workspace/parametric/materialized"
            ),
        },
        "limitations": [
            "The prototype is proposed evidence and is not wired into production selection.",
            "Only the three declared axis settings and one retained five-pair source episode are checked.",
            "Finite declared-rival disagreement does not prove uniqueness against every imaginable rule.",
            "The selected generator, canonical program, authority, and approval metadata remain unchanged.",
        ],
    }
    _write_json(out_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261021)
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
                "out": str(args.out),
                "artifact_dir": str(args.artifact_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
