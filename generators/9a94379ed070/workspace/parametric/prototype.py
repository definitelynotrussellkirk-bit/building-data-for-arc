#!/usr/bin/env python3
"""Proposed episode-level cyclic rank-offset extension for 9a94379ed070.

The canonical setting ``rank_offset=0`` paints cyan when an active macro block
and an active micro cell have the same row-major rank in the recovered motif.
The nearby setting ``rank_offset=1`` paints cyan when the micro rank is the next
active rank cyclically.  One setting is fixed for an entire episode.

This task-local prototype leaves the selected production generator, canonical
Racket authority, approval state, and training admission unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "9a94379ed070"
VERSION = "1.0.0"
SCHEMA = "arcpuzzles-cyclic-rank-offset-prototype-v1"
RANK_OFFSETS = (0, 1)
DEFAULT_RANK_OFFSET = 0
CANONICAL_SHA256 = "57b79c20b9ed9bf5ad1ca8b4b2547a7ef6d598e6bd06677f674870bafc4a9130"
PARAMETER_SPEC = {
    "name": "rank_offset",
    "values": RANK_OFFSETS,
    "default": DEFAULT_RANK_OFFSET,
    "meaning": (
        "paint cyan when micro-rank equals macro-rank plus rank_offset "
        "modulo the active motif-cell count"
    ),
}

ROOT = find_root(__file__)
_PRODUCTION, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=ROOT
)

_CANONICAL_COMPARISON = "(if (= (rank-of br bc) (rank-of tr tc)) 8 2)"
_OFFSET_ONE_COMPARISON = """(let* ((active-count (length tile-cells))
                              (macro-rank (rank-of br bc))
                              (micro-rank (rank-of tr tc)))
                         (if (= micro-rank
                                (remainder (+ macro-rank 1) active-count))
                             8
                             2))"""


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _grid_sha256(grid: Any) -> str:
    return _sha256(
        json.dumps(normalize_grid(grid), separators=(",", ":"), ensure_ascii=False)
    )


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer in 1..12 (not bool)")
    if not 1 <= value <= 12:
        raise ValueError(f"{name} must be in 1..12")
    return value


def _validate_rank_offset(rank_offset: Any) -> int:
    if type(rank_offset) is not int:
        raise TypeError("rank_offset must be the integer 0 or 1 (not bool)")
    if rank_offset not in RANK_OFFSETS:
        raise ValueError("rank_offset must be exactly 0 or 1")
    return rank_offset


def _root(value: Path | str | None) -> Path:
    return ROOT if value is None else Path(value).resolve()


def prototype_source_identity(
    *, root: Path | str | None = None
) -> dict[str, str]:
    """Bind retained evidence to the exact task-local prototype bytes."""
    root_path = _root(root)
    source_path = Path(__file__).resolve()
    try:
        relative = source_path.relative_to(root_path).as_posix()
    except ValueError as exc:
        raise ValueError("prototype source is outside the declared repository root") from exc
    return {"path": relative, "sha256": _sha256(source_path.read_bytes())}


def _production_for(root: Path):
    if root == ROOT:
        return _PRODUCTION, GENERATOR_PATH, GENERATOR_SHA256
    return load_selected_generator(TASK_ID, root=root)


def canonical_source(*, root: Path | str | None = None) -> str:
    """Load and pin the unique canonical Racket source for this task."""
    root_path = _root(root)
    sources: set[str] = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(
                row.get("program_solution"), str
            ):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(
            f"expected exactly one canonical source for {TASK_ID}, got {len(sources)}"
        )
    source = sources.pop()
    actual = _sha256(source)
    if actual != CANONICAL_SHA256:
        raise ValueError(
            f"canonical Racket source hash mismatch: {actual} != {CANONICAL_SHA256}"
        )
    return source


def materialize_rule(
    rank_offset: int = DEFAULT_RANK_OFFSET,
    *,
    root: Path | str | None = None,
) -> str:
    """Return the exact complete Racket source for one declared setting."""
    offset = _validate_rank_offset(rank_offset)
    source = canonical_source(root=root)
    if offset == DEFAULT_RANK_OFFSET:
        return source
    if source.count(_CANONICAL_COMPARISON) != 1:
        raise ValueError("canonical rank comparison is not uniquely replaceable")
    return source.replace(_CANONICAL_COMPARISON, _OFFSET_ONE_COMPARISON)


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Execute one exact Racket rule on one normalized input grid."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    # Use the repository-owned normalization pipeline.  Besides peeling the
    # outer rule! form and stripping line comments, wrap_rule supplies the
    # REPL's lexical h/w bindings required by this canonical lambda.
    expression = f"({wrap_rule(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def parameters_for_seed(seed: Any) -> dict[str, int]:
    """Choose one deterministic hidden setting for the complete episode."""
    seed = _validate_seed(seed)
    return {"rank_offset": RANK_OFFSETS[seed % len(RANK_OFFSETS)]}


def apply_python(
    grid: Any,
    rank_offset: Any,
    *,
    root: Path | str | None = None,
) -> list[list[int]]:
    """Independent Python authoring mirror for one declared setting."""
    offset = _validate_rank_offset(rank_offset)
    normalized = normalize_grid(grid)
    production, _path, _digest = _production_for(_root(root))
    errors = production.self_check(normalized)
    if errors:
        raise ValueError("input is outside the selected grammar: " + "; ".join(errors))
    facts = production.semantic_observables(normalized)
    q = facts["tile_size"]
    positions = [tuple(position) for position in facts["motif_positions"]]
    active_count = len(positions)
    output = [[0 for _ in row] for row in normalized]
    for macro_rank, (block_row, block_col) in enumerate(positions):
        row0 = block_row * (q + 1)
        col0 = block_col * (q + 1)
        target_micro_rank = (macro_rank + offset) % active_count
        for micro_rank, (tile_row, tile_col) in enumerate(positions):
            output[row0 + tile_row][col0 + tile_col] = (
                8 if micro_rank == target_micro_rank else 2
            )
    return output


def _input_rows(
    seed: int,
    count: int,
    *,
    root: Path,
) -> tuple[list[dict[str, Any]], str, str]:
    production, generator_path, generator_sha256 = _production_for(root)
    colors = (1, 2, 4, 5, 6, 7, 8, 9)
    textures = tuple(production.HELPFUL_TEXTURES)
    difficulties = ("easy", "medium", "hard")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    max_attempts = max(64, count * 8)
    for attempt in range(max_attempts):
        q = 3 + (attempt % 3)
        orientation = ("row", "column")[attempt % 2]
        overrides = {
            "tile_size": q,
            "tile_color": colors[(seed + attempt) % len(colors)],
            "stripe_orientation": orientation,
            "stripe_index": (seed + attempt) % q,
            "texture": textures[(seed + attempt) % len(textures)],
        }
        difficulty = difficulties[attempt % len(difficulties)]
        grid = production.generate(
            seed,
            attempt,
            difficulty=difficulty,
            **overrides,
        )
        errors = production.self_check(grid)
        if errors:
            raise RuntimeError("selected generator emitted an invalid grid: " + "; ".join(errors))
        digest = _grid_sha256(grid)
        if digest in seen:
            continue
        seen.add(digest)
        facts = production.semantic_observables(grid)
        rows.append(
            {
                "input": normalize_grid(grid),
                "input_sha256": digest,
                "sample_index": attempt,
                "difficulty": difficulty,
                "generation_overrides": overrides,
                "tile_size": facts["tile_size"],
                "motif_cell_count": facts["motif_cell_count"],
            }
        )
        if len(rows) == count:
            break
    if len(rows) != count:
        raise RuntimeError(
            f"could materialize only {len(rows)} of {count} distinct lawful inputs "
            f"after {max_attempts} attempts"
        )
    return rows, str(generator_path.relative_to(root)), generator_sha256


def make_episode(
    seed: Any,
    *,
    rank_offset: int | None = None,
    n_train: Any = 2,
    n_test: Any = 4,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one complete fixed-setting episode and label every pair in Racket."""
    seed = _validate_seed(seed)
    n_train = _validate_count("n_train", n_train)
    n_test = _validate_count("n_test", n_test)
    root_path = _root(root)
    offset = (
        parameters_for_seed(seed)["rank_offset"]
        if rank_offset is None
        else _validate_rank_offset(rank_offset)
    )
    rows, generator_path, generator_sha256 = _input_rows(
        seed, n_train + n_test, root=root_path
    )
    source = materialize_rule(offset, root=root_path)
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        assert active is not None
        pairs: list[dict[str, Any]] = []
        for row in rows:
            output = execute_rule(source, row["input"], bridge=active)
            python_output = apply_python(row["input"], offset, root=root_path)
            if output != python_output:
                raise RuntimeError("Python mirror disagrees with the matching Racket rule")
            pairs.append(
                {
                    **row,
                    "output": output,
                    "output_sha256": _grid_sha256(output),
                    "rank_offset": offset,
                }
            )
    return {
        "schema": SCHEMA,
        "version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": {"rank_offset": offset},
        "parameter_scope": "chosen once per episode",
        "n_train": n_train,
        "n_test": n_test,
        "generator_path": generator_path,
        "generator_sha256": generator_sha256,
        "prototype_source": prototype_source_identity(root=root_path),
        "program_sha256": _sha256(source),
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "pairs": pairs,
    }


