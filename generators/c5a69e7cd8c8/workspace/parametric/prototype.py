#!/usr/bin/env python3
"""Proposed episode-level ray-relation extension for ARC task c5a69e7cd8c8.

The canonical/default setting preserves the exact authoritative Racket source:
the singleton color paints zero cells on the ray opposite its one open cardinal
neighbour.  The alternative keeps the same singleton/opening analysis and paints
through the open side instead.  One setting is fixed for every demonstration and
query in an episode.

This is task-local authoring evidence only.  It does not change the production
generator, canonical authority, approval hashes, or training admission.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path, PurePosixPath
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

TASK_ID = "c5a69e7cd8c8"
VERSION = "1.0.0"
SCHEMA = "arcpuzzles-ray-relation-prototype-v1"
RAY_RELATIONS = ("opposite_opening", "through_opening")
DEFAULT_RAY_RELATION = "opposite_opening"
CANONICAL_SHA256 = "cd162c43ed682af8c42df94bcb1c099d019115b65f32e70077f02d447664267d"

CANONICAL_DIRECTION_BLOCK = """                  (dr (* -1 (first open-dir)))
                  (dc (* -1 (second open-dir))))"""
THROUGH_DIRECTION_BLOCK = """                  (dr (first open-dir))
                  (dc (second open-dir)))"""


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _grid_sha256(grid: Any) -> str:
    return _sha256(json.dumps(normalize_grid(grid), separators=(",", ":")))


def _validate_seed(seed: Any, *, name: str = "seed") -> None:
    if type(seed) is not int:
        raise TypeError(f"{name} must be a nonnegative integer (not bool)")
    if seed < 0:
        raise ValueError(f"{name} must be nonnegative")


def _validate_count(name: str, value: Any) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be a positive integer (not bool)")
    if not 1 <= value <= 12:
        raise ValueError(f"{name} must be in 1..12")


def _validate_ray_relation(ray_relation: Any) -> None:
    if type(ray_relation) is not str or ray_relation not in RAY_RELATIONS:
        raise ValueError(
            "ray_relation must be exactly 'opposite_opening' or 'through_opening'"
        )


def canonical_source(*, root: Path | str | None = None) -> str:
    """Load and pin the unique canonical Racket authority for this task."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
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
    if source.count(CANONICAL_DIRECTION_BLOCK) != 1:
        raise ValueError("canonical source does not contain the unique direction block")
    if THROUGH_DIRECTION_BLOCK in source:
        raise ValueError("canonical source unexpectedly contains the alternative block")
    return source


