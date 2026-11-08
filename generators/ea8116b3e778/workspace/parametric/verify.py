#!/usr/bin/env python3
"""Materialize and exact-Racket-verify the symmetry-mode prototype."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, load_selected_generator


HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
REPORT_SCHEMA = "ea8116b3e778-parametric-symmetry-mode-verification-v1"
DEFAULT_SEED = 53


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        "ea8116b3e778_symmetry_mode_prototype_verify",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _relative_or_absolute(path: Path, root: Path = ROOT) -> str:
    resolved = path.resolve()
    if resolved.is_relative_to(root.resolve()):
        return resolved.relative_to(root.resolve()).as_posix()
    return str(resolved)


def _portable_runtime_identity(identity: dict[str, Any]) -> dict[str, Any]:
    portable = deepcopy(identity)
    root = ROOT.resolve()
    for key, value in tuple(portable.items()):
        if not key.endswith("_path") or not isinstance(value, str):
            continue
        resolved = Path(value).resolve()
        if resolved.is_relative_to(root):
            portable[key] = resolved.relative_to(root).as_posix()
        else:
            portable[key] = resolved.name
    return portable


def _reset_artifacts(artifact_dir: Path) -> None:
    """Clear only this verifier's generated paths, preserving unrelated files."""
    artifact_dir = artifact_dir.resolve()
    if artifact_dir == ROOT.resolve() or artifact_dir == Path("/"):
        raise ValueError(f"refusing unsafe artifact directory: {artifact_dir}")
    if artifact_dir.exists() and (artifact_dir.is_symlink() or not artifact_dir.is_dir()):
        raise ValueError(f"artifact destination must be a real directory: {artifact_dir}")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    for name in ("public", "private"):
        path = artifact_dir / name
        if path.is_symlink():
            raise ValueError(f"refusing unsafe generated path: {path}")
        if path.exists():
            if not path.is_dir():
                raise ValueError(f"refusing unsafe generated path: {path}")
            shutil.rmtree(path)
    manifest = artifact_dir / "manifest.json"
    if manifest.is_symlink():
        raise ValueError(f"refusing unsafe generated manifest: {manifest}")
    if manifest.exists():
        if manifest.is_dir():
            raise ValueError(f"refusing unsafe generated manifest: {manifest}")
        manifest.unlink()


def _public_masked(public: dict[str, Any], serialized: str) -> bool:
    return (
        set(public) == {"train", "test"}
        and all(set(pair) == {"input", "output"} for pair in public["train"])
        and all(set(pair) == {"input"} for pair in public["test"])
        and all(
            token not in serialized
            for token in (
                "symmetry_mode",
                "parameters",
                "program",
                "program_normalized_sha256",
                "seed",
                "prototype_id",
            )
        )
    )


