#!/usr/bin/env python3
"""Task-local parametric rule prototype for ARC family 78e3f26e92aa.

The production generator and canonical authority remain unchanged.  This module
constructs episode-fixed variants of the same two-bar-pair reasoning:

* ``step_multiplier``: move outward every ``bar_height * multiplier`` rows.
  ``1`` is the exact canonical rule; ``2`` is a slower nearby variant.
* ``overlap_color``: color cells reached by both ray systems. ``6`` is the
  canonical value; ``2`` is the proposed alternative.

Inputs remain on the canonical-shaped generator manifold for every setting.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "78e3f26e92aa"
SCHEMA = "arcpuzzles-parametric-prototype-v1"
CANONICAL_STEP_MULTIPLIER = 1
CANONICAL_OVERLAP_COLOR = 6
MAX_QUERY_COUNT = 4
MAX_DEMO_COUNT = 8
ROOT = Path(find_root(__file__)).resolve()
CANONICAL_GENERATOR, CANONICAL_GENERATOR_PATH, CANONICAL_GENERATOR_SHA256 = (
    load_selected_generator(TASK_ID, root=ROOT)
)


class Setting:
    """One immutable rule setting, fixed across an episode."""

    __slots__ = ("step_multiplier", "overlap_color", "_locked")

    def __init__(self, step_multiplier: int, overlap_color: int):
        if type(step_multiplier) is not int:
            raise TypeError("step_multiplier must be an integer (not bool)")
        if type(overlap_color) is not int:
            raise TypeError("overlap_color must be an integer (not bool)")
        if step_multiplier not in (1, 2):
            raise ValueError("step_multiplier must be 1 or 2")
        if overlap_color not in (6, 2):
            raise ValueError("overlap_color must be 6 or 2")
        object.__setattr__(self, "step_multiplier", step_multiplier)
        object.__setattr__(self, "overlap_color", overlap_color)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name, value):  # pragma: no cover - defensive immutability
        if getattr(self, "_locked", False):
            raise AttributeError("Setting is immutable")
        object.__setattr__(self, name, value)

    def __repr__(self) -> str:
        return (
            f"Setting(step_multiplier={self.step_multiplier}, "
            f"overlap_color={self.overlap_color})"
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Setting)
            and self.step_multiplier == other.step_multiplier
            and self.overlap_color == other.overlap_color
        )

    def __hash__(self) -> int:
        return hash((self.step_multiplier, self.overlap_color))

    def as_dict(self) -> dict[str, int]:
        return {
            "step_multiplier": self.step_multiplier,
            "overlap_color": self.overlap_color,
        }


ALLOWED_SETTINGS = (
    Setting(1, 6),
    Setting(2, 6),
    Setting(1, 2),
    Setting(2, 2),
)
CANONICAL_SETTING = ALLOWED_SETTINGS[0]


def setting_for_seed(seed: int) -> Setting:
    """Choose one rule setting deterministically once for an episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    return ALLOWED_SETTINGS[seed % len(ALLOWED_SETTINGS)]


@lru_cache(maxsize=1)
def canonical_program() -> str:
    """Load the exact canonical program bytes for the assigned task."""
    ledger = canonical_path(ROOT)
    matches: list[str] = []
    with Path(ledger).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if isinstance(program, str) and program:
                    matches.append(program)
    unique = list(dict.fromkeys(matches))
    if len(unique) != 1:
        raise RuntimeError(f"expected one canonical program for {TASK_ID}, found {len(unique)}")
    return unique[0]


def racket_program(setting: Setting) -> str:
    """Materialize the exact legacy Racket rule for one proposed setting."""
    if not isinstance(setting, Setting):
        raise TypeError("setting must be a Setting")
    program = canonical_program()
    if setting.step_multiplier != 1:
        positive = "(quotient dr bh)"
        negative = "(quotient (+ (- 0 dr) (- bh 1)) bh)"
        if program.count(positive) != 1 or program.count(negative) != 1:
            raise RuntimeError("canonical step expression changed; inspect before deriving variant")
        period = f"(* bh {setting.step_multiplier})"
        program = program.replace(positive, f"(quotient dr {period})", 1)
        program = program.replace(
            negative,
            f"(quotient (+ (- 0 dr) (- {period} 1)) {period})",
            1,
        )
    if setting.overlap_color != 6:
        marker = "(cond ((and has-g has-c) 6) (has-g 3)"
        if program.count(marker) != 1:
            raise RuntimeError("canonical overlap expression changed; inspect before deriving variant")
        program = program.replace(
            marker,
            f"(cond ((and has-g has-c) {setting.overlap_color}) (has-g 3)",
            1,
        )
    return program


