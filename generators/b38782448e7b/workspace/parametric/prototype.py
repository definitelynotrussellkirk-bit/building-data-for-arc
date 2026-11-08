#!/usr/bin/env python3
"""Proposed episode-level gate and third-colour variants for b38782448e7b.

The production generator and canonical rule remain unchanged.  This task-local
prototype chooses one of four nearby gated vertical-sweep rules exactly once per
episode, executes every label and rival prediction in Racket, and keeps hidden
settings, programs, and query answers out of public challenge files.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "b38782448e7b"
ROOT = find_root(__file__)
STATUS = "proposed task-local prototype; not production-approved"

GATE_MODES = ("different", "same")
THIRD_COLOR_MODES = ("overwrite", "preserve")
DEFAULT_GATE_MODE = "different"
DEFAULT_THIRD_COLOR_MODE = "overwrite"
SETTINGS = tuple(
    (gate_mode, third_color_mode)
    for gate_mode in GATE_MODES
    for third_color_mode in THIRD_COLOR_MODES
)
DEFAULT_SETTING = (DEFAULT_GATE_MODE, DEFAULT_THIRD_COLOR_MODE)
DEFAULT_DEMONSTRATION_COUNT = 3
DEFAULT_QUERY_COUNT = 4
MAX_EPISODE_PAIR_COUNT = 32
MAX_CANDIDATE_ATTEMPTS = 512

_GATE_ANCHOR = "(or (< hh 2) (!= (at g 0 c) (at g 1 c)))"
_SAME_GATE = "(or (< hh 2) (= (at g 0 c) (at g 1 c)))"
_BODY_ANCHOR = """                     (if (= (hash-ref result (list r c) 0) marker)
                         (hash-set! result (list r c) bg)
                         (hash-set! result (list r c) marker))"""
_PRESERVE_THIRD_BODY = """                     (let ((cell (hash-ref result (list r c) 0)))
                       (cond
                         ((= cell marker)
                          (hash-set! result (list r c) bg))
                         ((= cell bg)
                          (hash-set! result (list r c) marker))
                         (else
                          (hash-set! result (list r c) cell))))"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode()
    return sha256_bytes(payload)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_record(*, root: Path | str = ROOT) -> dict[str, Any]:
    root = Path(root)
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise ValueError(f"canonical task not found: {TASK_ID}")


def load_base_generator(*, root: Path | str = ROOT):
    return load_selected_generator(TASK_ID, root=Path(root))


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_index(index: int) -> None:
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")


def _validate_modes(gate_mode: str, third_color_mode: str) -> None:
    if type(gate_mode) is not str or gate_mode not in GATE_MODES:
        raise ValueError(f"gate_mode must be one of {GATE_MODES}, got {gate_mode!r}")
    if type(third_color_mode) is not str or third_color_mode not in THIRD_COLOR_MODES:
        raise ValueError(
            "third_color_mode must be one of "
            f"{THIRD_COLOR_MODES}, got {third_color_mode!r}"
        )


def _normalize_setting(setting: Sequence[str]) -> tuple[str, str]:
    if (
        not isinstance(setting, (tuple, list))
        or len(setting) != 2
        or type(setting[0]) is not str
        or type(setting[1]) is not str
    ):
        raise ValueError("setting must be a two-item (gate_mode, third_color_mode) sequence")
    gate_mode, third_color_mode = setting
    try:
        _validate_modes(gate_mode, third_color_mode)
    except ValueError as exc:
        raise ValueError(f"invalid setting: {exc}") from exc
    return gate_mode, third_color_mode


def setting_key(setting: Sequence[str]) -> str:
    gate_mode, third_color_mode = _normalize_setting(setting)
    return f"gate-{gate_mode}__third-{third_color_mode}"


def setting_record(setting: Sequence[str]) -> dict[str, str]:
    gate_mode, third_color_mode = _normalize_setting(setting)
    return {"gate_mode": gate_mode, "third_color_mode": third_color_mode}