def materialize_rule(
    ray_relation: str = DEFAULT_RAY_RELATION,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    """Instantiate one declared setting while preserving the exact default."""
    _validate_ray_relation(ray_relation)
    canonical = canonical_source(root=root) if source is None else source
    if not isinstance(canonical, str) or _sha256(canonical) != CANONICAL_SHA256:
        raise ValueError("source must be the exact pinned canonical Racket program")
    if canonical.count(CANONICAL_DIRECTION_BLOCK) != 1:
        raise ValueError("source must contain the unique canonical direction block")
    if ray_relation == DEFAULT_RAY_RELATION:
        return canonical
    alternative = canonical.replace(
        CANONICAL_DIRECTION_BLOCK, THROUGH_DIRECTION_BLOCK, 1
    )
    if alternative.count(THROUGH_DIRECTION_BLOCK) != 1:
        raise AssertionError("failed to materialize through-opening rule")
    return alternative


def _restore_canonical(source: Any) -> str:
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    if source.count(THROUGH_DIRECTION_BLOCK) == 1:
        restored = source.replace(
            THROUGH_DIRECTION_BLOCK, CANONICAL_DIRECTION_BLOCK, 1
        )
    elif source.count(CANONICAL_DIRECTION_BLOCK) == 1:
        restored = source
    else:
        raise ValueError("Racket source must contain exactly one declared direction block")
    if _sha256(restored) != CANONICAL_SHA256:
        raise ValueError("Racket source is not a declared variant of the pinned authority")
    return restored


def rule_callable(source: str) -> str:
    """Return a bare-bridge-safe callable after validating the variant source."""
    _restore_canonical(source)
    return wrap_rule(source)


def _grid_literal(grid: Any) -> str:
    normalized = normalize_grid(grid)
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in normalized)
    return f"'({rows})"


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Execute one exact materialized Racket program on one input grid."""
    expression = f"({rule_callable(source)} {_grid_literal(grid)})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def parameters_for_seed(seed: Any) -> dict[str, str]:
    _validate_seed(seed)
    return {"ray_relation": RAY_RELATIONS[seed % len(RAY_RELATIONS)]}


def _episode_inputs(
    input_seed: int,
    count: int,
    *,
    root: Path,
) -> tuple[list[dict[str, Any]], str, str]:
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root
    )
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    attempt = 0
    difficulties = ("easy", "medium", "hard")
    while len(rows) < count and attempt < 256:
        generation_seed = input_seed * 1_000_003 + attempt * 97 + 17
        sample_index = attempt
        difficulty = difficulties[attempt % len(difficulties)]
        attempt += 1
        grid = normalize_grid(
            generator.generate(
                generation_seed,
                sample_index,
                difficulty=difficulty,
            )
        )
        errors = generator.self_check(grid, difficulty=difficulty)
        if errors:
            continue
        digest = _grid_sha256(grid)
        if digest in seen:
            continue
        seen.add(digest)
        rows.append(
            {
                "input": grid,
                "input_sha256": digest,
                "generation": {
                    "seed": generation_seed,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                },
            }
        )
    if len(rows) != count:
        raise RuntimeError(f"could only generate {len(rows)} unique inputs out of {count}")
    return rows, generator_path.relative_to(root).as_posix(), generator_sha256


def make_episode(
    seed: int,
    *,
    n_train: int = 3,
    n_test: int = 4,
    input_seed: int | None = None,
    ray_relation: str | None = None,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one fixed-setting episode with independent demo/query counts."""
    _validate_seed(seed)
    _validate_count("n_train", n_train)
    _validate_count("n_test", n_test)
    if input_seed is None:
        input_seed = seed
    _validate_seed(input_seed, name="input_seed")
    selected = parameters_for_seed(seed)["ray_relation"] if ray_relation is None else ray_relation
    _validate_ray_relation(selected)
    root = find_root(__file__) if root is None else Path(root).resolve()

    canonical = canonical_source(root=root)
    rules = {
        relation: materialize_rule(relation, source=canonical)
        for relation in RAY_RELATIONS
    }
    inputs, generator_path, generator_sha256 = _episode_inputs(
        input_seed, n_train + n_test, root=root
    )

    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        pairs = []
        for index, row in enumerate(inputs):
            output = execute_rule(rules[selected], row["input"], bridge=active)
            split = "train" if index < n_train else "test"
            pair_index = index if split == "train" else index - n_train
            pairs.append(
                {
                    "split": split,
                    "pair_index": pair_index,
                    "input": row["input"],
                    "output": output,
                    "input_sha256": row["input_sha256"],
                    "output_sha256": _grid_sha256(output),
                    "generation": row["generation"],
                    "ray_relation": selected,
                }
            )

    return {
        "schema": SCHEMA,
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "seed": seed,
        "input_seed": input_seed,
        "parameters": {"ray_relation": selected},
        "allowed_parameters": {"ray_relation": list(RAY_RELATIONS)},
        "default_parameters": {"ray_relation": DEFAULT_RAY_RELATION},
        "program_sha256": _sha256(rules[selected]),
        "generator_path": generator_path,
        "generator_sha256": generator_sha256,
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in pairs
            if pair["split"] == "train"
        ],
        "test": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in pairs
            if pair["split"] == "test"
        ],
        "pairs": pairs,
    }


def _episode_pairs(episode: dict[str, Any]) -> list[dict[str, Any]]:
    """Return pairs only when they are the exact private train/test backing."""
    pairs = episode.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("episode must contain nonempty pairs")
    projected: dict[str, list[dict[str, Any]]] = {"train": [], "test": []}
    indices: dict[str, list[Any]] = {"train": [], "test": []}
    for pair in pairs:
        if not isinstance(pair, dict) or pair.get("split") not in projected:
            raise ValueError("episode pairs must use only train/test splits")
        split = pair["split"]
        indices[split].append(pair.get("pair_index"))
        projected[split].append(
            {
                "input": normalize_grid(pair["input"]),
                "output": normalize_grid(pair["output"]),
            }
        )
    for split in ("train", "test"):
        if indices[split] != list(range(len(indices[split]))):
            raise ValueError(f"episode {split} pair indices must be contiguous from zero")
        visible = episode.get(split)
        if not isinstance(visible, list):
            raise ValueError("episode train/test must be lists")
        normalized = [
            {
                "input": normalize_grid(pair["input"]),
                "output": normalize_grid(pair["output"]),
            }
            for pair in visible
        ]
        if normalized != projected[split]:
            raise ValueError("episode train/test do not match pairs")
    return pairs