def _materialize(
    *,
    proto: Any,
    artifact_dir: Path,
    episodes: dict[str, dict[str, Any]],
    programs: dict[str, str],
) -> dict[str, Any]:
    _reset_artifacts(artifact_dir)
    files: dict[str, dict[str, Any]] = {}

    def retain(path: Path, data: bytes, *, kind: str, mode: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        relative = path.relative_to(artifact_dir).as_posix()
        files[relative] = {
            "kind": kind,
            "symmetry_mode": mode,
            "bytes": len(data),
            "sha256": _sha_bytes(data),
        }

    prepared = []
    for mode in proto.SYMMETRY_MODES:
        episode = episodes[mode]
        public = proto.public_challenge(episode)
        public_payload = proto.public_bytes(episode)
        public_id = proto.public_id(episode)
        public_text = public_payload.decode("utf-8")
        if not _public_masked(public, public_text):
            raise AssertionError(f"public challenge leaks private data for {mode}")
        if _sha_bytes(public_payload) != public_id:
            raise AssertionError("public challenge id is not its byte hash")
        prepared.append((public_id, mode, episode, public_payload))

    public_ids = [row[0] for row in prepared]
    if len(set(public_ids)) != len(public_ids):
        raise AssertionError("retained modes produced duplicate visible challenges")

    for public_id, mode, episode, public_payload in sorted(prepared):
        private_payload = (
            json.dumps(episode, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        ).encode("utf-8")
        program_payload = (programs[mode] + "\n").encode("utf-8")
        retain(
            artifact_dir / "private" / "episodes" / f"{mode}.json",
            private_payload,
            kind="private_complete_episode",
            mode=mode,
        )
        retain(
            artifact_dir / "private" / "programs" / f"{mode}.rkt",
            program_payload,
            kind="private_exact_program",
            mode=mode,
        )
        retain(
            artifact_dir / "public" / f"challenge-{public_id}.json",
            public_payload,
            kind="public_answer_free_challenge",
            mode=mode,
        )

    manifest = {
        "schema": "ea8116b3e778-parametric-symmetry-mode-materialization-v1",
        "status": "passed",
        "scope": "proposed task-local prototype; canonical production unchanged",
        "task_id": proto.TASK_ID,
        "prototype_id": proto.PROTOTYPE_ID,
        "public_filename_policy": "SHA-256 of exact visible challenge bytes",
        "public_challenge_ids": sorted(public_ids),
        "files": files,
    }
    _write_json(artifact_dir / "manifest.json", manifest)
    return manifest


def verify(
    *,
    seed: int = DEFAULT_SEED,
    out_path: Path,
    artifact_dir: Path,
    demonstration_count: int = 2,
    query_count: int = 4,
) -> dict[str, Any]:
    """Run the exact Racket programs, retain artifacts, and write a report."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    out_path = Path(out_path).resolve()
    artifact_dir = Path(artifact_dir).resolve()
    proto = _load_prototype()
    generator, generator_path, generator_sha256 = load_selected_generator(
        proto.TASK_ID,
        root=ROOT,
    )

    programs = {mode: proto.program_for(mode, root=ROOT) for mode in proto.SYMMETRY_MODES}
    canonical = proto.canonical_source(root=ROOT)
    canonical_exact = programs[proto.DEFAULT_SYMMETRY_MODE] == canonical
    if not canonical_exact:
        raise AssertionError("default prototype program is not exact canonical source")
    if not proto.normalized_program_hash("both", root=ROOT).startswith(
        proto.CANONICAL_NORMALIZED_HASH_PREFIX
    ):
        raise AssertionError("default prototype program hash drifted")
    if len({_sha_bytes(program.encode("utf-8")) for program in programs.values()}) != 4:
        raise AssertionError("the four declared settings do not have four programs")

    episodes = {
        mode: proto.generate_episode(
            seed,
            symmetry_mode=mode,
            difficulty="medium",
            demonstration_count=demonstration_count,
            query_count=query_count,
            root=ROOT,
        )
        for mode in proto.SYMMETRY_MODES
    }
    validation = {
        mode: proto.validate_episode(episode, root=ROOT)
        for mode, episode in episodes.items()
    }
    reference_inputs = [
        pair["input"]
        for split in ("train", "test")
        for pair in episodes[proto.DEFAULT_SYMMETRY_MODE][split]
    ]
    for mode, episode in episodes.items():
        inputs = [
            pair["input"]
            for split in ("train", "test")
            for pair in episode[split]
        ]
        if inputs != reference_inputs:
            raise AssertionError(f"source inputs drifted across settings for {mode}")

    checks: list[dict[str, Any]] = []
    with RacketBridge(timeout=30, max_calls_before_restart=192) as bridge:
        runtime_identity = _portable_runtime_identity(bridge.runtime_identity)
        function_names: dict[str, str] = {}
        for mode, program in programs.items():
            function_name = f"__symmetry_mode_{mode}"
            bridge.eval_text(f"(define {function_name} {wrap_rule(program)})")
            function_names[mode] = function_name

        for selected_mode, episode in episodes.items():
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    grid_name = f"__symmetry_input_{selected_mode}_{split}_{pair_index}"
                    bridge.define_grid(grid_name, pair["input"])
                    candidate_checks: dict[str, Any] = {}
                    for candidate_mode in proto.SYMMETRY_MODES:
                        racket_output = bridge.eval_text(
                            f"({function_names[candidate_mode]} {grid_name})"
                        )
                        python_output = proto.solve(
                            pair["input"],
                            symmetry_mode=candidate_mode,
                        )
                        racket_python_exact = racket_output == python_output
                        matches_selected = racket_output == pair["output"]
                        if not racket_python_exact:
                            raise AssertionError(
                                "Racket/Python mismatch for "
                                f"selected={selected_mode}, candidate={candidate_mode}, "
                                f"{split}[{pair_index}]"
                            )
                        if candidate_mode == selected_mode and not matches_selected:
                            raise AssertionError(
                                f"selected Racket program mislabeled {selected_mode} "
                                f"{split}[{pair_index}]"
                            )
                        if candidate_mode != selected_mode and matches_selected:
                            raise AssertionError(
                                f"rival {candidate_mode} agrees with {selected_mode} "
                                f"on {split}[{pair_index}]"
                            )
                        candidate_checks[candidate_mode] = {
                            "racket_output_sha256": _sha_json(racket_output),
                            "python_output_sha256": _sha_json(python_output),
                            "racket_python_exact": racket_python_exact,
                            "matches_selected_output": matches_selected,
                            "disagrees_with_selected_output": not matches_selected,
                        }
                    canonical_generator_exact = None
                    if selected_mode == proto.DEFAULT_SYMMETRY_MODE:
                        canonical_generator_exact = (
                            pair["output"] == generator.solve_python(pair["input"])
                        )
                        if not canonical_generator_exact:
                            raise AssertionError(
                                f"canonical generator mirror drift at {split}[{pair_index}]"
                            )
                    checks.append(
                        {
                            "selected_symmetry_mode": selected_mode,
                            "split": split,
                            "pair_index": pair_index,
                            "input_sha256": _sha_json(pair["input"]),
                            "selected_output_sha256": _sha_json(pair["output"]),
                            "canonical_generator_exact": canonical_generator_exact,
                            "program_checks": candidate_checks,
                        }
                    )

    train_rows = [row for row in checks if row["split"] == "train"]
    query_rows = [row for row in checks if row["split"] == "test"]
    all_racket_python_exact = all(
        candidate["racket_python_exact"]
        for row in checks
        for candidate in row["program_checks"].values()
    )
    all_demos_refute_every_rival = all(
        candidate["disagrees_with_selected_output"]
        for row in train_rows
        for mode, candidate in row["program_checks"].items()
        if mode != row["selected_symmetry_mode"]
    )
    all_queries_setting_sensitive = all(
        candidate["disagrees_with_selected_output"]
        for row in query_rows
        for mode, candidate in row["program_checks"].items()
        if mode != row["selected_symmetry_mode"]
    )
    if not all_racket_python_exact:
        raise AssertionError("at least one Racket/Python comparison failed")
    if not all_demos_refute_every_rival:
        raise AssertionError("at least one demonstration fails to refute a rival")
    if not all_queries_setting_sensitive:
        raise AssertionError("at least one query is insensitive to a rival setting")

    manifest = _materialize(
        proto=proto,
        artifact_dir=artifact_dir,
        episodes=episodes,
        programs=programs,
    )
    public_rows = [
        value
        for value in manifest["files"].values()
        if value["kind"] == "public_answer_free_challenge"
    ]
    all_public_challenges_masked = len(public_rows) == len(proto.SYMMETRY_MODES)

    source_paths = [
        Path(generator_path),
        HERE / "prototype.py",
        HERE / "verify.py",
        HERE / "README.md",
        HERE.parents[1] / "tests" / "test_parametric_symmetry_mode.py",
    ]
    report = {
        "schema": REPORT_SCHEMA,
        "status": "passed",
        "scope": "proposed task-local prototype; canonical production unchanged",
        "task_id": proto.TASK_ID,
        "prototype_id": proto.PROTOTYPE_ID,
        "seed": seed,
        "parameter": {
            "name": "symmetry_mode",
            "allowed_values": list(proto.SYMMETRY_MODES),
            "canonical_default": proto.DEFAULT_SYMMETRY_MODE,
            "selection_scope": "one setting per complete episode",
            "input_profile": "single_quadrant",
        },
        "canonical": {
            "exact_text_match": canonical_exact,
            "normalized_program_sha256": proto.normalized_program_hash(
                "both", root=ROOT
            ),
            "program_sha256": _sha_bytes(canonical.encode("utf-8")),
            "generator_rule_hash": generator.RULE_HASH,
            "all_canonical_pairs_match_generator_mirror": all(
                row["canonical_generator_exact"] is True
                for row in checks
                if row["selected_symmetry_mode"] == proto.DEFAULT_SYMMETRY_MODE
            ),
        },
        "generator": {
            "path": _relative_or_absolute(Path(generator_path)),
            "sha256": generator_sha256,
            "version": generator.VERSION,
        },
        "programs": {
            mode: {
                "sha256": _sha_bytes(program.encode("utf-8")),
                "normalized_program_sha256": proto.normalized_program_hash(
                    mode, root=ROOT
                ),
                "exact_canonical": mode == proto.DEFAULT_SYMMETRY_MODE,
            }
            for mode, program in programs.items()
        },
        "episodes": {
            mode: {
                "validation": validation[mode],
                "train_count": len(episode["train"]),
                "query_count": len(episode["test"]),
                "input_hashes": [
                    _sha_json(pair["input"])
                    for split in ("train", "test")
                    for pair in episode[split]
                ],
                "public_id": proto.public_id(episode),
            }
            for mode, episode in episodes.items()
        },
        "racket_runtime": runtime_identity,
        "counts": {
            "settings": len(programs),
            "episodes": len(episodes),
            "demonstrations_per_episode": demonstration_count,
            "queries_per_episode": query_count,
            "selected_pair_checks": len(checks),
            "racket_program_pair_checks": sum(
                len(row["program_checks"]) for row in checks
            ),
            "rival_demo_disagreements": sum(
                candidate["disagrees_with_selected_output"]
                for row in train_rows
                for mode, candidate in row["program_checks"].items()
                if mode != row["selected_symmetry_mode"]
            ),
            "rival_query_disagreements": sum(
                candidate["disagrees_with_selected_output"]
                for row in query_rows
                for mode, candidate in row["program_checks"].items()
                if mode != row["selected_symmetry_mode"]
            ),
        },
        "all_racket_python_exact": all_racket_python_exact,
        "all_demos_refute_every_rival": all_demos_refute_every_rival,
        "all_queries_setting_sensitive": all_queries_setting_sensitive,
        "all_public_challenges_masked": all_public_challenges_masked,
        "exact_disagreement_witness": checks[0],
        "checks": checks,
        "materialization": {
            "directory": _relative_or_absolute(artifact_dir),
            "manifest_sha256": _sha_bytes(
                (artifact_dir / "manifest.json").read_bytes()
            ),
            "file_count": len(manifest["files"]),
        },
        "source_hashes": {
            _relative_or_absolute(path): _sha_bytes(path.read_bytes())
            for path in source_paths
        },
        "replay": {
            "cwd": "packet_root",
            "command": (
                "python3 review.py run python3 "
                "generators/ea8116b3e778/workspace/parametric/verify.py "
                f"--seed {seed} --demonstrations {demonstration_count} "
                f"--queries {query_count} "
                "--out ../checks/parametric/ea8116b3e778-symmetry-mode.json "
                "--artifact-dir generators/ea8116b3e778/workspace/parametric/materialized"
            ),
        },
        "limitations": [
            "This is a task-local proposal and is not wired into production selection.",
            "Evidence retains one six-pair episode per declared setting, not every seed.",
            "All pairwise declared rivals are refuted; this is not a uniqueness proof over every imaginable ARC rule.",
            "The selected generator, canonical Racket authority, and approval metadata remain unchanged.",
        ],
    }
    _write_json(out_path, report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--demonstrations", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    report = verify(
        seed=args.seed,
        out_path=args.out,
        artifact_dir=args.artifact_dir,
        demonstration_count=args.demonstrations,
        query_count=args.queries,
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
