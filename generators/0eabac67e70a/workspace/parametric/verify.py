#!/usr/bin/env python3
"""Build bounded teaching and public-projection evidence for 0eabac67e70a."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load_module("pair_span_scope_verify_prototype", HERE / "prototype.py")
ADAPTER = _load_module("pair_span_scope_verify_adapter", HERE / "adapter.py")


def _reviewer_support():
    for parent in HERE.parents:
        source = parent / "shared" / "runtime" / "reviewer_support.py"
        if source.is_file() and not source.is_symlink():
            return _load_module("pair_span_scope_verify_reviewer_support", source)
    raise FileNotFoundError("cannot locate this checkout's reviewer_support.py")


SUPPORT = _reviewer_support()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _literal_query_index(value: Any, count: int) -> int:
    if type(value) is not int or not 0 <= value < count:
        raise ValueError(f"query_index must be a literal integer in 0..{count - 1}")
    return value


def public_projection(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    """Expose demonstrations and exactly one input-only query."""
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    query_index = _literal_query_index(query_index, len(test))
    return {
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }


def public_payload(episode: dict[str, Any], query_index: int) -> bytes:
    return SUPPORT.public_challenge_bytes(public_projection(episode, query_index))


def public_id(episode: dict[str, Any], query_index: int) -> str:
    return sha256_bytes(public_payload(episode, query_index))


def write_public_projection_batch(
    records: Iterable[dict[str, Any]], destination: Path | str
) -> list[dict[str, Any]]:
    """Preflight and write unique one-query projections with private index rows."""
    prepared: dict[str, tuple[bytes, dict[str, Any]]] = {}
    for record in records:
        if type(record) is not dict or set(record) != {"seed", "span_scope", "episode"}:
            raise ValueError("records must contain exactly seed, span_scope and episode")
        seed = record["seed"]
        scope = PROTOTYPE.validate_scope(record["span_scope"])
        episode = record["episode"]
        query_count = len(episode.get("test", [])) if type(episode) is dict else 0
        for query_index in range(query_count):
            payload = public_payload(episode, query_index)
            identifier = sha256_bytes(payload)
            if identifier in prepared:
                raise ValueError(f"duplicate visible challenge: {identifier}")
            prepared[identifier] = (
                payload,
                {
                    "public_id": identifier,
                    "filename": f"{identifier}.json",
                    "seed": seed,
                    "span_scope": scope,
                    "query_index": query_index,
                },
            )
    if not prepared:
        raise ValueError("at least one public projection is required")
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"public destination already exists: {destination}")
    ordered = [prepared[key] for key in sorted(prepared)]
    destination.mkdir(parents=True, exist_ok=False)
    created: list[Path] = []
    try:
        for payload, row in ordered:
            path = destination / row["filename"]
            with path.open("xb") as handle:
                created.append(path)
                handle.write(payload)
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        destination.rmdir()
        raise
    return [row for _payload, row in ordered]


def _setting_survivors(demos: list[dict[str, Any]]) -> list[str]:
    return [
        scope
        for scope in PROTOTYPE.SCOPES
        if all(PROTOTYPE.output_for(pair["input"], scope) == pair["output"] for pair in demos)
    ]


def _teaching_audit() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for seed in range(12):
        for demos in (2, 3, 6):
            paired: dict[str, Any] = {}
            for scope in PROTOTYPE.SCOPES:
                episode = ADAPTER.generate(seed, {"span_scope": scope}, demos, 4)
                survivors = _setting_survivors(episode["train"])
                row = {
                    "seed": seed,
                    "demos": demos,
                    "span_scope": scope,
                    "setting_survivors": survivors,
                }
                if survivors != [scope]:
                    failures.append({**row, "failure": "declared setting not uniquely identified"})
                if scope == "junction_cluster":
                    rival_audit = PROTOTYPE.audit_teaching_set(episode["train"])
                    row["rivals"] = rival_audit["rivals"]
                    unrefuted = [
                        name for name, result in rival_audit["rivals"].items() if not result["refuted"]
                    ]
                    if unrefuted:
                        failures.append({**row, "failure": "unrefuted rivals", "names": unrefuted})
                paired[scope] = episode
                rows.append(row)
            inputs_a = [pair["input"] for pair in paired["all_pairs"]["train"] + paired["all_pairs"]["test"]]
            inputs_b = [pair["input"] for pair in paired["junction_cluster"]["train"] + paired["junction_cluster"]["test"]]
            if inputs_a != inputs_b:
                failures.append({"seed": seed, "demos": demos, "failure": "setting inputs differ"})
            for index, (left, right) in enumerate(
                zip(
                    paired["all_pairs"]["train"] + paired["all_pairs"]["test"],
                    paired["junction_cluster"]["train"] + paired["junction_cluster"]["test"],
                )
            ):
                if left["output"] == right["output"]:
                    failures.append(
                        {"seed": seed, "demos": demos, "pair_index": index, "failure": "settings agree"}
                    )
    return {
        "schema": "arcpuzzles-pair-span-teaching-audit-v1",
        "status": "failed" if failures else "passed",
        "seeds_checked": 12,
        "demo_counts": [2, 3, 6],
        "settings": list(PROTOTYPE.SCOPES),
        "finite_rivals": [
            "fixed_first_demo_colors",
            "two_longest_spans",
            "two_shortest_spans",
            "two_center_nearest_spans",
        ],
        "records": rows,
        "failures": failures,
        "limits": "Finite settings and four named shortcuts only; not a proof of uniqueness against every ARC program.",
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_evidence(
    destination: Path | str, *, seeds: tuple[int, ...] = (0, 17), demos: int = 3
) -> dict[str, Any]:
    destination = Path(destination)
    if destination.is_symlink():
        raise ValueError("evidence destination cannot be a symlink")
    destination.mkdir(parents=True, exist_ok=True)
    seeds = tuple(PROTOTYPE._literal_int("seed", seed, 0, 2**63 - 1) for seed in seeds)
    if len(seeds) != 2 or len(set(seeds)) != 2:
        raise ValueError("evidence requires exactly two distinct seeds")
    demos = PROTOTYPE._literal_int("demos", demos, PROTOTYPE.MIN_DEMOS, PROTOTYPE.MAX_DEMOS)
    records: list[dict[str, Any]] = []
    for seed in seeds:
        for scope in PROTOTYPE.SCOPES:
            records.append(
                {
                    "seed": seed,
                    "span_scope": scope,
                    "episode": ADAPTER.generate(seed, {"span_scope": scope}, demos, 4),
                }
            )
    index_rows = write_public_projection_batch(records, destination / "public")
    teaching = _teaching_audit()
    index = {
        "schema": "arcpuzzles-one-query-projection-index-v1",
        "projection_policy": "one selected query input per public challenge; demos repeat; no total-count hint",
        "projections": index_rows,
    }
    summary = {
        "schema": "arcpuzzles-pair-span-parametric-evidence-v1",
        "status": "passed" if teaching["status"] == "passed" else "failed",
        "task_id": PROTOTYPE.TASK_ID,
        "settings": list(PROTOTYPE.SCOPES),
        "seeds": list(seeds),
        "demonstrations": demos,
        "queries_per_episode": PROTOTYPE.QUERY_COUNT,
        "public_files": len(index_rows),
        "public_projection": {
            "queries_visible_per_file": 1,
            "future_queries_visible": False,
            "query_answers_visible": False,
            "settings_programs_and_seeds_visible": False,
            "identity": "SHA-256 of exact reviewer_support.public_challenge_bytes",
        },
        "teaching_audit": {
            "status": teaching["status"],
            "seeds_checked": teaching["seeds_checked"],
            "demo_counts": teaching["demo_counts"],
            "finite_rivals": teaching["finite_rivals"],
            "failures": teaching["failures"],
        },
        "limits": [
            "Public projection evidence does not execute Racket or certify labels.",
            "Teaching evidence covers two declared settings and four finite shortcut families only.",
        ],
    }
    _write_json(destination / "projection-index.json", index)
    _write_json(destination / "teaching-audit.json", teaching)
    _write_json(destination / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--demos", type=int, default=3)
    options = parser.parse_args()
    seeds = tuple(options.seeds) if options.seeds is not None else (0, 17)
    try:
        summary = build_evidence(options.out, seeds=seeds, demos=options.demos)
    except (OSError, TypeError, ValueError, RuntimeError) as error:
        print(json.dumps({"status": "failed", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
