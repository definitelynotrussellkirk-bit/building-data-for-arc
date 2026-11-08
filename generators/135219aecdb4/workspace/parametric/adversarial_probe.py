#!/usr/bin/env python3
"""Bounded adversarial probe for sampler and public/private export surfaces."""
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

TASK_ID = "135219aecdb4"
HERE = Path(__file__).resolve().parent
SURFACES = [
    "sampler_count_retry_boundaries",
    "public_private_export_and_numeric_types",
]


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        "pass_budget_probe_prototype_135219aecdb4", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _validate_max_count(value: int) -> int:
    if type(value) is not int or not 1 <= value <= 64:
        raise ValueError("max_count must be an exact integer in 1..64")
    return value


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, sort_keys=True, separators=(",", ":"))


def _mutate_cell(grid: list[list[int]]) -> None:
    grid[0][0] = (grid[0][0] + 1) % 5


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
    changed["parameter"] = {"pass_count": 1}
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
    changed["test"][0]["output"] = [[9]]
    mutations.append(changed)

    for field in ("generator_seed", "sample_index", "n_erased"):
        changed = deepcopy(episode)
        changed["train"][0][field] = -999
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


def run_probe(
    out: Path | str,
    *,
    seed: int = 29,
    max_count: int = 64,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Run two bounded surfaces and write one reproducible JSON receipt."""
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
        pass_count=3,
        demo_count=max_count,
        query_count=max_count,
        root=source_root,
    )
    pairs = [*episode["train"], *episode["test"]]
    input_keys = {_grid_key(pair["input"]) for pair in pairs}
    all_three_pass = all(
        generator.semantic_observables(pair["input"])["passes_to_complete"] == 3
        for pair in pairs
    )
    if len(input_keys) != 2 * max_count:
        raise AssertionError("sampler emitted duplicate inputs at the authoring bound")
    if not all_three_pass:
        raise AssertionError("sampler emitted an input outside the three-pass profile")

    strict_rejections = {
        "pass_count": _expect_value_errors(
            (None, True, False, 0, 4, 1.0, "3"),
            lambda value: proto.racket_program(value, root=source_root),
        ),
        "demo_count": _expect_value_errors(
            (True, 0, 65, 1.5, "4"),
            lambda value: proto.generate_episode(
                seed,
                pass_count=3,
                demo_count=value,
                query_count=1,
                root=source_root,
            ),
        ),
        "query_count": _expect_value_errors(
            (True, 0, 65, 1.5, "4"),
            lambda value: proto.generate_episode(
                seed,
                pass_count=3,
                demo_count=1,
                query_count=value,
                root=source_root,
            ),
        ),
        "seed": _expect_value_errors(
            (True, -1, 1.5, "29"),
            lambda value: proto.generate_episode(
                value,
                pass_count=3,
                demo_count=1,
                query_count=1,
                root=source_root,
            ),
        ),
    }

    export_episode = proto.generate_episode(
        seed + 1,
        pass_count=2,
        demo_count=2,
        query_count=4,
        root=source_root,
    )
    public = proto.public_challenge(export_episode)
    public_bytes = public_challenge_bytes(public)
    base_id = public_challenge_id(public)
    base_name = proto.public_filename(export_episode)
    private_ids = [
        proto.public_filename(mutated)
        for mutated in _private_mutations(export_episode)
    ]
    visible_ids = [
        proto.public_filename(mutated)
        for mutated in _visible_mutations(export_episode)
    ]
    masked = (
        set(public) == {"train", "test"}
        and all(set(pair) == {"input", "output"} for pair in public["train"])
        and all(set(pair) == {"input"} for pair in public["test"])
    )
    opaque_name = bool(re.fullmatch(r"challenge-[0-9a-f]{64}\.json", base_name))

    summary = {
        "schema": "135219aecdb4-pass-budget-adversarial-v1",
        "status": "pass",
        "task_id": TASK_ID,
        "surfaces": SURFACES,
        "seed": seed,
        "sampler": {
            "demo_count": max_count,
            "query_count": max_count,
            "unique_input_count": len(input_keys),
            "all_inputs_require_three_passes": all_three_pass,
            "strict_rejections": strict_rejections,
        },
        "export": {
            "public_id": base_id,
            "public_sha256": hashlib.sha256(public_bytes).hexdigest(),
            "public_filename": base_name,
            "private_mutation_count": len(private_ids),
            "all_private_mutations_preserve_id": all(
                value == base_name for value in private_ids
            ),
            "visible_mutation_count": len(visible_ids),
            "all_visible_mutations_change_id": all(
                value != base_name for value in visible_ids
            ),
            "public_payload_masks_query_answers": masked,
            "opaque_filename": opaque_name,
        },
        "source": {
            "generator_path": str(generator_path.relative_to(source_root)),
            "generator_sha256": generator_sha,
            "generator_version": generator.VERSION,
            "prototype_path": str((HERE / "prototype.py").relative_to(source_root)),
        },
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }

    if not all(summary["export"][key] for key in (
        "all_private_mutations_preserve_id",
        "all_visible_mutations_change_id",
        "public_payload_masks_query_answers",
        "opaque_filename",
    )):
        raise AssertionError("public/private export boundary probe failed")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=29)
    parser.add_argument("--max-count", type=int, default=64)
    args = parser.parse_args(argv)
    summary = run_probe(args.out, seed=args.seed, max_count=args.max_count)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
