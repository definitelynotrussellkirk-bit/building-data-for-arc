"""Bounded authoring audit for the ``df74e338b4f5`` parametric family.

This tool checks matched inputs, declared-setting identification, pair
uniqueness, public projection hygiene, and a finite set of plausible rivals. It
also writes a source-bound request that can be executed through the packet's
protected Racket worker.  It is intentionally an authoring aid, not a proof of
unique induction and not an acceptance tool.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[3]
_TASK_ID = "df74e338b4f5"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load("_arc_df74e338b4f5_audit_prototype", _HERE / "prototype.py")
_ADAPTER = _load("_arc_df74e338b4f5_audit_adapter", _HERE / "adapter.py")


def _raw(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _literal_ints(name: str, values: Iterable[int], low: int, high: int) -> tuple[int, ...]:
    result = tuple(values)
    if not result or any(type(value) is not int or not low <= value <= high for value in result):
        raise ValueError(f"{name} must be nonempty literal integers in [{low}, {high}]")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must not contain duplicates")
    return result


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _setting_survivors(episode: dict[str, Any]) -> list[str]:
    return [
        scope
        for scope in _PROTOTYPE.SCOPES
        if all(
            _PROTOTYPE.apply_scope(pair["input"], scope) == pair["output"]
            for pair in episode["train"]
        )
    ]


def _job_record(seed: int, demos: int, queries: int, scope: str, episode: dict[str, Any]) -> dict:
    pairs = episode["train"] + episode["test"]
    encoded_inputs = [_raw(pair["input"]) for pair in pairs]
    if len(set(encoded_inputs)) != len(encoded_inputs):
        raise RuntimeError(f"duplicate input in seed={seed}, demos={demos}, scope={scope}")
    for pair in pairs:
        expected = _PROTOTYPE.apply_scope(pair["input"], scope)
        if expected != pair["output"]:
            raise RuntimeError(f"Python claim mismatch in seed={seed}, demos={demos}, scope={scope}")

    rival_rows: dict[str, dict[str, list[int]]] = {}
    visible_survivors: list[str] = []
    no_query_disagreement: list[str] = []
    for name, rival in _PROTOTYPE.audit_rivals(scope).items():
        demo_disagreements = [
            index
            for index, pair in enumerate(episode["train"])
            if rival(pair["input"]) != pair["output"]
        ]
        query_disagreements = [
            index
            for index, pair in enumerate(episode["test"])
            if rival(pair["input"]) != pair["output"]
        ]
        rival_rows[name] = {
            "demo_disagreements": demo_disagreements,
            "query_disagreements": query_disagreements,
        }
        if not demo_disagreements:
            visible_survivors.append(name)
        if not query_disagreements:
            no_query_disagreement.append(name)

    survivors = _setting_survivors(episode)
    if survivors != [scope]:
        raise RuntimeError(
            f"declared setting is not identified by visible demos: expected {[scope]}, got {survivors}"
        )

    public = _PROTOTYPE.public_projection(episode)
    if set(public) != {"train", "test"}:
        raise RuntimeError("public projection has unexpected top-level fields")
    if any(set(pair) != {"input"} for pair in public["test"]):
        raise RuntimeError("public query projection leaked a field besides input")
    if _PROTOTYPE.public_challenge_id(episode) != hashlib.sha256(
        _PROTOTYPE.public_challenge_bytes(episode)
    ).hexdigest():
        raise RuntimeError("public identifier is not the visible-byte hash")

    analyses = [_PROTOTYPE.analyze(pair["input"]) for pair in pairs]
    return {
        "seed": seed,
        "demos": demos,
        "queries": queries,
        "settings": {"recolor_scope": scope},
        "setting_survivors": survivors[0],
        "visible_demo_survivors": visible_survivors,
        "rivals_without_query_disagreement": no_query_disagreement,
        "rivals": rival_rows,
        "pair_count": len(pairs),
        "distinct_input_count": len(set(encoded_inputs)),
        "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest(),
        "public_challenge_id": episode["public_challenge_id"],
        "shapes": [[analysis["height"], analysis["width"]] for analysis in analyses],
        "selected_positive_depths": [analysis["selected_positive_depth"] for analysis in analyses],
        "positive_depth_histograms": [analysis["positive_depth_counts"] for analysis in analyses],
    }


def build_report(
    *,
    seeds: Iterable[int] = (0, 17, 97),
    demo_counts: Iterable[int] = (2, 3, 6),
    queries: int = 4,
) -> dict:
    """Build a deterministic finite self-audit report without executing Racket."""
    checked_seeds = _literal_ints("seeds", seeds, 0, 2**63 - 1)
    checked_demos = _literal_ints(
        "demo_counts", demo_counts, _PROTOTYPE.MIN_DEMOS, _PROTOTYPE.MAX_DEMOS
    )
    if type(queries) is not int or not _PROTOTYPE.MIN_QUERIES <= queries <= _PROTOTYPE.MAX_QUERIES:
        raise ValueError(
            f"queries must be a literal integer in [{_PROTOTYPE.MIN_QUERIES}, {_PROTOTYPE.MAX_QUERIES}]"
        )

    jobs: list[dict[str, Any]] = []
    for seed in checked_seeds:
        for demos in checked_demos:
            episodes = {
                scope: _ADAPTER.generate(
                    seed, {"recolor_scope": scope}, demos=demos, queries=queries
                )
                for scope in _PROTOTYPE.SCOPES
            }
            baseline_inputs = _inputs(episodes[_PROTOTYPE.DEFAULT_SCOPE])
            for scope, episode in episodes.items():
                if _inputs(episode) != baseline_inputs:
                    raise RuntimeError(
                        f"settings changed inputs for seed={seed}, demos={demos}, scope={scope}"
                    )
                jobs.append(_job_record(seed, demos, queries, scope, episode))

    rival_names = sorted(_PROTOTYPE.audit_rivals(_PROTOTYPE.DEFAULT_SCOPE))
    report = {
        "schema": "nesting-depth-scope-authoring-audit-v1",
        "task_id": _TASK_ID,
        "scope": {
            "seeds": list(checked_seeds),
            "demo_counts": list(checked_demos),
            "queries": queries,
            "settings": [{"recolor_scope": scope} for scope in _PROTOTYPE.SCOPES],
            "rivals": rival_names,
        },
        "source": {
            "adapter": str((_HERE / "adapter.py").relative_to(_ROOT)),
            "adapter_sha256": _sha256(_HERE / "adapter.py"),
            "prototype": str((_HERE / "prototype.py").relative_to(_ROOT)),
            "prototype_sha256": _sha256(_HERE / "prototype.py"),
            "promotion": str((_HERE / "promotion.json").relative_to(_ROOT)),
            "promotion_sha256": _sha256(_HERE / "promotion.json"),
            "program_sha256": {
                scope: hashlib.sha256(_ADAPTER.program({"recolor_scope": scope}).encode()).hexdigest()
                for scope in _PROTOTYPE.SCOPES
            },
        },
        "summary": {
            "jobs": len(jobs),
            "episodes": len(jobs),
            "pairs": sum(job["pair_count"] for job in jobs),
            "distinct_inputs": sum(job["distinct_input_count"] for job in jobs),
            "tested_rivals": len(rival_names),
            "surviving_visible_demo_rivals": sum(
                len(job["visible_demo_survivors"]) for job in jobs
            ),
            "rivals_without_query_disagreement": sum(
                len(job["rivals_without_query_disagreement"]) for job in jobs
            ),
        },
        "jobs": jobs,
        "limits": [
            "Finite declared-rival audit only; it does not prove unique induction.",
            "Python claims are authoring checks; protected Racket execution is recorded separately.",
            "No owner acceptance or training admission is performed by this tool.",
        ],
    }
    return report


def worker_request(
    root: Path = _ROOT,
    *,
    seeds: Iterable[int] = (0, 17, 97),
    demo_counts: Iterable[int] = (2, 3, 6),
    queries: int = 4,
) -> dict:
    """Return a complete request for ``arcpuzzles.parametric_worker``."""
    checked_seeds = _literal_ints("seeds", seeds, 0, 2**63 - 1)
    checked_demos = _literal_ints(
        "demo_counts", demo_counts, _PROTOTYPE.MIN_DEMOS, _PROTOTYPE.MAX_DEMOS
    )
    if type(queries) is not int or not _PROTOTYPE.MIN_QUERIES <= queries <= _PROTOTYPE.MAX_QUERIES:
        raise ValueError(
            f"queries must be a literal integer in [{_PROTOTYPE.MIN_QUERIES}, {_PROTOTYPE.MAX_QUERIES}]"
        )
    root = Path(root).resolve()
    contract = json.loads((_HERE / "promotion.json").read_text())
    jobs = [
        {
            "seed": seed,
            "settings": {"recolor_scope": scope},
            "demos": demos,
            "queries": queries,
        }
        for seed in checked_seeds
        for demos in checked_demos
        for scope in _PROTOTYPE.SCOPES
    ]
    return {
        "root": str(root),
        "task_id": _TASK_ID,
        "contract": contract,
        "jobs": jobs,
    }


def _write(path: Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_raw(value))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--demos", type=int, action="append", dest="demo_counts")
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--worker-request", type=Path, required=True)
    args = parser.parse_args(argv)
    seeds = tuple(args.seeds) if args.seeds is not None else (0, 17, 97)
    demo_counts = tuple(args.demo_counts) if args.demo_counts is not None else (2, 3, 6)
    report = build_report(seeds=seeds, demo_counts=demo_counts, queries=args.queries)
    request = worker_request(
        _ROOT, seeds=seeds, demo_counts=demo_counts, queries=args.queries
    )
    _write(args.out, report)
    _write(args.worker_request, request)
    print(
        json.dumps(
            {
                "status": "authoring_audit_complete",
                "report": str(args.out.resolve()),
                "worker_request": str(args.worker_request.resolve()),
                "summary": report["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