def _episode_pairs(episode: dict[str, Any]) -> list[dict[str, Any]]:
    pairs = episode.get("pairs")
    if isinstance(pairs, list):
        return pairs
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train/test pair lists")
    return [*train, *test]


def analyze_episode(
    episode: dict[str, Any],
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Check fixed-setting labels, mirror parity, and the sole declared rival."""
    root_path = _root(root)
    if episode.get("task_id") != TASK_ID:
        raise ValueError("episode task_id mismatch")
    if episode.get("prototype_source") != prototype_source_identity(root=root_path):
        raise ValueError("episode prototype source identity mismatch")
    parameters = episode.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("episode parameters are missing")
    offset = _validate_rank_offset(parameters.get("rank_offset"))
    rival = 1 - offset
    pairs = _episode_pairs(episode)
    n_train = _validate_count("n_train", episode.get("n_train"))
    n_test = _validate_count("n_test", episode.get("n_test"))
    if len(pairs) != n_train + n_test:
        raise ValueError("episode pair count does not match n_train+n_test")
    if any(pair.get("rank_offset") != offset for pair in pairs):
        raise ValueError("episode resamples rank_offset within its pairs")

    source = materialize_rule(offset, root=root_path)
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    racket_replay = True
    python_parity = True
    rival_differences: list[bool] = []
    with manager as active:
        assert active is not None
        for pair in pairs:
            saved = normalize_grid(pair.get("output"))
            racket_output = execute_rule(source, pair.get("input"), bridge=active)
            python_output = apply_python(pair.get("input"), offset, root=root_path)
            rival_output = apply_python(pair.get("input"), rival, root=root_path)
            racket_replay = racket_replay and racket_output == saved
            python_parity = python_parity and python_output == saved
            rival_differences.append(rival_output != saved)

    demonstrations_refuting = sum(rival_differences[:n_train])
    queries = [
        {
            "pair_index": index,
            "input_sha256": pairs[index]["input_sha256"],
            "rival_query_differs": rival_differences[index],
        }
        for index in range(n_train, len(pairs))
    ]
    identifiable = demonstrations_refuting > 0
    passed = racket_replay and python_parity and identifiable
    return {
        "status": "no_ambiguity_found" if passed else "failed",
        "passed": passed,
        "rank_offset": offset,
        "declared_rival": {"rank_offset": rival},
        "racket_replay": racket_replay,
        "python_parity": python_parity,
        "rival_fits_demonstrations": not identifiable,
        "demonstrations_refuting_rival": demonstrations_refuting,
        "queries": queries,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project an episode to visible demonstrations and unlabeled query inputs."""
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train/test lists")
    return {
        "train": [
            {
                "input": normalize_grid(pair.get("input")),
                "output": normalize_grid(pair.get("output")),
            }
            for pair in train
        ],
        "test": [{"input": normalize_grid(pair.get("input"))} for pair in test],
    }


def public_filename(challenge: dict[str, Any]) -> str:
    return f"challenge-{public_challenge_id(challenge)}.json"


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _setting_difference_witness(
    default_episode: dict[str, Any],
    alternative_episode: dict[str, Any],
    *,
    root: Path,
) -> dict[str, Any]:
    default_pair = default_episode["pairs"][0]
    alternative_pair = alternative_episode["pairs"][0]
    if default_pair["input"] != alternative_pair["input"]:
        raise ValueError("paired setting witness does not share one input")
    default_output = default_pair["output"]
    alternative_output = alternative_pair["output"]
    different = sum(
        left != right
        for left_row, right_row in zip(default_output, alternative_output)
        for left, right in zip(left_row, right_row)
    )
    production, _path, _digest = _production_for(root)
    facts = production.semantic_observables(default_pair["input"])
    positions = [tuple(position) for position in facts["motif_positions"]]
    last_macro = positions[-1]
    first_micro = positions[0]
    q = facts["tile_size"]
    row = last_macro[0] * (q + 1) + first_micro[0]
    col = last_macro[1] * (q + 1) + first_micro[1]
    wraparound = default_output[row][col] == 2 and alternative_output[row][col] == 8
    return {
        "input_sha256": default_pair["input_sha256"],
        "different_cell_count": different,
        "wraparound_cell": [row, col],
        "wraparound_verified": wraparound,
    }


def _counts(
    episodes: list[dict[str, Any]],
    analyses: list[dict[str, Any]],
    *,
    canonical_count: int,
    canonical_passed: int,
) -> dict[str, int]:
    all_pairs = [pair for episode in episodes for pair in episode["pairs"]]
    return {
        "settings": len(episodes),
        "episodes": len(episodes),
        "demonstrations": sum(len(episode["train"]) for episode in episodes),
        "queries": sum(len(episode["test"]) for episode in episodes),
        "episode_pairs": len(all_pairs),
        "distinct_input_payloads": len(
            {pair["input_sha256"] for pair in all_pairs}
        ),
        "racket_labels": len(all_pairs),
        "canonical_pairs": canonical_count,
        "canonical_pairs_passed": canonical_passed,
        "identifiable_episodes": sum(
            analysis["status"] == "no_ambiguity_found" for analysis in analyses
        ),
        "queries_refuting_rival": sum(
            row["rival_query_differs"]
            for analysis in analyses
            for row in analysis["queries"]
        ),
    }


def _canonical_check(
    *,
    root: Path,
    bridge: RacketBridge,
) -> tuple[int, int]:
    source = materialize_rule(DEFAULT_RANK_OFFSET, root=root)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    passed = 0
    for pair in pairs:
        racket_output = execute_rule(source, pair["input"], bridge=bridge)
        python_output = apply_python(pair["input"], DEFAULT_RANK_OFFSET, root=root)
        if racket_output == pair["output"] and python_output == pair["output"]:
            passed += 1
    return len(pairs), passed


def _report(
    episodes: list[dict[str, Any]],
    analyses: list[dict[str, Any]],
    *,
    canonical_count: int,
    canonical_passed: int,
    root: Path,
) -> dict[str, Any]:
    counts = _counts(
        episodes,
        analyses,
        canonical_count=canonical_count,
        canonical_passed=canonical_passed,
    )
    witness = _setting_difference_witness(episodes[0], episodes[1], root=root)
    passed = (
        canonical_count == canonical_passed
        and counts["identifiable_episodes"] == len(episodes)
        and counts["queries_refuting_rival"] == counts["queries"]
        and witness["different_cell_count"] > 0
        and witness["wraparound_verified"]
    )
    return {
        "schema": SCHEMA,
        "version": VERSION,
        "task_id": TASK_ID,
        "status": "no_ambiguity_found" if passed else "failed",
        "passed": passed,
        "approved": False,
        "parameter_spec": {
            **PARAMETER_SPEC,
            "values": list(PARAMETER_SPEC["values"]),
        },
        "canonical_authority_changed": False,
        "default_program_byte_identical": (
            materialize_rule(0, root=root) == canonical_source(root=root)
        ),
        "generator_path": episodes[0]["generator_path"],
        "generator_sha256": episodes[0]["generator_sha256"],
        "prototype_source": prototype_source_identity(root=root),
        "counts": counts,
        "setting_difference_witness": witness,
        "analyses": analyses,
        "limits": [
            "Evidence is bounded to rank_offset values 0 and 1.",
            "The declared rival family contains only the other retained offset.",
            "Prototype evidence does not change canonical approval or training admission.",
        ],
    }


def materialize(
    out_dir: Path | str,
    *,
    seed: Any = 31,
    n_train: Any = 2,
    n_test: Any = 4,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Write two paired fixed-setting episodes and compact verification metadata."""
    seed = _validate_seed(seed)
    n_train = _validate_count("n_train", n_train)
    n_test = _validate_count("n_test", n_test)
    root_path = _root(root)
    out = Path(out_dir).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"output directory must be empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        assert active is not None
        canonical_count, canonical_passed = _canonical_check(
            root=root_path, bridge=active
        )
        episodes = [
            make_episode(
                seed,
                rank_offset=offset,
                n_train=n_train,
                n_test=n_test,
                root=root_path,
                bridge=active,
            )
            for offset in RANK_OFFSETS
        ]
        analyses = [
            analyze_episode(episode, root=root_path, bridge=active)
            for episode in episodes
        ]

    entries: dict[str, dict[str, Any]] = {}
    for offset, episode in zip(RANK_OFFSETS, episodes):
        program_rel = f"programs/rank-offset-{offset}.rkt"
        private_rel = f"private/rank-offset-{offset}.json"
        public = public_challenge(episode)
        public_rel = f"public/{public_filename(public)}"
        _write(out / program_rel, materialize_rule(offset, root=root_path).encode("utf-8"))
        _write(out / private_rel, _json_bytes(episode))
        _write(out / public_rel, public_challenge_bytes(public))
        entries[str(offset)] = {
            "program": program_rel,
            "private_episode": private_rel,
            "public_challenge": public_rel,
        }

    report = _report(
        episodes,
        analyses,
        canonical_count=canonical_count,
        canonical_passed=canonical_passed,
        root=root_path,
    )
    _write(out / "report.json", _json_bytes(report))

    files = {}
    for path in sorted(out.rglob("*")):
        if path.is_file():
            relative = path.relative_to(out).as_posix()
            files[relative] = _sha256(path.read_bytes())
    manifest = {
        "schema": f"{SCHEMA}-manifest",
        "version": VERSION,
        "task_id": TASK_ID,
        "seed": seed,
        "n_train": n_train,
        "n_test": n_test,
        "prototype_source": prototype_source_identity(root=root_path),
        "entries": entries,
        "files": files,
    }
    _write(out / "manifest.json", _json_bytes(manifest))
    return report


def _validate_retained_episode(
    episode: dict[str, Any],
    *,
    offset: int,
    seed: int,
    n_train: int,
    n_test: int,
    expected_rows: list[dict[str, Any]],
    generator_path: str,
    generator_sha256: str,
    prototype_source: dict[str, str],
    program_sha256: str,
) -> None:
    """Reject stale or internally split private episode metadata."""
    expected_header = {
        "schema": SCHEMA,
        "version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": {"rank_offset": offset},
        "parameter_scope": "chosen once per episode",
        "n_train": n_train,
        "n_test": n_test,
        "generator_path": generator_path,
        "generator_sha256": generator_sha256,
        "prototype_source": prototype_source,
        "program_sha256": program_sha256,
    }
    for field, expected in expected_header.items():
        if episode.get(field) != expected:
            raise ValueError(f"private episode {field} mismatch")

    train = episode.get("train")
    test = episode.get("test")
    pairs = episode.get("pairs")
    if not isinstance(train, list) or not isinstance(test, list) or not isinstance(pairs, list):
        raise ValueError("private episode train/test/pairs must be lists")
    if len(pairs) != n_train + n_test or len(expected_rows) != len(pairs):
        raise ValueError("private episode pair count mismatch")
    if train != pairs[:n_train] or test != pairs[n_train:]:
        raise ValueError("private episode train/test split differs from pairs")

    for index, (pair, expected_row) in enumerate(zip(pairs, expected_rows)):
        if not isinstance(pair, dict):
            raise ValueError(f"private episode pair {index} must be a mapping")
        for field, expected in expected_row.items():
            if pair.get(field) != expected:
                raise ValueError(f"private episode pair {index} {field} mismatch")
        if pair.get("rank_offset") != offset:
            raise ValueError(f"private episode pair {index} rank_offset mismatch")
        if _grid_sha256(pair.get("input")) != pair.get("input_sha256"):
            raise ValueError(f"private episode pair {index} input hash mismatch")
        if _grid_sha256(pair.get("output")) != pair.get("output_sha256"):
            raise ValueError(f"private episode pair {index} output hash mismatch")


def verify_tree(
    out_dir: Path | str,
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Verify a materialized evidence tree from its retained bytes."""
    root_path = _root(root)
    out = Path(out_dir).resolve()
    manifest_path = out / "manifest.json"
    for retained_path in out.rglob("*"):
        if retained_path.is_symlink():
            raise ValueError(
                f"symlinked retained evidence is not allowed: "
                f"{retained_path.relative_to(out).as_posix()}"
            )
    if not manifest_path.is_file():
        raise ValueError("missing manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != f"{SCHEMA}-manifest" or manifest.get("task_id") != TASK_ID:
        raise ValueError("manifest schema/task mismatch")
    expected_prototype_source = prototype_source_identity(root=root_path)
    if manifest.get("prototype_source") != expected_prototype_source:
        raise ValueError("manifest prototype source identity mismatch")
    seed = _validate_seed(manifest.get("seed"))
    n_train = _validate_count("n_train", manifest.get("n_train"))
    n_test = _validate_count("n_test", manifest.get("n_test"))
    expected_rows, expected_generator_path, expected_generator_sha256 = _input_rows(
        seed, n_train + n_test, root=root_path
    )
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ValueError("manifest files mapping is missing")
    if any(
        not isinstance(relative, str) or not isinstance(expected, str)
        for relative, expected in files.items()
    ):
        raise ValueError("manifest file entries must map paths to SHA-256 strings")
    actual_files = {
        path.relative_to(out).as_posix()
        for path in out.rglob("*")
        if path.is_file() and path != manifest_path
    }
    if actual_files != set(files):
        raise ValueError("manifest file inventory mismatch")
    for relative, expected in files.items():
        actual = _sha256((out / relative).read_bytes())
        if actual != expected:
            raise ValueError(f"file hash mismatch: {relative}")

    entries = manifest.get("entries")
    if not isinstance(entries, dict) or set(entries) != {"0", "1"}:
        raise ValueError("manifest entries must contain offsets 0 and 1")
    episodes: list[dict[str, Any]] = []
    for offset in RANK_OFFSETS:
        entry = entries[str(offset)]
        if not isinstance(entry, dict):
            raise ValueError(f"manifest entry for rank_offset={offset} must be a mapping")

        def retained_entry_path(field: str) -> Path:
            relative = entry.get(field)
            if not isinstance(relative, str) or relative not in files:
                raise ValueError(
                    f"manifest entry path is outside retained inventory: "
                    f"rank_offset={offset} field={field}"
                )
            return out / relative

        program_path = retained_entry_path("program")
        private_path = retained_entry_path("private_episode")
        public_path = retained_entry_path("public_challenge")
        expected_program = materialize_rule(offset, root=root_path).encode("utf-8")
        if program_path.read_bytes() != expected_program:
            raise ValueError(f"program bytes differ for rank_offset={offset}")
        episode = json.loads(private_path.read_text(encoding="utf-8"))
        _validate_retained_episode(
            episode,
            offset=offset,
            seed=seed,
            n_train=n_train,
            n_test=n_test,
            expected_rows=expected_rows,
            generator_path=expected_generator_path,
            generator_sha256=expected_generator_sha256,
            prototype_source=expected_prototype_source,
            program_sha256=_sha256(expected_program),
        )
        public = public_challenge(episode)
        expected_public = public_challenge_bytes(public)
        if public_path.read_bytes() != expected_public:
            raise ValueError(f"public bytes mismatch: {public_path.name}")
        if public_path.name != public_filename(public):
            raise ValueError(f"public filename mismatch: {public_path.name}")
        episodes.append(episode)

    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        assert active is not None
        canonical_count, canonical_passed = _canonical_check(
            root=root_path, bridge=active
        )
        analyses = [
            analyze_episode(episode, root=root_path, bridge=active)
            for episode in episodes
        ]
    recomputed = _report(
        episodes,
        analyses,
        canonical_count=canonical_count,
        canonical_passed=canonical_passed,
        root=root_path,
    )
    stored_report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    if stored_report != recomputed:
        raise ValueError("report does not match recomputed evidence")
    if not recomputed["passed"]:
        raise ValueError("recomputed evidence did not pass")
    return {
        "status": "pass",
        "task_id": TASK_ID,
        "prototype_source": expected_prototype_source,
        "counts": recomputed["counts"],
        "files_verified": len(files),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    materialize_parser = sub.add_parser("materialize")
    materialize_parser.add_argument("--out-dir", type=Path, required=True)
    materialize_parser.add_argument("--seed", type=int, default=31)
    materialize_parser.add_argument("--train", type=int, default=2)
    materialize_parser.add_argument("--test", type=int, default=4)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--out-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "materialize":
        result = materialize(
            args.out_dir,
            seed=args.seed,
            n_train=args.train,
            n_test=args.test,
        )
    else:
        result = verify_tree(args.out_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("passed", result.get("status") == "pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