def _validate_pair_counts(demonstration_count: int, query_count: int) -> None:
    for name, value in (
        ("demonstration_count", demonstration_count),
        ("query_count", query_count),
    ):
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive exact integer")
    total = demonstration_count + query_count
    if total > MAX_EPISODE_PAIR_COUNT:
        raise ValueError(
            f"episode requests {total} pairs; maximum is {MAX_EPISODE_PAIR_COUNT}"
        )


def program_for(
    gate_mode: str = DEFAULT_GATE_MODE,
    third_color_mode: str = DEFAULT_THIRD_COLOR_MODE,
    *,
    root: Path | str = ROOT,
) -> str:
    """Return exact canonical Racket or one bounded two-parameter variant."""
    _validate_modes(gate_mode, third_color_mode)
    canonical = canonical_record(root=root)["program_solution"]
    if canonical.count(_GATE_ANCHOR) != 1:
        raise ValueError("canonical gate anchor changed; prototype requires review")
    if canonical.count(_BODY_ANCHOR) != 1:
        raise ValueError("canonical body anchor changed; prototype requires review")

    program = canonical
    if gate_mode == "same":
        program = program.replace(_GATE_ANCHOR, _SAME_GATE, 1)
    if third_color_mode == "preserve":
        program = program.replace(_BODY_ANCHOR, _PRESERVE_THIRD_BODY, 1)
    return program


def _callable_text(program: str) -> str:
    return wrap_rule(program)


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def application(program: str, grid: list[list[int]]) -> str:
    return f"({_callable_text(program)} {_grid_literal(grid)})"


