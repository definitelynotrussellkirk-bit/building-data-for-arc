#!/usr/bin/env python3
"""Execute both proposed Racket settings and retain source-bound evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import prototype  # noqa: E402


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_program(root: Path) -> str:
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == prototype.TASK_ID:
            return row["program_solution"]
    raise RuntimeError("canonical program missing")


def _racket_callable(source: str) -> str:
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("prototype program must use one `(rule! EXPR)` form")
    expression = stripped[len("(rule!") : -1].strip()
    if not expression.startswith("(lambda"):
        raise ValueError("prototype rule expression must be a lambda")
    return expression


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"'({rows})"


def _application(source: str, grid: list[list[int]]) -> str:
    return f"({_racket_callable(source)} {_grid_literal(grid)})"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _positive_count(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("count must be a positive integer")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--train-count", type=_positive_count, default=3)
    parser.add_argument("--test-count", type=_positive_count, default=4)
    parser.add_argument("--out", required=True)
    parser.add_argument("--artifact-dir")
    args = parser.parse_args()

    root = find_root(__file__)
    canonical = _canonical_program(root)
    programs = {
        connectivity: prototype.program_for(connectivity)
        for connectivity in prototype.ALLOWED_CONNECTIVITIES
    }
    if programs[prototype.DEFAULT_CONNECTIVITY] != canonical:
        raise SystemExit("default setting no longer exactly matches canonical authority")
    if len({_sha256_bytes(source.encode()) for source in programs.values()}) != len(programs):
        raise SystemExit("declared settings materialize the same Racket program")

    episodes = {
        connectivity: prototype.build_episode(
            args.seed,
            connectivity=connectivity,
            n_train=args.train_count,
            n_test=args.test_count,
        )
        for connectivity in prototype.ALLOWED_CONNECTIVITIES
    }
    for connectivity, episode in episodes.items():
        errors = prototype.episode_errors(episode)
        if errors:
            raise SystemExit(f"connectivity {connectivity} episode invalid: {errors}")

    checks: list[dict[str, Any]] = []
    bridge = RacketBridge(timeout=30, max_calls_before_restart=64)
    try:
        runtime_identity = bridge.runtime_identity
        for selected, episode in episodes.items():
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    outputs: dict[str, Any] = {}
                    for candidate, source in programs.items():
                        racket_output = bridge.eval_text(_application(source, pair["input"]))
                        python_output = prototype.apply_python(pair["input"], candidate)
                        if racket_output != python_output:
                            raise SystemExit(
                                f"Racket/Python mismatch for selected={selected} "
                                f"{split}[{index}] candidate={candidate}"
                            )
                        outputs[str(candidate)] = racket_output
                    if outputs[str(selected)] != pair["output"]:
                        raise SystemExit(
                            f"selected label mismatch for connectivity {selected} {split}[{index}]"
                        )
                    checks.append(
                        {
                            "episode_connectivity": selected,
                            "split": split,
                            "pair_index": index,
                            "sampling": pair["sampling"],
                            "input": pair["input"],
                            "outputs": outputs,
                            "settings_disagree": outputs["4"] != outputs["8"],
                        }
                    )
    finally:
        bridge.shutdown()

    if not checks or not all(row["settings_disagree"] for row in checks):
        raise SystemExit("a retained pair does not distinguish the declared settings")

    identifiability: dict[str, Any] = {}
    identifiable_queries = 0
    for selected, episode in episodes.items():
        rival = 8 if selected == 4 else 4
        selected_rows = [row for row in checks if row["episode_connectivity"] == selected]
        train_rows = [row for row in selected_rows if row["split"] == "train"]
        test_rows = [row for row in selected_rows if row["split"] == "test"]
        rival_fits_demonstrations = all(
            row["outputs"][str(rival)] == episode["train"][row["pair_index"]]["output"]
            for row in train_rows
        )
        query_rows = []
        for row in test_rows:
            query_identifiable = (
                not rival_fits_demonstrations and row["outputs"][str(selected)] != row["outputs"][str(rival)]
            )
            row["rival_fits_demonstrations"] = rival_fits_demonstrations
            row["query_identifiable_from_demonstrations"] = query_identifiable
            identifiable_queries += int(query_identifiable)
            query_rows.append(
                {
                    "query_index": row["pair_index"],
                    "rival_output_differs": row["settings_disagree"],
                    "identifiable_from_demonstrations": query_identifiable,
                }
            )
        identifiability[str(selected)] = {
            "selected_connectivity": selected,
            "rival_connectivity": rival,
            "rival_fits_demonstrations": rival_fits_demonstrations,
            "queries": query_rows,
        }
    if identifiable_queries != len(episodes) * args.test_count:
        raise SystemExit("a retained query is not identifiable from its demonstrations")

    generator_sha = next(iter(episodes.values()))["generator_sha256"]
    if any(episode["generator_sha256"] != generator_sha for episode in episodes.values()):
        raise SystemExit("episodes used different selected generator bytes")

    first = checks[0]
    report = {
        "schema": "a631936f7715-parametric-verification-v2",
        "status": "passed",
        "scope": "proposed prototype; not selected canonical execution",
        "task_id": prototype.TASK_ID,
        "seed": args.seed,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "parameter": {
            "name": "component_connectivity",
            "allowed_values": list(prototype.ALLOWED_CONNECTIVITIES),
            "default": prototype.DEFAULT_CONNECTIVITY,
            "chosen_once_per_episode": True,
            "meaning": (
                "segment magenta source cells with orthogonal or eight-neighbor connectivity; "
                "label lookup remains orthogonal"
            ),
            "input_constraints": (
                "each retained pair has a diagonal-only contact between two 4-components and "
                "one label across that pair, avoiding multi-label order ambiguity"
            ),
        },
        "programs": {
            str(connectivity): {
                "source": source,
                "sha256": _sha256_bytes(source.encode()),
            }
            for connectivity, source in programs.items()
        },
        "canonical_program_sha256": _sha256_bytes(canonical.encode()),
        "generator_sha256": generator_sha,
        "prototype_source_sha256": {
            name: _sha256_bytes((HERE / name).read_bytes())
            for name in ("prototype.py", "verify.py", "README.md")
        },
        "racket_runtime": runtime_identity,
        "episode_errors": {
            str(connectivity): prototype.episode_errors(episode)
            for connectivity, episode in episodes.items()
        },
        "counts": {
            "settings": len(episodes),
            "train_pairs_per_setting": args.train_count,
            "test_pairs_per_setting": args.test_count,
            "episode_pairs": len(checks),
            "racket_executions": len(checks) * len(programs),
            "distinguishing_pairs": sum(row["settings_disagree"] for row in checks),
            "identifiable_queries": identifiable_queries,
        },
        "identifiability": identifiability,
        "exact_disagreement": {
            "input": first["input"],
            "connectivity_4_output": first["outputs"]["4"],
            "connectivity_8_output": first["outputs"]["8"],
        },
        "checks": checks,
        "limitations": [
            "This is a task-local prototype and is not wired into production generation or approval metadata.",
            "Evidence covers two complete episodes at one retained seed, not every possible lawful input.",
            "Demonstrations eliminate the one declared parameter rival, not every imaginable transformation.",
        ],
    }
    out_path = Path(args.out)
    _write_json(out_path, report)

    if args.artifact_dir:
        prototype.write_batch(list(episodes.values()), Path(args.artifact_dir))

    print(json.dumps({"status": "passed", "out": str(out_path), "counts": report["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
