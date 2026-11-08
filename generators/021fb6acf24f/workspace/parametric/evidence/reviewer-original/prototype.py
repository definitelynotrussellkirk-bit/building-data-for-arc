"""Proposed episode-level color-order extension for ARC task 021fb6acf24f.

This is task-local prototype evidence only.  It does not alter the canonical
Racket authority or add a production generator axis.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import nullcontext
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "021fb6acf24f"
VERSION = "1.0.0"
SCHEMA = "arcpuzzles-color-order-prototype-v1"
COLOR_ORDERS = ("ascending", "descending")
DEFAULT_COLOR_ORDER = "ascending"
CANONICAL_SHA256 = "f7b49e9ffb4c0dcaa332d46e67bd1f4d5c9be35200705fc34f394548380bcbb3"
CANONICAL_COLOR_EXPRESSION = """(filter (lambda (v) (!= 0 v))
                                (unique (map third (grid-cells g))))"""
DESCENDING_COLOR_EXPRESSION = """(reverse (filter (lambda (v) (!= 0 v))
                                (unique (map third (grid-cells g)))))"""

FIXTURE_SPECS = (
    {
        "fixture_id": "compact-easy",
        "seed": 101,
        "sample_index": 1,
        "difficulty": "easy",
        "overrides": {"grid_h": 7, "grid_w": 8, "n_colors": 2},
    },
    {
        "fixture_id": "medium-wide",
        "seed": 202,
        "sample_index": 2,
        "difficulty": "medium",
        "overrides": {"grid_h": 9, "grid_w": 10, "n_colors": 2},
    },
    {
        "fixture_id": "large-hard",
        "seed": 303,
        "sample_index": 3,
        "difficulty": "hard",
        "overrides": {"grid_h": 10, "grid_w": 11, "n_colors": 2},
    },
    {
        "fixture_id": "small-tall-default",
        "seed": 404,
        "sample_index": 7,
        "difficulty": None,
        "overrides": {"grid_h": 6, "grid_w": 9, "n_colors": 2},
    },
)


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _grid_sha256(grid: Any) -> str:
    normalized = normalize_grid(grid)
    return _sha256(json.dumps(normalized, separators=(",", ":"), sort_keys=False))


def _validate_seed(seed: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")


def _validate_color_order(color_order: Any) -> None:
    if type(color_order) is not str or color_order not in COLOR_ORDERS:
        raise ValueError("color_order must be exactly 'ascending' or 'descending'")


def _check_canonical_source(source: Any) -> str:
    if not isinstance(source, str):
        raise ValueError("canonical Racket source must be text")
    actual = _sha256(source)
    if actual != CANONICAL_SHA256:
        raise ValueError(
            f"canonical Racket source hash mismatch: {actual} != {CANONICAL_SHA256}"
        )
    if source.count(CANONICAL_COLOR_EXPRESSION) != 1:
        raise ValueError("canonical source does not contain the unique color expression")
    if DESCENDING_COLOR_EXPRESSION in source:
        raise ValueError("canonical source unexpectedly contains descending color order")
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
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical source for {TASK_ID}, got {len(sources)}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    color_order: str = DEFAULT_COLOR_ORDER,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    """Instantiate one declared setting while preserving the exact default."""
    _validate_color_order(color_order)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if color_order == DEFAULT_COLOR_ORDER:
        return canonical
    alternative = canonical.replace(
        CANONICAL_COLOR_EXPRESSION,
        DESCENDING_COLOR_EXPRESSION,
        1,
    )
    if alternative.count(DESCENDING_COLOR_EXPRESSION) != 1:
        raise AssertionError("failed to materialize descending color order")
    return alternative


def _restore_canonical(source: Any) -> str:
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    canonical_count = source.count(CANONICAL_COLOR_EXPRESSION)
    descending_count = source.count(DESCENDING_COLOR_EXPRESSION)
    # The canonical expression is a literal substring of the wrapped descending
    # expression, so recognize the more specific form first.
    if descending_count == 1:
        restored = source.replace(
            DESCENDING_COLOR_EXPRESSION,
            CANONICAL_COLOR_EXPRESSION,
            1,
        )
    elif canonical_count == 1:
        restored = source
    else:
        raise ValueError("Racket source must contain exactly one declared color expression")
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


def _load_fixture_generator(root: Path):
    """Load this task's source mirror without crossing dependency trees.

    Portable task tests intentionally include both an execution layout and a
    repository-layout mirror. Other tests may already have imported
    ``puzzle_generators`` from ``shared/runtime`` before this prototype runs, so
    asking ``load_selected_generator`` to switch to the execution layout would
    correctly trip its cross-tree guard. The task-local prototype only needs its
    own source bytes; load the repository-layout mirror that travels beside the
    tests and record its exact hash.
    """
    explicit = os.environ.get("GENERATOR_UNDER_TEST")
    source = Path(explicit).resolve() if explicit else (
        root / "generators" / TASK_ID / "generator.py"
    ).resolve()
    if not source.is_file() or not source.is_relative_to(root):
        raise ValueError(f"selected generator source is unavailable or unsafe: {source}")
    body = source.read_bytes()
    digest = _sha256(body)
    spec = importlib.util.spec_from_file_location(
        f"_parametric_fixture_{TASK_ID}_{digest}", source
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load selected generator from {source}")
    module = importlib.util.module_from_spec(spec)
    dependency_root = root / "shared" / "runtime"
    before_path = list(sys.path)
    try:
        if dependency_root.is_dir():
            sys.path.insert(0, str(dependency_root))
        exec(compile(body, str(source), "exec"), module.__dict__)
    finally:
        sys.path[:] = before_path
    return module, source, digest


def fixtures(*, root: Path | str | None = None) -> list[dict[str, Any]]:
    """Generate four fixed legal overlap contests independent of the parameter."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    generator, generator_path, generator_sha256 = _load_fixture_generator(root)
    rows: list[dict[str, Any]] = []
    for spec in FIXTURE_SPECS:
        overrides = copy.deepcopy(spec["overrides"])
        grid = generator.generate(
            spec["seed"],
            spec["sample_index"],
            difficulty=spec["difficulty"],
            **overrides,
        )
        errors = generator.self_check(grid)
        if errors:
            raise AssertionError(f"fixture {spec['fixture_id']} is outside grammar: {errors}")
        if generator.observe_overrides(grid) != overrides:
            raise AssertionError(f"fixture {spec['fixture_id']} did not honor exact overrides")
        rows.append(
            {
                "fixture_id": spec["fixture_id"],
                "generation": {
                    "seed": spec["seed"],
                    "sample_index": spec["sample_index"],
                    "difficulty": spec["difficulty"],
                    "overrides": overrides,
                    "generator_path": generator_path.relative_to(root).as_posix(),
                    "generator_sha256": generator_sha256,
                },
                "input": normalize_grid(grid),
                "input_sha256": _grid_sha256(grid),
            }
        )
    if len({_grid_sha256(row["input"]) for row in rows}) != len(rows):
        raise AssertionError("fixture inputs must be unique")
    return rows


