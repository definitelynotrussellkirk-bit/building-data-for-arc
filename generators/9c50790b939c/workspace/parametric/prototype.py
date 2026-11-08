#!/usr/bin/env python3
"""Racket-backed episode-level ``growth_delta`` prototype for 9c50790b939c.

The selected production generator and canonical authority stay fixed.  This
prototype changes only how many additional cells are painted on the target rail:
``target_block_length = source_block_length + growth_delta``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "9c50790b939c"
ALLOWED_GROWTH_DELTAS = (0, 1, 2)
DEFAULT_GROWTH_DELTA = 1
DIFFICULTY = "medium"
DEMONSTRATION_INDICES = (0, 1, 2)
QUERY_INDICES = (3, 4, 5, 6)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = ROOT / "shared/data/canonical/puzzles.jsonl"
RULE_DIR = HERE / "rules"
EXAMPLE_DIR = HERE / "examples"


def _literal_int(value: object, *, name: str, nonnegative: bool = False) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not bool)")
    if nonnegative and value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _validate_growth_delta(value: object) -> int:
    if type(value) is not int:
        raise TypeError("growth_delta must be a literal integer")
    if value not in ALLOWED_GROWTH_DELTAS:
        raise ValueError(
            f"growth_delta must be one of {ALLOWED_GROWTH_DELTAS}, got {value!r}"
        )
    return value


def normalized_hash(source: str) -> str:
    """Return the repository's 12-hex whitespace-normalized rule hash."""
    return hashlib.sha256(" ".join(source.split()).encode("utf-8")).hexdigest()[:12]


