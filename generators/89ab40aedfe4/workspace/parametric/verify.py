#!/usr/bin/env python3
"""Racket-backed verifier for the legend-selected population-sort prototype."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import prototype  # noqa: E402
import public_focus  # noqa: E402


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _normalized_hash(source: str) -> str:
    return _sha256(" ".join(source.split()).encode())


def _grid_hash(grid: list[list[int]]) -> str:
    return _sha256(json.dumps(grid, separators=(",", ":")).encode())


def _racket_callable(source: str) -> str:
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("prototype program must be one `(rule! EXPR)` form")
    expression = stripped[len("(rule!") : -1].strip()
    if not expression.startswith("(lambda"):
        raise ValueError("prototype rule expression must be a lambda")
    return expression


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"'({rows})"


def _application(source: str, grid: list[list[int]]) -> str:
    return f"({_racket_callable(source)} {_grid_literal(grid)})"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _prepare_artifact_dir(path: Path) -> None:
    """Replace only a hash-matching prior materialization; reject unknown debris."""
    if path.is_symlink():
        raise SystemExit("artifact directory must not be a symlink")
    path.mkdir(parents=True, exist_ok=True)
    entries = {entry.name: entry for entry in path.iterdir()}
    if not entries:
        return
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise SystemExit("nonempty artifact directory needs a regular prior manifest.json")
    try:
        prior = json.loads(manifest_path.read_text(encoding="utf-8"))
        if prior.get("schema") != "89ab40aedfe4-legend-selector-materialization-v1":
            raise ValueError("unrecognized materialization schema")
        prior_files = prior["files"]
        if not isinstance(prior_files, dict):
            raise TypeError("files must be an object")
        declared = set(prior_files)
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise SystemExit("cannot validate prior artifact manifest") from error
    fixed_names = {
        "all-slots.rkt",
        "all-slots-private.json",
        "all-slots-public.json",
        "contains-key.rkt",
        "contains-key-private.json",
        "contains-key-public.json",
    }
    def generated_name(name: str) -> bool:
        if name in fixed_names:
            return True
        if not (name.startswith("public-") and name.endswith(".json")):
            return False
        digest = name[len("public-") : -len(".json")]
        return len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)
    unexpected_names = sorted(name for name in declared if not generated_name(name))
    if unexpected_names:
        raise SystemExit(f"unexpected prior artifact name: {unexpected_names}")
    expected = declared | {"manifest.json"}
    if set(entries) != expected:
        unknown = sorted(set(entries) - expected)
        missing = sorted(expected - set(entries))
        raise SystemExit(f"artifact directory differs from prior manifest: unknown={unknown} missing={missing}")
    for name, entry in entries.items():
        if entry.is_symlink() or not entry.is_file():
            raise SystemExit(f"unsafe prior artifact entry: {name}")
        if name == "manifest.json":
            continue
        row = prior_files.get(name)
        body = entry.read_bytes()
        if (
            not isinstance(row, dict)
            or row.get("sha256") != _sha256(body)
            or row.get("bytes") != len(body)
        ):
            raise SystemExit(f"prior artifact hash/size mismatch: {name}")
    for name in sorted(declared):
        entries[name].unlink()
    manifest_path.unlink()


def _load_generator(root: Path):
    path = root / "generators" / prototype.TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("verify_generator_89ab40aedfe4", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


def _public_task(root: Path) -> dict[str, Any]:
    path = root / "shared" / "data" / "raw" / "arc-agi_evaluation_challenges.json"
    return json.loads(path.read_text(encoding="utf-8"))[prototype.PUBLIC_PARENT_ID]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--out", required=True)
    parser.add_argument("--artifact-dir")
    args = parser.parse_args()

    root = find_root(__file__)
    generator, generator_path = _load_generator(root)
    programs = {
        mode: prototype.program_for(mode, root=root)
        for mode in prototype.SELECTION_MODES
    }
    if programs[prototype.DEFAULT_SELECTION_MODE] != prototype._canonical_program(root=root):
        raise SystemExit("default setting no longer equals the exact canonical authority")
    if len({_normalized_hash(source) for source in programs.values()}) != len(programs):
        raise SystemExit("declared settings materialize identical Racket programs")

    episodes = {
        mode: prototype.build_episode(
            args.seed,
            selection_mode=mode,
            demonstration_count=3,
            query_count=4,
            root=root,
        )
        for mode in prototype.SELECTION_MODES
    }
    input_hashes = {
        mode: [
            _grid_hash(pair["input"])
            for pair in episode["train"] + episode["test"]
        ]
        for mode, episode in episodes.items()
    }
    for mode, hashes in input_hashes.items():
        if len(set(hashes)) != len(hashes):
            raise SystemExit(f"duplicate demonstration/query input in {mode} episode")
    paired_inputs_equal = input_hashes["all_slots"] == input_hashes["contains_key"]
    if not paired_inputs_equal:
        raise SystemExit("parameter settings no longer share paired sampler inputs")

    for mode, episode in episodes.items():
        for split in ("train", "test"):
            for index, pair in enumerate(episode[split]):
                errors = generator.self_check(pair["input"])
                if errors:
                    raise SystemExit(f"invalid generated input: mode={mode} {split}[{index}] {errors}")

    public_task = _public_task(root)
    public_training_exact = all(
        public_focus.apply_rule(pair["input"]) == pair["output"]
        for pair in public_task["train"]
    )
    if not public_training_exact:
        raise SystemExit("public-focus solver does not match every supplied demonstration")
    public_prediction = public_focus.apply_rule(public_task["test"][0]["input"])

    checks: list[dict[str, Any]] = []
    bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
    try:
        runtime_identity = bridge.runtime_identity
        for selected_mode, episode in episodes.items():
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    outputs: dict[str, list[list[int]]] = {}
                    matches: dict[str, bool] = {}
                    for candidate_mode, source in programs.items():
                        racket_output = bridge.eval_text(_application(source, pair["input"]))
                        python_output = prototype.apply_python(pair["input"], candidate_mode)
                        matches[candidate_mode] = racket_output == python_output
                        if not matches[candidate_mode]:
                            raise SystemExit(
                                "Racket/Python mismatch: "
                                f"selected={selected_mode} {split}[{index}] candidate={candidate_mode}"
                            )
                        outputs[candidate_mode] = racket_output
                    if outputs[selected_mode] != pair["output"]:
                        raise SystemExit(
                            f"selected label mismatch: mode={selected_mode} {split}[{index}]"
                        )
                    checks.append(
                        {
                            "episode_selection_mode": selected_mode,
                            "split": split,
                            "pair_index": index,
                            "input_sha256": _grid_hash(pair["input"]),
                            "selected_output_sha256": _grid_hash(pair["output"]),
                            "candidate_output_sha256": {
                                mode: _grid_hash(output) for mode, output in outputs.items()
                            },
                            "python_racket_match": all(matches.values()),
                            "settings_distinct": len({_grid_hash(output) for output in outputs.values()})
                            == len(outputs),
                        }
                    )
    finally:
        bridge.shutdown()

    demonstrations = [row for row in checks if row["split"] == "train"]
    if not all(row["settings_distinct"] for row in demonstrations):
        raise SystemExit("one or more retained demonstrations fail to distinguish the settings")
    if not all(row["settings_distinct"] for row in checks):
        raise SystemExit("one or more retained queries fail to distinguish the settings")

    source_paths = {
        "prototype.py": HERE / "prototype.py",
        "public_focus.py": HERE / "public_focus.py",
        "verify.py": Path(__file__).resolve(),
        "generator.py": generator_path,
    }
    witness_input = episodes["all_slots"]["train"][0]["input"]
    report = {
        "schema": "89ab40aedfe4-legend-selector-verification-v1",
        "status": "passed",
        "scope": prototype.STATUS,
        "task_id": prototype.TASK_ID,
        "seed": args.seed,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "public_parent": {
            "task_id": prototype.PUBLIC_PARENT_ID,
            "public_challenge_sha256": "1df30e2f02c4e10a00bbcb8b302b840362158c24d60ab57248befc023557462c",
            "rule": (
                "read non-background colors from the 3x3 color-3-bordered legend; "
                "erase each external four-connected non-7 region containing every legend color"
            ),
            "training_exact": public_training_exact,
            "training_pairs": len(public_task["train"]),
            "test_prediction": public_prediction,
            "transferred_dependency": (
                "the first bit-column is a legend of required body rows; later columns containing "
                "every required row participate in stable population sorting"
            ),
        },
        "parameter": {
            "name": "selection_mode",
            "allowed_values": list(prototype.SELECTION_MODES),
            "default": prototype.DEFAULT_SELECTION_MODE,
            "chosen_once_per_episode": True,
            "meanings": {
                "all_slots": "exact canonical stable ascending population sort of every bit column",
                "contains_key": (
                    "keep the first legend column fixed and stable-sort only later bit columns "
                    "containing every foreground body row named by that legend"
                ),
            },
        },
        "programs": {
            mode: {
                "source": source,
                "sha256": _sha256(source.encode()),
                "normalized_sha256": _normalized_hash(source),
                "is_exact_canonical": mode == prototype.DEFAULT_SELECTION_MODE,
            }
            for mode, source in programs.items()
        },
        "prototype_source_sha256": {
            name: _sha256(path.read_bytes()) for name, path in source_paths.items()
        },
        "racket_runtime": runtime_identity,
        "input_uniqueness": {
            **{mode: len(set(hashes)) for mode, hashes in input_hashes.items()},
            "paired_inputs_equal": paired_inputs_equal,
        },
        "counts": {
            "settings": 2,
            "train_pairs_per_setting": 3,
            "query_pairs_per_setting": 4,
            "episode_pairs": len(checks),
            "racket_executions": len(checks) * len(programs),
            "distinguishing_demonstrations": sum(
                row["settings_distinct"] for row in demonstrations
            ),
            "public_parent_train_pairs": len(public_task["train"]),
        },
        "exact_disagreement": {
            "input": witness_input,
            "all_slots_output": prototype.apply_python(witness_input, "all_slots"),
            "contains_key_output": prototype.apply_python(witness_input, "contains_key"),
        },
        "checks": checks,
        "limitations": [
            "This is a proposed task-local prototype and is not wired into production generation, catalog selection, approval metadata, or training admission.",
            "The first bit column receives a new legend role only in contains_key episodes; the canonical all_slots setting remains byte-for-byte authoritative.",
            "Evidence covers two settings at one retained seed with three demonstrations and four queries per setting, not every lawful grid.",
            "Generated contains_key scenes guarantee three matching candidates and two nonmatching candidates; behavior outside that prototype domain is not claimed.",
            "Finite demonstrations distinguish the declared all_slots rival, not every possible participation or ordering rule.",
            "The public-task prediction is visible-rule evidence only; no private evaluation label was available or consulted.",
        ],
    }
    out_path = Path(args.out)

    if args.artifact_dir:
        artifact_dir = Path(args.artifact_dir)
        _prepare_artifact_dir(artifact_dir)
        files: dict[str, bytes] = {}
        public_manifest: dict[str, dict[str, str]] = {}
        seen_public_ids: set[str] = set()
        for mode, episode in episodes.items():
            stem = mode.replace("_", "-")
            files[f"{stem}.rkt"] = (programs[mode] + "\n").encode("utf-8")
            files[f"{stem}-private.json"] = (
                json.dumps(episode, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
            public = prototype.public_challenge(episode)
            public_id = public_challenge_id(public)
            if public_id in seen_public_ids:
                raise SystemExit("duplicate visible public challenge across settings")
            seen_public_ids.add(public_id)
            public_name = f"public-{public_id}.json"
            files[public_name] = public_challenge_bytes(public)
            public_manifest[mode] = {"public_id": public_id, "path": public_name}
        manifest = {
            "schema": "89ab40aedfe4-legend-selector-materialization-v1",
            "seed": args.seed,
            "public": public_manifest,
            "files": {},
        }
        for name, body in files.items():
            path = artifact_dir / name
            path.write_bytes(body)
            manifest["files"][name] = {
                "sha256": _sha256(body),
                "bytes": len(body),
            }
        _write_json(artifact_dir / "manifest.json", manifest)

    _write_json(out_path, report)
    print(json.dumps({"status": "passed", "out": str(out_path), "counts": report["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
