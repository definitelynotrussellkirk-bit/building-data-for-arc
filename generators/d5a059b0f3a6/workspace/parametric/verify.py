#!/usr/bin/env python3
"""Racket-verify and materialize the d5a059b0f3a6 mirror-mode prototype."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

HERE = Path(__file__).resolve().parent


def _install_packet_scripts_namespace(root: Path) -> None:
    """Expose the packet parser required by the shared rule wrapper."""
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
        "d5a059b0f3a6_parametric_verify", path
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


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


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
        "seed",
    )
    leaked = [token for token in forbidden if token in serialized]
    if leaked:
        raise AssertionError(f"public challenge leaks hidden metadata: {leaked}")
    if any("output" in pair for pair in challenge.get("test", [])):
        raise AssertionError("public challenge leaks a query output")


def _public_materialization_plan(
    *,
    prototype: Any,
    episodes: dict[str, dict[str, Any]],
) -> list[tuple[str, str, dict[str, Any]]]:
    """Stage public challenges in an order derived only from visible filenames."""
    plan = []
    seen_names: set[str] = set()
    for setting, episode in episodes.items():
        challenge = prototype.public_challenge(episode)
        _assert_public_redacted(challenge, prototype)
        public_name = prototype.public_identifier(challenge)
        if public_name in seen_names:
            raise AssertionError("visible-derived public identifier collision")
        seen_names.add(public_name)
        plan.append((public_name, setting, challenge))
    return sorted(plan, key=lambda row: row[0])


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
    file_records: dict[str, dict[str, Any]] = {}
    public_plan = _public_materialization_plan(
        prototype=prototype,
        episodes=episodes,
    )
    public_name_to_setting = {
        public_name: setting
        for public_name, setting, _challenge in public_plan
    }

    def retain(relative: str, payload: str, *, kind: str, setting: str) -> None:
        path = artifact_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
        data = payload.encode()
        file_records[relative] = {
            "sha256": _sha256_bytes(data),
            "bytes": len(data),
            "kind": kind,
            "setting": setting,
        }

    for setting in prototype.ALLOWED_SETTINGS:
        episode = episodes[setting]
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

    for public_name, setting, challenge in public_plan:
        retain(
            f"public/challenges/{public_name}",
            json.dumps(challenge, indent=2, sort_keys=True) + "\n",
            kind="public_answer_free_challenge",
            setting=setting,
        )

    manifest = {
        "schema": "d5a059b0f3a6-parametric-materialization-v1",
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
        "public_filename_policy": (
            "challenge-<sha256 visible demos plus query inputs>.json; "
            "independent of private setting, seed and query answers"
        ),
        "public_write_order_policy": (
            "lexicographic visible-derived filename; independent of "
            "ALLOWED_SETTINGS order"
        ),
        "private_public_name_map": public_name_to_setting,
        "files": file_records,
    }
    _write_json(artifact_dir / "private" / "manifest.json", manifest)
    return manifest


def verify(*, seed: int, out_path: Path, artifact_dir: Path) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
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
    reference_inputs = [
        pair["input"]
        for split in ("train", "test")
        for pair in episodes[prototype.DEFAULT_SETTING][split]
    ]
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

    bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
    checks: list[dict[str, Any]] = []
    try:
        runtime_identity = bridge.runtime_identity
        rule_names = {}
        for setting, program in programs.items():
            name = f"__mirror_mode_{setting}"
            bridge.eval_text(f"(define {name} {wrap_rule(program)})")
            rule_names[setting] = name

        for pair_index, grid in enumerate(reference_inputs):
            grid_name = f"__mirror_mode_input_{pair_index}"
            bridge.define_grid(grid_name, grid)
            candidate_outputs = {}
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
            if candidate_outputs[prototype.ALLOWED_SETTINGS[0]] == candidate_outputs[
                prototype.ALLOWED_SETTINGS[1]
            ]:
                raise AssertionError(f"pair {pair_index} is not setting-sensitive")
            checks.append(
                {
                    "pair_index": pair_index,
                    "split": (
                        "train"
                        if pair_index < prototype.DEFAULT_N_TRAIN
                        else "test"
                    ),
                    "split_index": (
                        pair_index
                        if pair_index < prototype.DEFAULT_N_TRAIN
                        else pair_index - prototype.DEFAULT_N_TRAIN
                    ),
                    "input_sha256": _sha256_json(grid),
                    "outputs": {
                        setting: {
                            "sha256": _sha256_json(output),
                            "racket_python_exact": True,
                        }
                        for setting, output in candidate_outputs.items()
                    },
                    "settings_disagree": True,
                }
            )
    finally:
        bridge.shutdown()

    for setting, episode in episodes.items():
        expected = [
            pair["output"]
            for split in ("train", "test")
            for pair in episode[split]
        ]
        selected_hashes = [
            row["outputs"][setting]["sha256"] for row in checks
        ]
        if selected_hashes != [_sha256_json(output) for output in expected]:
            raise AssertionError(f"retained labels do not match Racket for {setting}")

    materialization = _materialize(
        artifact_dir=artifact_dir,
        seed=seed,
        prototype=prototype,
        programs=programs,
        episodes=episodes,
        generator_sha256=generator_sha256,
    )
    source_files = [HERE / "prototype.py", HERE / "verify.py", HERE / "README.md"]
    report = {
        "schema": "d5a059b0f3a6-parametric-verification-v1",
        "status": "passed",
        "scope": "proposed task-local prototype; not catalog approval",
        "task_id": prototype.TASK_ID,
        "seed": seed,
        "parameter": {
            "name": prototype.PARAMETER_NAME,
            "allowed_values": list(prototype.ALLOWED_SETTINGS),
            "original_default": prototype.DEFAULT_SETTING,
            "selection": "one deterministic SHA-256-derived value per episode seed",
            "fixed_across_episode": True,
            "input_constraint": (
                "all retained inputs are lawful production scenes on which the "
                "two settings produce different outputs"
            ),
        },
        "counts": {
            "demonstrations_per_episode": prototype.DEFAULT_N_TRAIN,
            "queries_per_episode": prototype.DEFAULT_N_TEST,
            "episodes": len(episodes),
            "distinct_shared_inputs": len(reference_inputs),
            "racket_calls_checked": len(checks) * len(programs),
        },
        "canonical_binding": {
            "generator_path": str(generator_path.relative_to(root)),
            "generator_sha256": generator_sha256,
            "rule_hash": prototype.CANONICAL_RULE_HASH,
            "default_program_exact_canonical": True,
        },
        "programs": {
            setting: {
                "text": program,
                "sha256": _sha256_bytes(program.encode()),
                "normalized_rule_hash": _normalized_rule_hash(program),
            }
            for setting, program in programs.items()
        },
        "episodes": episodes,
        "checks": checks,
        "teaching": {
            "every_demo_refutes_rival": all(
                row["settings_disagree"] for row in checks if row["split"] == "train"
            ),
            "every_query_setting_sensitive": all(
                row["settings_disagree"] for row in checks if row["split"] == "test"
            ),
            "query_answers_used_to_choose_demos": False,
        },
        "racket_runtime": runtime_identity,
        "materialization": materialization,
        "prototype_sources": {
            str(path.relative_to(HERE)): _sha256_file(path)
            for path in source_files
        },
        "command": (
            "python3 review.py run python3 "
            "generators/d5a059b0f3a6/workspace/parametric/verify.py "
            f"--seed {seed} --out ../checks/parametric/verification.json "
            "--artifact-dir ../checks/parametric/artifacts"
        ),
        "limitations": [
            "Only the two declared settings and one retained input seed are Racket-evidenced.",
            "The finite setting rival is not an exhaustive hypothesis class.",
            "The production generator and canonical selected authority are unchanged.",
            "This prototype is proposed and is not catalog-approved or runtime-integrated.",
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