def _sha256_text(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def canonical_source(*, root: Path | str = ROOT) -> str:
    path = Path(root) / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source.strip():
                    raise ValueError(f"{TASK_ID}: canonical program_solution missing")
                return source
    raise FileNotFoundError(f"{TASK_ID}: canonical task row not found in {path}")


def block_length_form(growth_delta: int) -> str:
    delta = _validate_growth_delta(growth_delta)
    return f"(block-len (+ {delta} (length nines)))"


def materialize_rule(
    growth_delta: object,
    *,
    root: Path | str = ROOT,
    source: str | None = None,
) -> str:
    """Materialize the complete Racket rule for one bounded parameter value."""
    delta = _validate_growth_delta(growth_delta)
    canonical = canonical_source(root=root) if source is None else source
    if not isinstance(canonical, str):
        raise TypeError("source must be Racket text")

    original = block_length_form(DEFAULT_GROWTH_DELTA)
    if canonical.count(original) != 1:
        raise ValueError("canonical rule must contain exactly one block-length form")
    if delta == DEFAULT_GROWTH_DELTA:
        return canonical
    return canonical.replace(original, block_length_form(delta), 1)


def parameters_for_seed(seed: object) -> dict[str, int]:
    """Choose one hidden setting deterministically for the whole episode."""
    literal_seed = _literal_int(seed, name="seed")
    digest = hashlib.sha256(
        f"{TASK_ID}:growth-delta:v1:{literal_seed}".encode("utf-8")
    ).digest()
    delta = ALLOWED_GROWTH_DELTAS[
        int.from_bytes(digest[:8], "big") % len(ALLOWED_GROWTH_DELTAS)
    ]
    return {"growth_delta": delta}


def find_seed_for_growth_delta(growth_delta: object, *, start: int = 0) -> int:
    delta = _validate_growth_delta(growth_delta)
    candidate = _literal_int(start, name="start", nonnegative=True)
    while candidate < start + 100_000:
        if parameters_for_seed(candidate)["growth_delta"] == delta:
            return candidate
        candidate += 1
    raise RuntimeError(f"could not find seed for growth_delta={delta}")


def _load_generator(*, root: Path | str = ROOT):
    path = Path(root) / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"generator_{TASK_ID}_parametric", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load selected generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _racket_literal(value: Any) -> str:
    if isinstance(value, list):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError(f"not an ARC literal: {value!r}")
    return str(value)


def _callable_racket_source(source: str) -> str:
    stripped = source.strip()
    prefix = "(rule! "
    if not stripped.startswith(prefix) or not stripped.endswith(")"):
        raise ValueError("expected a plain (rule! <lambda>) Racket program")
    callable_source = stripped[len(prefix) : -1].strip()
    if not callable_source.startswith("(lambda "):
        raise ValueError("prototype rule body must be a lambda")
    return callable_source


def execute_rule(
    source: str,
    grid: list[list[int]],
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Execute the exact materialized Racket rule on one grid."""
    expression = f"({_callable_racket_source(source)} '{_racket_literal(grid)})"
    if bridge is None:
        with RacketBridge() as owned:
            result = owned.eval_text(expression)
    else:
        result = bridge.eval_text(expression)
    if not isinstance(result, list) or not result or not all(
        isinstance(row, list) for row in result
    ):
        raise RuntimeError(f"Racket rule returned a non-grid result: {result!r}")
    return [[int(value) for value in row] for row in result]


def _python_output(generator: Any, grid: list[list[int]], growth_delta: int):
    scene = generator._scene(grid)
    return generator._apply_with_block_length(
        grid, len(scene["nines"]) + growth_delta
    )


def _episode_inputs(generator: Any, *, seed: int, difficulty: str):
    indices = (*DEMONSTRATION_INDICES, *QUERY_INDICES)
    return [
        generator.generate(seed, index, difficulty=difficulty) for index in indices
    ]


def _make_episode(
    seed: int,
    *,
    root: Path,
    bridge: RacketBridge,
    difficulty: str,
) -> dict[str, Any]:
    generator = _load_generator(root=root)
    parameters = parameters_for_seed(seed)
    chosen = parameters["growth_delta"]
    canonical = canonical_source(root=root)
    sources = {
        delta: materialize_rule(delta, source=canonical)
        for delta in ALLOWED_GROWTH_DELTAS
    }
    inputs = _episode_inputs(generator, seed=seed, difficulty=difficulty)

    outputs: dict[int, list[list[list[int]]]] = {}
    for delta, source in sources.items():
        racket_outputs = [execute_rule(source, grid, bridge=bridge) for grid in inputs]
        python_outputs = [_python_output(generator, grid, delta) for grid in inputs]
        if racket_outputs != python_outputs:
            raise AssertionError(f"growth_delta={delta}: Python/Racket parity failed")
        outputs[delta] = racket_outputs

    train: list[dict[str, Any]] = []
    for index, grid, output in zip(
        DEMONSTRATION_INDICES,
        inputs[: len(DEMONSTRATION_INDICES)],
        outputs[chosen][: len(DEMONSTRATION_INDICES)],
        strict=True,
    ):
        train.append(
            {
                "sample_index": index,
                "growth_delta": chosen,
                "input": grid,
                "output": output,
                "input_sha256": _digest(grid),
                "output_sha256": _digest(output),
            }
        )

    test: list[dict[str, Any]] = []
    for index, grid, output in zip(
        QUERY_INDICES,
        inputs[len(DEMONSTRATION_INDICES) :],
        outputs[chosen][len(DEMONSTRATION_INDICES) :],
        strict=True,
    ):
        test.append(
            {
                "sample_index": index,
                "growth_delta": chosen,
                "input": grid,
                "output": output,
                "input_sha256": _digest(grid),
                "output_sha256": _digest(output),
            }
        )

    rivals: list[dict[str, Any]] = []
    ambiguities: list[str] = []
    for rival in ALLOWED_GROWTH_DELTAS:
        if rival == chosen:
            continue
        demo_mismatches = [
            index
            for index, left, right in zip(
                DEMONSTRATION_INDICES,
                outputs[chosen][: len(DEMONSTRATION_INDICES)],
                outputs[rival][: len(DEMONSTRATION_INDICES)],
                strict=True,
            )
            if left != right
        ]
        query_mismatches = [
            index
            for index, left, right in zip(
                QUERY_INDICES,
                outputs[chosen][len(DEMONSTRATION_INDICES) :],
                outputs[rival][len(DEMONSTRATION_INDICES) :],
                strict=True,
            )
            if left != right
        ]
        status = (
            "refuted_by_demonstrations"
            if demo_mismatches
            else "not_refuted_by_demonstrations"
        )
        if not demo_mismatches:
            ambiguities.append(
                f"growth_delta={rival} agrees with all demonstrations"
            )
        rivals.append(
            {
                "growth_delta": rival,
                "status": status,
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        )

    source = sources[chosen]
    return {
        "schema": "arcpuzzles-parametric-episode-v1",
        "task_id": TASK_ID,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "difficulty": difficulty,
        "parameters": parameters,
        "parameter_scope": "chosen_once_per_episode",
        "racket_source": source,
        "racket_sha256": _sha256_text(source),
        "racket_normalized_hash": normalized_hash(source),
        "train": train,
        "test": test,
        "parameter_rivals": rivals,
        "ambiguities": ambiguities,
    }


def make_episode(
    seed: object,
    *,
    root: Path | str = ROOT,
    bridge: RacketBridge | None = None,
    difficulty: str = DIFFICULTY,
) -> dict[str, Any]:
    literal_seed = _literal_int(seed, name="seed")
    root_path = Path(root)
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(
                literal_seed,
                root=root_path,
                bridge=owned,
                difficulty=difficulty,
            )
    return _make_episode(
        literal_seed,
        root=root_path,
        bridge=bridge,
        difficulty=difficulty,
    )


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return the exact helper-defined model-visible challenge projection."""
    return json.loads(public_challenge_bytes(episode))


def public_export_plan(episodes: Any) -> list[dict[str, Any]]:
    """Sort private episodes by visible-content ID and reject public duplicates."""
    rows: list[dict[str, Any]] = []
    seen: dict[str, bytes] = {}
    for episode in episodes:
        payload = public_challenge_bytes(episode)
        identifier = public_challenge_id(episode)
        prior = seen.get(identifier)
        if prior is not None:
            if prior == payload:
                raise ValueError(f"duplicate visible public payload: {identifier}")
            raise RuntimeError(f"public challenge SHA-256 collision: {identifier}")
        seen[identifier] = payload
        rows.append(
            {
                "public_id": identifier,
                "public_bytes": payload,
                "episode": episode,
            }
        )
    return sorted(rows, key=lambda row: row["public_id"])


def write_public_challenges(
    episodes: Any,
    public_dir: Path | str,
    *,
    root: Path | str = ROOT,
) -> list[dict[str, Any]]:
    """Write visible-only challenges under content-derived filenames.

    The returned rows are private evidence metadata. Public files contain only
    the helper-defined visible bytes; seed, parameter, rule text and query
    labels remain in the private evidence report.
    """
    root_path = Path(root).resolve()
    directory_arg = Path(public_dir)
    directory = (
        directory_arg.resolve()
        if directory_arg.is_absolute()
        else (root_path / directory_arg).resolve()
    )
    try:
        directory.relative_to(root_path)
    except ValueError as error:
        raise ValueError("public_dir must be inside root") from error

    plan = public_export_plan(episodes)
    directory.mkdir(parents=True, exist_ok=True)
    expected_names: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in plan:
        name = f"{row['public_id']}.json"
        path = directory / name
        path.write_bytes(row["public_bytes"])
        expected_names.add(name)
        episode = row["episode"]
        result.append(
            {
                "public_id": row["public_id"],
                "public_path": str(path.relative_to(root_path)),
                "sha256": row["public_id"],
                "bytes": len(row["public_bytes"]),
                "seed": episode.get("seed"),
                "parameters": episode.get("parameters"),
            }
        )

    # The directory is dedicated to generated public examples. Remove stale
    # ordinal or superseded content only after every replacement file exists.
    for path in directory.glob("*.json"):
        if path.name not in expected_names:
            path.unlink()
    return result


def public_export_files_match(
    episodes: Any,
    rows: Any,
    *,
    root: Path | str = ROOT,
) -> bool:
    """Return whether retained public files exactly match visible episode bytes."""
    root_path = Path(root).resolve()
    try:
        expected: dict[str, bytes] = {}
        for episode in episodes:
            identifier = public_challenge_id(episode)
            if identifier in expected:
                return False
            expected[identifier] = public_challenge_bytes(episode)

        seen: set[str] = set()
        for row in rows:
            identifier = row["public_id"]
            relative = Path(row["public_path"])
            if (
                not isinstance(identifier, str)
                or identifier in seen
                or identifier not in expected
                or relative.is_absolute()
            ):
                return False
            path = (root_path / relative).resolve()
            if not path.is_relative_to(root_path):
                return False
            payload = path.read_bytes()
            if (
                path.name != f"{identifier}.json"
                or payload != expected[identifier]
                or hashlib.sha256(payload).hexdigest() != identifier
                or row.get("sha256") != identifier
                or row.get("bytes") != len(payload)
            ):
                return False
            seen.add(identifier)
        return seen == set(expected)
    except (KeyError, OSError, TypeError, ValueError):
        return False


def build_evidence(
    *,
    root: Path | str = ROOT,
    difficulty: str = DIFFICULTY,
    seed_search_start: int = 0,
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    task_path = root_path / "generators" / TASK_ID
    generator_path = task_path / "generator.py"
    parametric_path = task_path / "workspace" / "parametric"
    prototype_path = parametric_path / "prototype.py"
    rule_dir = parametric_path / "rules"
    canonical_path = root_path / "shared" / "data" / "canonical" / "puzzles.jsonl"

    generator = _load_generator(root=root_path)
    canonical = canonical_source(root=root_path)
    sources = {
        delta: materialize_rule(delta, source=canonical)
        for delta in ALLOWED_GROWTH_DELTAS
    }

    rules: dict[str, Any] = {}
    for delta, source in sources.items():
        path = rule_dir / f"growth_{delta}.rkt"
        if not path.is_file() or path.read_text(encoding="utf-8") != source:
            raise AssertionError(f"retained rule differs from materialized source: {path}")
        rules[str(delta)] = {
            "path": str(path.relative_to(root_path)),
            "sha256": _sha256_text(source),
            "normalized_hash": normalized_hash(source),
            "source": source,
        }

    seeds = {
        delta: find_seed_for_growth_delta(delta, start=seed_search_start)
        for delta in ALLOWED_GROWTH_DELTAS
    }
    with RacketBridge() as bridge:
        episodes = {
            str(delta): make_episode(
                seed,
                root=root_path,
                bridge=bridge,
                difficulty=difficulty,
            )
            for delta, seed in seeds.items()
        }

        witness_input = generator.generate(20261022, 7, difficulty="medium")
        witness_outputs = {
            str(delta): execute_rule(source, witness_input, bridge=bridge)
            for delta, source in sources.items()
        }

        canonical_row = None
        with canonical_path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    canonical_row = row
                    break
        if canonical_row is None:
            raise AssertionError("canonical task row missing")
        canonical_pairs = [*canonical_row["train"], *canonical_row["test"]]
        canonical_replay = [
            execute_rule(sources[DEFAULT_GROWTH_DELTA], pair["input"], bridge=bridge)
            == pair["output"]
            for pair in canonical_pairs
        ]

    all_rivals_refuted = all(
        not episode["ambiguities"]
        and all(
            rival["status"] == "refuted_by_demonstrations"
            for rival in episode["parameter_rivals"]
        )
        for episode in episodes.values()
    )
    witness_distinct = len(
        {_digest(output) for output in witness_outputs.values()}
    ) == len(ALLOWED_GROWTH_DELTAS)
    episode_pair_counts_match = all(
        len(episode["train"]) == len(DEMONSTRATION_INDICES)
        and len(episode["test"]) == len(QUERY_INDICES)
        for episode in episodes.values()
    )
    query_inputs_distinct = all(
        len({pair["input_sha256"] for pair in episode["test"]})
        == len(QUERY_INDICES)
        for episode in episodes.values()
    )
    queries_distinct_from_demonstrations = all(
        {pair["input_sha256"] for pair in episode["test"]}.isdisjoint(
            pair["input_sha256"] for pair in episode["train"]
        )
        for episode in episodes.values()
    )
    checks = {
        "default_rule_exactly_canonical": sources[DEFAULT_GROWTH_DELTA] == canonical,
        "default_normalized_hash_matches_selected": normalized_hash(canonical)
        == generator.RULE_HASH,
        "canonical_default_replay": canonical_replay,
        "all_episode_rivals_refuted_by_demonstrations": all_rivals_refuted,
        "same_input_distinguishes_all_settings": witness_distinct,
        "all_episode_pair_counts_match": episode_pair_counts_match,
        "all_query_inputs_distinct": query_inputs_distinct,
        "all_queries_distinct_from_demonstrations": (
            queries_distinct_from_demonstrations
        ),
        "all_passed": bool(
            sources[DEFAULT_GROWTH_DELTA] == canonical
            and normalized_hash(canonical) == generator.RULE_HASH
            and all(canonical_replay)
            and all_rivals_refuted
            and witness_distinct
            and episode_pair_counts_match
            and query_inputs_distinct
            and queries_distinct_from_demonstrations
        ),
    }

    return {
        "schema": "arcpuzzles-parametric-rule-prototype-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "episode_shape": {
            "demonstration_count": len(DEMONSTRATION_INDICES),
            "query_count": len(QUERY_INDICES),
            "demonstration_indices": list(DEMONSTRATION_INDICES),
            "query_indices": list(QUERY_INDICES),
        },
        "parameter": {
            "name": "growth_delta",
            "allowed_values": list(ALLOWED_GROWTH_DELTAS),
            "default": DEFAULT_GROWTH_DELTA,
            "chosen_once_per_episode": True,
            "semantics": (
                "paint source_block_length + growth_delta cells on the matching "
                "end of the unique target rail"
            ),
            "input_constraints": [
                "the source contains a nonempty proper end-aligned 9 block",
                "the target is exactly two cells longer than the source",
                "growth_delta in {0,1,2}, so the painted block always fits",
            ],
            "invariant_reasoning": [
                "identify the unique mixed 8/9 source rail",
                "infer which end contains the source block",
                "find the unique all-8 rail exactly two cells longer",
                "clear the source and transfer the block to the matching target end",
            ],
        },
        "source_bindings": {
            "prototype": {
                "path": str(prototype_path.relative_to(root_path)),
                "sha256": _sha256_file(prototype_path),
            },
            "selected_generator": {
                "path": str(generator_path.relative_to(root_path)),
                "sha256": _sha256_file(generator_path),
                "version": generator.VERSION,
                "rule_hash": generator.RULE_HASH,
            },
            "canonical_data": {
                "path": str(canonical_path.relative_to(root_path)),
                "sha256": _sha256_file(canonical_path),
            },
        },
        "rules": rules,
        "episodes": episodes,
        "distinguishing_witness": {
            "seed": 20261022,
            "sample_index": 7,
            "difficulty": "medium",
            "input": witness_input,
            "input_sha256": _digest(witness_input),
            "outputs": witness_outputs,
            "output_sha256": {
                delta: _digest(output) for delta, output in witness_outputs.items()
            },
        },
        "checks": checks,
        "runtime": racket_runtime_status(),
        "limitations": [
            "This is task-local prototype evidence, not a production parametric API.",
            "Only the target block growth count varies; target selection, colors, "
            "rail geometry, and input sampling remain canonical.",
            "Three seven-pair deterministic episodes (three demonstrations and four "
            "queries each) are bounded evidence, not a proof over every seed or "
            "downstream curriculum assembly.",
            "Public challenges intentionally omit the hidden parameter, Racket "
            "program, and query answer; private evidence must remain separate.",
        ],
    }


# ---------------------------------------------------------------------------
# Native bounded parametric adapter surface retained alongside the original
# authoring/evidence helpers above.

NATIVE_CANDIDATE_NAMES = (
    "growth_0",
    "growth_1",
    "growth_2",
    "half_target",
    "fixed_2",
    "fixed_3",
    "source_length",
    "whole_target",
    "opposite_end_0",
    "opposite_end_1",
    "opposite_end_2",
    "leave_source_0",
    "leave_source_1",
    "leave_source_2",
)

_NATIVE_PROFILES: dict[str, tuple[dict[str, Any], ...]] = {
    "demo": (
        {"shape": (12, 15), "source_length": 4, "block_length": 1,
         "distractors": (2, 3, 5, 7, 9, 10)},
        {"shape": (14, 16), "source_length": 6, "block_length": 3,
         "distractors": (2, 4, 5, 7, 9, 10, 11)},
        {"shape": (16, 18), "source_length": 8, "block_length": 2,
         "distractors": (2, 4, 6, 7, 9, 11, 12)},
        {"shape": (18, 20), "source_length": 5, "block_length": 2,
         "distractors": (2, 4, 6, 8, 9, 10, 12, 14)},
        {"shape": (20, 22), "source_length": 10, "block_length": 4,
         "distractors": (2, 5, 7, 9, 11, 13, 15, 17)},
        {"shape": (22, 24), "source_length": 12, "block_length": 6,
         "distractors": (2, 4, 6, 8, 10, 13, 16, 18, 20)},
    ),
    "query": (
        {"shape": (12, 15), "source_length": 5, "block_length": 2,
         "distractors": (2, 3, 4, 6, 8, 9, 10)},
        {"shape": (18, 20), "source_length": 8, "block_length": 3,
         "distractors": (2, 4, 6, 7, 9, 11, 12, 14, 16)},
        {"shape": (24, 27), "source_length": 10, "block_length": 4,
         "distractors": (2, 4, 6, 8, 11, 13, 15, 17, 19, 21)},
        {"shape": (30, 30), "source_length": 12, "block_length": 5,
         "distractors": (2, 4, 6, 8, 10, 12, 16, 18, 20, 22, 24, 26)},
    ),
}


def _native_integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(
            f"{name} must be an exact integer in {low}..{high}; bool is forbidden"
        )
    return value


def _native_setting(settings: Any) -> int:
    if type(settings) is not dict or set(settings) != {"growth_delta"}:
        raise ValueError("settings must contain exactly growth_delta")
    return _validate_growth_delta(settings["growth_delta"])


def program(settings: dict[str, Any]) -> str:
    delta = _native_setting(settings)
    path = HERE / "canonical.rkt" if delta == 1 else RULE_DIR / f"growth_{delta}.rkt"
    return path.read_text(encoding="utf-8")


def _native_validate_grid(grid: Any) -> tuple[list[list[int]], int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    clean: list[list[int]] = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or value not in (7, 8, 9) for value in row):
            raise ValueError("native rail grids may contain only colors 7, 8, and 9")
        clean.append(list(row))
    return clean, len(clean), width


def _native_runs(grid: list[list[int]], colors: tuple[int, ...]) -> list[dict[str, int]]:
    height = len(grid)
    width = len(grid[0])
    runs: list[dict[str, int]] = []
    allowed = set(colors)
    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] not in allowed:
                row += 1
                continue
            start = row
            while row + 1 < height and grid[row + 1][col] in allowed:
                row += 1
            end = row
            runs.append({"column": col, "start": start, "end": end,
                         "length": end - start + 1})
            row += 1
    return runs


def native_analyze(grid: Any) -> dict[str, Any]:
    values, height, width = _native_validate_grid(grid)
    nines = [(row, col) for row in range(height) for col in range(width)
             if values[row][col] == 9]
    if not nines:
        raise ValueError("grid must contain a nonempty color-9 source block")
    columns = {col for _, col in nines}
    if len(columns) != 1:
        raise ValueError("all source-block cells must occupy one column")
    source_col = next(iter(columns))
    rmin = min(row for row, _ in nines)
    rmax = max(row for row, _ in nines)
    source_start = rmin
    while source_start > 0 and values[source_start - 1][source_col] in (8, 9):
        source_start -= 1
    source_end = rmax
    while source_end + 1 < height and values[source_end + 1][source_col] in (8, 9):
        source_end += 1
    source_length = source_end - source_start + 1
    source_rows = [(row, source_col) for row in range(source_start, source_end + 1)]
    source_nines = [(row, source_col) for row in range(source_start, source_end + 1)
                    if values[row][source_col] == 9]
    if source_nines != nines:
        raise ValueError("all color-9 cells must belong to the source rail")
    nine_rows = [row for row, _ in source_nines]
    if nine_rows != list(range(min(nine_rows), max(nine_rows) + 1)):
        raise ValueError("source-block cells must be contiguous")
    top_aligned = min(nine_rows) == source_start
    bottom_aligned = max(nine_rows) == source_end
    if top_aligned == bottom_aligned and len(source_nines) != source_length:
        raise ValueError("source block must be aligned to exactly one rail end")
    if len(source_nines) == source_length:
        raise ValueError("source block must be a proper subset of the source rail")

    base = [row[:] for row in values]
    for row, col in source_nines:
        base[row][col] = 8
    target_length = source_length + 2
    target_candidates = [run for run in _native_runs(base, (8,))
                         if run["length"] == target_length]
    if len(target_candidates) != 1:
        raise ValueError(
            f"expected one pure-8 target rail of length {target_length}, "
            f"found {len(target_candidates)}"
        )
    target = target_candidates[0]
    return {
        "height": height,
        "width": width,
        "source": {
            "column": source_col,
            "start": source_start,
            "end": source_end,
            "length": source_length,
            "block_length": len(source_nines),
            "block_end": "top" if top_aligned else "bottom",
            "cells": [list(cell) for cell in source_rows],
            "nines": [list(cell) for cell in source_nines],
        },
        "target": dict(target),
        "target_length": target_length,
    }


def _native_apply(
    grid: Any,
    transfer_length: int,
    *,
    matching_end: bool = True,
    clear_source: bool = True,
) -> list[list[int]]:
    values, _, _ = _native_validate_grid(grid)
    analysis = native_analyze(values)
    target = analysis["target"]
    length = _native_integer(transfer_length, 1, target["length"], "transfer_length")
    output = [row[:] for row in values]
    if clear_source:
        for row, col in (tuple(cell) for cell in analysis["source"]["nines"]):
            output[row][col] = 8
    use_top = analysis["source"]["block_end"] == "top"
    if not matching_end:
        use_top = not use_top
    start = target["start"] if use_top else target["end"] - length + 1
    for row in range(start, start + length):
        output[row][target["column"]] = 9
    return output


def native_solve(grid: Any, policy: int | str) -> list[list[int]]:
    analysis = native_analyze(grid)
    source = analysis["source"]
    target = analysis["target"]
    if type(policy) is int:
        delta = _validate_growth_delta(policy)
        return _native_apply(grid, source["block_length"] + delta)
    if type(policy) is not str or policy not in NATIVE_CANDIDATE_NAMES:
        raise ValueError(f"unknown native policy {policy!r}")
    if policy.startswith("growth_"):
        delta = int(policy.rsplit("_", 1)[1])
        return _native_apply(grid, source["block_length"] + delta)
    if policy == "half_target":
        return _native_apply(grid, max(1, target["length"] // 2))
    if policy == "fixed_2":
        return _native_apply(grid, 2)
    if policy == "fixed_3":
        return _native_apply(grid, 3)
    if policy == "source_length":
        return _native_apply(grid, source["length"])
    if policy == "whole_target":
        return _native_apply(grid, target["length"])
    if policy.startswith("opposite_end_"):
        delta = int(policy.rsplit("_", 1)[1])
        return _native_apply(
            grid, source["block_length"] + delta, matching_end=False
        )
    if policy.startswith("leave_source_"):
        delta = int(policy.rsplit("_", 1)[1])
        return _native_apply(
            grid, source["block_length"] + delta, clear_source=False
        )
    raise AssertionError("unreachable native policy")


def _native_rng(seed: int, split: str, index: int):
    import random

    raw = json.dumps(
        [TASK_ID, "growth-delta-native-v1", seed, split, index],
        separators=(",", ":"),
    ).encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def native_sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _native_integer(seed, 0, 2**63 - 1, "seed")
    if split not in _NATIVE_PROFILES:
        raise ValueError("split must be demo or query")
    profiles = _NATIVE_PROFILES[split]
    profile = profiles[_native_integer(index, 0, len(profiles) - 1, "index")]
    height, width = profile["shape"]
    source_length = profile["source_length"]
    block_length = profile["block_length"]
    target_length = source_length + 2
    distractors = tuple(profile["distractors"])
    lengths = (source_length, target_length, *distractors)
    if len(lengths) > width or any(not 1 <= length <= height for length in lengths):
        raise ValueError("invalid native rail profile")
    if target_length in distractors:
        raise ValueError("target length must be unique")
    rng = _native_rng(seed, split, index)
    required = [0, width - 1] if split == "query" and index == 3 else []
    pool = [col for col in range(width) if col not in required]
    rng.shuffle(pool)
    columns = required + pool[: len(lengths) - len(required)]
    rng.shuffle(columns)
    grid = [[7] * width for _ in range(height)]
    starts: list[int] = []
    for ordinal, length in enumerate(lengths):
        if ordinal % 4 == 0:
            start = 0
        elif ordinal % 4 == 1:
            start = height - length
        else:
            start = rng.randint(0, height - length)
        starts.append(start)
    for col, start, length in zip(columns, starts, lengths, strict=True):
        for row in range(start, start + length):
            grid[row][col] = 8
    source_col = columns[0]
    source_start = starts[0]
    top = bool(rng.getrandbits(1))
    block_start = source_start if top else source_start + source_length - block_length
    for row in range(block_start, block_start + block_length):
        grid[row][source_col] = 9
    native_analyze(grid)
    return grid


def native_teaching_survivors(train: list[dict[str, Any]]) -> list[str]:
    if type(train) is not list:
        raise TypeError("train must be a list")
    return [
        candidate
        for candidate in NATIVE_CANDIDATE_NAMES
        if all(
            type(pair) is dict
            and set(pair) >= {"input", "output"}
            and native_solve(pair["input"], candidate) == pair["output"]
            for pair in train
        )
    ]


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    literal_seed = _native_integer(seed, 0, 2**63 - 1, "seed")
    delta = _native_setting(settings)
    demo_count = _native_integer(demos, 2, 6, "demos")
    query_count = _native_integer(queries, 1, 4, "queries")
    train_inputs = [
        native_sample_input(literal_seed, "demo", index)
        for index in range(demo_count)
    ]
    test_inputs = [
        native_sample_input(literal_seed, "query", index)
        for index in range(query_count)
    ]
    serialized = [
        json.dumps(grid, separators=(",", ":"))
        for grid in (*train_inputs, *test_inputs)
    ]
    if len(serialized) != len(set(serialized)):
        raise ValueError("native episode inputs must be distinct")
    train = [
        {"input": grid, "output": native_solve(grid, delta)}
        for grid in train_inputs
    ]
    test = [
        {"input": grid, "output": native_solve(grid, delta)}
        for grid in test_inputs
    ]
    survivors = native_teaching_survivors(train[:2])
    if survivors != [f"growth_{delta}"]:
        raise ValueError(
            f"minimum native demonstration prefix leaves finite survivors {survivors}"
        )
    return {
        "train": train,
        "test": test,
        "program_solution": program({"growth_delta": delta}),
        "sampling": {"draws": demo_count + query_count, "duplicate_rejections": 0},
    }

def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--difficulty", default=DIFFICULTY, choices=("easy", "medium", "hard"))
    parser.add_argument("--seed-search-start", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--public-dir", type=Path, required=True)
    args = parser.parse_args()

    report = build_evidence(
        root=ROOT,
        difficulty=args.difficulty,
        seed_search_start=args.seed_search_start,
    )
    public_exports = write_public_challenges(
        report["episodes"].values(), args.public_dir, root=ROOT
    )
    report["public_exports"] = public_exports
    report["checks"]["public_exports_use_visible_content_ids"] = (
        public_export_files_match(
            report["episodes"].values(), public_exports, root=ROOT
        )
    )
    report["checks"]["all_passed"] = bool(
        report["checks"]["all_passed"]
        and report["checks"]["public_exports_use_visible_content_ids"]
    )
    _write_json(args.out, report)

    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": TASK_ID,
                "out": str(args.out),
                "public_dir": str(args.public_dir),
                "checks": report["checks"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["checks"]["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