def analyze_episode(
    episode: dict[str, Any],
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Re-execute both declared settings and test demo-only identifiability."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    selected = episode.get("parameters", {}).get("ray_relation")
    _validate_ray_relation(selected)
    rival = next(value for value in RAY_RELATIONS if value != selected)
    canonical = canonical_source(root=root)
    rules = {
        relation: materialize_rule(relation, source=canonical)
        for relation in RAY_RELATIONS
    }
    pairs = _episode_pairs(episode)

    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        rows = []
        for pair in pairs:
            expected = normalize_grid(pair["output"])
            selected_output = execute_rule(
                rules[selected], pair["input"], bridge=active
            )
            rival_output = execute_rule(rules[rival], pair["input"], bridge=active)
            rows.append(
                {
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "selected_matches": selected_output == expected,
                    "rival_matches": rival_output == expected,
                    "rival_query_differs": rival_output != expected,
                    "selected_output_sha256": _grid_sha256(selected_output),
                    "rival_output_sha256": _grid_sha256(rival_output),
                }
            )

    demonstrations = [row for row in rows if row["split"] == "train"]
    queries = [row for row in rows if row["split"] == "test"]
    selected_matches = all(row["selected_matches"] for row in rows)
    rival_fits_demonstrations = all(row["rival_matches"] for row in demonstrations)
    all_queries_distinguish = bool(queries) and all(
        row["rival_query_differs"] for row in queries
    )
    status = (
        "no_ambiguity_found"
        if selected_matches and not rival_fits_demonstrations and all_queries_distinguish
        else "ambiguous_or_invalid"
    )
    return {
        "schema": f"{SCHEMA}-analysis-v1",
        "status": status,
        "selected": selected,
        "rival": rival,
        "selected_matches_all_pairs": selected_matches,
        "rival_fits_demonstrations": rival_fits_demonstrations,
        "demonstrations": demonstrations,
        "queries": queries,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project one private episode to model-visible demonstrations and inputs."""
    public = {
        "train": [
            {
                "input": normalize_grid(pair["input"]),
                "output": normalize_grid(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": normalize_grid(pair["input"])}
            for pair in episode["test"]
        ],
    }
    public_challenge_bytes(public)
    return public


def public_filename(public: dict[str, Any]) -> str:
    return f"challenge-{public_challenge_id(public)}.json"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _evidence_path(out: Path, relative: Any) -> Path:
    if type(relative) is not str or not relative or "\\" in relative:
        raise ValueError("report path must stay inside evidence root")
    logical = PurePosixPath(relative)
    if logical.is_absolute() or ".." in logical.parts:
        raise ValueError("report path must stay inside evidence root")
    path = out.joinpath(*logical.parts)
    try:
        path.resolve().relative_to(out)
    except ValueError as exc:
        raise ValueError("report path must stay inside evidence root") from exc
    return path


def _file_record(path: Path) -> dict[str, Any]:
    body = path.read_bytes()
    return {"bytes": len(body), "sha256": _sha256(body)}


def _manifest_files(out: Path) -> dict[str, dict[str, Any]]:
    return {
        path.relative_to(out).as_posix(): _file_record(path)
        for path in sorted(out.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }


def materialize(
    out: Path | str,
    *,
    seed: int = 0,
    n_train: int = 3,
    n_test: int = 4,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Write public/private episodes, exact rules, report, and hash manifest."""
    _validate_seed(seed)
    _validate_count("n_train", n_train)
    _validate_count("n_test", n_test)
    out = Path(out).resolve()
    root = find_root(__file__) if root is None else Path(root).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"output directory must be empty: {out}")

    canonical = canonical_source(root=root)
    rules = {
        relation: materialize_rule(relation, source=canonical)
        for relation in RAY_RELATIONS
    }

    manager = nullcontext(bridge) if bridge is not None else RacketBridge(
        max_calls_before_restart=512
    )
    prepared_rows: list[dict[str, Any]] = []
    seen_public_bytes: set[bytes] = set()
    seen_public_ids: set[str] = set()
    with manager as active:
        runtime_identity = copy.deepcopy(active.runtime_identity)
        for index, relation in enumerate(RAY_RELATIONS):
            parameter_seed = seed * 2 + index
            episode = make_episode(
                parameter_seed,
                input_seed=seed,
                ray_relation=relation,
                n_train=n_train,
                n_test=n_test,
                root=root,
                bridge=active,
            )
            analysis = analyze_episode(episode, root=root, bridge=active)
            if analysis["status"] != "no_ambiguity_found":
                raise ValueError(f"episode is not identifiable: {relation}")
            public = public_challenge(episode)
            visible_bytes = public_challenge_bytes(public)
            filename = public_filename(public)
            public_id = filename.removeprefix("challenge-").removesuffix(".json")
            if visible_bytes in seen_public_bytes:
                raise ValueError("duplicate visible public payload across settings")
            if public_id in seen_public_ids:
                raise ValueError(f"public ID collision: {public_id}")
            seen_public_bytes.add(visible_bytes)
            seen_public_ids.add(public_id)
            prepared_rows.append(
                {
                    "relation": relation,
                    "public": public,
                    "public_bytes": visible_bytes,
                    "public_id": public_id,
                    "episode": episode,
                    "analysis": analysis,
                    "parameter_seed": parameter_seed,
                }
            )

        canonical_checks = []
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute_rule(canonical, pair["input"], bridge=active)
            if actual != pair["output"]:
                raise ValueError(
                    "default program failed canonical pair "
                    f"{pair['variant']}:{pair['split']}:{pair['pair_index']}"
                )
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": _grid_sha256(pair["input"]),
                    "output_sha256": _grid_sha256(actual),
                }
            )

    for folder in ("public", "private", "rules"):
        (out / folder).mkdir(parents=True, exist_ok=True)
    for relation, source in rules.items():
        (out / "rules" / f"{relation.replace('_', '-')}.rkt").write_text(
            source, encoding="utf-8"
        )

    episode_rows = []
    for prepared in sorted(prepared_rows, key=lambda row: row["public_id"]):
        relation = prepared["relation"]
        public_id = prepared["public_id"]
        public_path = Path("public") / f"challenge-{public_id}.json"
        private_path = Path("private") / f"challenge-{public_id}.private.json"
        (out / public_path).write_bytes(prepared["public_bytes"])
        _write_json(
            out / private_path,
            {
                "episode": prepared["episode"],
                "analysis": prepared["analysis"],
                "rule_path": f"rules/{relation.replace('_', '-')}.rkt",
                "rule_sha256": _sha256(rules[relation]),
            },
        )
        episode_rows.append(
            {
                "public_id": public_id,
                "public_path": public_path.as_posix(),
                "private_path": private_path.as_posix(),
                "parameters": {"ray_relation": relation},
                "parameter_seed": prepared["parameter_seed"],
                "input_seed": seed,
                "demonstrations": n_train,
                "queries": n_test,
            }
        )
    _write_json(out / "private" / "canonical-checks.json", canonical_checks)

    _, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    prototype_path = Path(__file__).resolve()
    report = {
        "schema": f"{SCHEMA}-report-v1",
        "status": "no_ambiguity_found",
        "task_id": TASK_ID,
        "prototype_status": "proposed_unapproved",
        "approved": False,
        "parameters": {
            "ray_relation": {
                "allowed": list(RAY_RELATIONS),
                "default": DEFAULT_RAY_RELATION,
                "episode_fixed": True,
                "input_constraints_depend_on_parameter": False,
            }
        },
        "counts": {
            "episodes": len(episode_rows),
            "demonstrations": len(episode_rows) * n_train,
            "queries": len(episode_rows) * n_test,
        },
        "episodes": sorted(episode_rows, key=lambda row: row["public_id"]),
        "canonical_sha256": CANONICAL_SHA256,
        "rule_sha256": {
            relation: _sha256(source) for relation, source in rules.items()
        },
        "generator_path": generator_path.relative_to(root).as_posix(),
        "generator_sha256": generator_sha256,
        "prototype_path": prototype_path.relative_to(root).as_posix(),
        "prototype_source_sha256": _sha256(prototype_path.read_bytes()),
        "racket_runtime": runtime_identity,
        "limits": [
            "finite two-setting rival family only",
            "two materialized episodes with one shared input seed",
            "prototype is not production-approved or training-admitted",
        ],
    }
    _write_json(out / "report.json", report)
    _write_json(
        out / "manifest.json",
        {
            "schema": f"{SCHEMA}-manifest-v1",
            "files": _manifest_files(out),
        },
    )
    return report