def program_sha256(setting: Setting) -> str:
    return hashlib.sha256(racket_program(setting).encode("utf-8")).hexdigest()


def _bar_descriptor(grid: Sequence[Sequence[int]], color: int) -> tuple[int, int, int, int]:
    cells = [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == color
    ]
    if not cells:
        raise ValueError(f"color {color} is absent")
    row1 = min(row for row, _ in cells)
    row2 = max(row for row, _ in cells)
    left_col = min(col for _, col in cells)
    right_col = max(col for _, col in cells)
    return row1, row2 - row1 + 1, left_col, right_col


def _step_for_row(row1: int, period: int, row: int) -> int:
    delta = row - row1
    if delta >= 0:
        return delta // period
    return (-delta + period - 1) // period


def python_mirror(grid: Sequence[Sequence[int]], setting: Setting) -> list[list[int]]:
    """Independent Python mirror used for selection and parity checks."""
    if not isinstance(setting, Setting):
        raise TypeError("setting must be a Setting")
    errors = CANONICAL_GENERATOR.self_check(grid)
    if errors:
        raise ValueError("input is outside the canonical-shaped support: " + "; ".join(errors))
    h = len(grid)
    w = len(grid[0])
    green = _bar_descriptor(grid, 3)
    cyan = _bar_descriptor(grid, 8)
    output = [[0 for _ in range(w)] for _ in range(h)]
    for row in range(h):
        for col in range(w):
            reached: list[bool] = []
            for row1, bar_height, left_col, right_col in (green, cyan):
                period = bar_height * setting.step_multiplier
                step = _step_for_row(row1, period, row)
                reached.append(col == left_col - step or col == right_col + step)
            has_green, has_cyan = reached
            if has_green and has_cyan:
                output[row][col] = setting.overlap_color
            elif has_green:
                output[row][col] = 3
            elif has_cyan:
                output[row][col] = 8
    return output


def python_labeler(grids: Sequence[Sequence[Sequence[int]]], setting: Setting) -> list[list[list[int]]]:
    return [python_mirror(grid, setting) for grid in grids]


