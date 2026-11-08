#!/usr/bin/env python3
"""Proposed episode-level ``rank_order`` extension for fe947dc3e12c.

The canonical production generator remains unchanged.  This authoring
prototype preserves the original reasoning pattern—extract three components,
measure their cell counts, sort, and apply the rank palette 1/4/2—while making
one small episode-level parameter explicit:

``largest_first`` (canonical default)
    Sort component sizes descending.
``smallest_first``
    Sort component sizes ascending.

One setting is pinned for the complete three-demo/one-query episode.  The CLI
executes both instantiated Racket programs and retains source hashes, labels,
and a public challenge with query outputs removed.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TASK_ID = "fe947dc3e12c"
VERSION = "rank-order-prototype-v1"
PARAMETER_NAME = "rank_order"
SETTINGS = ("largest_first", "smallest_first")
DEFAULT_SETTING = "largest_first"
CANONICAL_SORT_KEY = "(* -1 (obj-size o))"
ALTERNATIVE_SORT_KEY = "(obj-size o)"


def _sha256(value: str | bytes) -> str:
    data = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(data).hexdigest()


def _grid_sha256(grid) -> str:
    payload = json.dumps(normalize_grid(grid), separators=(",", ":"), sort_keys=False)
    return _sha256(payload)


def _validate_seed(seed: Any) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")


def _validate_setting(rank_order: Any) -> str:
    if type(rank_order) is not str or rank_order not in SETTINGS:
        raise ValueError(f"rank_order must be one of {SETTINGS}")
    return rank_order


def canonical_rule_source(*, root: Path | str | None = None) -> str:
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(f"expected one canonical program_solution for {TASK_ID}")
    source = sources.pop()
    if source.count(CANONICAL_SORT_KEY) != 1:
        raise ValueError("canonical source no longer has the unique declared sort key")
    if ALTERNATIVE_SORT_KEY in source.replace(CANONICAL_SORT_KEY, "", 1):
        raise ValueError("canonical source unexpectedly contains the alternative sort key")
    return source


def instantiate_rule(
    rank_order: str = DEFAULT_SETTING,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    rank_order = _validate_setting(rank_order)
    canonical = canonical_rule_source(root=root) if source is None else source
    if canonical.count(CANONICAL_SORT_KEY) != 1:
        raise ValueError("source must contain exactly one canonical size-sort key")
    if rank_order == DEFAULT_SETTING:
        return canonical
    alternative = canonical.replace(CANONICAL_SORT_KEY, ALTERNATIVE_SORT_KEY, 1)
    if alternative == canonical or alternative.count(ALTERNATIVE_SORT_KEY) != 1:
        raise AssertionError("failed to instantiate smallest-first Racket rule")
    return alternative


def _components(grid):
    grid = normalize_grid(grid)
    height, width = len(grid), len(grid[0])
    seen, groups = set(), []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack, cells = [(row, col)], set()
            seen.add((row, col))
            while stack:
                current = stack.pop()
                cells.add(current)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = current[0] + dr, current[1] + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] != 0
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            groups.append(cells)
    return groups


def solve_python(grid, *, rank_order: str = DEFAULT_SETTING):
    rank_order = _validate_setting(rank_order)
    normalized = normalize_grid(grid)
    groups = _components(normalized)
    if len(groups) != 3 or len({len(group) for group in groups}) != 3:
        raise ValueError("prototype domain requires three differently-sized components")
    reverse = rank_order == "largest_first"
    groups = sorted(groups, key=lambda cells: len(cells), reverse=reverse)
    result = [row[:] for row in normalized]
    for color, cells in zip((1, 4, 2), groups):
        for row, col in cells:
            result[row][col] = color
    return result


def _racket_callable(source: str) -> str:
    source = source.strip()
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("expected a single outer rule! wrapper")
    body = source[len("(rule!") : -1].strip()
    if not body.startswith("(lambda (g)"):
        raise ValueError("expected rule! to wrap a grid lambda")
    return body


def _grid_literal(grid) -> str:
    grid = normalize_grid(grid)
    return "'(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


def racket_status() -> dict[str, Any]:
    return racket_runtime_status()


def racket_outputs(
    grids,
    *,
    rank_order: str = DEFAULT_SETTING,
    root: Path | str | None = None,
):
    source = instantiate_rule(rank_order, root=root)
    callable_source = _racket_callable(source)
    outputs = []
    with RacketBridge() as bridge:
        for grid in grids:
            expression = f"({callable_source} {_grid_literal(grid)})"
            outputs.append(normalize_grid(bridge.eval_text(expression)))
    return outputs


def _fixture_specs(seed: int):
    return (
        {"seed": seed + 11, "sample_index": 0, "texture": "bbox_witness", "palette_mode": "canonical"},
        {"seed": seed + 29, "sample_index": 1, "texture": "bars", "palette_mode": "varied"},
        {"seed": seed + 47, "sample_index": 2, "texture": "bbox_witness", "palette_mode": "varied"},
        {"seed": seed + 71, "sample_index": 3, "texture": "bars", "palette_mode": "canonical"},
    )


def _fixtures(seed: int, *, root: Path | str | None = None):
    root = find_root(__file__) if root is None else Path(root).resolve()
    generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    rows = []
    for index, spec in enumerate(_fixture_specs(seed)):
        overrides = {
            "grid_h": 10,
            "grid_w": 10,
            "texture": spec["texture"],
            "palette_mode": spec["palette_mode"],
        }
        grid = generator.generate(
            spec["seed"], spec["sample_index"], difficulty="medium", **overrides
        )
        if generator.self_check(grid):
            raise AssertionError(f"fixture {index} is outside the canonical generator domain")
        observed = generator.observe_overrides(grid)
        if observed != overrides:
            raise AssertionError(f"fixture {index} override mismatch: {observed} != {overrides}")
        rows.append(
            {
                "fixture_id": f"fixture-{index}",
                "input": normalize_grid(grid),
                "input_sha256": _grid_sha256(grid),
                "generation": {
                    "seed": spec["seed"],
                    "sample_index": spec["sample_index"],
                    "difficulty": "medium",
                    "overrides": overrides,
                    "generator_path": Path(generator_path).relative_to(root).as_posix(),
                    "generator_sha256": generator_sha256,
                },
            }
        )
    return rows


def make_episode(
    seed: int,
    *,
    rank_order: str = DEFAULT_SETTING,
    root: Path | str | None = None,
):
    _validate_seed(seed)
    rank_order = _validate_setting(rank_order)
    source = instantiate_rule(rank_order, root=root)
    rows = _fixtures(seed, root=root)
    pairs = [
        {
            "fixture_id": row["fixture_id"],
            "input": copy.deepcopy(row["input"]),
            "output": solve_python(row["input"], rank_order=rank_order),
            "input_sha256": row["input_sha256"],
            "generation": row["generation"],
        }
        for row in rows
    ]
    other = next(setting for setting in SETTINGS if setting != rank_order)
    distinguishing = [
        pair["fixture_id"]
        for pair in pairs[:3]
        if solve_python(pair["input"], rank_order=other) != pair["output"]
    ]
    if not distinguishing:
        raise AssertionError("training demonstrations do not distinguish the chosen setting")
    return {
        "schema": "fe947dc3e12c-rank-order-episode-v1",
        "task_id": TASK_ID,
        "version": VERSION,
        "seed": seed,
        "parameter": {PARAMETER_NAME: rank_order},
        "canonical_default": rank_order == DEFAULT_SETTING,
        "rule_source": source,
        "rule_source_sha256": _sha256(source),
        "rule_hash_12": _sha256(" ".join(source.split()))[:12],
        "distinguishing_demo_fixture_ids": distinguishing,
        "train": pairs[:3],
        "test": pairs[3:],
    }


def _public_episode(episode):
    public = copy.deepcopy(episode)
    for pair in public["test"]:
        pair.pop("output", None)
    return public


def build_evidence(seed: int, out_dir: Path, *, root: Path | str | None = None) -> dict:
    _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root).resolve()
    out_dir = out_dir.resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty evidence directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rules").mkdir()

    status = racket_status()
    episodes = []
    for setting in SETTINGS:
        episode = make_episode(seed, rank_order=setting, root=root)
        grids = [pair["input"] for pair in episode["train"] + episode["test"]]
        expected = [pair["output"] for pair in episode["train"] + episode["test"]]
        if not status["available"]:
            raise RuntimeError(status["reason"])
        actual = racket_outputs(grids, rank_order=setting, root=root)
        if actual != expected:
            raise AssertionError(f"Racket/Python label mismatch for {setting}")
        episode["racket_verified"] = True
        episode["racket_output_sha256"] = [_grid_sha256(grid) for grid in actual]
        episodes.append(episode)
        (out_dir / "rules" / f"{setting}.rkt").write_text(
            episode["rule_source"] + "\n", encoding="utf-8"
        )

    public = [_public_episode(episode) for episode in episodes]
    (out_dir / "episodes-private.json").write_text(
        json.dumps(episodes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "episodes-public.json").write_text(
        json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report = {
        "schema": "fe947dc3e12c-rank-order-prototype-report-v1",
        "task_id": TASK_ID,
        "prototype_status": "proposed_not_selected",
        "parameter": PARAMETER_NAME,
        "settings": list(SETTINGS),
        "default_setting": DEFAULT_SETTING,
        "seed": seed,
        "episode_count": len(episodes),
        "demonstrations_per_episode": 3,
        "queries_per_episode": 1,
        "all_racket_matches_python": True,
        "all_demo_sets_distinguish_selected_setting": all(
            episode["distinguishing_demo_fixture_ids"] for episode in episodes
        ),
        "racket_runtime": status,
        "rule_hashes": {
            episode["parameter"][PARAMETER_NAME]: {
                "source_sha256": episode["rule_source_sha256"],
                "normalized_hash_12": episode["rule_hash_12"],
            }
            for episode in episodes
        },
        "limits": [
            "Prototype only; it does not change the selected canonical rule or production generator.",
            "Evidence covers two finite settings and four deterministic lawful fixtures per setting.",
            "Demo distinction is measured against the other declared rank-order setting, not every conceivable rule.",
        ],
    }
    (out_dir / "prototype-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261020)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    report = build_evidence(args.seed, args.out_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
