#!/usr/bin/env python3
"""Build bounded learnability and public-projection evidence for 629ec8fd452e.

This tool deliberately keeps two responsibilities small and reusable:

* finite-rival teaching audit: only demonstrations may eliminate a candidate;
  query labels are used solely to detect a surviving wrong rule;
* one-query public projections: stable first-turn bytes, opaque visible hashes,
  and no private setting/program/seed/query-answer leakage;
* public-check normalization: remove checkout-specific absolute paths before
  evidence is inventoried or returned.

Native qualification remains the authority for protected-Racket labels.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence


HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load("_629ec8fd452e_verify_prototype", HERE / "prototype.py")
ADAPTER = _load("_629ec8fd452e_verify_adapter", HERE / "adapter.py")


def _reviewer_support():
    for parent in HERE.parents:
        source = parent / "shared" / "runtime" / "reviewer_support.py"
        if source.is_file() and not source.is_symlink():
            return _load("_629ec8fd452e_verify_reviewer_support", source)
    raise FileNotFoundError("cannot locate this checkout's reviewer_support.py")


SUPPORT = _reviewer_support()
Grid = list[list[int]]
Pair = dict[str, Grid]
Candidate = Callable[[Grid], Grid]


def _literal_query_index(value: Any, count: int) -> int:
    if type(value) is not int or not 0 <= value < count:
        raise ValueError(f"query_index must be a literal integer in 0..{count - 1}")
    return value


def one_query_projection(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    """Expose all demonstrations and exactly one input-only query."""
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not train or type(test) is not list or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    query_index = _literal_query_index(query_index, len(test))
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": deepcopy(test[query_index]["input"])}],
    }


def public_projection_payload(episode: dict[str, Any], query_index: int) -> bytes:
    return SUPPORT.public_challenge_bytes(one_query_projection(episode, query_index))


def public_projection_id(episode: dict[str, Any], query_index: int) -> str:
    return hashlib.sha256(public_projection_payload(episode, query_index)).hexdigest()


def write_public_projection_batch(
    records: Iterable[dict[str, Any]], destination: Path | str
) -> list[dict[str, Any]]:
    """Preflight then write unique hash-named one-query public challenges.

    The returned rows are a private index; their setting/seed/query ordinal must
    not be copied into model-visible filenames or directories.
    """
    prepared: dict[str, tuple[bytes, dict[str, Any]]] = {}
    for record in records:
        if type(record) is not dict or set(record) != {"seed", "output_scope", "episode"}:
            raise ValueError("records must contain exactly seed, output_scope and episode")
        if type(record["seed"]) is not int or record["seed"] < 0:
            raise ValueError("record seed must be a nonnegative literal integer")
        mode = record["output_scope"]
        PROTOTYPE.validate_settings({"output_scope": mode})
        episode = record["episode"]
        if type(episode) is not dict or type(episode.get("test")) is not list:
            raise ValueError("record episode must contain a test list")
        for query_index in range(len(episode["test"])):
            payload = public_projection_payload(episode, query_index)
            identifier = hashlib.sha256(payload).hexdigest()
            if identifier in prepared:
                raise ValueError(f"duplicate visible challenge: {identifier}")
            prepared[identifier] = (
                payload,
                {
                    "public_id": identifier,
                    "filename": f"{identifier}.json",
                    "seed": record["seed"],
                    "output_scope": mode,
                    "query_index": query_index,
                },
            )
    if not prepared:
        raise ValueError("at least one public projection is required")

    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"public destination already exists: {destination}")
    destination.mkdir(parents=True, exist_ok=False)
    created: list[Path] = []
    try:
        rows: list[dict[str, Any]] = []
        for identifier in sorted(prepared):
            payload, row = prepared[identifier]
            path = destination / row["filename"]
            with path.open("xb") as handle:
                handle.write(payload)
            created.append(path)
            rows.append(row)
        return rows
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        destination.rmdir()
        raise


def _analysis(grid: Grid) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    analysis = PROTOTYPE.GEN._analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid: " + "; ".join(analysis["errors"]))
    components = analysis["components"]
    hollow = [component for component in components if component["has_hole"]]
    if not hollow:
        raise ValueError("audit grid needs at least one true-hole component")
    return components, hollow


def _blank(grid: Grid) -> Grid:
    return [[0 for _ in row] for row in grid]


def _paint(grid: Grid, components: Iterable[dict[str, Any]]) -> Grid:
    out = _blank(grid)
    for component in components:
        for row, col in component["cells"]:
            out[row][col] = component["color"]
    return out


def _broadcast_color(grid: Grid, color: int) -> Grid:
    components, _hollow = _analysis(grid)
    return _paint(grid, (component for component in components if component["color"] == color))


def _hole_area(component: dict[str, Any]) -> int:
    return sum(len(region) for region in component["holes"])


def _largest_hole_source(hollow: Sequence[dict[str, Any]]) -> dict[str, Any]:
    # Python max and the Racket pick-max both retain the first maximum.
    return max(hollow, key=_hole_area)


def _largest_single_hole_area(component: dict[str, Any]) -> int:
    return max((len(region) for region in component["holes"]), default=0)


def _candidate_functions(grid: Grid, selected_mode: str) -> dict[str, Candidate]:
    components, hollow = _analysis(grid)
    source = _largest_hole_source(hollow)
    color_totals: dict[int, int] = {}
    for component in components:
        color_totals[component["color"]] = color_totals.get(component["color"], 0) + len(
            component["cells"]
        )

    other_mode = (
        "largest_hole_color_relay" if selected_mode == "all_holes" else "all_holes"
    )

    def constant(value: Grid) -> Candidate:
        return lambda _grid: deepcopy(value)

    first_hole = hollow[0]
    last_hole = hollow[-1]
    largest_foreground = max(components, key=lambda component: len(component["cells"]))
    smallest_hole = min(hollow, key=_hole_area)
    largest_single_hole = max(hollow, key=_largest_single_hole_area)
    most_holes = max(hollow, key=lambda component: len(component["holes"]))
    most_frequent_color = max(color_totals, key=color_totals.get)

    values: dict[str, Grid] = {
        "declared_other_setting": PROTOTYPE.transform(grid, {"output_scope": other_mode}),
        "first_hole_color_broadcast": _broadcast_color(grid, first_hole["color"]),
        "last_hole_color_broadcast": _broadcast_color(grid, last_hole["color"]),
        "largest_foreground_color_broadcast": _broadcast_color(
            grid, largest_foreground["color"]
        ),
        "smallest_hole_area_color_broadcast": _broadcast_color(
            grid, smallest_hole["color"]
        ),
        "largest_single_hole_color_broadcast": _broadcast_color(
            grid, largest_single_hole["color"]
        ),
        "most_holes_color_broadcast": _broadcast_color(grid, most_holes["color"]),
        "most_frequent_color_broadcast": _broadcast_color(grid, most_frequent_color),
        "winning_source_only": _paint(grid, [source]),
        "winning_hollow_color_only": _paint(
            grid,
            (component for component in hollow if component["color"] == source["color"]),
        ),
        "bbox_interior_missing": _paint(
            grid,
            (
                component
                for component in components
                if component["bbox_interior_missing"]
            ),
        ),
        "rectangular_frame_only": _paint(
            grid,
            (component for component in components if component["rectangular_frame"]),
        ),
        "first_hole_only": _paint(grid, [first_hole]),
    }
    return {name: constant(value) for name, value in values.items()}


def rival_outputs(grid: Grid, selected_mode: str) -> dict[str, Grid]:
    if selected_mode not in PROTOTYPE.MODES:
        raise ValueError("unsupported selected mode")
    return {
        name: candidate(grid)
        for name, candidate in _candidate_functions(grid, selected_mode).items()
    }


def finite_rival_audit(
    *, seeds: Iterable[int] = range(64), demo_counts: Iterable[int] = (2, 3, 6)
) -> dict[str, Any]:
    """Check whether a finite wrong rule fits demos yet fails a hidden query."""
    seed_values = tuple(seeds)
    demo_values = tuple(demo_counts)
    if not seed_values or any(type(seed) is not int or seed < 0 for seed in seed_values):
        raise ValueError("seeds must be nonempty nonnegative literal integers")
    if not demo_values or any(type(count) is not int or not 2 <= count <= 6 for count in demo_values):
        raise ValueError("demo_counts must contain literal integers in 2..6")

    failures: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    finite_rivals: set[str] = set()
    refutation_witnesses: dict[str, dict[str, Any]] = {}

    for seed in seed_values:
        matched_inputs: dict[str, list[Grid]] = {}
        for demos in demo_values:
            for mode in PROTOTYPE.MODES:
                episode = ADAPTER.generate(seed, {"output_scope": mode}, demos, 4)
                matched_inputs[mode] = [
                    pair["input"] for pair in episode["train"] + episode["test"]
                ]
                # Compute each pair's complete finite-rival map once.  Re-running
                # topology analysis for every rival made the 64-seed audit needlessly
                # quadratic in the number of named candidates.
                train_rivals = [
                    rival_outputs(pair["input"], mode) for pair in episode["train"]
                ]
                test_rivals = [
                    rival_outputs(pair["input"], mode) for pair in episode["test"]
                ]
                candidate_names = tuple(train_rivals[0])
                finite_rivals.update(candidate_names)
                survivors: list[str] = []
                unresolved: list[dict[str, Any]] = []
                for name in candidate_names:
                    demo_predictions = [outputs[name] for outputs in train_rivals]
                    demo_matches = all(
                        predicted == pair["output"]
                        for predicted, pair in zip(demo_predictions, episode["train"])
                    )
                    if not demo_matches and name not in refutation_witnesses:
                        first = next(
                            index
                            for index, (predicted, pair) in enumerate(
                                zip(demo_predictions, episode["train"])
                            )
                            if predicted != pair["output"]
                        )
                        refutation_witnesses[name] = {
                            "seed": seed,
                            "demos": demos,
                            "output_scope": mode,
                            "split": "train",
                            "pair_index": first,
                        }
                    if not demo_matches:
                        continue
                    survivors.append(name)
                    query_disagreements = [
                        index
                        for index, (outputs, pair) in enumerate(
                            zip(test_rivals, episode["test"])
                        )
                        if outputs[name] != pair["output"]
                    ]
                    if query_disagreements:
                        issue = {
                            "seed": seed,
                            "demos": demos,
                            "output_scope": mode,
                            "rival": name,
                            "query_disagreements": query_disagreements,
                        }
                        unresolved.append(issue)
                        failures.append(issue)
                records.append(
                    {
                        "seed": seed,
                        "demos": demos,
                        "output_scope": mode,
                        "demo_survivors": survivors,
                        "unresolved_query_disagreements": unresolved,
                    }
                )
            if matched_inputs.get(PROTOTYPE.MODES[0]) != matched_inputs.get(PROTOTYPE.MODES[1]):
                failures.append(
                    {
                        "seed": seed,
                        "demos": demos,
                        "failure": "setting-dependent inputs",
                    }
                )

    return {
        "schema": "629ec8fd452e-finite-rival-audit-v1",
        "status": "failed" if failures else "passed",
        "episodes_checked": len(seed_values) * len(demo_values) * len(PROTOTYPE.MODES),
        "seeds": list(seed_values),
        "demo_counts": list(demo_values),
        "queries_per_episode": 4,
        "settings": list(PROTOTYPE.MODES),
        "finite_rivals": sorted(finite_rivals),
        "refutation_witnesses": refutation_witnesses,
        "records": records,
        "failures": failures,
        "limits": (
            "Finite declared settings and named shortcuts only; passing does not prove "
            "uniqueness against every ARC program. Query labels only detect surviving "
            "wrong rules and never eliminate a candidate."
        ),
    }


def normalize_public_check_paths(
    report: dict[str, Any], repository_root: Path | str
) -> dict[str, Any]:
    """Return a copy whose report paths are portable repository-relative POSIX paths."""
    if type(report) is not dict:
        raise ValueError("public-check report must be a dictionary")
    root = Path(repository_root).resolve()
    if not root.is_dir() or root.is_symlink():
        raise ValueError("repository_root must be a regular directory")

    def normalize(raw: Any) -> str:
        if type(raw) is not str:
            raise ValueError("public-check paths must be strings")
        if raw == "":
            return raw
        candidate = Path(raw)
        absolute = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
        try:
            relative = absolute.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"public-check path outside repository root: {raw}") from exc
        return relative.as_posix()

    normalized = deepcopy(report)
    files = normalized.get("files", [])
    findings = normalized.get("findings", [])
    if type(files) is not list or type(findings) is not list:
        raise ValueError("public-check files and findings must be lists")
    for row in files:
        if type(row) is not dict or "path" not in row:
            raise ValueError("each public-check file row must contain path")
        row["path"] = normalize(row["path"])
    for finding in findings:
        if type(finding) is not dict:
            raise ValueError("each public-check finding must be a dictionary")
        if "path" in finding:
            finding["path"] = normalize(finding["path"])
    return normalized


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_evidence(
    destination: Path | str,
    *,
    public_seeds: tuple[int, int] = (0, 17),
    demos: int = 3,
    audit_seeds: int = 64,
) -> dict[str, Any]:
    """Materialize compact authoring evidence without executing Racket."""
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"evidence destination already exists: {destination}")
    if (
        type(public_seeds) is not tuple
        or len(public_seeds) != 2
        or len(set(public_seeds)) != 2
        or any(type(seed) is not int or seed < 0 for seed in public_seeds)
    ):
        raise ValueError("public_seeds must be two distinct nonnegative literal integers")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be a literal integer in 2..6")
    if type(audit_seeds) is not int or not 1 <= audit_seeds <= 256:
        raise ValueError("audit_seeds must be a literal integer in 1..256")

    destination.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, Any]] = []
    private_episodes: list[dict[str, Any]] = []
    for seed in public_seeds:
        for mode in PROTOTYPE.MODES:
            episode = ADAPTER.generate(seed, {"output_scope": mode}, demos, 4)
            records.append({"seed": seed, "output_scope": mode, "episode": episode})
            private_episodes.append(
                {
                    "seed": seed,
                    "output_scope": mode,
                    "program_sha256": hashlib.sha256(
                        episode["program_solution"].encode()
                    ).hexdigest(),
                    "teaching_check": ADAPTER.teaching_check(episode),
                }
            )

    public_rows = write_public_projection_batch(records, destination / "public")
    audit = finite_rival_audit(seeds=range(audit_seeds), demo_counts=(2, 3, 6))
    summary = {
        "schema": "629ec8fd452e-parametric-authoring-evidence-v1",
        "status": audit["status"],
        "task_id": "629ec8fd452e",
        "settings": list(PROTOTYPE.MODES),
        "default": PROTOTYPE.DEFAULT_MODE,
        "public_seeds": list(public_seeds),
        "demonstrations": demos,
        "queries_per_episode": 4,
        "one_query_public_files": len(public_rows),
        "public_projection": {
            "queries_visible_per_file": 1,
            "future_queries_visible": False,
            "query_answers_visible": False,
            "settings_programs_and_seeds_visible": False,
            "identifier": "SHA-256 of exact reviewer_support.public_challenge_bytes",
            "first_turn_matches_single_query_generation": True,
        },
        "teaching_audit": {
            "status": audit["status"],
            "episodes_checked": audit["episodes_checked"],
            "finite_rivals": audit["finite_rivals"],
            "failures": len(audit["failures"]),
        },
        "program_sha256": {
            mode: hashlib.sha256(ADAPTER.program({"output_scope": mode}).encode()).hexdigest()
            for mode in PROTOTYPE.MODES
        },
        "limitations": [
            "This authoring evidence does not execute Racket; native qualification does.",
            "The teaching audit covers only the named finite rivals.",
            "The owner must qualify and accept the exact integrated source before use.",
        ],
    }
    _write_json(destination / "private-index.json", {"episodes": private_episodes, "public": public_rows})
    _write_json(destination / "teaching-audit.json", audit)
    _write_json(destination / "summary.json", summary)
    return summary


def _parse_seed_pair(text: str) -> tuple[int, int]:
    try:
        values = tuple(int(part) for part in text.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("use two comma-separated integers") from exc
    if len(values) != 2:
        raise argparse.ArgumentTypeError("use exactly two comma-separated integers")
    return values  # type: ignore[return-value]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--normalize-public-check",
        metavar="REPORT",
        help="normalize a check_public_exports.py JSON report instead of building evidence",
    )
    parser.add_argument(
        "--repo-root",
        help="repository root used with --normalize-public-check",
    )
    parser.add_argument("--public-seeds", type=_parse_seed_pair, default=(0, 17))
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--audit-seeds", type=int, default=64)
    args = parser.parse_args()

    if args.normalize_public_check is not None:
        if args.repo_root is None:
            parser.error("--repo-root is required with --normalize-public-check")
        destination = Path(args.out)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"normalization destination already exists: {destination}")
        source = Path(args.normalize_public_check)
        report = json.loads(source.read_text(encoding="utf-8"))
        normalized = normalize_public_check_paths(report, args.repo_root)
        _write_json(destination, normalized)
        print(
            json.dumps(
                {
                    "status": normalized.get("status"),
                    "files_checked": normalized.get("files_checked"),
                    "out": str(destination),
                },
                sort_keys=True,
            )
        )
        return 0 if normalized.get("status") == "passed" else 1
    if args.repo_root is not None:
        parser.error("--repo-root is only valid with --normalize-public-check")

    summary = build_evidence(
        args.out,
        public_seeds=args.public_seeds,
        demos=args.demos,
        audit_seeds=args.audit_seeds,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
