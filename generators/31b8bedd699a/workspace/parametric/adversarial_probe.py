#!/usr/bin/env python3
"""Bounded adversarial probe for the token-size/tie-policy prototype."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import time
from typing import Any, Callable, Iterable

from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "31b8bedd699a"
HERE = Path(__file__).resolve().parent
SURFACES = [
    "sampler_boundaries_and_deterministic_replay",
    "public_private_export_and_verifier_rejection",
]


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        "token_tie_probe_prototype_31b8bedd699a", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _validate_max_count(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= 64:
        raise ValueError("max_count must be an exact integer in 1..64")
    return value


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"), ensure_ascii=False)


def _mutate_cell(grid: list[list[int]]) -> None:
    grid[0][0] = (grid[0][0] + 1) % 10


def _expect_value_errors(
    values: Iterable[Any], operation: Callable[[Any], Any]
) -> int:
    rejected = 0
    for value in values:
        try:
            operation(value)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(f"adversarial value was accepted: {value!r}")
    return rejected


def _private_mutations(episode: dict[str, Any]) -> list[dict[str, Any]]:
    mutations: list[dict[str, Any]] = []

    changed = deepcopy(episode)
    changed["seed"] += 1
    mutations.append(changed)

    changed = deepcopy(episode)
    changed["parameter"] = {"token_size": 3, "tie_policy": "vertical"}
    mutations.append(changed)

    changed = deepcopy(episode)
    changed["parameter_draw_count"] = 999
    mutations.append(changed)

    changed = deepcopy(episode)
    changed["program"] = "private-program-text"
    mutations.append(changed)

    changed = deepcopy(episode)
    changed["schema"] = "private-schema-revision"
    mutations.append(changed)

    changed = deepcopy(episode)
    changed["status"] = "private-status-revision"
    mutations.append(changed)

    changed = deepcopy(episode)
    changed["prototype_version"] = "private-version-revision"
    mutations.append(changed)

    changed = deepcopy(episode)
    changed["test"][0]["output"] = [[9]]
    mutations.append(changed)

    for field in ("generator_seed", "sample_index", "profile", "controls"):
        changed = deepcopy(episode)
        changed["train"][0][field] = "private-metadata"
        mutations.append(changed)

    return mutations


def _visible_mutations(episode: dict[str, Any]) -> list[dict[str, Any]]:
    mutations: list[dict[str, Any]] = []

    changed = deepcopy(episode)
    _mutate_cell(changed["train"][0]["input"])
    mutations.append(changed)

    changed = deepcopy(episode)
    _mutate_cell(changed["train"][0]["output"])
    mutations.append(changed)

    changed = deepcopy(episode)
    _mutate_cell(changed["test"][0]["input"])
    mutations.append(changed)

    return mutations


def _public_exact_ints(public: dict[str, Any]) -> bool:
    grids = []
    for pair in public["train"]:
        grids.extend((pair["input"], pair["output"]))
    for pair in public["test"]:
        grids.append(pair["input"])
    return all(
        type(cell) is int and 0 <= cell <= 9
        for grid in grids
        for row in grid
        for cell in row
    )


def _tampered_episodes(episode: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}

    changed = deepcopy(episode)
    changed["program"] = "(rule! (lambda (grid) grid))"
    cases["wrong_program"] = changed

    changed = deepcopy(episode)
    _mutate_cell(changed["train"][0]["output"])
    cases["wrong_output"] = changed

    changed = deepcopy(episode)
    changed["test"][0]["input"] = deepcopy(changed["train"][0]["input"])
    cases["duplicate_input"] = changed

    changed = deepcopy(episode)
    changed["train"] = [deepcopy(pair) for pair in changed["train"] if pair["profile"] != "tie"]
    cases["underidentified_demos"] = changed

    changed = deepcopy(episode)
    changed["parameter_draw_count"] = 2
    cases["multiple_parameter_draws"] = changed

    return cases


def run_probe(
    out: Path | str,
    *,
    seed: int = 41,
    max_count: int = 64,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Run two bounded attack surfaces and write one reproducible receipt."""
    max_count = _validate_max_count(max_count)
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError(f"refusing to overwrite existing receipt: {out}")

    source_root = find_root(__file__) if root is None else Path(root).resolve()
    proto = _load_prototype()
    generator, generator_path, generator_sha = load_selected_generator(
        TASK_ID, root=source_root
    )
    started = time.monotonic()

    episode = proto.generate_episode(
        seed,
        token_size=5,
        tie_policy="vertical",
        demo_count=max_count,
        query_count=max_count,
        root=source_root,
    )
    replay = proto.generate_episode(
        seed,
        token_size=5,
        tie_policy="vertical",
        demo_count=max_count,
        query_count=max_count,
        root=source_root,
    )
    pairs = [*episode["train"], *episode["test"]]
    input_keys = {_grid_key(pair["input"]) for pair in pairs}
    verifier_errors = proto.episode_errors(episode, root=source_root)
    if len(input_keys) != 2 * max_count:
        raise AssertionError("sampler emitted duplicate inputs at the authoring bound")
    if episode != replay:
        raise AssertionError("sampler replay changed for identical arguments")
    if verifier_errors:
        raise AssertionError(f"max-count episode verifier failed: {verifier_errors}")

    strict_rejections = {
        "token_size": _expect_value_errors(
            (None, True, False, 2, 6, 4.0, "4"),
            lambda value: proto.racket_program(value, "horizontal", root=source_root),
        ),
        "tie_policy": _expect_value_errors(
            (None, True, 0, "both", "Horizontal"),
            lambda value: proto.racket_program(4, value, root=source_root),
        ),
        "demo_count": _expect_value_errors(
            (True, 0, 65, 1.5, "4"),
            lambda value: proto.generate_episode(
                seed,
                token_size=4,
                tie_policy="horizontal",
                demo_count=value,
                query_count=1,
                root=source_root,
            ),
        ),
        "query_count": _expect_value_errors(
            (True, 0, 65, 1.5, "4"),
            lambda value: proto.generate_episode(
                seed,
                token_size=4,
                tie_policy="horizontal",
                demo_count=1,
                query_count=value,
                root=source_root,
            ),
        ),
        "seed": _expect_value_errors(
            (True, -1, 1.5, "41"),
            lambda value: proto.generate_episode(
                value,
                token_size=4,
                tie_policy="horizontal",
                demo_count=1,
                query_count=1,
                root=source_root,
            ),
        ),
    }

    export_episode = proto.generate_episode(
        seed + 1,
        token_size=4,
        tie_policy="vertical",
        demo_count=3,
        query_count=4,
        root=source_root,
    )
    public = proto.public_challenge(export_episode)
    public_bytes = public_challenge_bytes(public)
    base_id = public_challenge_id(public)
    base_name = proto.public_filename(export_episode)
    private_names = [
        proto.public_filename(mutated)
        for mutated in _private_mutations(export_episode)
    ]
    visible_names = [
        proto.public_filename(mutated)
        for mutated in _visible_mutations(export_episode)
    ]
    masked = (
        set(public) == {"train", "test"}
        and all(set(pair) == {"input", "output"} for pair in public["train"])
        and all(set(pair) == {"input"} for pair in public["test"])
    )
    opaque_name = bool(re.fullmatch(r"challenge-[0-9a-f]{64}\.json", base_name))

    verifier_details = {
        name: proto.episode_errors(candidate, root=source_root)
        for name, candidate in _tampered_episodes(export_episode).items()
    }
    verifier_rejections = {
        name: bool(errors) for name, errors in verifier_details.items()
    }

    summary = {
        "schema": "31b8bedd699a-token-size-tie-policy-adversarial-v1",
        "status": "pass",
        "task_id": TASK_ID,
        "surfaces": SURFACES,
        "seed": seed,
        "sampler": {
            "demo_count": max_count,
            "query_count": max_count,
            "unique_input_count": len(input_keys),
            "deterministic_replay": episode == replay,
            "episode_verifier_errors": verifier_errors,
            "strict_rejections": strict_rejections,
        },
        "export": {
            "public_id": base_id,
            "public_sha256": hashlib.sha256(public_bytes).hexdigest(),
            "public_filename": base_name,
            "private_mutation_count": len(private_names),
            "all_private_mutations_preserve_id": all(
                name == base_name for name in private_names
            ),
            "visible_mutation_count": len(visible_names),
            "all_visible_mutations_change_id": all(
                name != base_name for name in visible_names
            ),
            "public_payload_masks_query_answers": masked,
            "public_numeric_types_are_exact_ints": _public_exact_ints(public),
            "opaque_filename": opaque_name,
        },
        "verifier": {
            "rejections": verifier_rejections,
            "all_tampered_episodes_rejected": all(verifier_rejections.values()),
            "diagnostics": verifier_details,
        },
        "source": {
            "generator_path": str(generator_path.relative_to(source_root)),
            "generator_sha256": generator_sha,
            "generator_version": generator.VERSION,
            "prototype_path": str((HERE / "prototype.py").relative_to(source_root)),
        },
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }

    required = [
        summary["sampler"]["deterministic_replay"],
        not summary["sampler"]["episode_verifier_errors"],
        summary["export"]["all_private_mutations_preserve_id"],
        summary["export"]["all_visible_mutations_change_id"],
        summary["export"]["public_payload_masks_query_answers"],
        summary["export"]["public_numeric_types_are_exact_ints"],
        summary["export"]["opaque_filename"],
        summary["verifier"]["all_tampered_episodes_rejected"],
    ]
    if not all(required):
        raise AssertionError("adversarial sampler/export/verifier probe failed")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=41)
    parser.add_argument("--max-count", type=int, default=64)
    args = parser.parse_args(argv)
    summary = run_probe(args.out, seed=args.seed, max_count=args.max_count)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
