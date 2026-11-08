#!/usr/bin/env python3
"""Racket-verify and retain evidence for the shift-direction prototype."""
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
TEST_PATH = HERE.parents[1] / "tests" / "test_parametric_shift_direction.py"


def _install_packet_scripts_namespace(root: Path) -> None:
    """Expose packet parser helpers under the staged runtime namespace."""
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
        "parametric_shift_direction_6d06c5b96c19_verify", path
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


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _assert_public_redacted(challenge: dict[str, Any], prototype: Any) -> None:
    serialized = json.dumps(challenge, sort_keys=True)
    forbidden = (prototype.PARAMETER_NAME, "rule!", "sampling", "program", "parameter")
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
    public_names = {
        setting: f"challenge-{index:02d}.json"
        for index, setting in enumerate(prototype.ALLOWED_SETTINGS, start=1)
    }

    def retain(relative: str, text: str, *, kind: str, setting: str) -> None:
        path = artifact_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        files[relative] = {
            "sha256": _sha256_bytes(text.encode()),
            "bytes": len(text.encode()),
            "kind": kind,
            "setting": setting,
        }

    for setting in prototype.ALLOWED_SETTINGS:
        episode = episodes[setting]
        public = prototype.public_challenge(episode)
        _assert_public_redacted(public, prototype)
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
            f"public/challenges/{public_names[setting]}",
            json.dumps(public, indent=2, sort_keys=True) + "\n",
            kind="public_answer_free_challenge",
            setting=setting,
        )

    manifest = {
        "schema": "6d06c5b96c19-parametric-materialization-v1",
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
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    prototype = _load_prototype()
    root = find_root(__file__)
    _install_packet_scripts_namespace(root)
    generator, generator_path, generator_sha256 = load_selected_generator(
        prototype.TASK_ID, root=root
    )

    canonical_program = _canonical_program(prototype.TASK_ID, root)
    programs = {setting: prototype.program_for(setting) for setting in prototype.ALLOWED_SETTINGS}
    if programs[prototype.DEFAULT_SETTING] != canonical_program:
        raise AssertionError("default prototype program is not exact canonical text")
    canonical_hash = _normalized_rule_hash(canonical_program)
    if canonical_hash != prototype.CANONICAL_RULE_HASH:
        raise AssertionError("canonical rule hash drift")
    if generator.RULE_HASH != prototype.CANONICAL_RULE_HASH:
        raise AssertionError("selected generator RULE_HASH disagrees with prototype")

    episodes = {
        setting: prototype.build_episode(seed, setting=setting)
        for setting in prototype.ALLOWED_SETTINGS
    }
    for setting, episode in episodes.items():
        errors = prototype.episode_errors(episode)
        if errors:
            raise AssertionError(f"invalid {setting} episode: {errors}")
        if episode["generator_sha256"] != generator_sha256:
            raise AssertionError(f"{setting} episode used different generator bytes")

    reference_inputs = [
        pair["input"]
        for split in ("train", "test")
        for pair in episodes[prototype.DEFAULT_SETTING][split]
    ]
    for setting, episode in episodes.items():
        inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
        if inputs != reference_inputs:
            raise AssertionError(f"input drift across settings for {setting}")

    bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
    checks: list[dict[str, Any]] = []
    try:
        runtime_identity = bridge.runtime_identity
        rule_names: dict[str, str] = {}
        for setting, program in programs.items():
            name = f"__shift_direction_{setting}"
            bridge.eval_text(f"(define {name} {wrap_rule(program)})")
            rule_names[setting] = name

        for selected, episode in episodes.items():
            rival = next(value for value in prototype.ALLOWED_SETTINGS if value != selected)
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    grid_name = f"__shift_input_{selected}_{split}_{pair_index}"
                    bridge.define_grid(grid_name, pair["input"])
                    candidates: dict[str, Any] = {}
                    for candidate in prototype.ALLOWED_SETTINGS:
                        racket_output = bridge.eval_text(f"({rule_names[candidate]} {grid_name})")
                        python_output = prototype.apply_python(pair["input"], candidate)
                        if racket_output != python_output:
                            raise AssertionError(
                                f"Racket/Python mismatch: selected={selected} "
                                f"candidate={candidate} {split}[{pair_index}]"
                            )
                        matches_selected = racket_output == pair["output"]
                        if candidate == selected and not matches_selected:
                            raise AssertionError(
                                f"selected Racket output mismatch: {selected} {split}[{pair_index}]"
                            )
                        candidates[candidate] = {
                            "racket_output_sha256": _sha256_json(racket_output),
                            "python_output_sha256": _sha256_json(python_output),
                            "racket_python_exact": True,
                            "matches_selected_output": matches_selected,
                        }
                    checks.append(
                        {
                            "selected_setting": selected,
                            "rival_setting": rival,
                            "split": split,
                            "pair_index": pair_index,
                            "sampling": pair["sampling"],
                            "input_sha256": _sha256_json(pair["input"]),
                            "selected_output_sha256": _sha256_json(pair["output"]),
                            "program_checks": candidates,
                        }
                    )
    finally:
        bridge.shutdown()

    for selected in prototype.ALLOWED_SETTINGS:
        selected_rows = [row for row in checks if row["selected_setting"] == selected]
        train_rows = [row for row in selected_rows if row["split"] == "train"]
        test_rows = [row for row in selected_rows if row["split"] == "test"]
        if not any(
            not row["program_checks"][row["rival_setting"]]["matches_selected_output"]
            for row in train_rows
        ):
            raise AssertionError(f"training does not distinguish setting {selected}")
        if not all(
            not row["program_checks"][row["rival_setting"]]["matches_selected_output"]
            for row in test_rows
        ):
            raise AssertionError(f"query is not direction-sensitive for setting {selected}")

    manifest = _materialize(
        artifact_dir=artifact_dir,
        seed=seed,
        prototype=prototype,
        programs=programs,
        episodes=episodes,
        generator_sha256=generator_sha256,
    )
    train_disagreements = sum(
        not row["program_checks"][row["rival_setting"]]["matches_selected_output"]
        for row in checks
        if row["split"] == "train"
    )
    test_disagreements = sum(
        not row["program_checks"][row["rival_setting"]]["matches_selected_output"]
        for row in checks
        if row["split"] == "test"
    )

    source_paths = [generator_path, HERE / "prototype.py", HERE / "verify.py", HERE / "README.md", TEST_PATH]
    report = {
        "schema": "6d06c5b96c19-parametric-shift-direction-verification-v1",
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
        },
        "canonical": {
            "exact_text_match": programs[prototype.DEFAULT_SETTING] == canonical_program,
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
        "racket_runtime": runtime_identity,
        "counts": {
            "settings": len(programs),
            "episodes": len(episodes),
            "pairs_per_episode": 5,
            "racket_program_pair_checks": sum(len(row["program_checks"]) for row in checks),
            "train_rival_disagreements": train_disagreements,
            "test_rival_disagreements": test_disagreements,
        },
        "all_racket_python_exact": all(
            candidate["racket_python_exact"]
            for row in checks
            for candidate in row["program_checks"].values()
        ),
        "training_identifies_setting": True,
        "queries_are_setting_sensitive": True,
        "exact_disagreement": next(
            row for row in checks
            if not row["program_checks"][row["rival_setting"]]["matches_selected_output"]
        ),
        "checks": checks,
        "materialization": {
            "directory": str(artifact_dir),
            "manifest_sha256": _sha256_file(artifact_dir / "manifest.json"),
            "file_count": len(manifest["files"]),
        },
        "source_hashes": {
            str(path.relative_to(root)): _sha256_file(path) for path in source_paths
        },
        "replay": {
            "cwd": "packet_root",
            "command": (
                "python3 review.py run python3 "
                "generators/6d06c5b96c19/workspace/parametric/verify.py "
                f"--seed {seed} --out ../checks/parametric/verification.json "
                "--artifact-dir generators/6d06c5b96c19/workspace/parametric/materialized"
            ),
        },
        "limitations": [
            "The prototype is proposed evidence and is not wired into production selection.",
            "Only the two declared direction settings and one retained five-pair source episode are checked.",
            "Finite rival disagreement does not prove uniqueness against every imaginable rule.",
            "Canonical examples, canonical program, authority, and approval metadata remain unchanged.",
        ],
    }
    _write_json(out_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    report = verify(seed=args.seed, out_path=args.out, artifact_dir=args.artifact_dir)
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
