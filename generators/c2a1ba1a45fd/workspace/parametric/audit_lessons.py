#!/usr/bin/env python3
"""Regenerate compact audits and public exports for the object-order family.

This is deliberately separate from qualification: it exercises the Python
teaching grammar over every admitted demo/query count, records finite-rival
identifiability, checks visible-ID boundaries, and emits canonical public-only
challenge files that the packet's read-only export checker can inspect.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
TASK_ID = "c2a1ba1a45fd"
SCHEMA = "c2a1ba1a45fd-object-order-audit-v1"


def _load_family():
    path = HERE / "family.py"
    spec = importlib.util.spec_from_file_location(
        "c2a1ba1a45fd_object_order_audit_family", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adjacent family source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FAMILY = _load_family()


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _seeds(values: Iterable[int]) -> list[int]:
    result = list(values)
    if not result:
        raise ValueError("at least one seed is required")
    for seed in result:
        if type(seed) is not int:
            raise TypeError("seeds must be exact integers (bool is forbidden)")
        if not 0 <= seed <= 2**63 - 1:
            raise ValueError("seeds must be in 0..2**63-1")
    if len(result) != len(set(result)):
        raise ValueError("seeds must be distinct")
    return result


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _program_hash(setting: str) -> str:
    source = FAMILY.program({FAMILY.PARAMETER_NAME: setting})
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _large_query_facts(episode: dict[str, Any]) -> dict[str, Any] | None:
    for pair in episode["test"]:
        grid = pair["input"]
        if (len(grid), len(grid[0])) != (30, 30):
            continue
        facts = FAMILY.scene_facts(grid)
        source_cells = [cell for obj in facts["source_objects"] for cell in obj["cells"]]
        return {
            "shape": [30, 30],
            "source_cells": len(source_cells),
            "distractor_cells": facts["distractor_cell_count"],
            "touches_boundary": any(
                row in (0, 29) or col in (0, 29) for row, col in source_cells
            ),
            "row_major_sizes": [obj["size"] for obj in facts["source_objects"]],
            "size_ascending_indices": facts["size_ascending_indices"],
        }
    return None


def _failure(code: str, identity: dict[str, Any], detail: Any) -> dict[str, Any]:
    return {"code": code, **identity, "detail": detail}


def _sweep(seeds: Iterable[int]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[tuple[str, bytes]]]:
    seeds = _seeds(seeds)
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    public_records: list[dict[str, Any]] = []
    public_files: list[tuple[str, bytes]] = []
    ambiguous = 0
    shortcut_survivors = 0
    substantive = 0

    for seed in seeds:
        maximal = {
            setting: FAMILY.generate(
                seed, {FAMILY.PARAMETER_NAME: setting}, demos=6, queries=4
            )
            for setting in FAMILY.SETTINGS
        }
        neutral_inputs = _inputs(maximal[FAMILY.SETTINGS[0]])
        for setting in FAMILY.SETTINGS[1:]:
            if _inputs(maximal[setting]) != neutral_inputs:
                failures.append(
                    _failure(
                        "setting_changed_inputs",
                        {"seed": seed, "setting": setting},
                        "maximal episodes do not share exact inputs",
                    )
                )

        for setting in FAMILY.SETTINGS:
            settings = {FAMILY.PARAMETER_NAME: setting}
            maximum = maximal[setting]
            for demos in range(2, 7):
                for queries in range(1, 5):
                    identity = {
                        "seed": seed,
                        "setting": setting,
                        "demos": demos,
                        "queries": queries,
                    }
                    episode = FAMILY.generate(seed, settings, demos, queries)
                    inputs = _inputs(episode)
                    survivors = FAMILY.finite_program_survivors(episode["train"])
                    shortcut_rows = FAMILY.audit_shortcuts(
                        episode["train"], selected=setting
                    )
                    alive = [row["rival"] for row in shortcut_rows if not row["refuted"]]
                    ambiguous += int(survivors != [setting])
                    shortcut_survivors += len(alive)

                    if len(episode["train"]) != demos or len(episode["test"]) != queries:
                        failures.append(_failure("wrong_counts", identity, None))
                    if len({_grid_key(grid) for grid in inputs}) != demos + queries:
                        failures.append(_failure("duplicate_input", identity, None))
                    if episode["train"] != maximum["train"][:demos]:
                        failures.append(_failure("demo_prefix_drift", identity, None))
                    if episode["test"] != maximum["test"][:queries]:
                        failures.append(_failure("query_prefix_drift", identity, None))
                    if survivors != [setting]:
                        failures.append(_failure("ambiguous_setting", identity, survivors))
                    if alive:
                        failures.append(_failure("shortcut_survived", identity, alive))
                    expected_program = FAMILY.program(settings)
                    if episode["program_solution"] != expected_program:
                        failures.append(_failure("program_drift", identity, None))

                    large = _large_query_facts(episode)
                    if large is not None:
                        ok = (
                            large["source_cells"] >= 120
                            and large["distractor_cells"] >= 8
                            and large["touches_boundary"]
                            and large["row_major_sizes"]
                            != sorted(large["row_major_sizes"])
                        )
                        substantive += int(ok)
                        if not ok:
                            failures.append(
                                _failure("weak_30x30_query", identity, large)
                            )

                    records.append(
                        {
                            **identity,
                            "survivors": survivors,
                            "shortcut_audit": shortcut_rows,
                            "program_sha256": hashlib.sha256(
                                episode["program_solution"].encode("utf-8")
                            ).hexdigest(),
                            "input_shapes": [
                                [len(grid), len(grid[0])] for grid in inputs
                            ],
                            "large_query": large,
                        }
                    )

            export_episode = FAMILY.generate(seed, settings, demos=3, queries=4)
            public = FAMILY.public_challenge(export_episode)
            raw = public_challenge_bytes(public)
            identifier = public_challenge_id(public)
            if hashlib.sha256(raw).hexdigest() != identifier:
                failures.append(
                    _failure(
                        "public_id_not_byte_hash",
                        {"seed": seed, "setting": setting},
                        identifier,
                    )
                )

            private_mutation = deepcopy(export_episode)
            private_mutation["program_solution"] = "private-only mutation"
            private_mutation["test"][0]["output"][0][0] = (
                private_mutation["test"][0]["output"][0][0] + 1
            ) % 10
            stable_public = FAMILY.public_challenge(private_mutation)
            private_stable = (
                public_challenge_bytes(stable_public) == raw
                and public_challenge_id(stable_public) == identifier
            )
            visible_mutation = deepcopy(public)
            visible_mutation["test"][0]["input"][0][0] = (
                visible_mutation["test"][0]["input"][0][0] + 1
            ) % 10
            visible_changes_id = public_challenge_id(visible_mutation) != identifier
            if not private_stable:
                failures.append(
                    _failure(
                        "private_data_changed_public_id",
                        {"seed": seed, "setting": setting},
                        None,
                    )
                )
            if not visible_changes_id:
                failures.append(
                    _failure(
                        "visible_data_did_not_change_public_id",
                        {"seed": seed, "setting": setting},
                        None,
                    )
                )
            public_records.append(
                {
                    "seed": seed,
                    "setting": setting,
                    "public_challenge_id": identifier,
                    "bytes": len(raw),
                    "private_mutation_stable": private_stable,
                    "visible_mutation_changes_id": visible_changes_id,
                }
            )
            public_files.append((f"challenge-{identifier}.json", raw))

    summary = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "seeds": seeds,
        "settings": list(FAMILY.SETTINGS),
        "demo_counts": list(range(2, 7)),
        "query_counts": list(range(1, 5)),
        "episode_count": len(records),
        "failure_count": len(failures),
        "ambiguous_episode_count": ambiguous,
        "shortcut_survivor_count": shortcut_survivors,
        "substantive_30x30_episode_count": substantive,
        "public_export_count": len(public_files),
        "program_sha256": {
            setting: _program_hash(setting) for setting in FAMILY.SETTINGS
        },
        "limits": (
            "Finite deterministic sweep and authored-rival audit; protected-Racket "
            "qualification and owner acceptance remain separate gates."
        ),
    }
    audit = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "records": records,
        "failures": failures,
    }
    identity = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "records": public_records,
    }
    return summary, audit, identity, public_files


def build_report(seeds: Iterable[int]) -> dict[str, Any]:
    """Return the compact sweep summary without writing artifacts."""
    summary, _, _, _ = _sweep(seeds)
    return summary


def write_evidence(output: str | Path, seeds: Iterable[int]) -> list[Path]:
    """Write deterministic audit JSON plus canonical public challenge files."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if not output.is_dir():
        raise ValueError("output must be a directory")
    summary, audit, identity, public_files = _sweep(seeds)
    values = {
        "summary.json": summary,
        "lesson-audit.json": audit,
        "public-identity.json": identity,
    }
    written: list[Path] = []
    for name, value in values.items():
        path = output / name
        path.write_bytes(_json_bytes(value))
        written.append(path)

    public_dir = output / "public"
    public_dir.mkdir(exist_ok=True)
    for stale in public_dir.glob("challenge-*.json"):
        stale.unlink()
    for name, raw in public_files:
        (public_dir / name).write_bytes(raw)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    args = parser.parse_args(argv)
    seeds = args.seeds if args.seeds is not None else [0, 17, 101, 2**32 + 9]
    paths = write_evidence(args.out, seeds)
    summary = json.loads((args.out / "summary.json").read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "output": str(args.out),
                "files": [str(path) for path in paths],
                "summary": summary,
            },
            sort_keys=True,
        )
    )
    return 0 if summary["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
