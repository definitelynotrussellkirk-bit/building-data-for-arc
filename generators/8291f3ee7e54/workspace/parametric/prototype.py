"""Proposed episode-level ring-order extension for ARC task 8291f3ee7e54.

The canonical/default setting keeps the exact authoritative Racket source:
component spans are sorted largest-to-smallest and their own colors are painted
from the outside inward.  The alternative keeps those exact ring geometries but
assigns the color sequence in reverse, placing the smallest component's color
outside.  One setting is fixed for an entire episode.

This is task-local authoring evidence only.  It does not change the canonical
rule, production API, approval hashes, or training admission.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "8291f3ee7e54"
VERSION = "1.1.0"
SCHEMA = "arcpuzzles-ring-order-prototype-v1"
RING_ORDERS = ("largest_outside", "smallest_outside")
DEFAULT_RING_ORDER = "largest_outside"
CANONICAL_SHA256 = "79951c1fb8d60053930868df5a4f183a5ed50884fe0e479e954ea446b7b8b6bb"
PUBLIC_PARENT_ID = "45a5af55"
PUBLIC_PARENT_SHA256 = "08adaedc3b2ae02781394888ed2fef2f0223ca07f149c484464f93d4c922f7ff"

CANONICAL_TAIL = '''             (define n (obj-size (first layers)))
             (define (paint-layer out obj)
               (let* ((s (obj-size obj))
                      (off (quotient (- n s) 2))
                      (color (obj-color obj)))
                 (for*/fold ((acc out))
                            ((r (in-range off (+ off s))) (c (in-range off (+ off s))))
                            (if (or
                                  (= r off)
                                  (= r (- (+ off s) 1))
                                  (= c off)
                                  (= c (- (+ off s) 1)))
                                (set-cell acc r c color)
                                acc))))
             (for/fold ((out (empty-grid n n 0))) ((obj layers)) (paint-layer out obj))))))'''

ALTERNATIVE_TAIL = '''             (define n (obj-size (first layers)))
             (define ring-colors (reverse (map obj-color layers)))
             (define (paint-layer out obj color)
               (let* ((s (obj-size obj))
                      (off (quotient (- n s) 2)))
                 (for*/fold ((acc out))
                            ((r (in-range off (+ off s))) (c (in-range off (+ off s))))
                            (if (or
                                  (= r off)
                                  (= r (- (+ off s) 1))
                                  (= c off)
                                  (= c (- (+ off s) 1)))
                                (set-cell acc r c color)
                                acc))))
             (for/fold ((out (empty-grid n n 0)))
                       ((obj layers) (color ring-colors))
               (paint-layer out obj color))))))'''

LAYOUT_SEQUENCE = ("distractor", "scattered", "overlap", "clipped")
SIZE_SEQUENCE = (12, 14, 16, 18, 20, 22)
DIFFICULTY_SEQUENCE = ("easy", "medium", "hard")


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _grid_sha256(grid: Any) -> str:
    return _sha256(json.dumps(normalize_grid(grid), separators=(",", ":")))


def _validate_seed(seed: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")


def _validate_count(name: str, value: Any) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be a positive integer (not bool)")
    if not 1 <= value <= 12:
        raise ValueError(f"{name} must be in 1..12")


def _validate_ring_order(ring_order: Any) -> None:
    if type(ring_order) is not str or ring_order not in RING_ORDERS:
        raise ValueError(
            "ring_order must be exactly 'largest_outside' or 'smallest_outside'"
        )


def _check_canonical_source(source: Any) -> str:
    if not isinstance(source, str):
        raise ValueError("canonical Racket source must be text")
    actual = _sha256(source)
    if actual != CANONICAL_SHA256:
        raise ValueError(
            f"canonical Racket source hash mismatch: {actual} != {CANONICAL_SHA256}"
        )
    if source.count(CANONICAL_TAIL) != 1:
        raise ValueError("canonical source does not contain the unique pinned tail")
    if ALTERNATIVE_TAIL in source:
        raise ValueError("canonical source unexpectedly contains the alternative tail")
    return source


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
    return _check_canonical_source(sources.pop())


def materialize_rule(
    ring_order: str = DEFAULT_RING_ORDER,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    """Instantiate one declared setting while preserving the exact default."""
    _validate_ring_order(ring_order)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if ring_order == DEFAULT_RING_ORDER:
        return canonical
    alternative = canonical.replace(CANONICAL_TAIL, ALTERNATIVE_TAIL, 1)
    if alternative.count(ALTERNATIVE_TAIL) != 1:
        raise AssertionError("failed to materialize smallest-outside rule")
    return alternative


def _restore_canonical(source: Any) -> str:
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    if source.count(ALTERNATIVE_TAIL) == 1:
        restored = source.replace(ALTERNATIVE_TAIL, CANONICAL_TAIL, 1)
    elif source.count(CANONICAL_TAIL) == 1:
        restored = source
    else:
        raise ValueError("Racket source must contain exactly one declared rule tail")
    return _check_canonical_source(restored)


def rule_callable(source: str) -> str:
    """Strip only the outer rule! wrapper and retain the selected rule body."""
    _restore_canonical(source)
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    body = source[len("(rule!") : -1].strip()
    marker = "(lambda (g)"
    if body.count(marker) != 1:
        raise ValueError("expected exactly one wrapped grid lambda")
    lambda_body = body[body.index(marker) :]
    return (
        "(lambda (g) "
        "(let* ((h (rows g)) (w (cols g))) "
        f"({lambda_body} g)))"
    )


def execute_rule(source: str, grid: Any, *, bridge: RacketBridge | None = None):
    """Execute one exact instantiated Racket rule on one normalized grid."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def parameters_for_seed(seed: Any) -> dict[str, str]:
    _validate_seed(seed)
    return {"ring_order": RING_ORDERS[seed % len(RING_ORDERS)]}