def _input_key(grid: Sequence[Sequence[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"), ensure_ascii=False)


def _validate_count(name: str, value: int, *, maximum: int) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not bool)")
    if not 1 <= value <= maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}")


def _candidate_inputs(seed: int, *, limit: int = 256) -> list[list[list[int]]]:
    """Return deterministic, unique canonical-shaped inputs for authoring."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    result: list[list[list[int]]] = []
    seen: set[str] = set()
    difficulties = ("easy", "medium", "hard")
    for index in range(limit):
        grid = CANONICAL_GENERATOR.generate(
            seed + 104729 * index,
            index,
            difficulty=difficulties[index % len(difficulties)],
        )
        key = _input_key(grid)
        if key in seen:
            continue
        seen.add(key)
        result.append(grid)
    return result


def _rivals(setting: Setting) -> tuple[Setting, ...]:
    return tuple(candidate for candidate in ALLOWED_SETTINGS if candidate != setting)


def _coverage(grid: Sequence[Sequence[int]], setting: Setting) -> set[Setting]:
    target = python_mirror(grid, setting)
    return {
        rival
        for rival in _rivals(setting)
        if python_mirror(grid, rival) != target
    }


def lesson_ambiguities(
    demonstrations: Sequence[dict[str, Any]],
    query: dict[str, Any],
    setting: Setting,
) -> list[str]:
    """Report rival settings that fit demos but change this query."""
    if not demonstrations:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must be a labeled pair"]
    for index, pair in enumerate(demonstrations):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demonstration {index} is not a labeled pair"]
    reasons: list[str] = []
    for rival in _rivals(setting):
        if all(python_mirror(pair["input"], rival) == pair["output"] for pair in demonstrations):
            if python_mirror(query["input"], rival) != query["output"]:
                reasons.append(f"{rival.as_dict()} fits every demonstration but changes the query")
    return reasons


def build_episode(
    seed: int,
    setting: Setting | None = None,
    *,
    demo_count: int = 3,
    query_count: int = 4,
    labeler: Callable[[Sequence[Sequence[Sequence[int]]], Setting], list[list[list[int]]]] = python_labeler,
    candidate_limit: int = 256,
) -> dict[str, Any]:
    """Build one deterministic, identifiable episode with a fixed setting."""
    _validate_count("demo_count", demo_count, maximum=MAX_DEMO_COUNT)
    _validate_count("query_count", query_count, maximum=MAX_QUERY_COUNT)
    if setting is None:
        setting = setting_for_seed(seed)
    if not isinstance(setting, Setting):
        raise TypeError("setting must be a Setting or None")
    if not callable(labeler):
        raise TypeError("labeler must be callable")

    candidates = _candidate_inputs(seed, limit=candidate_limit)
    rival_order = _rivals(setting)
    unresolved = set(rival_order)
    selected_demo_indices: list[int] = []
    used: set[int] = set()

    while unresolved and len(selected_demo_indices) < demo_count:
        best_index = None
        best_gain: set[Setting] = set()
        for index, grid in enumerate(candidates):
            if index in used:
                continue
            gain = _coverage(grid, setting) & unresolved
            if len(gain) > len(best_gain):
                best_index = index
                best_gain = gain
        if best_index is None or not best_gain:
            break
        selected_demo_indices.append(best_index)
        used.add(best_index)
        unresolved -= best_gain

    if unresolved:
        raise ValueError(
            "demo_count does not identify the setting; unresolved rivals: "
            + ", ".join(repr(rival) for rival in rival_order if rival in unresolved)
        )

    for index, grid in enumerate(candidates):
        if len(selected_demo_indices) >= demo_count:
            break
        if index in used:
            continue
        if _coverage(grid, setting):
            selected_demo_indices.append(index)
            used.add(index)
    if len(selected_demo_indices) != demo_count:
        raise ValueError(f"could not construct {demo_count} distinct demonstrations")

    selected_query_indices: list[int] = []
    for index, grid in enumerate(candidates):
        if len(selected_query_indices) >= query_count:
            break
        if index in used:
            continue
        if not _coverage(grid, setting):
            continue
        selected_query_indices.append(index)
        used.add(index)
    if len(selected_query_indices) != query_count:
        raise ValueError(f"could not construct {query_count} distinct discriminating queries")

    selected_indices = selected_demo_indices + selected_query_indices
    selected_grids = [candidates[index] for index in selected_indices]
    outputs = labeler(selected_grids, setting)
    if not isinstance(outputs, list) or len(outputs) != len(selected_grids):
        raise ValueError("labeler must return one output grid per input")
    for position, (grid, output) in enumerate(zip(selected_grids, outputs)):
        expected = python_mirror(grid, setting)
        if output != expected:
            raise ValueError(f"labeler mismatch at selected pair {position}")

    labeled = [
        {"input": grid, "output": output}
        for grid, output in zip(selected_grids, outputs)
    ]
    train = labeled[:demo_count]
    test = labeled[demo_count:]
    refuted = [
        rival
        for rival in rival_order
        if any(python_mirror(pair["input"], rival) != pair["output"] for pair in train)
    ]
    if tuple(refuted) != rival_order:
        raise AssertionError("constructed demonstrations do not refute every rival setting")
    for query in test:
        reasons = lesson_ambiguities(train, query, setting)
        if reasons:
            raise AssertionError("constructed query is ambiguous: " + "; ".join(reasons))

    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "seed": seed,
        "setting": setting.as_dict(),
        "default_setting": CANONICAL_SETTING.as_dict(),
        "input_constraints_depend_on_parameters": False,
        "demo_count": demo_count,
        "query_count": query_count,
        "program": racket_program(setting),
        "program_sha256": program_sha256(setting),
        "generator_source": str(CANONICAL_GENERATOR_PATH.relative_to(ROOT)),
        "generator_sha256": CANONICAL_GENERATOR_SHA256,
        "candidate_limit": candidate_limit,
        "selected_candidate_indices": selected_indices,
        "refuted_settings": [rival.as_dict() for rival in refuted],
        "train": train,
        "test": test,
    }


RACKET_RECEIPT_SCHEMA = "arcpuzzles-parametric-racket-receipt-v1"
EXPORT_SCHEMA = "arcpuzzles-parametric-export-v1"
SETTING_ALIASES = {
    "canonical": CANONICAL_SETTING,
    "slow": ALLOWED_SETTINGS[1],
    "recolor": ALLOWED_SETTINGS[2],
    "slow-recolor": ALLOWED_SETTINGS[3],
}


def _canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _value_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def public_episode_bytes(episode: dict[str, Any]) -> bytes:
    """Return the shared source-bound public projection for one episode."""
    return public_challenge_bytes(episode)


def public_episode_id(episode: dict[str, Any]) -> str:
    """Return the SHA-256 content ID of exactly :func:`public_episode_bytes`."""
    return public_challenge_id(episode)


def execute_racket_labels(
    grids: Sequence[Sequence[Sequence[int]]],
    setting: Setting,
) -> dict[str, Any]:
    """Execute the setting's exact Racket rule and return outputs plus receipt."""
    if not isinstance(setting, Setting):
        raise TypeError("setting must be a Setting")
    if type(grids) not in (list, tuple) or not grids:
        raise ValueError("grids must be a nonempty list or tuple")
    normalized = [normalize_grid(grid) for grid in grids]

    # Import lazily so pure construction and projection remain usable without a
    # configured Racket runtime. The packet wrapper supplies the protected
    # runtime for this execution boundary.
    from arc_repl.executor import ArcExecutor

    program = racket_program(setting)
    task = {"train": [], "test": [{"input": grid} for grid in normalized]}
    outputs: list[list[list[int]]] = []
    applications: list[dict[str, Any]] = []
    with ArcExecutor(task, use_racket=True) as executor:
        runtime = executor.runtime_identity
        if runtime.get("backend") != "racket" or runtime.get("protected") is not True:
            raise RuntimeError("protected Racket runtime is required")
        rule_response = executor.step(program)
        if "ERROR" in rule_response:
            raise RuntimeError(f"Racket rejected rule: {rule_response}")
        for index in range(len(normalized)):
            command = f"(apply! {index})"
            response = executor.step(command)
            if "ERROR" in response:
                raise RuntimeError(f"Racket apply failed for test {index}: {response}")
            refs = executor.state_summary["applied_results"].get(index, [])
            if len(refs) != 1:
                raise RuntimeError(f"expected one Racket result for test {index}, found {len(refs)}")
            result_ref = refs[0]
            result = executor._results.get(result_ref)  # task-local bridge adapter
            data = getattr(result, "data", None)
            output = normalize_grid(data)
            outputs.append(output)
            applications.append(
                {
                    "test_index": index,
                    "command": command,
                    "response": response,
                    "result_ref": result_ref,
                    "output_sha256": _value_sha256(output),
                }
            )

    return {
        "outputs": outputs,
        "receipt": {
            "schema": RACKET_RECEIPT_SCHEMA,
            "task_id": TASK_ID,
            "setting": setting.as_dict(),
            "program": program,
            "program_sha256": hashlib.sha256(program.encode("utf-8")).hexdigest(),
            "runtime": runtime,
            "rule_response": rule_response,
            "applications": applications,
        },
    }


class RacketLabeler:
    """Callable labeler that retains one protected-Racket receipt per call."""

    def __init__(self):
        self.receipts: list[dict[str, Any]] = []

    def __call__(
        self,
        grids: Sequence[Sequence[Sequence[int]]],
        setting: Setting,
    ) -> list[list[list[int]]]:
        execution = execute_racket_labels(grids, setting)
        self.receipts.append(execution["receipt"])
        return execution["outputs"]


def _validate_receipt(episode: dict[str, Any], receipt: dict[str, Any] | None) -> None:
    if receipt is None:
        return
    if not isinstance(receipt, dict):
        raise TypeError("each receipt must be a dictionary or None")
    expected = {
        "task_id": episode.get("task_id"),
        "setting": episode.get("setting"),
        "program_sha256": episode.get("program_sha256"),
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError(f"Racket receipt {key} does not match its episode")


def write_batch(
    episodes: Sequence[dict[str, Any]],
    output_dir: str | Path,
    *,
    receipts: Sequence[dict[str, Any] | None] | None = None,
) -> dict[str, Any]:
    """Write opaque public challenges and complete private authoring evidence.

    Duplicate detection happens before creating any output directories, so a
    hidden-metadata-only duplicate cannot silently overwrite a public challenge.
    """
    if type(episodes) not in (list, tuple) or not episodes:
        raise ValueError("episodes must be a nonempty list or tuple")
    if receipts is None:
        receipt_list: list[dict[str, Any] | None] = [None] * len(episodes)
    elif type(receipts) not in (list, tuple) or len(receipts) != len(episodes):
        raise ValueError("receipts must contain exactly one entry per episode")
    else:
        receipt_list = list(receipts)

    prepared: list[tuple[dict[str, Any], dict[str, Any] | None, str, bytes]] = []
    seen_ids: set[str] = set()
    for index, (episode, receipt) in enumerate(zip(episodes, receipt_list)):
        if not isinstance(episode, dict):
            raise TypeError(f"episode {index} must be a dictionary")
        if episode.get("task_id") != TASK_ID:
            raise ValueError(f"episode {index} belongs to another task")
        _validate_receipt(episode, receipt)
        public_bytes = public_episode_bytes(episode)
        public_id = hashlib.sha256(public_bytes).hexdigest()
        if public_id in seen_ids:
            raise ValueError(f"duplicate visible payload: {public_id}")
        seen_ids.add(public_id)
        prepared.append((episode, receipt, public_id, public_bytes))

    prepared.sort(key=lambda item: item[2])

    destination = Path(output_dir)
    if destination.exists():
        if not destination.is_dir():
            raise ValueError(f"output path is not a directory: {destination}")
        if any(destination.iterdir()):
            raise FileExistsError(f"output directory must be empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    public_dir = destination / "public"
    private_dir = destination / "private"
    public_dir.mkdir()
    private_dir.mkdir()

    entries: list[dict[str, Any]] = []
    for episode, receipt, public_id, public_bytes in prepared:
        public_relative = Path("public") / f"{public_id}.json"
        private_relative = Path("private") / f"{public_id}.private.json"
        (destination / public_relative).write_bytes(public_bytes)
        private_record = {
            "schema": EXPORT_SCHEMA,
            "public_id": public_id,
            "public_bytes_sha256": hashlib.sha256(public_bytes).hexdigest(),
            "episode": episode,
            "racket_receipt": receipt,
        }
        (destination / private_relative).write_text(
            json.dumps(private_record, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        entries.append(
            {
                "public_id": public_id,
                "public_path": public_relative.as_posix(),
                "private_path": private_relative.as_posix(),
                "seed": episode.get("seed"),
                "setting": episode.get("setting"),
                "demo_count": episode.get("demo_count"),
                "query_count": episode.get("query_count"),
                "program_sha256": episode.get("program_sha256"),
                "racket_receipt_present": receipt is not None,
            }
        )

    source_path = Path(__file__).resolve()
    manifest = {
        "schema": EXPORT_SCHEMA,
        "task_id": TASK_ID,
        "episode_count": len(entries),
        "setting_fixed_per_episode": True,
        "canonical_default": CANONICAL_SETTING.as_dict(),
        "public_projection": "reviewer_support.public_challenge_bytes",
        "public_identifier": "sha256(public_challenge_bytes)",
        "public_identifier_status": "source-bound-visible-bytes-v1",
        "prototype_source": str(source_path.relative_to(ROOT)),
        "prototype_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "canonical_generator_source": str(CANONICAL_GENERATOR_PATH.relative_to(ROOT)),
        "canonical_generator_sha256": CANONICAL_GENERATOR_SHA256,
        "episodes": entries,
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


VERIFICATION_SCHEMA = "arcpuzzles-parametric-verification-v1"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_batch(output_dir: str | Path) -> dict[str, Any]:
    """Offline verification for a batch written by :func:`write_batch`."""
    destination = Path(output_dir).resolve()
    manifest_path = destination / "manifest.json"
    _require(manifest_path.is_file() and not manifest_path.is_symlink(), "manifest is missing or unsafe")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _require(manifest.get("schema") == EXPORT_SCHEMA, "manifest schema mismatch")
    _require(manifest.get("task_id") == TASK_ID, "manifest task_id mismatch")
    entries = manifest.get("episodes")
    _require(type(entries) is list and entries, "manifest must contain episodes")
    _require(manifest.get("episode_count") == len(entries), "manifest episode_count mismatch")
    _require(manifest.get("setting_fixed_per_episode") is True, "fixed-setting declaration missing")
    _require(manifest.get("canonical_default") == CANONICAL_SETTING.as_dict(), "canonical default mismatch")

    source_path = Path(__file__).resolve()
    _require(
        manifest.get("prototype_source") == str(source_path.relative_to(ROOT)),
        "prototype source path mismatch",
    )
    _require(
        manifest.get("prototype_sha256") == hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "prototype source hash mismatch",
    )
    _require(
        manifest.get("canonical_generator_source")
        == str(CANONICAL_GENERATOR_PATH.relative_to(ROOT)),
        "canonical generator source path mismatch",
    )
    _require(
        manifest.get("canonical_generator_sha256") == CANONICAL_GENERATOR_SHA256,
        "canonical generator source hash mismatch",
    )

    expected_public_files: set[str] = set()
    expected_private_files: set[str] = set()
    public_ids: list[str] = []
    settings: list[dict[str, int]] = []
    seen_ids: set[str] = set()

    for entry_index, entry in enumerate(entries):
        _require(isinstance(entry, dict), f"manifest episode {entry_index} is not an object")
        public_id = entry.get("public_id")
        _require(
            isinstance(public_id, str)
            and len(public_id) == 64
            and all(char in "0123456789abcdef" for char in public_id),
            f"manifest episode {entry_index} has invalid public_id",
        )
        _require(public_id not in seen_ids, f"duplicate public content ID: {public_id}")
        seen_ids.add(public_id)
        public_ids.append(public_id)

        public_relative = f"public/{public_id}.json"
        private_relative = f"private/{public_id}.private.json"
        _require(entry.get("public_path") == public_relative, f"public path mismatch for {public_id}")
        _require(entry.get("private_path") == private_relative, f"private path mismatch for {public_id}")
        expected_public_files.add(f"{public_id}.json")
        expected_private_files.add(f"{public_id}.private.json")

        public_path = destination / public_relative
        private_path = destination / private_relative
        _require(public_path.is_file() and not public_path.is_symlink(), f"public file missing or unsafe: {public_id}")
        _require(private_path.is_file() and not private_path.is_symlink(), f"private file missing or unsafe: {public_id}")
        public_bytes = public_path.read_bytes()
        _require(hashlib.sha256(public_bytes).hexdigest() == public_id, f"public content ID mismatch for {public_id}")

        private = json.loads(private_path.read_text(encoding="utf-8"))
        _require(private.get("schema") == EXPORT_SCHEMA, f"private schema mismatch for {public_id}")
        _require(private.get("public_id") == public_id, f"private public_id mismatch for {public_id}")
        _require(private.get("public_bytes_sha256") == public_id, f"private public hash mismatch for {public_id}")
        episode = private.get("episode")
        receipt = private.get("racket_receipt")
        _require(isinstance(episode, dict), f"private episode missing for {public_id}")
        _require(public_episode_bytes(episode) == public_bytes, f"public bytes mismatch for {public_id}")
        _require(public_episode_id(episode) == public_id, f"public content ID mismatch for {public_id}")

        _require(episode.get("task_id") == TASK_ID, f"episode task_id mismatch for {public_id}")
        setting_data = episode.get("setting")
        _require(isinstance(setting_data, dict), f"setting missing for {public_id}")
        try:
            setting = Setting(
                setting_data.get("step_multiplier"),
                setting_data.get("overlap_color"),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid setting for {public_id}: {exc}") from exc
        settings.append(setting.as_dict())
        _require(episode.get("default_setting") == CANONICAL_SETTING.as_dict(), f"default setting mismatch for {public_id}")
        _require(episode.get("input_constraints_depend_on_parameters") is False, f"input constraint declaration mismatch for {public_id}")
        seed = episode.get("seed")
        _require(type(seed) is int and seed >= 0, f"invalid seed for {public_id}")
        _require(setting_for_seed(seed) == setting, f"seed does not select setting for {public_id}")
        _require(entry.get("seed") == seed, f"manifest seed mismatch for {public_id}")
        _require(entry.get("setting") == setting.as_dict(), f"manifest setting mismatch for {public_id}")

        train = episode.get("train")
        test = episode.get("test")
        _require(type(train) is list and type(test) is list, f"pair lists missing for {public_id}")
        _require(episode.get("demo_count") == len(train), f"demo count mismatch for {public_id}")
        _require(episode.get("query_count") == len(test), f"query count mismatch for {public_id}")
        _require(entry.get("demo_count") == len(train), f"manifest demo count mismatch for {public_id}")
        _require(entry.get("query_count") == len(test), f"manifest query count mismatch for {public_id}")
        _validate_count("demo_count", len(train), maximum=MAX_DEMO_COUNT)
        _validate_count("query_count", len(test), maximum=MAX_QUERY_COUNT)

        program = episode.get("program")
        _require(program == racket_program(setting), f"Racket program mismatch for {public_id}")
        program_hash = hashlib.sha256(program.encode("utf-8")).hexdigest()
        _require(episode.get("program_sha256") == program_hash, f"episode program hash mismatch for {public_id}")
        _require(entry.get("program_sha256") == program_hash, f"manifest program hash mismatch for {public_id}")
        _require(episode.get("generator_sha256") == CANONICAL_GENERATOR_SHA256, f"generator hash mismatch for {public_id}")

        pairs = train + test
        input_keys: set[str] = set()
        for pair_index, pair in enumerate(pairs):
            _require(isinstance(pair, dict), f"pair {pair_index} is invalid for {public_id}")
            grid = normalize_grid(pair.get("input"))
            output = normalize_grid(pair.get("output"))
            key = _input_key(grid)
            _require(key not in input_keys, f"duplicate input in episode {public_id}")
            input_keys.add(key)
            errors = CANONICAL_GENERATOR.self_check(grid)
            _require(not errors, f"input {pair_index} leaves canonical support for {public_id}: {'; '.join(errors)}")
            _require(output == python_mirror(grid, setting), f"Python parity mismatch at pair {pair_index} for {public_id}")

        expected_refuted = [rival.as_dict() for rival in _rivals(setting)]
        _require(episode.get("refuted_settings") == expected_refuted, f"refuted settings mismatch for {public_id}")
        for query_index, query in enumerate(test):
            reasons = lesson_ambiguities(train, query, setting)
            _require(not reasons, f"query {query_index} is ambiguous for {public_id}: {'; '.join(reasons)}")

        _require(isinstance(receipt, dict), f"Racket receipt missing for {public_id}")
        _require(entry.get("racket_receipt_present") is True, f"manifest receipt flag mismatch for {public_id}")
        _require(receipt.get("schema") == RACKET_RECEIPT_SCHEMA, f"receipt schema mismatch for {public_id}")
        _validate_receipt(episode, receipt)
        _require(receipt.get("program") == program, f"receipt program mismatch for {public_id}")
        runtime = receipt.get("runtime")
        _require(
            isinstance(runtime, dict)
            and runtime.get("backend") == "racket"
            and runtime.get("protected") is True,
            f"protected Racket identity missing for {public_id}",
        )
        _require("ERROR" not in str(receipt.get("rule_response", "ERROR")), f"Racket rule failed for {public_id}")
        applications = receipt.get("applications")
        _require(type(applications) is list and len(applications) == len(pairs), f"Racket application count mismatch for {public_id}")
        for pair_index, (pair, application) in enumerate(zip(pairs, applications)):
            _require(isinstance(application, dict), f"invalid Racket application {pair_index} for {public_id}")
            _require(application.get("test_index") == pair_index, f"Racket test index mismatch for {public_id}")
            _require(application.get("command") == f"(apply! {pair_index})", f"Racket command mismatch for {public_id}")
            _require("ERROR" not in str(application.get("response", "ERROR")), f"Racket application failed for {public_id}")
            _require(str(application.get("result_ref", "")).startswith("_"), f"Racket result ref missing for {public_id}")
            _require(application.get("output_sha256") == _value_sha256(pair["output"]), f"Racket output hash mismatch at pair {pair_index} for {public_id}")

    _require(public_ids == sorted(public_ids), "manifest episodes must be sorted by public_id")

    public_dir = destination / "public"
    private_dir = destination / "private"
    _require(public_dir.is_dir() and not public_dir.is_symlink(), "public directory missing or unsafe")
    _require(private_dir.is_dir() and not private_dir.is_symlink(), "private directory missing or unsafe")
    actual_public_files = {path.name for path in public_dir.iterdir() if path.is_file()}
    actual_private_files = {path.name for path in private_dir.iterdir() if path.is_file()}
    _require(actual_public_files == expected_public_files, "unexpected or missing public files")
    _require(actual_private_files == expected_private_files, "unexpected or missing private files")

    return {
        "schema": VERIFICATION_SCHEMA,
        "status": "pass",
        "task_id": TASK_ID,
        "episode_count": len(entries),
        "public_ids": public_ids,
        "settings": settings,
        "checks": {
            "source_hashes": "pass",
            "public_projection": "pass",
            "input_uniqueness_and_support": "pass",
            "python_parity": "pass",
            "demo_identifiability": "pass",
            "protected_racket_receipts": "pass",
        },
    }


def _settings_for_cli(name: str) -> tuple[Setting, ...]:
    if name == "all":
        return ALLOWED_SETTINGS
    return (SETTING_ALIASES[name],)


def _episode_seed(batch_seed: int, setting: Setting) -> int:
    """Bind each explicit setting to a seed that selects it deterministically."""
    if type(batch_seed) is not int or batch_seed < 0:
        raise ValueError("seed must be a non-negative integer")
    index = ALLOWED_SETTINGS.index(setting)
    result = batch_seed * len(ALLOWED_SETTINGS) + index
    if setting_for_seed(result) != setting:  # defensive contract check
        raise AssertionError("derived episode seed does not select requested setting")
    return result


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="build protected-Racket-labeled episodes")
    build.add_argument("--seed", type=int, required=True, help="non-negative deterministic batch seed")
    build.add_argument(
        "--setting",
        choices=("all", *SETTING_ALIASES),
        default="all",
        help="one named setting or all four (default: all)",
    )
    build.add_argument("--demo-count", type=int, default=3)
    build.add_argument("--query-count", type=int, default=4)
    build.add_argument("--out", type=Path, required=True)
    verify = subparsers.add_parser("verify", help="verify an exported batch offline")
    verify.add_argument("--input", type=Path, required=True)
    verify.add_argument("--report", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_cli_parser().parse_args(argv)
    if args.command == "verify":
        report = verify_batch(args.input)
        if args.report is not None:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(
                json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(report, sort_keys=True))
        return 0
    if args.command != "build":  # pragma: no cover - argparse enforces this
        raise AssertionError(args.command)
    if args.seed < 0:
        raise ValueError("seed must be non-negative")

    episodes: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    for setting in _settings_for_cli(args.setting):
        episode_seed = _episode_seed(args.seed, setting)
        labeler = RacketLabeler()
        episode = build_episode(
            episode_seed,
            demo_count=args.demo_count,
            query_count=args.query_count,
            labeler=labeler,
        )
        if episode["setting"] != setting.as_dict():
            raise AssertionError("seed-selected setting changed during episode construction")
        episodes.append(episode)
        receipts.append(labeler.receipts[0])

    manifest = write_batch(episodes, args.out, receipts=receipts)
    print(
        json.dumps(
            {
                "episode_count": manifest["episode_count"],
                "manifest": str(args.out / "manifest.json"),
                "public_ids": [entry["public_id"] for entry in manifest["episodes"]],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
