#!/usr/bin/env python3
"""Racket-backed verifier/materializer for the path-selection prototype."""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
PROTOTYPE_PATH = HERE.with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("db63430eeffa_path_prototype", PROTOTYPE_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(PROTOTYPE_PATH)
prototype = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = prototype
_spec.loader.exec_module(prototype)

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from reviewer_support import canonical_pairs, find_root, normalize_grid  # noqa: E402


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _racket_grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


def _rule_callable(source: str) -> str:
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("unexpected rule! wrapper")
    callable_source = source[len("(rule!") : -1].strip()
    if not callable_source.startswith("(lambda (g)"):
        raise ValueError("expected a grid lambda")
    return callable_source


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge,
) -> list[list[int]]:
    normalized = normalize_grid(grid)
    expression = f"({_rule_callable(source)} {_racket_grid_literal(normalized)})"
    return normalize_grid(bridge.eval_text(expression))


def _portable_runtime_identity(identity: dict[str, Any], *, root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in identity.items():
        if key.endswith("_path") and isinstance(value, str):
            path = Path(value).resolve()
            if path.is_relative_to(root):
                result[key] = path.relative_to(root).as_posix()
            elif key == "binary_path":
                result[key] = path.name
            else:
                result[key] = path.name
        else:
            result[key] = value
    return result


def verify(*, out: Path, seed: int = 17) -> dict[str, Any]:
    root = find_root(__file__)
    out = out.resolve()
    private_rules = out / "private" / "rules"
    private_episodes = out / "private" / "episodes"
    public_dir = out / "public"
    for path in (private_rules, private_episodes, public_dir):
        path.mkdir(parents=True, exist_ok=True)

    programs = {
        mode: prototype.program_for(mode, root=root)
        for mode in prototype.PATH_MODES
    }
    rule_records: dict[str, dict[str, Any]] = {}
    for mode, source in programs.items():
        path = private_rules / f"path-mode-{mode}.rkt"
        path.write_text(source + "\n", encoding="utf-8")
        rule_records[mode] = {
            "path": path.relative_to(out).as_posix(),
            "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "file_sha256": _sha256_file(path),
        }

    canonical_checks: list[dict[str, Any]] = []
    episode_records: list[dict[str, Any]] = []
    with RacketBridge(timeout=30, max_calls_before_restart=96) as bridge:
        for index, pair in enumerate(canonical_pairs(prototype.TASK_ID, root=root)):
            actual = execute_rule(programs[prototype.DEFAULT_PATH_MODE], pair["input"], bridge=bridge)
            if actual != pair["output"]:
                raise AssertionError(f"canonical default mismatch at pair {index}")
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "status": "pass",
                }
            )

        for mode in prototype.PATH_MODES:
            episode = prototype.generate_episode(
                seed,
                path_mode=mode,
                n_train=prototype.DEFAULT_N_TRAIN,
                n_test=prototype.DEFAULT_N_TEST,
                root=root,
            )
            racket_predictions: dict[str, list[list[list[int]]]] = {
                candidate: [] for candidate in prototype.PATH_MODES
            }
            pairs = episode["train"] + episode["test"]
            for pair_index, pair in enumerate(pairs):
                for candidate in prototype.PATH_MODES:
                    predicted = execute_rule(
                        programs[candidate], pair["input"], bridge=bridge
                    )
                    mirror = prototype.solve(pair["input"], path_mode=candidate)
                    if predicted != mirror:
                        raise AssertionError(
                            f"Racket/Python mismatch mode={candidate} pair={pair_index}"
                        )
                    racket_predictions[candidate].append(predicted)
                if racket_predictions[mode][-1] != pair["output"]:
                    raise AssertionError(
                        f"selected Racket label mismatch mode={mode} pair={pair_index}"
                    )

            train_count = len(episode["train"])
            demo_mismatches = {
                candidate: [
                    index
                    for index, prediction in enumerate(
                        racket_predictions[candidate][:train_count]
                    )
                    if prediction != episode["train"][index]["output"]
                ]
                for candidate in prototype.PATH_MODES
            }
            surviving = [
                candidate
                for candidate, mismatches in demo_mismatches.items()
                if not mismatches
            ]
            if surviving != [mode]:
                raise AssertionError(
                    f"demos do not identify {mode}: surviving={surviving}"
                )

            analysis = prototype.analyze_episode(episode)
            if not analysis["identified"]:
                raise AssertionError(f"Python analysis failed for {mode}: {analysis}")
            episode["racket_verification"] = {
                "all_labels_match_python_mirror": True,
                "demo_mismatches": demo_mismatches,
                "surviving_modes": surviving,
                "identified": True,
            }
            private_path = private_episodes / f"episode-{mode}.json"
            private_path.write_text(
                json.dumps(episode, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            public_bytes = prototype.public_bytes(episode)
            public_id = prototype.public_id(episode)
            public_path = public_dir / f"challenge-{public_id}.json"
            public_path.write_bytes(public_bytes)
            if _sha256_bytes(public_bytes) != public_id:
                raise AssertionError("public filename is not visible-byte-derived")

            episode_records.append(
                {
                    "path_mode": mode,
                    "seed": seed,
                    "demo_count": len(episode["train"]),
                    "query_count": len(episode["test"]),
                    "distinct_input_count": len(
                        {
                            pair["input_sha256"]
                            for pair in episode["train"] + episode["test"]
                        }
                    ),
                    "identified_from_demos": True,
                    "surviving_modes": surviving,
                    "private_episode": {
                        "path": private_path.relative_to(out).as_posix(),
                        "sha256": _sha256_file(private_path),
                    },
                    "public_challenge": {
                        "path": public_path.relative_to(out).as_posix(),
                        "sha256": _sha256_file(public_path),
                        "public_id": public_id,
                    },
                }
            )

        runtime_identity = _portable_runtime_identity(
            bridge.runtime_identity,
            root=root,
        )

    report = {
        "schema": "arcpuzzles-path-selection-verification-v1",
        "status": "pass",
        "approval": "proposed_unapproved",
        "task_id": prototype.TASK_ID,
        "prototype_version": prototype.PROTOTYPE_VERSION,
        "parameter": {
            "name": "path_mode",
            "allowed_values": list(prototype.PATH_MODES),
            "default": prototype.DEFAULT_PATH_MODE,
        },
        "invariant_reasoning": [
            "find the two color-8 endpoints in reading order",
            "derive row/column signs and diagonal/straight step counts",
            "keep endpoints color 8 and paint selected path cells color 3",
        ],
        "changed_reasoning": (
            "path_mode chooses the union, diagonal-first path, or straight-first path"
        ),
        "canonical_default": {
            "exact_source_sha256": prototype.exact_program_hash("both", root=root),
            "normalized_source_sha256": prototype.normalized_program_hash("both", root=root),
            "canonical_pairs_checked": len(canonical_checks),
            "checks": canonical_checks,
        },
        "rules": rule_records,
        "episodes": episode_records,
        "shared_input_seed": seed,
        "runtime": runtime_identity,
        "limits": [
            "finite evidence covers one seven-pair episode per declared setting",
            "declared-rival identifiability is limited to the three path_mode values",
            "prototype is not catalog-selected, approved, or admitted to training",
        ],
    }
    report_path = out / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report["report"] = {
        "path": report_path.as_posix(),
        "sha256": _sha256_file(report_path),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args(argv)
    report = verify(out=args.out, seed=args.seed)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