def parameters_for_seed(seed: Any) -> dict[str, str]:
    _validate_seed(seed)
    return {"color_order": COLOR_ORDERS[seed % len(COLOR_ORDERS)]}


def make_episode(
    seed: int,
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one complete three-demonstration/one-query private episode."""
    _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root).resolve()
    parameters = parameters_for_seed(seed)
    canonical = canonical_source(root=root)
    rules = {
        order: materialize_rule(order, source=canonical) for order in COLOR_ORDERS
    }
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        fixture_rows = fixtures(root=root)
        outputs = {
            order: [
                execute_rule(source, fixture["input"], bridge=active)
                for fixture in fixture_rows
            ]
            for order, source in rules.items()
        }
    for index, fixture in enumerate(fixture_rows):
        if outputs["ascending"][index] == outputs["descending"][index]:
            raise AssertionError(f"fixture {fixture['fixture_id']} does not distinguish settings")

    chosen = parameters["color_order"]
    pairs = []
    for fixture, output in zip(fixture_rows, outputs[chosen], strict=True):
        pairs.append(
            {
                **copy.deepcopy(fixture),
                "color_order": chosen,
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
        "parameter_selection": "COLOR_ORDERS[seed % 2], selected once for all four pairs",
        "input_constraints_depend_on_parameter": False,
        "racket_source": source,
        "racket_sha256": _sha256(source),
        "pairs": pairs,
        "train": copy.deepcopy(pairs[:3]),
        "test": copy.deepcopy(pairs[3:]),
    }


def analyze_episode(
    episode: dict[str, Any],
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Refute the sole alternate setting for production and all query rotations."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    chosen = episode.get("parameters", {}).get("color_order")
    _validate_color_order(chosen)
    rival_order = next(order for order in COLOR_ORDERS if order != chosen)
    rival_source = materialize_rule(rival_order, root=root)
    pairs = episode.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != 4:
        raise ValueError("episode must contain exactly four private pairs")
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        rival_outputs = [
            execute_rule(rival_source, pair["input"], bridge=active) for pair in pairs
        ]

    def score(query_index: int) -> dict[str, Any]:
        demonstrations = [index for index in range(4) if index != query_index]
        refutations = [
            index
            for index in demonstrations
            if rival_outputs[index] != pairs[index]["output"]
        ]
        query_differs = rival_outputs[query_index] != pairs[query_index]["output"]
        fits = not refutations
        return {
            "query_index": query_index,
            "demonstration_indices": demonstrations,
            "rival": {
                "name": f"color_order={rival_order}",
                "parameters": {"color_order": rival_order},
                "racket_sha256": _sha256(rival_source),
                "refuting_demonstration_indices": refutations,
                "fits_demonstrations": fits,
                "query_differs": query_differs,
            },
            "status": "ambiguous" if fits and query_differs else "no_ambiguity_found",
        }

    return {
        "production": score(3),
        "rotations": [score(index) for index in range(4)],
        "counterfactual_color_order": rival_order,
        "counterfactual_outputs": rival_outputs,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project private episode evidence to ordinary ARC challenge JSON."""
    pairs = episode.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != 4:
        raise ValueError("episode must contain exactly four private pairs")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in pairs[:3]
        ],
        "test": [{"input": copy.deepcopy(pairs[3]["input"])}],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_inventory(out: Path, *, exclude: tuple[str, ...] = ()) -> dict[str, dict[str, Any]]:
    omitted = set(exclude)
    return {
        path.relative_to(out).as_posix(): {
            "sha256": _sha256(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
        for path in sorted(out.rglob("*"))
        if path.is_file() and path.relative_to(out).as_posix() not in omitted
    }


def materialize(
    out: Path | str,
    *,
    seed: int = 0,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Create a new public/private evidence tree covering both settings."""
    _validate_seed(seed)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__) if root is None else Path(root).resolve()
    generator, generator_path, generator_sha = _load_fixture_generator(root)
    del generator
    canonical = canonical_source(root=root)
    rules = {order: materialize_rule(order, source=canonical) for order in COLOR_ORDERS}
    report: dict[str, Any] = {
        "schema": f"{SCHEMA}-report-v1",
        "status": "incomplete",
        "scope": "Proposed unapproved task-local extension; canonical authority and production axes unchanged.",
        "parameter_spec": {
            "color_order": {
                "allowed": list(COLOR_ORDERS),
                "original_default": DEFAULT_COLOR_ORDER,
                "meaning": "Ascending or descending numeric order for zero-only bbox fill precedence.",
            }
        },
        "choice_policy": "Exactly one value per episode: COLOR_ORDERS[seed % 2].",
        "lesson_policy": "Three demonstrations plus one query; test every single-query rotation.",
        "source_hashes": {
            "prototype.py": _sha256(Path(__file__).read_bytes()),
            "selected_generator": generator_sha,
            "selected_generator_path": generator_path.relative_to(root).as_posix(),
            "canonical_racket": _sha256(canonical),
        },
        "invocation": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv], "seed": seed},
        "canonical_checks": [],
        "episodes": [],
    }
    try:
        manager = nullcontext(bridge) if bridge is not None else RacketBridge()
        with manager as active:
            report["runtime"] = {
                "python": sys.version,
                "racket_version": active.eval_text("(version)"),
                "bridge_sha256": _sha256(Path(sys.modules[RacketBridge.__module__].__file__).read_bytes()),
                "prelude_sha256": _sha256(Path(active.prelude_path).read_bytes()),
            }
            for order, source in rules.items():
                path = out / "private" / "rules" / f"color-order-{order}.rkt"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")

            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute_rule(rules[DEFAULT_COLOR_ORDER], pair["input"], bridge=active)
                report["canonical_checks"].append(
                    {
                        "variant": pair["variant"],
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "passed": actual == pair["output"],
                    }
                )

            for index in range(2):
                episode = make_episode(seed + index, root=root, bridge=active)
                analysis = analyze_episode(episode, root=root, bridge=active)
                public_path = f"public/episode-{index + 1:03d}.json"
                private_path = f"private/episode-{index + 1:03d}.json"
                _write_json(out / public_path, public_challenge(episode))
                _write_json(out / private_path, {**episode, "rival_checks": analysis})
                report["episodes"].append(
                    {
                        "seed": episode["seed"],
                        "parameters": episode["parameters"],
                        "racket_sha256": episode["racket_sha256"],
                        "public_path": public_path,
                        "private_path": private_path,
                        "production": analysis["production"],
                        "rotations": analysis["rotations"],
                    }
                )

            canonical_passed = sum(row["passed"] for row in report["canonical_checks"])
            production_ambiguities = sum(
                row["production"]["status"] == "ambiguous" for row in report["episodes"]
            )
            rotation_ambiguities = sum(
                score["status"] == "ambiguous"
                for row in report["episodes"]
                for score in row["rotations"]
            )
            settings_seen = {
                row["parameters"]["color_order"] for row in report["episodes"]
            }
            report["counts"] = {
                "canonical_labels_checked": len(report["canonical_checks"]),
                "canonical_labels_passed": canonical_passed,
                "episodes": 2,
                "demonstrations": 6,
                "queries": 2,
                "episode_labels": 8,
                "counterfactual_labels": 8,
                "production_ambiguities": production_ambiguities,
                "rotation_ambiguities": rotation_ambiguities,
                "query_rotations": 8,
            }
            report["status"] = (
                "no_ambiguity_found"
                if canonical_passed == len(report["canonical_checks"])
                and production_ambiguities == 0
                and rotation_ambiguities == 0
                and settings_seen == set(COLOR_ORDERS)
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
        {"schema": f"{SCHEMA}-manifest-v1", "files": _file_inventory(out)},
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
    """Verify hashes, privacy projection, Racket labels, and rival analysis."""
    out = Path(out).resolve()
    root = find_root(__file__) if root is None else Path(root).resolve()
    errors: list[str] = []
    try:
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return {"schema": f"{SCHEMA}-verification-v1", "status": "fail", "errors": [f"metadata: {type(exc).__name__}: {exc}"]}

    for relative, expected in manifest.get("files", {}).items():
        path = out / relative
        if not path.is_file():
            errors.append(f"missing manifest file: {relative}")
            continue
        if path.stat().st_size != expected.get("bytes"):
            errors.append(f"byte count mismatch: {relative}")
        if _sha256(path.read_bytes()) != expected.get("sha256"):
            errors.append(f"sha256 mismatch: {relative}")

    try:
        canonical = canonical_source(root=root)
        rule_paths = {
            order: out / "private" / "rules" / f"color-order-{order}.rkt"
            for order in COLOR_ORDERS
        }
        rules = {order: path.read_text(encoding="utf-8") for order, path in rule_paths.items()}
        if rules["ascending"] != canonical:
            errors.append("ascending rule is not the exact canonical source")
        if rules["descending"] != materialize_rule("descending", source=canonical):
            errors.append("descending rule does not match the declared one-expression transform")

        manager = nullcontext(bridge) if bridge is not None else RacketBridge()
        with manager as active:
            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                if execute_rule(rules["ascending"], pair["input"], bridge=active) != pair["output"]:
                    errors.append(
                        f"canonical replay mismatch: {pair['split']}[{pair['pair_index']}]"
                    )
            for row in report.get("episodes", []):
                private_path = out / row["private_path"]
                public_path = out / row["public_path"]
                episode = json.loads(private_path.read_text(encoding="utf-8"))
                public = json.loads(public_path.read_text(encoding="utf-8"))
                if public != public_challenge(episode):
                    errors.append(f"public/private projection mismatch: {row['public_path']}")
                chosen = episode["parameters"]["color_order"]
                for index, pair in enumerate(episode["pairs"]):
                    actual = execute_rule(rules[chosen], pair["input"], bridge=active)
                    if actual != pair["output"]:
                        errors.append(f"episode label mismatch: {private_path.name} pair {index}")
                analysis = analyze_episode(episode, root=root, bridge=active)
                if analysis["production"]["status"] != "no_ambiguity_found":
                    errors.append(f"production ambiguity: {private_path.name}")
                if any(score["status"] != "no_ambiguity_found" for score in analysis["rotations"]):
                    errors.append(f"rotation ambiguity: {private_path.name}")
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
    materialize_parser.add_argument("--out", type=Path, required=True)
    verify_parser = subparsers.add_parser("verify", help="verify existing evidence")
    verify_parser.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "materialize":
        result = materialize(args.out, seed=args.seed)
    else:
        result = verify_tree(args.out)
    print(json.dumps(result, sort_keys=True))
    return int(result.get("status") not in {"pass", "no_ambiguity_found"})


if __name__ == "__main__":
    raise SystemExit(main())