def _input_rows(
    seed: int,
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
    while len(rows) < count and attempt < 600:
        index = len(rows)
        layout_kind = LAYOUT_SEQUENCE[index % len(LAYOUT_SEQUENCE)]
        grid_size = SIZE_SEQUENCE[index % len(SIZE_SEQUENCE)]
        n_layers = 3 + (index % 3)
        difficulty = DIFFICULTY_SEQUENCE[index % len(DIFFICULTY_SEQUENCE)]
        generation_seed = seed * 1_000_003 + attempt * 97 + 17
        sample_index = seed * 101 + attempt
        attempt += 1
        try:
            grid = generator.generate(
                generation_seed,
                sample_index,
                difficulty=difficulty,
                layout_kind=layout_kind,
                grid_size=grid_size,
                n_layers=n_layers,
            )
        except ValueError:
            continue
        errors = generator.self_check(grid, difficulty=difficulty)
        if errors:
            continue
        if len(grid) != grid_size:
            continue
        if generator.observe_overrides(grid).get("n_layers") != n_layers:
            continue
        digest = _grid_sha256(grid)
        if digest in seen:
            continue
        seen.add(digest)
        rows.append(
            {
                "fixture_id": f"fixture-{index + 1:02d}",
                "input": normalize_grid(grid),
                "input_sha256": digest,
                "generation": {
                    "seed": generation_seed,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                    "overrides": {
                        "layout_kind": layout_kind,
                        "grid_size": grid_size,
                        "n_layers": n_layers,
                    },
                },
            }
        )
    if len(rows) != count:
        raise RuntimeError(f"could only generate {len(rows)} unique inputs out of {count}")
    return rows, generator_path.relative_to(root).as_posix(), generator_sha256


def make_episode(
    seed: int,
    *,
    n_train: int = 2,
    n_test: int = 4,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one complete fixed-setting episode with independent query count."""
    _validate_seed(seed)
    _validate_count("n_train", n_train)
    _validate_count("n_test", n_test)
    root = find_root(__file__) if root is None else Path(root).resolve()
    parameters = parameters_for_seed(seed)
    canonical = canonical_source(root=root)
    rules = {
        order: materialize_rule(order, source=canonical) for order in RING_ORDERS
    }
    inputs, generator_path, generator_sha256 = _input_rows(
        seed, n_train + n_test, root=root
    )
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        outputs = {
            order: [
                execute_rule(source, row["input"], bridge=active)
                for row in inputs
            ]
            for order, source in rules.items()
        }
    for index, row in enumerate(inputs):
        if outputs[RING_ORDERS[0]][index] == outputs[RING_ORDERS[1]][index]:
            raise AssertionError(
                f"fixture {row['fixture_id']} does not distinguish ring-order settings"
            )

    chosen = parameters["ring_order"]
    pairs: list[dict[str, Any]] = []
    for row, output in zip(inputs, outputs[chosen], strict=True):
        pairs.append(
            {
                **copy.deepcopy(row),
                "ring_order": chosen,
                "output": output,
                "output_sha256": _grid_sha256(output),
            }
        )
    source = rules[chosen]
    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "parameter_selection": "RING_ORDERS[seed % 2], fixed across the episode",
        "input_constraints_depend_on_parameter": False,
        "n_train": n_train,
        "n_test": n_test,
        "generator_path": generator_path,
        "generator_sha256": generator_sha256,
        "racket_source": source,
        "racket_sha256": _sha256(source),
        "pairs": pairs,
        "train": copy.deepcopy(pairs[:n_train]),
        "test": copy.deepcopy(pairs[n_train:]),
    }


def analyze_episode(
    episode: dict[str, Any],
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Check the sole alternate setting using demonstrations only."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    chosen = episode.get("parameters", {}).get("ring_order")
    _validate_ring_order(chosen)
    rival = next(order for order in RING_ORDERS if order != chosen)
    pairs = episode.get("pairs")
    n_train = episode.get("n_train")
    n_test = episode.get("n_test")
    if not isinstance(pairs, list) or len(pairs) != n_train + n_test:
        raise ValueError("episode pair count does not match n_train+n_test")
    rival_source = materialize_rule(rival, root=root)
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        rival_outputs = [
            execute_rule(rival_source, pair["input"], bridge=active)
            for pair in pairs
        ]
    demo_refutations = [
        index
        for index in range(n_train)
        if rival_outputs[index] != pairs[index]["output"]
    ]
    query_rows = [
        {
            "query_index": query_index,
            "pair_index": n_train + query_index,
            "rival_query_differs": (
                rival_outputs[n_train + query_index]
                != pairs[n_train + query_index]["output"]
            ),
        }
        for query_index in range(n_test)
    ]
    rival_fits = not demo_refutations
    status = (
        "no_ambiguity_found"
        if not rival_fits and all(row["rival_query_differs"] for row in query_rows)
        else "ambiguous"
    )
    return {
        "schema": f"{SCHEMA}-analysis-v1",
        "status": status,
        "chosen": chosen,
        "rival": rival,
        "demonstration_refutations": demo_refutations,
        "rival_fits_demonstrations": rival_fits,
        "queries": query_rows,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project one private episode to visible demonstrations and query inputs."""
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train/test lists")
    public = {
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in test],
    }
    public_challenge_bytes(public)
    return public


def public_filename(challenge: dict[str, Any]) -> str:
    return f"challenge-{public_challenge_id(challenge)}.json"


def _sorted_unique_episode_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return batch metadata sorted by visible-content ID, rejecting collisions."""
    seen: set[str] = set()
    for row in rows:
        public_id = row.get("public_id")
        if not isinstance(public_id, str) or not public_id:
            raise ValueError("episode row is missing a visible public challenge ID")
        if public_id in seen:
            raise ValueError(f"duplicate visible public challenge ID: {public_id}")
        seen.add(public_id)
    return sorted(rows, key=lambda row: row["public_id"])


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_inventory(out: Path, *, exclude: tuple[str, ...] = ()) -> dict[str, dict[str, Any]]:
    excluded = set(exclude)
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(row for row in out.rglob("*") if row.is_file()):
        relative = path.relative_to(out).as_posix()
        if relative in excluded:
            continue
        body = path.read_bytes()
        result[relative] = {"bytes": len(body), "sha256": _sha256(body)}
    return result


def materialize(
    out: Path | str,
    *,
    seed: int = 0,
    n_train: int = 2,
    n_test: int = 4,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Write two complete settings, public projections, and replayable evidence."""
    _validate_seed(seed)
    _validate_count("n_train", n_train)
    _validate_count("n_test", n_test)
    root = find_root(__file__) if root is None else Path(root).resolve()
    out = Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"output directory must be new or empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    canonical = canonical_source(root=root)
    rules = {
        order: materialize_rule(order, source=canonical) for order in RING_ORDERS
    }
    report: dict[str, Any] = {
        "schema": f"{SCHEMA}-report-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "running",
        "approved": False,
        "parameter": {
            "name": "ring_order",
            "allowed_values": list(RING_ORDERS),
            "default": DEFAULT_RING_ORDER,
            "input_constraints_depend_on_parameter": False,
        },
        "public_focus": {
            "task_id": PUBLIC_PARENT_ID,
            "challenge_sha256": PUBLIC_PARENT_SHA256,
            "transfer": (
                "45a5af55 maps an ordered stripe sequence to outer-to-inner ring depth. "
                "This prototype retains span-ranked component geometry and parameterizes "
                "whether that ordered color sequence is consumed forward or reversed."
            ),
            "lineage_status": "inspired_extension_unverified",
        },
        "canonical_source_sha256": _sha256(canonical),
        "prototype_source_sha256": _sha256(Path(__file__).read_bytes()),
        "canonical_checks": [],
        "episodes": [],
    }

    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    try:
        with manager as active:
            for order, source in rules.items():
                path = out / "private" / "rules" / f"ring-order-{order}.rkt"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")

            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute_rule(canonical, pair["input"], bridge=active)
                report["canonical_checks"].append(
                    {
                        "variant": pair["variant"],
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "passed": actual == pair["output"],
                    }
                )

            planned_episodes: list[dict[str, Any]] = []
            for index in range(2):
                episode = make_episode(
                    seed + index,
                    n_train=n_train,
                    n_test=n_test,
                    root=root,
                    bridge=active,
                )
                analysis = analyze_episode(episode, root=root, bridge=active)
                public = public_challenge(episode)
                public_id = public_challenge_id(public)
                public_path = "public/" + public_filename(public)
                private_path = f"private/episode-{index + 1:03d}.json"
                episode_row = {
                    "seed": episode["seed"],
                    "parameters": episode["parameters"],
                    "n_train": n_train,
                    "n_test": n_test,
                    "generator_sha256": episode["generator_sha256"],
                    "racket_sha256": episode["racket_sha256"],
                    "public_path": public_path,
                    "public_id": public_id,
                    "private_path": private_path,
                    "analysis": analysis,
                }
                planned_episodes.append(
                    {
                        "row": episode_row,
                        "episode": episode,
                        "public": public,
                        "public_bytes": public_challenge_bytes(public),
                    }
                )

            # Validate the complete batch before publishing any episode.  In
            # particular, a visible-content collision must not leave a partial
            # public/private tree behind.
            ordered_rows = _sorted_unique_episode_rows(
                [item["row"] for item in planned_episodes]
            )
            planned_by_id = {
                item["row"]["public_id"]: item for item in planned_episodes
            }
            report["episodes"] = ordered_rows
            report["public_write_order"] = [
                row["public_id"] for row in ordered_rows
            ]

            for row in ordered_rows:
                item = planned_by_id[row["public_id"]]
                public_path = row["public_path"]
                private_path = row["private_path"]
                public_file = out / public_path
                public_file.parent.mkdir(parents=True, exist_ok=True)
                public_file.write_bytes(item["public_bytes"])
                _write_json(
                    out / private_path,
                    {**item["episode"], "rival_checks": row["analysis"]},
                )

        canonical_passed = sum(row["passed"] for row in report["canonical_checks"])
        settings_seen = {
            row["parameters"]["ring_order"] for row in report["episodes"]
        }
        ambiguities = sum(
            row["analysis"]["status"] != "no_ambiguity_found"
            for row in report["episodes"]
        )
        report["counts"] = {
            "canonical_labels_checked": len(report["canonical_checks"]),
            "canonical_labels_passed": canonical_passed,
            "episodes": len(report["episodes"]),
            "demonstrations": len(report["episodes"]) * n_train,
            "queries": len(report["episodes"]) * n_test,
            "episode_labels": len(report["episodes"]) * (n_train + n_test),
            "rival_ambiguities": ambiguities,
        }
        report["status"] = (
            "no_ambiguity_found"
            if canonical_passed == len(report["canonical_checks"])
            and settings_seen == set(RING_ORDERS)
            and ambiguities == 0
            else "failed"
        )
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        _write_json(out / "report.json", report)
        raise

    _write_json(out / "report.json", report)
    _write_json(
        out / "manifest.json",
        {
            "schema": f"{SCHEMA}-manifest-v1",
            "files": _file_inventory(
                out, exclude=("manifest.json", "verification.json")
            ),
        },
    )
    verification = verify_tree(out, root=root, bridge=bridge)
    _write_json(out / "verification.json", verification)
    if verification["status"] != "pass":
        raise RuntimeError(f"materialized evidence failed verification: {verification}")
    return report


def verify_tree(
    out: Path | str,
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Replay hashes, privacy projection, canonical labels, and rival checks."""
    out = Path(out).resolve()
    root = find_root(__file__) if root is None else Path(root).resolve()
    errors: list[str] = []
    try:
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "schema": f"{SCHEMA}-verification-v1",
            "status": "fail",
            "errors": [f"metadata: {type(exc).__name__}: {exc}"],
        }

    for relative, expected in manifest.get("files", {}).items():
        path = out / relative
        if not path.is_file():
            errors.append(f"missing manifest file: {relative}")
            continue
        body = path.read_bytes()
        if len(body) != expected.get("bytes"):
            errors.append(f"byte count mismatch: {relative}")
        if _sha256(body) != expected.get("sha256"):
            errors.append(f"sha256 mismatch: {relative}")

    current_prototype_sha256 = _sha256(Path(__file__).read_bytes())
    if report.get("prototype_source_sha256") != current_prototype_sha256:
        errors.append("prototype source SHA-256 does not match the current prototype")

    try:
        canonical = canonical_source(root=root)
        if report.get("canonical_source_sha256") != _sha256(canonical):
            errors.append("canonical source SHA-256 does not match the current authority")
        _, _, current_generator_sha256 = load_selected_generator(TASK_ID, root=root)
        rule_paths = {
            order: out / "private" / "rules" / f"ring-order-{order}.rkt"
            for order in RING_ORDERS
        }
        rules = {
            order: path.read_text(encoding="utf-8")
            for order, path in rule_paths.items()
        }
        if rules[DEFAULT_RING_ORDER] != canonical:
            errors.append("default rule is not the exact canonical source")
        if rules["smallest_outside"] != materialize_rule(
            "smallest_outside", source=canonical
        ):
            errors.append("alternative rule does not match the declared tail transform")

        manager = nullcontext(bridge) if bridge is not None else RacketBridge()
        with manager as active:
            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                if execute_rule(canonical, pair["input"], bridge=active) != pair["output"]:
                    errors.append(
                        f"canonical replay mismatch: {pair['split']}[{pair['pair_index']}]"
                    )
            episode_rows = report.get("episodes", [])
            if episode_rows != _sorted_unique_episode_rows(episode_rows):
                errors.append("report episodes are not sorted by visible public challenge ID")
            expected_public_write_order = [
                row["public_id"] for row in episode_rows
            ]
            if report.get("public_write_order") != expected_public_write_order:
                errors.append("public write order does not match sorted visible IDs")
            for row in episode_rows:
                private_path = out / row["private_path"]
                public_path = out / row["public_path"]
                episode = json.loads(private_path.read_text(encoding="utf-8"))
                public = json.loads(public_path.read_text(encoding="utf-8"))
                if public != public_challenge(episode):
                    errors.append(
                        f"public/private projection mismatch: {row['public_path']}"
                    )
                actual_public_id = public_challenge_id(public)
                if row.get("public_id") != actual_public_id:
                    errors.append(f"report public ID mismatch: {row['public_path']}")
                if public_filename(public) != public_path.name:
                    errors.append(f"public content filename mismatch: {row['public_path']}")
                n_train = episode.get("n_train")
                n_test = episode.get("n_test")
                if row.get("n_train") != n_train or row.get("n_test") != n_test:
                    errors.append(f"report/private count mismatch: {private_path.name}")
                if len(episode.get("train", [])) != n_train or len(public.get("train", [])) != n_train:
                    errors.append(f"demonstration count mismatch: {private_path.name}")
                if len(episode.get("test", [])) != n_test or len(public.get("test", [])) != n_test:
                    errors.append(f"query count mismatch: {private_path.name}")
                if episode.get("generator_sha256") != current_generator_sha256 or row.get("generator_sha256") != current_generator_sha256:
                    errors.append(f"generator source SHA-256 mismatch: {private_path.name}")
                chosen = episode["parameters"]["ring_order"]
                if episode.get("racket_sha256") != _sha256(rules[chosen]) or row.get("racket_sha256") != _sha256(rules[chosen]):
                    errors.append(f"Racket source SHA-256 mismatch: {private_path.name}")
                input_digests = [_grid_sha256(pair["input"]) for pair in episode["pairs"]]
                if len(input_digests) != len(set(input_digests)):
                    errors.append(f"episode contains duplicate inputs: {private_path.name}")
                for index, pair in enumerate(episode["pairs"]):
                    actual = execute_rule(rules[chosen], pair["input"], bridge=active)
                    if actual != pair["output"]:
                        errors.append(
                            f"episode label mismatch: {private_path.name} pair {index}"
                        )
                analysis = analyze_episode(episode, root=root, bridge=active)
                if analysis["status"] != "no_ambiguity_found":
                    errors.append(f"episode ambiguity: {private_path.name}")
    except Exception as exc:
        errors.append(f"semantic verification: {type(exc).__name__}: {exc}")

    if report.get("status") != "no_ambiguity_found":
        errors.append(f"report status is {report.get('status')!r}")
    return {
        "schema": f"{SCHEMA}-verification-v1",
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "manifest_files_checked": len(manifest.get("files", {})),
        "episodes_checked": len(report.get("episodes", [])),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    materialize_parser = subparsers.add_parser("materialize", help="write fresh evidence")
    materialize_parser.add_argument("--seed", type=int, default=0)
    materialize_parser.add_argument("--demos", type=int, default=2)
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
