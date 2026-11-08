"""Deterministically regenerate task-local evidence for the parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "fe0dc9f32b7b_palette_direction_evidence_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling palette-direction prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)

_SCHEMA = "nested-palette-parametric-evidence-v1"


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _normalized_seeds(seeds: Iterable[int]) -> list[int]:
    result = list(seeds)
    if not result:
        raise ValueError("at least one seed is required")
    for seed in result:
        _PROTOTYPE._integer("seed", seed, 0, 2**63 - 1)
    if len(result) != len(set(result)):
        raise ValueError("seeds must be distinct")
    return result


def _sweep(seeds: Iterable[int]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    seeds = _normalized_seeds(seeds)
    audits: list[dict[str, Any]] = []
    public_turns: list[dict[str, Any]] = []
    ambiguous = 0
    substantive = 0

    for seed in seeds:
        for setting in _PROTOTYPE.PALETTE_DIRECTIONS:
            for demos in range(_PROTOTYPE.MIN_DEMOS, _PROTOTYPE.MAX_DEMOS + 1):
                episode = _PROTOTYPE.generate_episode(
                    seed,
                    palette_direction=setting,
                    demos=demos,
                    queries=_PROTOTYPE.QUERY_COUNT,
                )
                audit = _PROTOTYPE.audit_episode(episode)
                ambiguous += int(bool(audit["surviving_rivals"]))
                first_public = _PROTOTYPE.public_single_query_payload(episode)
                public_raw = _PROTOTYPE.public_bytes(first_public)
                query_facts = episode["scene_facts"]["test"]
                is_substantive = any(
                    facts["shape"] == [30, 30]
                    and facts["color8_cells"] >= 120
                    and facts["qualifying_components"] >= 4
                    for facts in query_facts
                )
                substantive += int(is_substantive)
                identity = {
                    "seed": seed,
                    "palette_direction": setting,
                    "demos": demos,
                    "queries": _PROTOTYPE.QUERY_COUNT,
                }
                audits.append(
                    {
                        **identity,
                        "program_sha256": episode["program_sha256"],
                        "audit": audit,
                        "query_scene_facts": query_facts,
                    }
                )
                public_turns.append(
                    {
                        **identity,
                        "sha256": hashlib.sha256(public_raw).hexdigest(),
                        "bytes": len(public_raw),
                        "first_query_input_sha256": _PROTOTYPE._grid_hash(
                            first_public["test"][0]["input"]
                        ),
                        "training_pair_sha256": [
                            hashlib.sha256(
                                json.dumps(
                                    pair,
                                    sort_keys=True,
                                    separators=(",", ":"),
                                    ensure_ascii=False,
                                ).encode("utf-8")
                            ).hexdigest()
                            for pair in first_public["train"]
                        ],
                    }
                )

    hashes = [row["sha256"] for row in public_turns]
    report = {
        "schema": _SCHEMA,
        "task_id": _PROTOTYPE.TASK_ID,
        "seeds": seeds,
        "settings": list(_PROTOTYPE.PALETTE_DIRECTIONS),
        "demo_counts": list(range(_PROTOTYPE.MIN_DEMOS, _PROTOTYPE.MAX_DEMOS + 1)),
        "query_count": _PROTOTYPE.QUERY_COUNT,
        "episode_count": len(audits),
        "ambiguous_episode_count": ambiguous,
        "substantive_30x30_episode_count": substantive,
        "first_public_turn_sha256": hashes,
        "canonical_program_sha256": hashlib.sha256(
            _PROTOTYPE.CANONICAL_PROGRAM.encode("utf-8")
        ).hexdigest(),
        "alternate_program_sha256": hashlib.sha256(
            _PROTOTYPE.REVERSED_PROGRAM.encode("utf-8")
        ).hexdigest(),
        "limits": (
            "Finite declared-rival audit over deterministic samples; protected-Racket "
            "qualification is separate evidence."
        ),
    }
    return report, audits, public_turns


def build_report(seeds: Iterable[int]) -> dict[str, Any]:
    """Return the compact deterministic sweep summary without writing files."""
    report, _, _ = _sweep(seeds)
    return report


def write_evidence(output: str | Path, seeds: Iterable[int]) -> list[Path]:
    """Write compact summary, detailed self-audits, and first-turn public payloads."""
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    if not destination.is_dir():
        raise ValueError("evidence output must be a directory")
    report, audits, public_turns = _sweep(seeds)
    values = {
        "summary.json": report,
        "self-audit.json": {
            "schema": _SCHEMA,
            "task_id": _PROTOTYPE.TASK_ID,
            "records": audits,
        },
        "first-public-turns.json": {
            "schema": _SCHEMA,
            "task_id": _PROTOTYPE.TASK_ID,
            "records": public_turns,
        },
    }
    paths = []
    for name, value in values.items():
        path = destination / name
        path.write_bytes(_json_bytes(value))
        paths.append(path)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    args = parser.parse_args(argv)
    seeds = args.seeds if args.seeds is not None else [0, 17, 83, 991]
    paths = write_evidence(args.out, seeds)
    print(
        json.dumps(
            {
                "output": str(args.out),
                "files": [str(path) for path in paths],
                "summary": build_report(seeds),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
