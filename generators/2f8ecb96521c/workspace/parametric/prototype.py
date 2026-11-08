#!/usr/bin/env python3
"""Episode-level rank-order prototype for generator ``2f8ecb96521c``.

This research prototype deliberately lives outside ``generator.py``.  It keeps
input generation fixed and chooses one hidden ranking direction once per ARC
episode:

* ``small_to_large`` — the canonical rule (smaller interior -> 1, larger -> 2)
* ``large_to_small`` — the exact directional rival (larger interior -> 1,
  smaller -> 2)

Every retained label is produced by executing the corresponding exact Racket
program through the protected bridge and is cross-checked against an independent
Python mirror.  Public challenge files omit the hidden setting, rule source, and
query answer; private evidence retains all three.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.base import stable_rng
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "2f8ecb96521c"
PROTOTYPE_VERSION = "rank-order-prototype-v1"
RANK_ORDERS = ("small_to_large", "large_to_small")
DEFAULT_RANK_ORDER = "small_to_large"
N_TRAIN = 4
N_TEST = 1
_ASCENDING_FRAGMENT = "(sort-by (objects grid 0) obj-size)"
_DESCENDING_FRAGMENT = "(reverse (sort-by (objects grid 0) obj-size))"

PARAMETER_SPEC = {
    "rank_order": {
        "allowed": list(RANK_ORDERS),
        "canonical_default": DEFAULT_RANK_ORDER,
        "chosen_once_per_episode": True,
        "meaning": {
            "small_to_large": "rank color 1 goes to the smaller rectangle interior",
            "large_to_small": "rank color 1 goes to the larger rectangle interior",
        },
        "distinguishability_contract": (
            "every generated grid contains exactly two distinct-area rectangles "
            "with nonempty interiors, so the two settings disagree on every pair"
        ),
    }
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_generator_for_root(root: Path):
    """Load the selected bytes without mixing portable-runtime package trees.

    The task-test snapshot intentionally contains both execution-layout sources
    (``puzzle_generators/per_puzzle``) and repository-layout mirrors
    (``generators/<id>``). Earlier tests may already have imported dependencies
    from the repository-layout ``shared/runtime`` mirror. In that one manifest-
    bound case, ``load_selected_generator`` correctly rejects crossing to the
    execution-layout package tree. We therefore execute the repository mirror
    only after proving its bytes equal the manifest-selected generator hash.
    Normal repository and standalone runs continue to use the shared loader.
    """
    manifest_path = root / "RUNTIME_MANIFEST.json"
    mirror_path = root / "generators" / TASK_ID / "generator.py"
    if manifest_path.is_file() and mirror_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        library_path = f"generators/{TASK_ID}/generator.py"
        matches = [
            row for row in manifest.get("files", [])
            if row.get("library_path") == library_path
            and row.get("runtime_path") != library_path
        ]
        if len(matches) != 1:
            raise ValueError(
                f"expected one manifest-selected generator for {TASK_ID}, found {len(matches)}"
            )
        actual_sha = _sha256_file(mirror_path)
        expected_sha = matches[0].get("sha256")
        if actual_sha != expected_sha:
            raise ValueError(
                "portable repository mirror does not match the manifest-selected "
                f"generator: {actual_sha} != {expected_sha}"
            )
        module_name = f"_rank_order_selected_{TASK_ID}_{actual_sha}"
        spec = importlib.util.spec_from_file_location(module_name, mirror_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot import selected generator mirror: {mirror_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, mirror_path, actual_sha
    return load_selected_generator(TASK_ID, root=root)


def _canonical_row(root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    if len(rows) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, found {len(rows)}")
    if not isinstance(rows[0].get("program_solution"), str):
        raise ValueError("canonical row has no string program_solution")
    return rows[0]


def _validate_rank_order(rank_order: Any) -> str:
    if type(rank_order) is not str:
        raise TypeError("rank_order must be a string")
    if rank_order not in RANK_ORDERS:
        raise ValueError(f"rank_order must be one of {RANK_ORDERS}")
    return rank_order


def program_for(
    rank_order: str = DEFAULT_RANK_ORDER,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize the exact bounded Racket rule for ``rank_order``.

    The canonical setting returns the ledger bytes unchanged.  The alternate
    setting changes exactly one expression: it reverses the area-sorted object
    list before the existing ``zip-lists`` assigns rank colors 1 and 2.
    """
    rank_order = _validate_rank_order(rank_order)
    resolved = Path(root).resolve() if root is not None else find_root(__file__)
    canonical = _canonical_row(resolved)["program_solution"]
    count = canonical.count(_ASCENDING_FRAGMENT)
    if count != 1:
        raise ValueError(
            "canonical rule drift: expected exactly one area-order fragment, "
            f"found {count}"
        )
    if rank_order == DEFAULT_RANK_ORDER:
        return canonical
    return canonical.replace(_ASCENDING_FRAGMENT, _DESCENDING_FRAGMENT, 1)