def verify_tree(
    out: Path | str,
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Verify hashes, source bindings, public privacy, and Racket semantics."""
    out = Path(out).resolve()
    root = find_root(__file__) if root is None else Path(root).resolve()
    errors: list[str] = []
    episodes_checked = 0
    try:
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        expected_files = manifest.get("files", {})
        actual_files = _manifest_files(out)
        if expected_files != actual_files:
            errors.append("manifest file hashes do not match the evidence tree")
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        if manifest.get("schema") != f"{SCHEMA}-manifest-v1":
            errors.append("manifest schema mismatch")
        if report.get("schema") != f"{SCHEMA}-report-v1":
            errors.append("report schema mismatch")
        if report.get("task_id") != TASK_ID:
            errors.append("report task ID mismatch")
        if report.get("approved") is not False:
            errors.append("report approval status must remain false")
        if report.get("prototype_status") != "proposed_unapproved":
            errors.append("report prototype status mismatch")
        expected_parameters = {
            "ray_relation": {
                "allowed": list(RAY_RELATIONS),
                "default": DEFAULT_RAY_RELATION,
                "episode_fixed": True,
                "input_constraints_depend_on_parameter": False,
            }
        }
        if report.get("parameters") != expected_parameters:
            errors.append("report parameter contract mismatch")
    except Exception as exc:
        return {
            "schema": f"{SCHEMA}-verification-v1",
            "status": "fail",
            "errors": [f"evidence structure: {type(exc).__name__}: {exc}"],
            "episodes_checked": 0,
        }

    prototype_path = Path(__file__).resolve()
    prototype_sha256 = _sha256(prototype_path.read_bytes())
    if report.get("prototype_source_sha256") != prototype_sha256:
        errors.append("prototype source binding is stale")
    try:
        expected_prototype_path = prototype_path.relative_to(root).as_posix()
        if report.get("prototype_path") != expected_prototype_path:
            errors.append("prototype path binding is stale")
        _, generator_path, generator_sha256 = load_selected_generator(
            TASK_ID, root=root
        )
        if report.get("generator_sha256") != generator_sha256:
            errors.append("generator source binding is stale")
        if report.get("generator_path") != generator_path.relative_to(root).as_posix():
            errors.append("generator path binding is stale")
        if report.get("canonical_sha256") != CANONICAL_SHA256:
            errors.append("canonical source binding is stale")
        canonical = canonical_source(root=root)
        rules = {
            relation: materialize_rule(relation, source=canonical)
            for relation in RAY_RELATIONS
        }
        expected_rule_sha256 = {
            relation: _sha256(source) for relation, source in rules.items()
        }
        if report.get("rule_sha256") != expected_rule_sha256:
            errors.append("report rule hashes are stale")
        for relation, source in rules.items():
            path = out / "rules" / f"{relation.replace('_', '-')}.rkt"
            if path.read_text(encoding="utf-8") != source:
                errors.append(f"rule file differs from materialized source: {relation}")
    except Exception as exc:
        errors.append(f"source binding: {type(exc).__name__}: {exc}")
        rules = {}

    episode_rows = report.get("episodes")
    if not isinstance(episode_rows, list):
        episode_rows = []
        errors.append("episode coverage must be a list")
    relations: list[Any] = []
    public_ids: list[Any] = []
    public_paths: list[Any] = []
    private_paths: list[Any] = []
    for row in episode_rows:
        if not isinstance(row, dict):
            relations.append(None)
            public_ids.append(None)
            public_paths.append(None)
            private_paths.append(None)
            continue
        parameters = row.get("parameters")
        relations.append(
            parameters.get("ray_relation") if isinstance(parameters, dict) else None
        )
        public_ids.append(row.get("public_id"))
        public_paths.append(row.get("public_path"))
        private_paths.append(row.get("private_path"))

    def unique_strings(values: list[Any]) -> bool:
        return (
            len(values) == len(episode_rows)
            and all(type(value) is str and value for value in values)
            and len(set(values)) == len(values)
        )

    if (
        len(episode_rows) != len(RAY_RELATIONS)
        or not all(type(value) is str for value in relations)
        or set(relations) != set(RAY_RELATIONS)
        or not unique_strings(public_ids)
        or not unique_strings(public_paths)
        or not unique_strings(private_paths)
    ):
        errors.append(
            "episode coverage must contain one unique public/private episode "
            "for each declared ray_relation"
        )

    count_rows_valid = all(
        isinstance(row, dict)
        and type(row.get("demonstrations")) is int
        and row["demonstrations"] >= 0
        and type(row.get("queries")) is int
        and row["queries"] >= 0
        for row in episode_rows
    )
    expected_counts = (
        {
            "episodes": len(episode_rows),
            "demonstrations": sum(row["demonstrations"] for row in episode_rows),
            "queries": sum(row["queries"] for row in episode_rows),
        }
        if count_rows_valid
        else None
    )
    if expected_counts is None or report.get("counts") != expected_counts:
        errors.append("report counts do not match episode rows")

    manager = nullcontext(bridge) if bridge is not None else RacketBridge(
        max_calls_before_restart=512
    )
    try:
        with manager as active:
            for row in episode_rows:
                public_path = _evidence_path(out, row.get("public_path"))
                private_path = _evidence_path(out, row.get("private_path"))
                public_bytes = public_path.read_bytes()
                public = json.loads(public_bytes.decode("utf-8"))
                private = json.loads(private_path.read_text(encoding="utf-8"))
                episode = private["episode"]
                relation = row.get("parameters", {}).get("ray_relation")
                if episode.get("parameters", {}).get("ray_relation") != relation:
                    errors.append(f"report/private parameter mismatch: {private_path.name}")
                if row.get("public_id") != public_challenge_id(public):
                    errors.append(f"report public ID mismatch: {public_path.name}")
                if row.get("parameter_seed") != episode.get("seed"):
                    errors.append(f"report parameter seed mismatch: {private_path.name}")
                if row.get("input_seed") != episode.get("input_seed"):
                    errors.append(f"report input seed mismatch: {private_path.name}")
                if row.get("demonstrations") != len(public.get("train", [])):
                    errors.append(f"report demonstration count mismatch: {public_path.name}")
                if row.get("queries") != len(public.get("test", [])):
                    errors.append(f"report query count mismatch: {public_path.name}")
                if relation in rules:
                    expected_rule_path = f"rules/{relation.replace('_', '-')}.rkt"
                    if private.get("rule_path") != expected_rule_path:
                        errors.append(f"private rule path mismatch: {private_path.name}")
                    if private.get("rule_sha256") != _sha256(rules[relation]):
                        errors.append(f"private rule hash mismatch: {private_path.name}")
                if public_bytes != public_challenge_bytes(public):
                    errors.append(
                        f"public file bytes are not canonical: {public_path.name}"
                    )
                if public_filename(public) != public_path.name:
                    errors.append(f"public filename does not match visible content: {public_path.name}")
                if public_challenge(episode) != public:
                    errors.append(f"public/private projection mismatch: {public_path.name}")
                analysis = analyze_episode(episode, root=root, bridge=active)
                if analysis["status"] != "no_ambiguity_found":
                    errors.append(f"episode ambiguity: {private_path.name}")
                if analysis != private.get("analysis"):
                    errors.append(f"stored analysis is stale: {private_path.name}")
                episodes_checked += 1
    except Exception as exc:
        errors.append(f"semantic verification: {type(exc).__name__}: {exc}")

    if report.get("status") != "no_ambiguity_found":
        errors.append(f"report status is {report.get('status')!r}")
    if episodes_checked != 2:
        errors.append(f"expected two episodes, checked {episodes_checked}")
    return {
        "schema": f"{SCHEMA}-verification-v1",
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "manifest_files_checked": len(manifest.get("files", {})),
        "episodes_checked": episodes_checked,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    materialize_parser = subparsers.add_parser(
        "materialize", help="write fresh evidence"
    )
    materialize_parser.add_argument("--seed", type=int, default=0)
    materialize_parser.add_argument("--demos", type=int, default=3)
    materialize_parser.add_argument("--queries", type=int, default=4)
    materialize_parser.add_argument("--out", type=Path, required=True)
    verify_parser = subparsers.add_parser("verify", help="verify existing evidence")
    verify_parser.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "materialize":
        result = materialize(
            args.out,
            seed=args.seed,
            n_train=args.demos,
            n_test=args.queries,
        )
    else:
        result = verify_tree(args.out)
    print(json.dumps(result, sort_keys=True))
    return int(result.get("status") not in {"pass", "no_ambiguity_found"})


if __name__ == "__main__":
    raise SystemExit(main())
