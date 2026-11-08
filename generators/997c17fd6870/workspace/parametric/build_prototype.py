#!/usr/bin/env python3
"""Build source-bound, live-Racket evidence for both tile-width settings."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator

from prototype import (
    ALLOWED_TILE_WIDTHS,
    DEFAULT_TILE_WIDTH,
    PARAMETER_NAME,
    PARAMETER_SPEC,
    PROTOTYPE_VERSION,
    TASK_ID,
    build_input,
    choose_parameters,
    grid_literal,
    public_challenge,
    python_reference,
    racket_program,
)


def _sha(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _first_seed_for(tile_width: int) -> int:
    for seed in range(10_000):
        if choose_parameters(seed)[PARAMETER_NAME] == tile_width:
            return seed
    raise AssertionError(f"no deterministic episode seed selects tile_width={tile_width}")


def _execute(bridge: RacketBridge, source: str, grid: list[list[int]]) -> list[list[int]]:
    result = bridge.eval_text(f"({source} {grid_literal(grid)})")
    if not (
        isinstance(result, list)
        and result
        and all(isinstance(row, list) and row for row in result)
    ):
        raise RuntimeError(f"Racket returned a non-grid: {result!r}")
    return [[int(value) for value in row] for row in result]


def _unique_canonical(root: Path) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        key = tuple(map(tuple, pair["input"]))
        if key not in seen:
            seen.add(key)
            result.append(pair)
    return result


def _build_episode(gen: Any, bridge: RacketBridge, seed: int) -> dict[str, Any]:
    parameters = choose_parameters(seed)
    selected = parameters[PARAMETER_NAME]
    source = racket_program(parameters)
    alternatives = {
        width: racket_program({PARAMETER_NAME: width})
        for width in ALLOWED_TILE_WIDTHS
        if width != selected
    }

    pairs = []
    alternative_outputs = []
    for pair_index in range(4):
        grid = build_input(seed, pair_index)
        grammar_errors = gen.self_check(grid)
        if grammar_errors:
            raise AssertionError(f"prototype input left selected grammar: {grammar_errors}")
        output = _execute(bridge, source, grid)
        mirror = python_reference(grid, tile_width=selected)
        if output != mirror:
            raise AssertionError("executed Racket disagrees with independent Python mirror")
        if selected == DEFAULT_TILE_WIDTH and output != gen.rule_mirror(grid):
            raise AssertionError("default setting diverges from selected canonical rule")
        rival_outputs = {
            str(width): _execute(bridge, rival_source, grid)
            for width, rival_source in alternatives.items()
        }
        if any(value == output for value in rival_outputs.values()):
            raise AssertionError("retained pair does not distinguish tile-width settings")
        pairs.append({"input": grid, "output": output})
        alternative_outputs.append(rival_outputs)

    episode = {"demos": pairs[:3], "query": pairs[3]}
    demo_distinction = {
        str(width): any(
            alternative_outputs[index][str(width)] != pairs[index]["output"]
            for index in range(3)
        )
        for width in alternatives
    }
    if not all(demo_distinction.values()):
        raise AssertionError("demonstrations do not identify the episode setting")

    return {
        "schema": "arc-parametric-episode-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "episode_seed": seed,
        "parameters": parameters,
        "parameter_spec": PARAMETER_SPEC,
        "racket_program": source,
        "racket_sha256": _sha(source),
        "episode": episode,
        "alternative_outputs": alternative_outputs,
        "checks": {
            "parameter_chosen_once_for_episode": True,
            "three_demonstrations": len(episode["demos"]) == 3,
            "one_query": bool(episode["query"].get("input")),
            "all_labels_from_live_racket": True,
            "python_mirror_parity": True,
            "selected_generator_grammar": True,
            "default_matches_selected_rule": (
                selected != DEFAULT_TILE_WIDTH
                or all(
                    pair["output"] == gen.rule_mirror(pair["input"])
                    for pair in pairs
                )
            ),
            "demos_distinguish_every_alternative": demo_distinction,
            "every_pair_distinguishes_every_alternative": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists():
        parser.error("--out-dir already exists; use a new path to preserve evidence")
    (out / "public").mkdir(parents=True)
    (out / "private/programs").mkdir(parents=True)

    root = Path(find_root(__file__))
    gen, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    source_dir = Path(__file__).resolve().parent
    command = {"cwd": os.getcwd(), "argv": [sys.executable, *sys.argv]}

    programs = {
        width: racket_program({PARAMETER_NAME: width})
        for width in ALLOWED_TILE_WIDTHS
    }
    for width, source in programs.items():
        (out / f"private/programs/tile-width-{width}.rkt").write_text(
            source + "\n", encoding="utf-8"
        )

    with RacketBridge(timeout=20, max_calls_before_restart=64) as bridge:
        canonical_checks = []
        for pair in _unique_canonical(root):
            actual = _execute(bridge, programs[DEFAULT_TILE_WIDTH], pair["input"])
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "racket_matches_canonical_label": actual == pair["output"],
                    "racket_matches_selected_python_mirror": actual
                    == gen.rule_mirror(pair["input"]),
                }
            )
        if not canonical_checks or not all(
            row["racket_matches_canonical_label"]
            and row["racket_matches_selected_python_mirror"]
            for row in canonical_checks
        ):
            raise AssertionError("default tile-width Racket lost canonical parity")

        episodes = []
        private_payloads = []
        for width in ALLOWED_TILE_WIDTHS:
            seed = _first_seed_for(width)
            evidence = _build_episode(gen, bridge, seed)
            challenge = public_challenge(evidence["episode"])
            public_path = out / f"public/episode-tile-width-{width}.json"
            private_path = out / f"private/episode-tile-width-{width}.json"
            _write_json(public_path, challenge)
            evidence.update(
                {
                    "public_challenge": str(public_path.relative_to(out)),
                    "public_challenge_sha256": _sha(public_path.read_bytes()),
                    "source_hashes": {
                        "prototype.py": _sha((source_dir / "prototype.py").read_bytes()),
                        "build_prototype.py": _sha(Path(__file__).read_bytes()),
                        "selected_generator.py": generator_sha,
                    },
                    "selected_generator_path": str(generator_path.relative_to(root)),
                    "command": command,
                }
            )
            _write_json(private_path, evidence)
            private_payloads.append(evidence)
            episodes.append(
                {
                    "tile_width": width,
                    "episode_seed": seed,
                    "public": str(public_path.relative_to(out)),
                    "public_sha256": _sha(public_path.read_bytes()),
                    "private": str(private_path.relative_to(out)),
                    "private_sha256": _sha(private_path.read_bytes()),
                    "racket_sha256": evidence["racket_sha256"],
                    "checks": evidence["checks"],
                }
            )

    default_episode = next(
        item for item in private_payloads
        if item["parameters"][PARAMETER_NAME] == DEFAULT_TILE_WIDTH
    )
    witness_grid = default_episode["episode"]["demos"][0]["input"]
    witness = {
        "schema": "arc-parametric-setting-difference-v1",
        "task_id": TASK_ID,
        "input": witness_grid,
        "outputs": {
            str(width): python_reference(witness_grid, tile_width=width)
            for width in ALLOWED_TILE_WIDTHS
        },
    }
    witness["different"] = len(
        {tuple(map(tuple, value)) for value in witness["outputs"].values()}
    ) == len(ALLOWED_TILE_WIDTHS)
    _write_json(out / "private/setting-difference-witness.json", witness)
    _write_json(out / "private/canonical-default-parity.json", canonical_checks)

    passed = (
        witness["different"]
        and sorted(item["tile_width"] for item in episodes)
        == list(ALLOWED_TILE_WIDTHS)
        and all(
            item["checks"]["all_labels_from_live_racket"]
            and item["checks"]["python_mirror_parity"]
            and item["checks"]["selected_generator_grammar"]
            and all(item["checks"]["demos_distinguish_every_alternative"].values())
            for item in episodes
        )
    )
    summary = {
        "schema": "arc-parametric-prototype-summary-v1",
        "task_id": TASK_ID,
        "status": "prototype",
        "selected_canonical_path_unchanged": True,
        "parameter_spec": PARAMETER_SPEC,
        "settings_covered": sorted(item["tile_width"] for item in episodes),
        "canonical_default_checks": "private/canonical-default-parity.json",
        "setting_difference_witness": "private/setting-difference-witness.json",
        "episodes": episodes,
        "source_hashes": {
            "prototype.py": _sha((source_dir / "prototype.py").read_bytes()),
            "build_prototype.py": _sha(Path(__file__).read_bytes()),
            "selected_generator.py": generator_sha,
        },
        "command": command,
        "limitations": [
            "This is an isolated proposal, not an approved production API.",
            "Evidence covers two tile widths and one deterministic full episode per setting.",
            "The alternative width is restricted to inputs whose width is divisible by both 2 and 3.",
        ],
        "passed": passed,
    }
    _write_json(out / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