def choose_rank_order(seed: int) -> str:
    """Choose one hidden setting deterministically from the episode seed."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    rng = stable_rng(seed, f"{TASK_ID}|rank_order", PROTOTYPE_VERSION)
    return RANK_ORDERS[rng.randrange(len(RANK_ORDERS))]


def select_seeds(base_seed: int, *, per_setting: int = 1) -> dict[str, Any]:
    """Find deterministic episode seeds covering every bounded setting."""
    if type(base_seed) is not int:
        raise TypeError("base_seed must be an integer (not bool)")
    if type(per_setting) is not int or per_setting < 1:
        raise ValueError("per_setting must be a positive integer (not bool)")
    buckets = {setting: [] for setting in RANK_ORDERS}
    offset = 0
    max_scan = max(10_000, per_setting * len(RANK_ORDERS) * 100)
    while any(len(values) < per_setting for values in buckets.values()):
        if offset >= max_scan:
            raise RuntimeError("failed to cover every rank-order setting")
        seed = base_seed + offset
        setting = choose_rank_order(seed)
        if len(buckets[setting]) < per_setting:
            buckets[setting].append(seed)
        offset += 1
    return {
        "base_seed": base_seed,
        "per_setting": per_setting,
        "scanned_seed_count": offset,
        "seeds_by_setting": buckets,
    }


def _components4(grid: list[list[int]], color: int = 4) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] != color or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _python_output(grid: list[list[int]], rank_order: str) -> list[list[int]]:
    """Independent semantic mirror used only to audit Racket outputs."""
    rank_order = _validate_rank_order(rank_order)
    components = _components4(grid)
    if len(components) != 2:
        raise ValueError(f"expected exactly two color-4 components, found {len(components)}")

    def descriptor(cells: list[tuple[int, int]]) -> tuple[int, int, int, int, int]:
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        return len(cells), min(rows), min(cols), max(rows), max(cols)

    described = [(descriptor(cells), cells) for cells in components]
    described.sort(key=lambda item: item[0][0], reverse=rank_order == "large_to_small")
    if described[0][0][0] == described[1][0][0]:
        raise ValueError("rank-order prototype requires distinct component areas")

    output = deepcopy(grid)
    for rank_color, (desc, _cells) in enumerate(described, start=1):
        _area, r1, c1, r2, c2 = desc
        if r2 - r1 < 2 or c2 - c1 < 2:
            raise ValueError("rank-order prototype requires nonempty strict interiors")
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                if grid[r][c] == 4:
                    output[r][c] = rank_color
    return output


def _racket_body(program: str) -> str:
    return strip_rule_wrapper(strip_line_comments(program))


def _apply_racket(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    bridge.define_grid("g", grid)
    value = bridge.eval_text(f"({_racket_body(program)} g)")
    if not isinstance(value, list) or not value or not all(isinstance(row, list) for row in value):
        raise TypeError(f"Racket rule returned a non-grid value: {type(value).__name__}")
    return value


def _public_episode(
    grids: list[list[list[int]]], selected_outputs: list[list[list[int]]]
) -> dict[str, Any]:
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(
                grids[:N_TRAIN], selected_outputs[:N_TRAIN], strict=True
            )
        ],
        "test": [{"input": grid} for grid in grids[N_TRAIN:]],
    }


def _private_pairs(
    grids: list[list[list[int]]],
    selected: list[list[list[int]]],
    rival: list[list[list[int]]],
    differences: list[bool],
    start: int,
    stop: int,
) -> list[dict[str, Any]]:
    return [
        {
            "input": grids[index],
            "output": selected[index],
            "rival_output": rival[index],
            "settings_disagree": differences[index],
        }
        for index in range(start, stop)
    ]


def run_probe(
    *,
    base_seed: int,
    per_setting: int = 1,
    difficulty: str = "medium",
    out_dir: Path | str,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Generate, Racket-label, cross-check, and retain a balanced probe."""
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    resolved = Path(root).resolve() if root is not None else find_root(__file__)
    output_root = Path(out_dir).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    if any(output_root.iterdir()):
        raise FileExistsError(f"refusing to mix evidence into nonempty directory: {output_root}")

    selection = select_seeds(base_seed, per_setting=per_setting)
    generator, generator_path, generator_sha = _load_generator_for_root(resolved)
    ledger_path = canonical_path(resolved)
    prototype_path = Path(__file__).resolve()
    programs = {setting: program_for(setting, root=resolved) for setting in RANK_ORDERS}

    rules_dir = output_root / "private" / "rules"
    for setting, text in programs.items():
        path = rules_dir / f"rank-order-{setting}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    episodes: list[dict[str, Any]] = []
    application_count = 0
    first_witness: dict[str, Any] | None = None
    with RacketBridge(timeout=15.0, startup_timeout=45.0) as bridge:
        runtime_identity = bridge.runtime_identity
        episode_index = 0
        for expected_setting in RANK_ORDERS:
            for seed in selection["seeds_by_setting"][expected_setting]:
                rank_order = choose_rank_order(seed)
                if rank_order != expected_setting:
                    raise AssertionError("selected seed does not reproduce its recorded setting")
                rival_order = next(value for value in RANK_ORDERS if value != rank_order)
                sample_start = stable_rng(
                    seed,
                    f"{TASK_ID}|episode_start",
                    PROTOTYPE_VERSION,
                ).randrange(10_000)
                grids = [
                    generator.generate(
                        seed,
                        sample_start + index,
                        difficulty=difficulty,
                    )
                    for index in range(N_TRAIN + N_TEST)
                ]
                for index, grid in enumerate(grids):
                    findings = generator.self_check(grid, difficulty=difficulty)
                    if findings:
                        raise AssertionError(
                            f"generated grid {index} failed self_check: {findings}"
                        )

                outputs: dict[str, list[list[list[int]]]] = {
                    setting: [] for setting in RANK_ORDERS
                }
                for setting in RANK_ORDERS:
                    for grid in grids:
                        actual = _apply_racket(bridge, programs[setting], grid)
                        application_count += 1
                        expected = _python_output(grid, setting)
                        if actual != expected:
                            raise AssertionError(
                                f"Racket output disagrees with Python mirror for {setting}"
                            )
                        outputs[setting].append(actual)

                differences = [
                    outputs[RANK_ORDERS[0]][index] != outputs[RANK_ORDERS[1]][index]
                    for index in range(len(grids))
                ]
                demonstration_differences = [
                    index for index, differs in enumerate(differences[:N_TRAIN]) if differs
                ]
                query_differences = [
                    index
                    for index, differs in enumerate(differences[N_TRAIN:])
                    if differs
                ]
                if demonstration_differences != list(range(N_TRAIN)):
                    raise AssertionError("not every demonstration distinguishes rank order")
                if query_differences != list(range(N_TEST)):
                    raise AssertionError("not every query distinguishes rank order")

                selected_outputs = outputs[rank_order]
                rival_outputs = outputs[rival_order]
                public = _public_episode(grids, selected_outputs)
                private = {
                    "schema": "arc-parametric-private-evidence-v1",
                    "task_id": TASK_ID,
                    "prototype_status": "proposed",
                    "prototype_version": PROTOTYPE_VERSION,
                    "seed": seed,
                    "difficulty": difficulty,
                    "sample_start": sample_start,
                    "rank_order": rank_order,
                    "rival_rank_order": rival_order,
                    "parameter_spec": PARAMETER_SPEC,
                    "racket_verified": True,
                    "python_parity_verified": True,
                    "programs": {
                        setting: {
                            "path": f"../rules/rank-order-{setting}.rkt",
                            "sha256": _sha256_text(text),
                        }
                        for setting, text in programs.items()
                    },
                    "train": _private_pairs(
                        grids,
                        selected_outputs,
                        rival_outputs,
                        differences,
                        0,
                        N_TRAIN,
                    ),
                    "test": _private_pairs(
                        grids,
                        selected_outputs,
                        rival_outputs,
                        differences,
                        N_TRAIN,
                        N_TRAIN + N_TEST,
                    ),
                }
                public_relative = Path("public") / f"episode-{episode_index:03d}.json"
                private_relative = (
                    Path("private") / "episodes" / f"episode-{episode_index:03d}.json"
                )
                _write_json(output_root / public_relative, public)
                _write_json(output_root / private_relative, private)
                episodes.append(
                    {
                        "episode_index": episode_index,
                        "seed": seed,
                        "sample_start": sample_start,
                        "rank_order": rank_order,
                        "rival_rank_order": rival_order,
                        "demonstration_difference_indices": demonstration_differences,
                        "query_difference_indices": query_differences,
                        "public_path": public_relative.as_posix(),
                        "private_path": private_relative.as_posix(),
                    }
                )
                if first_witness is None:
                    first_witness = {
                        "schema": "arc-parametric-cross-setting-witness-v1",
                        "task_id": TASK_ID,
                        "seed": seed,
                        "sample_index": sample_start,
                        "input": grids[0],
                        "outputs": {
                            setting: outputs[setting][0] for setting in RANK_ORDERS
                        },
                        "outputs_disagree": (
                            outputs[RANK_ORDERS[0]][0] != outputs[RANK_ORDERS[1]][0]
                        ),
                        "racket_verified": True,
                        "python_parity_verified": True,
                    }
                episode_index += 1

    if first_witness is None or not first_witness["outputs_disagree"]:
        raise AssertionError("probe produced no cross-setting disagreement witness")
    _write_json(output_root / "private" / "cross-setting-witness.json", first_witness)

    expected_applications = (
        len(episodes) * len(RANK_ORDERS) * (N_TRAIN + N_TEST)
    )
    if application_count != expected_applications:
        raise AssertionError(
            f"Racket application accounting mismatch: {application_count} != {expected_applications}"
        )

    report = {
        "schema": "arc-parametric-probe-report-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "prototype_status": "proposed",
        "prototype_version": PROTOTYPE_VERSION,
        "parameter_spec": PARAMETER_SPEC,
        "base_seed": base_seed,
        "per_setting": per_setting,
        "difficulty": difficulty,
        "seed_selection": selection,
        "episode_count": len(episodes),
        "settings_observed": sorted({episode["rank_order"] for episode in episodes}),
        "racket_application_count": application_count,
        "racket_verified": True,
        "python_parity_verified": True,
        "episodes": episodes,
        "runtime_identity": runtime_identity,
        "sources": {
            "prototype_path": str(prototype_path),
            "prototype_sha256": _sha256_file(prototype_path),
            "generator_path": str(generator_path),
            "generator_sha256": generator_sha,
            "canonical_path": str(ledger_path),
            "canonical_sha256": _sha256_file(ledger_path),
            "program_sha256": {
                setting: _sha256_text(text) for setting, text in programs.items()
            },
        },
        "limitations": [
            "prototype only; generator.py and the canonical rule remain unchanged",
            "the bounded parameter changes ranking direction, not object extraction or recoloring mechanics",
            "evidence covers retained deterministic seeds, not every seed or every conceivable rival",
        ],
    }
    _write_json(output_root / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-seed", type=int, default=20261020)
    parser.add_argument("--per-setting", type=int, default=1)
    parser.add_argument(
        "--difficulty",
        choices=("easy", "medium", "hard"),
        default="medium",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run_probe(
        base_seed=args.base_seed,
        per_setting=args.per_setting,
        difficulty=args.difficulty,
        out_dir=args.out,
        root=find_root(__file__),
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