def execute(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    return bridge.eval_text(application(program, grid))


def select_setting(seed: int) -> tuple[str, str]:
    _validate_seed(seed)
    return SETTINGS[seed % len(SETTINGS)]


def prototype_input(
    seed: int,
    index: int,
    *,
    root: Path | str = ROOT,
) -> list[list[int]]:
    """Generate a lawful shared input exposing all four declared settings."""
    _validate_seed(seed)
    _validate_index(index)
    generator, _, _ = load_base_generator(root=root)
    input_seed = (seed * 1_000_003 + index * 97_409 + 0xB387824) & 0x7FFFFFFF
    sample_index = seed * 37 + index
    grid = generator.generate(
        input_seed,
        sample_index,
        difficulty="medium",
        grid_h=20 + ((seed + 3 * index) % 11),
        grid_w=20 + ((2 * seed + 5 * index) % 11),
        bg_color=(8 + seed + 7 * index) % 10,
        palette_size=4 + ((seed + index) % 4),
        n_markers=3 + ((seed + index) % 3),
        n_decoys=2 + ((seed + index) % 2),
    )
    analysis = generator._analysis(grid)
    if analysis["errors"]:
        raise RuntimeError("prototype input is outside canonical grammar")
    if len(analysis["markers"]) < 2 or len(analysis["decoys"]) < 2:
        raise RuntimeError("prototype input lacks both gate-polarity witness classes")
    bg = analysis["bg"]
    if not all(
        grid[1][col] not in (bg, grid[0][col])
        and grid[2][col] == grid[0][col]
        and grid[3][col] == bg
        for col in analysis["markers"]
    ):
        raise RuntimeError("different-gate controls lack overwrite/preserve witnesses")
    if not all(
        grid[1][col] == grid[0][col]
        and grid[2][col] not in (bg, grid[0][col])
        and grid[3][col] == bg
        for col in analysis["decoys"]
    ):
        raise RuntimeError("same-gate controls lack overwrite/preserve witnesses")
    return grid


def generate_episode(
    seed: int,
    bridge: RacketBridge,
    *,
    setting: Sequence[str] | None = None,
    demonstration_count: int = DEFAULT_DEMONSTRATION_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    root: Path | str = ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build one fixed-setting episode and evaluator-only Racket evidence."""
    _validate_seed(seed)
    _validate_pair_counts(demonstration_count, query_count)
    selected = select_setting(seed) if setting is None else _normalize_setting(setting)
    programs = {
        candidate: program_for(*candidate, root=root) for candidate in SETTINGS
    }

    requested = demonstration_count + query_count
    grids: list[list[list[int]]] = []
    outputs_by_pair: list[dict[tuple[str, str], list[list[int]]]] = []
    input_hashes: list[str] = []
    seen_inputs: set[str] = set()
    attempts = 0
    for candidate_index in range(MAX_CANDIDATE_ATTEMPTS):
        attempts += 1
        grid = prototype_input(seed, candidate_index, root=root)
        input_hash = grid_sha256(grid)
        if input_hash in seen_inputs:
            continue
        outputs = {
            candidate: execute(bridge, program, grid)
            for candidate, program in programs.items()
        }
        if len({grid_sha256(output) for output in outputs.values()}) != len(SETTINGS):
            continue
        seen_inputs.add(input_hash)
        input_hashes.append(input_hash)
        grids.append(grid)
        outputs_by_pair.append(outputs)
        if len(grids) == requested:
            break
    else:
        raise RuntimeError(
            f"could not sample {requested} distinct four-setting witnesses within "
            f"{MAX_CANDIDATE_ATTEMPTS} attempts"
        )

    selected_outputs = [outputs[selected] for outputs in outputs_by_pair]
    public = {
        "train": [
            {"input": deepcopy(grid), "output": deepcopy(output)}
            for grid, output in zip(
                grids[:demonstration_count],
                selected_outputs[:demonstration_count],
            )
        ],
        "test": [
            {"input": deepcopy(grid)} for grid in grids[demonstration_count:]
        ],
    }

    rival_checks: dict[str, Any] = {}
    executions: list[dict[str, Any]] = []
    for candidate in SETTINGS:
        candidate_outputs = [outputs[candidate] for outputs in outputs_by_pair]
        demo_diffs = [
            index
            for index in range(demonstration_count)
            if candidate_outputs[index] != selected_outputs[index]
        ]
        query_diffs = [
            index
            for index in range(query_count)
            if candidate_outputs[demonstration_count + index]
            != selected_outputs[demonstration_count + index]
        ]
        key = setting_key(candidate)
        rival_checks[key] = {
            "parameter": setting_record(candidate),
            "matches_all_demonstrations": not demo_diffs,
            "distinguishing_demo_indices": demo_diffs,
            "query_diff_indices": query_diffs,
            "demonstration_output_sha256": [
                grid_sha256(output) for output in candidate_outputs[:demonstration_count]
            ],
            "query_output_sha256": [
                grid_sha256(output) for output in candidate_outputs[demonstration_count:]
            ],
        }
        for pair_index, (grid, output) in enumerate(zip(grids, candidate_outputs)):
            executions.append(
                {
                    "setting": key,
                    "pair_index": pair_index,
                    "input_sha256": input_hashes[pair_index],
                    "output_sha256": grid_sha256(output),
                    "application_sha256": sha256_bytes(
                        application(programs[candidate], grid).encode()
                    ),
                }
            )

    survivors = [
        key
        for key, check in rival_checks.items()
        if check["matches_all_demonstrations"]
    ]
    selected_key = setting_key(selected)
    if survivors != [selected_key]:
        raise RuntimeError(f"demonstrations do not identify the selected setting: {survivors}")
    expected_query_diffs = list(range(query_count))
    for key, check in rival_checks.items():
        if key == selected_key:
            continue
        if check["query_diff_indices"] != expected_query_diffs:
            raise RuntimeError(f"query set does not separate rival setting {key}")

    private = {
        "schema": "b38782448e7b-parametric-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter_seed": seed,
        "parameter": setting_record(selected),
        "selection_scope": "once_per_episode",
        "demonstration_count": demonstration_count,
        "query_count": query_count,
        "candidate_attempts": attempts,
        "input_sha256": input_hashes,
        "selected_program_sha256": sha256_bytes(programs[selected].encode()),
        "program_sha256": {
            setting_key(candidate): sha256_bytes(program.encode())
            for candidate, program in programs.items()
        },
        "query_answers": deepcopy(selected_outputs[demonstration_count:]),
        "rival_checks": rival_checks,
        "executions": executions,
    }
    return public, private


def _validate_public_challenge(challenge: dict[str, Any]) -> None:
    if not isinstance(challenge, dict) or set(challenge) != {"train", "test"}:
        raise ValueError("public challenge must contain exactly train and test")
    if not isinstance(challenge["train"], list) or not challenge["train"]:
        raise ValueError("public challenge requires demonstrations")
    if not isinstance(challenge["test"], list) or not challenge["test"]:
        raise ValueError("public challenge requires queries")
    if any(not isinstance(pair, dict) or set(pair) != {"input", "output"} for pair in challenge["train"]):
        raise ValueError("public demonstrations must contain exactly input and output")
    if any(not isinstance(pair, dict) or set(pair) != {"input"} for pair in challenge["test"]):
        raise ValueError("public queries must contain input only")


def write_public_batch(
    challenges: Iterable[dict[str, Any]],
    out_dir: Path | str,
) -> list[dict[str, Any]]:
    """Write stable public files named by exact visible bytes, rejecting duplicates."""
    plans: list[tuple[str, bytes]] = []
    by_id: dict[str, bytes] = {}
    for challenge in challenges:
        _validate_public_challenge(challenge)
        payload = public_challenge_bytes(challenge)
        identifier = public_challenge_id(challenge)
        previous = by_id.get(identifier)
        if previous is not None:
            if previous == payload:
                raise ValueError(f"duplicate public payload: {identifier}")
            raise ValueError(f"public ID collision: {identifier}")
        by_id[identifier] = payload
        plans.append((identifier, payload))

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if any(out_dir.iterdir()):
        raise ValueError(f"public output directory is not empty: {out_dir}")
    rows = []
    for identifier, payload in sorted(plans):
        path = out_dir / f"challenge-{identifier}.json"
        path.write_bytes(payload)
        rows.append(
            {
                "public_id": identifier,
                "path": str(path),
                "public_sha256": sha256_bytes(payload),
            }
        )
    return rows


def _prepare_output_root(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise ValueError(f"evidence output directory is not empty: {out}")
    (out / "public").mkdir()
    (out / "private" / "episodes").mkdir(parents=True)
    (out / "private" / "rules").mkdir(parents=True)


def _manifest_episode_inventory(
    out: Path,
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return validated rows whose paths exactly cover the materialized episodes."""
    rows = manifest.get("episodes")
    if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError("evidence manifest episode inventory is missing or malformed")

    expected_public_paths: list[str] = []
    expected_private_paths: list[str] = []
    seeds: list[int] = []
    for row in rows:
        public_id = row.get("public_id")
        seed = row.get("seed")
        if type(public_id) is not str or type(seed) is not int or seed < 0:
            raise ValueError("evidence manifest episode inventory has an invalid ID or seed")
        public_path = f"public/challenge-{public_id}.json"
        private_path = f"private/episodes/{public_id}.json"
        if row.get("public_path") != public_path or row.get("private_path") != private_path:
            raise ValueError("evidence manifest episode inventory has a redirected path")
        expected_public_paths.append(public_path)
        expected_private_paths.append(private_path)
        seeds.append(seed)

    if (
        len(set(expected_public_paths)) != len(rows)
        or len(set(expected_private_paths)) != len(rows)
        or len(set(seeds)) != len(rows)
    ):
        raise ValueError("evidence manifest episode inventory contains duplicates")

    public_dir = out / "public"
    private_dir = out / "private" / "episodes"
    if not public_dir.is_dir() or not private_dir.is_dir():
        raise ValueError("evidence manifest episode inventory directories are missing")
    public_entries = list(public_dir.iterdir())
    private_entries = list(private_dir.iterdir())
    if any(not path.is_file() for path in [*public_entries, *private_entries]):
        raise ValueError("evidence manifest episode inventory contains a non-file entry")
    actual_public_paths = {
        path.relative_to(out).as_posix() for path in public_entries
    }
    actual_private_paths = {
        path.relative_to(out).as_posix() for path in private_entries
    }
    if (
        actual_public_paths != set(expected_public_paths)
        or actual_private_paths != set(expected_private_paths)
    ):
        raise ValueError("evidence manifest episode inventory does not match materialized files")
    return rows


def write_evidence(
    out: Path | str,
    *,
    seeds: Sequence[int] = (0, 1, 2, 3),
    demonstration_count: int = DEFAULT_DEMONSTRATION_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    root: Path | str = ROOT,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Materialize exact programs, private executions, and redacted public files."""
    out = Path(out)
    root = Path(root)
    _validate_pair_counts(demonstration_count, query_count)
    if not isinstance(seeds, (list, tuple)) or not seeds:
        raise ValueError("seeds must be a non-empty sequence")
    normalized_seeds = []
    for seed in seeds:
        _validate_seed(seed)
        normalized_seeds.append(seed)
    if len(set(normalized_seeds)) != len(normalized_seeds):
        raise ValueError("seeds must be distinct")
    _prepare_output_root(out)

    programs = {setting: program_for(*setting, root=root) for setting in SETTINGS}
    for setting, program in programs.items():
        (out / "private" / "rules" / f"{setting_key(setting)}.rkt").write_text(
            program,
            encoding="utf-8",
        )

    publics: list[dict[str, Any]] = []
    privates: list[dict[str, Any]] = []
    bridge_context = (
        nullcontext(bridge)
        if bridge is not None
        else RacketBridge(max_calls_before_restart=512)
    )
    with bridge_context as active_bridge:
        runtime_identity = active_bridge.runtime_identity
        for seed in normalized_seeds:
            public, private = generate_episode(
                seed,
                active_bridge,
                demonstration_count=demonstration_count,
                query_count=query_count,
                root=root,
            )
            publics.append(public)
            privates.append(private)

        canonical_checks = []
        default_program = programs[DEFAULT_SETTING]
        labeled_pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
        for pair_index, pair in enumerate(labeled_pairs):
            actual = execute(active_bridge, default_program, pair["input"])
            if actual != pair["output"]:
                raise RuntimeError(f"canonical default failed labeled pair {pair_index}")
            canonical_checks.append(
                {
                    "pair_index": pair_index,
                    "input_sha256": grid_sha256(pair["input"]),
                    "output_sha256": grid_sha256(actual),
                }
            )
        _write_json(out / "private" / "canonical-checks.json", canonical_checks)

        witness_input = prototype_input(0, 0, root=root)
        witness_outputs = {
            setting_key(setting): execute(active_bridge, program, witness_input)
            for setting, program in programs.items()
        }
        if len({grid_sha256(output) for output in witness_outputs.values()}) != len(SETTINGS):
            raise RuntimeError("shared witness failed to distinguish all settings")
        _write_json(
            out / "private" / "shared-witness.json",
            {"input": witness_input, "outputs": witness_outputs},
        )

    public_rows = write_public_batch(publics, out / "public")
    public_by_bytes = {
        public_challenge_bytes(public): public for public in publics
    }
    private_by_seed = {private["parameter_seed"]: private for private in privates}
    episode_rows = []
    for row in public_rows:
        payload = Path(row["path"]).read_bytes()
        public = public_by_bytes[payload]
        matching_private = next(
            private
            for private in privates
            if private["input_sha256"]
            == [
                grid_sha256(pair["input"])
                for pair in [*public["train"], *public["test"]]
            ]
        )
        public_id = row["public_id"]
        private_path = out / "private" / "episodes" / f"{public_id}.json"
        private_record = {
            **matching_private,
            "public_id": public_id,
            "public_sha256": row["public_sha256"],
            "public_path": f"public/challenge-{public_id}.json",
        }
        _write_json(private_path, private_record)
        episode_rows.append(
            {
                "seed": matching_private["parameter_seed"],
                "parameter": matching_private["parameter"],
                "public_id": public_id,
                "public_sha256": row["public_sha256"],
                "public_path": f"public/challenge-{public_id}.json",
                "private_path": f"private/episodes/{public_id}.json",
                "demonstration_count": demonstration_count,
                "query_count": query_count,
            }
        )
    episode_rows.sort(key=lambda row: row["public_id"])

    generator, generator_source, generator_sha256 = load_base_generator(root=root)
    del generator, private_by_seed
    prototype_path = Path(__file__).resolve()
    canonical = canonical_record(root=root)["program_solution"]
    manifest = {
        "schema": "b38782448e7b-parametric-gated-xor-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "settings": [setting_record(setting) for setting in SETTINGS],
        "canonical_default": setting_record(DEFAULT_SETTING),
        "canonical_default_unchanged": programs[DEFAULT_SETTING] == canonical,
        "demonstration_count": demonstration_count,
        "query_count": query_count,
        "program_sha256": {
            setting_key(setting): sha256_bytes(program.encode())
            for setting, program in programs.items()
        },
        "episodes": episode_rows,
        "generator_source": str(Path(generator_source).relative_to(root)),
        "generator_sha256": generator_sha256,
        "prototype_source": str(prototype_path.relative_to(root)),
        "prototype_source_sha256": sha256_bytes(prototype_path.read_bytes()),
        "canonical_file_sha256": sha256_bytes(canonical_path(root).read_bytes()),
        "canonical_pair_count": len(canonical_checks),
        "racket_runtime": runtime_identity,
        "limitations": [
            "prototype only; production remains pinned to different/overwrite",
            "finite evidence covers four declared settings and materialized seeds",
            "the sampler intentionally supplies explicit witnesses for both parameters",
        ],
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def verify_evidence(
    out: Path | str,
    *,
    root: Path | str = ROOT,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Fail closed on changed source, program, public bytes, or Racket replay."""
    out = Path(out)
    root = Path(root)
    manifest_path = out / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("missing evidence manifest")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema") != "b38782448e7b-parametric-gated-xor-evidence-v1":
        raise ValueError("unexpected evidence schema")
    if manifest.get("task_id") != TASK_ID:
        raise ValueError("evidence task ID mismatch")

    _, generator_source, generator_sha256 = load_base_generator(root=root)
    if manifest.get("generator_source") != str(Path(generator_source).relative_to(root)):
        raise ValueError("generator source path mismatch")
    if manifest.get("generator_sha256") != generator_sha256:
        raise ValueError("generator source hash mismatch")
    if manifest.get("prototype_source_sha256") != sha256_bytes(Path(__file__).read_bytes()):
        raise ValueError("prototype source hash mismatch")
    if manifest.get("canonical_file_sha256") != sha256_bytes(canonical_path(root).read_bytes()):
        raise ValueError("canonical file hash mismatch")
    episode_rows = _manifest_episode_inventory(out, manifest)

    programs = {setting: program_for(*setting, root=root) for setting in SETTINGS}
    for setting, program in programs.items():
        key = setting_key(setting)
        rule_path = out / "private" / "rules" / f"{key}.rkt"
        if not rule_path.is_file() or rule_path.read_text() != program:
            raise ValueError(f"rule bytes mismatch for {key}")
        if manifest["program_sha256"].get(key) != sha256_bytes(program.encode()):
            raise ValueError(f"rule hash mismatch for {key}")

    # Validate visible bytes before any expensive replay, including canonical
    # serialization and content-derived filename identity.
    for row in episode_rows:
        public_path = out / row["public_path"]
        if not public_path.is_file():
            raise ValueError(f"missing public challenge: {row['public_path']}")
        try:
            public = json.loads(public_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid public challenge: {row['public_path']}") from exc
        canonical_bytes = public_challenge_bytes(public)
        actual_bytes = public_path.read_bytes()
        if actual_bytes != canonical_bytes:
            raise ValueError(f"public bytes are not canonical: {row['public_path']}")
        identifier = public_challenge_id(public)
        if identifier != row["public_id"]:
            raise ValueError(f"public ID mismatch: {row['public_path']}")
        if public_path.name != f"challenge-{identifier}.json":
            raise ValueError(f"public filename mismatch: {row['public_path']}")
        if sha256_bytes(actual_bytes) != row["public_sha256"]:
            raise ValueError(f"public bytes hash mismatch: {row['public_path']}")
        _validate_public_challenge(public)

    execution_count = 0
    bridge_context = (
        nullcontext(bridge)
        if bridge is not None
        else RacketBridge(max_calls_before_restart=512)
    )
    with bridge_context as active_bridge:
        for row in episode_rows:
            private_path = out / row["private_path"]
            if not private_path.is_file():
                raise ValueError(f"missing private episode: {row['private_path']}")
            private = json.loads(private_path.read_text())
            expected_metadata = {
                "seed": private.get("parameter_seed"),
                "parameter": private.get("parameter"),
                "public_id": private.get("public_id"),
                "public_sha256": private.get("public_sha256"),
                "public_path": private.get("public_path"),
                "private_path": f"private/episodes/{private.get('public_id')}.json",
                "demonstration_count": private.get("demonstration_count"),
                "query_count": private.get("query_count"),
            }
            if any(row.get(key) != value for key, value in expected_metadata.items()):
                raise ValueError(
                    f"evidence manifest episode metadata mismatch: {row['private_path']}"
                )
            selected = _normalize_setting(
                (
                    private["parameter"]["gate_mode"],
                    private["parameter"]["third_color_mode"],
                )
            )
            public, regenerated_private = generate_episode(
                private["parameter_seed"],
                active_bridge,
                setting=selected,
                demonstration_count=private["demonstration_count"],
                query_count=private["query_count"],
                root=root,
            )
            execution_count += (
                private["demonstration_count"] + private["query_count"]
            ) * len(SETTINGS)
            public_path = out / row["public_path"]
            if public_path.read_bytes() != public_challenge_bytes(public):
                raise ValueError(f"public bytes differ from Racket replay: {row['public_path']}")
            expected_private = dict(private)
            for extra in ("public_id", "public_sha256", "public_path"):
                expected_private.pop(extra, None)
            if regenerated_private != expected_private:
                raise ValueError(f"private episode differs from Racket replay: {row['private_path']}")

        labeled_pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
        for pair_index, pair in enumerate(labeled_pairs):
            actual = execute(active_bridge, programs[DEFAULT_SETTING], pair["input"])
            execution_count += 1
            if actual != pair["output"]:
                raise ValueError(f"canonical default failed labeled pair {pair_index}")

    receipt = {
        "schema": "b38782448e7b-parametric-gated-xor-verification-v1",
        "status": "pass",
        "task_id": TASK_ID,
        "episode_count": len(episode_rows),
        "canonical_pair_count": len(labeled_pairs),
        "racket_execution_count": execution_count,
        "generator_sha256": generator_sha256,
        "prototype_source_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
    }
    return receipt


def _parse_setting(text: str | None) -> tuple[str, str] | None:
    if text is None:
        return None
    parts = text.split(",")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("setting must be GATE,THIRD")
    try:
        return _normalize_setting(parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    emit = subparsers.add_parser("emit", help="materialize public/private evidence")
    emit.add_argument("--out", type=Path, required=True)
    emit.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3])
    emit.add_argument("--demonstrations", type=int, default=DEFAULT_DEMONSTRATION_COUNT)
    emit.add_argument("--queries", type=int, default=DEFAULT_QUERY_COUNT)

    verify = subparsers.add_parser("verify", help="reexecute an evidence directory")
    verify.add_argument("evidence", type=Path)
    verify.add_argument("--out", type=Path)

    episode = subparsers.add_parser("episode", help="print one complete or public episode")
    episode.add_argument("--seed", type=int, required=True)
    episode.add_argument("--setting", type=_parse_setting)
    episode.add_argument("--demonstrations", type=int, default=DEFAULT_DEMONSTRATION_COUNT)
    episode.add_argument("--queries", type=int, default=DEFAULT_QUERY_COUNT)
    episode.add_argument("--public", action="store_true")
    episode.add_argument("--out", type=Path)

    args = parser.parse_args(argv)
    if args.command == "emit":
        manifest = write_evidence(
            args.out,
            seeds=args.seeds,
            demonstration_count=args.demonstrations,
            query_count=args.queries,
        )
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    if args.command == "verify":
        receipt = verify_evidence(args.evidence)
        text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0

    with RacketBridge(max_calls_before_restart=512) as bridge:
        public, private = generate_episode(
            args.seed,
            bridge,
            setting=args.setting,
            demonstration_count=args.demonstrations,
            query_count=args.queries,
        )
    payload = public if args.public else {"public": public, "private": private}
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
