"""Episode-fixed distance-metric variants for framed Voronoi partitions.

The source task computes, for every frame-interior cell, a distance vector to
all colored seeds (step A).  It then selects the uniquely nearest seed color,
or black when multiple colors share the minimum (step B).  ``metric`` changes
step A while preserving the same non-collapsing minimum/tie decision in step B.

Python labels are deterministic claims for authoring and diagnostics.  Native
qualification and this module's evidence CLI re-execute them through protected
Racket; the exact canonical Racket bytes remain the default authority.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from functools import lru_cache
from pathlib import Path
import random
import sys
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
REPO = HERE.parents[3]
TASK_ID = "9ea9f1e62275"
METRICS = ("manhattan", "chebyshev", "euclidean_sq")
PARAMETERS = {"metric": list(METRICS)}
DEFAULT = {"metric": "manhattan"}
SETTINGS = tuple({"metric": metric} for metric in METRICS)

_GENERATOR_PATH = TASK_HOME / "generator.py"
_GENERATOR_SPEC = importlib.util.spec_from_file_location(
    f"_{TASK_ID}_generator_for_parametric", _GENERATOR_PATH
)
if _GENERATOR_SPEC is None or _GENERATOR_SPEC.loader is None:
    raise ImportError(f"cannot load {_GENERATOR_PATH}")
_GENERATOR = importlib.util.module_from_spec(_GENERATOR_SPEC)
_GENERATOR_SPEC.loader.exec_module(_GENERATOR)

# Full canvas height/width, seed count, require two seeds adjacent to the inner
# frame boundary.  Every query role has a materially different geometry.
_DEMO_PROFILES = (
    (10, 12, 4, False, "compact"),
    (12, 15, 5, True, "boundary"),
    (16, 13, 5, False, "portrait"),
    (18, 20, 6, True, "wide"),
    (22, 17, 7, False, "tall"),
    (24, 26, 8, True, "dense"),
)
_QUERY_PROFILES = (
    (30, 30, 8, True, "stress30"),
    (9, 26, 6, True, "thin_wide"),
    (26, 11, 6, True, "tall_narrow"),
    (18, 21, 7, True, "boundary_mix"),
)

_RIVAL_DISTANCE_KINDS = ("vertical_only", "horizontal_only", "weighted_row", "weighted_col")
_RIVAL_TIE_POLICIES = ("lowest_color", "highest_color", "first_seed")


def _exact_integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"metric"}:
        raise ValueError("settings must contain exactly metric")
    metric = settings["metric"]
    if type(metric) is not str or metric not in METRICS:
        raise ValueError(f"metric must be one of {METRICS!r}")
    return {"metric": metric}


def program(settings: Any) -> str:
    metric = _settings(settings)["metric"]
    filename = {
        "manhattan": "canonical.rkt",
        "chebyshev": "chebyshev.rkt",
        "euclidean_sq": "euclidean_sq.rkt",
    }[metric]
    return (HERE / filename).read_text(encoding="utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _rng(seed: int, domain: str, index: int = 0, nonce: int = 0) -> random.Random:
    return random.Random(int(_digest([TASK_ID, "metric-family-v1", seed, domain, index, nonce]), 16))


def _distance(seed: tuple[int, int, int], row: int, col: int, kind: str) -> int:
    dr = abs(seed[0] - row)
    dc = abs(seed[1] - col)
    if kind == "manhattan":
        return dr + dc
    if kind == "chebyshev":
        return max(dr, dc)
    if kind == "euclidean_sq":
        return dr * dr + dc * dc
    if kind == "vertical_only":
        return dr
    if kind == "horizontal_only":
        return dc
    if kind == "weighted_row":
        return 2 * dr + dc
    if kind == "weighted_col":
        return dr + 2 * dc
    raise ValueError(f"unknown distance kind: {kind!r}")


def _analyze(grid: Any) -> dict[str, Any]:
    facts = _GENERATOR.analyze_grid(grid)
    if facts["errors"]:
        raise ValueError(f"invalid framed Voronoi grid: {facts['errors']}")
    if not 2 <= len(facts["seeds"]) <= 8:
        raise ValueError("grid must contain 2..8 distinct-colored seeds")
    colors = [seed[2] for seed in facts["seeds"]]
    if len(colors) != len(set(colors)):
        raise ValueError("seed colors must be distinct")
    return facts


def _apply_rule(grid: Any, distance_kind: str, tie_policy: str = "black") -> list[list[int]]:
    facts = _analyze(grid)
    r0, c0, r1, c1 = facts["frame_bbox"]
    seeds = tuple(facts["seeds"])
    output = [list(row) for row in grid]
    for row in range(r0 + 1, r1):
        for col in range(c0 + 1, c1):
            values = [_distance(seed, row, col, distance_kind) for seed in seeds]
            minimum = min(values)
            winners = [seed for seed, value in zip(seeds, values) if value == minimum]
            colors = sorted({seed[2] for seed in winners})
            if len(colors) == 1:
                output[row][col] = colors[0]
            elif tie_policy == "black":
                output[row][col] = 0
            elif tie_policy == "lowest_color":
                output[row][col] = colors[0]
            elif tie_policy == "highest_color":
                output[row][col] = colors[-1]
            elif tie_policy == "first_seed":
                output[row][col] = winners[0][2]
            else:
                raise ValueError(f"unknown tie policy: {tie_policy!r}")
    return output


def apply_metric(grid: Any, metric: str) -> list[list[int]]:
    if type(metric) is not str or metric not in METRICS:
        raise ValueError(f"metric must be one of {METRICS!r}")
    return _apply_rule(grid, metric)


def _paint_frame(
    height: int, width: int, rng: random.Random
) -> tuple[list[list[int]], tuple[int, int, int, int]]:
    # Vary frame offset and extent while preserving at least one zero-padding
    # cell and the source task's minimum 6x8 frame.
    layouts = [
        (top, left, height - bottom_margin - 1, width - right_margin - 1)
        for top in (1, 2)
        for bottom_margin in (1, 2)
        for left in (1, 2, 3)
        for right_margin in (1, 2, 3)
        if height - top - bottom_margin >= 6
        and width - left - right_margin >= 8
    ]
    if not layouts:
        raise ValueError("canvas cannot hold a padded 6x8 frame")
    top, left, bottom, right = rng.choice(layouts)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            if row in {top, bottom} or col in {left, right}:
                grid[row][col] = 1
    return grid, (top, left, bottom, right)


def _candidate_scene(
    seed: int,
    domain: str,
    index: int,
    profile: tuple[int, int, int, bool, str],
    nonce: int,
) -> list[list[int]]:
    height, width, seed_count, require_boundary, _role = profile
    rng = _rng(seed, domain, index, nonce)
    grid, (top, left, bottom, right) = _paint_frame(height, width, rng)
    interior = [
        (row, col)
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
    ]
    positions: list[tuple[int, int]] = []
    if require_boundary:
        boundary = [
            (row, col)
            for row, col in interior
            if row in {top + 1, bottom - 1} or col in {left + 1, right - 1}
        ]
        positions.extend(rng.sample(boundary, 2))
    available = [cell for cell in interior if cell not in positions]
    positions.extend(rng.sample(available, seed_count - len(positions)))
    colors = rng.sample(list(range(2, 10)), seed_count)
    # Decouple color rank from position order and vary it per scene.
    rng.shuffle(colors)
    for (row, col), color in zip(positions, colors):
        grid[row][col] = color
    return grid


def _interior_values(
    grid: list[list[int]], frame_bbox: tuple[int, int, int, int]
) -> list[int]:
    # Completed outputs color every interior cell, so they cannot be re-parsed as
    # sparse seed inputs.  The input-derived frame bounds are the stable contract.
    r0, c0, r1, c1 = frame_bbox
    return [grid[row][col] for row in range(r0 + 1, r1) for col in range(c0 + 1, c1)]


def _scene_quality(grid: list[list[int]]) -> bool:
    facts = _analyze(grid)
    outputs = {metric: apply_metric(grid, metric) for metric in METRICS}
    if len({_digest(output) for output in outputs.values()}) != len(METRICS):
        return False
    r0, c0, r1, c1 = facts["frame_bbox"]
    minimum_disagreement = max(3, ((r1 - r0 - 1) * (c1 - c0 - 1)) // 50)
    for index, left in enumerate(METRICS):
        for right in METRICS[index + 1 :]:
            disagreement = sum(
                a != b
                for row_a, row_b in zip(outputs[left], outputs[right])
                for a, b in zip(row_a, row_b)
            )
            if disagreement < minimum_disagreement:
                return False
    seed_colors = {seed[2] for seed in facts["seeds"]}
    for output in outputs.values():
        interior = _interior_values(output, facts["frame_bbox"])
        if 0 not in interior:  # visibly teach black tie retention
            return False
        if not seed_colors.issubset(set(interior)):
            return False
    return True


def _scene(
    seed: int,
    domain: str,
    index: int,
    profile: tuple[int, int, int, bool, str],
    bank_nonce: int,
) -> list[list[int]]:
    for attempt in range(512):
        grid = _candidate_scene(seed, domain, index, profile, bank_nonce * 1000 + attempt)
        if _scene_quality(grid):
            return grid
    raise RuntimeError(f"could not construct a distinguishing {domain} scene for profile {profile!r}")


def metric_survivors(train_inputs: Any, chosen_metric: str) -> list[str]:
    if type(train_inputs) is not list or not train_inputs:
        raise ValueError("train_inputs must be a nonempty list")
    if chosen_metric not in METRICS:
        raise ValueError(f"unknown chosen metric: {chosen_metric!r}")
    labels = [apply_metric(grid, chosen_metric) for grid in train_inputs]
    return [
        metric
        for metric in METRICS
        if all(apply_metric(grid, metric) == label for grid, label in zip(train_inputs, labels))
    ]


def rival_survivors(train_inputs: Any, chosen_metric: str) -> list[str]:
    if type(train_inputs) is not list or not train_inputs:
        raise ValueError("train_inputs must be a nonempty list")
    if chosen_metric not in METRICS:
        raise ValueError(f"unknown chosen metric: {chosen_metric!r}")
    labels = [apply_metric(grid, chosen_metric) for grid in train_inputs]
    rivals: list[tuple[str, Callable[[Any], list[list[int]]]]] = []
    for policy in _RIVAL_TIE_POLICIES:
        rivals.append(
            (
                f"{chosen_metric}_ties_{policy}",
                lambda grid, policy=policy: _apply_rule(grid, chosen_metric, policy),
            )
        )
    for distance_kind in _RIVAL_DISTANCE_KINDS:
        rivals.append(
            (
                distance_kind,
                lambda grid, distance_kind=distance_kind: _apply_rule(grid, distance_kind),
            )
        )
    return [
        name
        for name, rival in rivals
        if all(rival(grid) == label for grid, label in zip(train_inputs, labels))
    ]


def _valid_minimum_lesson(train: list[list[list[int]]]) -> bool:
    return all(
        metric_survivors(train[:2], metric) == [metric]
        and rival_survivors(train[:2], metric) == []
        for metric in METRICS
    )


def _frozen_grid(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _thawed_grid(grid: tuple[tuple[int, ...], ...]) -> list[list[int]]:
    return [list(row) for row in grid]


@lru_cache(maxsize=256)
def _cached_bank(seed: int) -> tuple[tuple[tuple[tuple[int, ...], ...], ...], tuple[tuple[tuple[int, ...], ...], ...], tuple[str, ...]]:
    _exact_integer(seed, -(2**63), 2**63 - 1, "seed")
    demos: list[list[list[int]]] | None = None
    for bank_nonce in range(128):
        candidate = [
            _scene(seed, "demo", index, profile, bank_nonce)
            for index, profile in enumerate(_DEMO_PROFILES)
        ]
        if _valid_minimum_lesson(candidate):
            demos = candidate
            break
    if demos is None:
        raise RuntimeError("could not construct a two-demonstration identifying lesson")

    # Query generation is a separate seed stream: changing demo count or retry
    # history cannot change the four stored queries.  Shuffle the complete bank
    # before any one-query projection so source slot zero is not always first.
    queries = [
        _scene(seed, "query", index, profile, 0)
        for index, profile in enumerate(_QUERY_PROFILES)
    ]
    order = list(range(4))
    _rng(seed, "query-order").shuffle(order)
    queries = [queries[index] for index in order]
    roles = tuple(_QUERY_PROFILES[index][4] for index in order)

    all_grids = demos + queries
    if len({_digest(grid) for grid in all_grids}) != len(all_grids):
        raise RuntimeError("generated duplicate demonstration/query input")
    return (
        tuple(_frozen_grid(grid) for grid in demos),
        tuple(_frozen_grid(grid) for grid in queries),
        roles,
    )


def build_input_bank(seed: int, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _exact_integer(seed, -(2**63), 2**63 - 1, "seed")
    _exact_integer(demos, 2, 6, "demos")
    if type(queries) is not int:
        raise TypeError("queries must be an exact integer")
    if queries != 4:
        raise ValueError("queries must equal 4")
    frozen_demos, frozen_queries, roles = _cached_bank(seed)
    return {
        "train": [_thawed_grid(grid) for grid in frozen_demos[:demos]],
        "test": [_thawed_grid(grid) for grid in frozen_queries],
        "query_roles": list(roles),
    }


def certify(episode: Any, execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    chosen = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program_solution does not match settings")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train and test lists")
    _exact_integer(len(train), 2, 6, "demos")
    if len(test) != 4:
        raise ValueError("episode must contain exactly four queries")

    seen: set[str] = set()
    for pair in train + test:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each private pair must contain exactly input and output")
        _analyze(pair["input"])
        output_errors = _GENERATOR._grid_errors(pair["output"])
        if output_errors:
            raise ValueError(f"invalid output grid: {output_errors}")
        if (
            len(pair["output"]) != len(pair["input"])
            or len(pair["output"][0]) != len(pair["input"][0])
        ):
            raise ValueError("output grid must match input dimensions")
        key = _digest(pair["input"])
        if key in seen:
            raise ValueError("all demonstration and query inputs must be distinct")
        seen.add(key)

    apply = execute or (lambda source, grid: apply_metric(grid, _metric_for_program(source)))
    records = []
    for setting in SETTINGS:
        source = program(setting)
        disagreements = [
            index
            for index, pair in enumerate(train)
            if apply(source, pair["input"]) != pair["output"]
        ]
        records.append({"settings": dict(setting), "disagreeing_demo_indices": disagreements})
    survivors = [row["settings"] for row in records if not row["disagreeing_demo_indices"]]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify the selected metric: {survivors!r}")

    inputs = [pair["input"] for pair in train]
    shortcuts = rival_survivors(inputs, chosen["metric"])
    if shortcuts:
        raise ValueError(f"demonstrations leave declared shortcuts alive: {shortcuts!r}")

    source = program(chosen)
    for pair in train + test:
        prediction = apply(source, pair["input"])
        if prediction != pair["output"]:
            raise ValueError("retained label disagrees with selected Racket rule")
    return {
        "scope": "three declared metrics plus seven metric/tie shortcuts",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "demo_refutations": records,
        "shortcut_survivors": shortcuts,
        "query_input_sha256": [_digest(pair["input"]) for pair in test],
    }


def _metric_for_program(source: str) -> str:
    matches = [setting["metric"] for setting in SETTINGS if program(setting) == source]
    if len(matches) != 1:
        raise ValueError("source does not identify exactly one metric")
    return matches[0]


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _exact_integer(seed, -(2**63), 2**63 - 1, "seed")
    chosen = _settings(settings)
    bank = build_input_bank(seed, demos=demos, queries=queries)
    metric = chosen["metric"]
    episode = {
        "schema": "9ea9-distance-metric-parametric-proposal-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": [
            {"input": grid, "output": apply_metric(grid, metric)} for grid in bank["train"]
        ],
        "test": [
            {"input": grid, "output": apply_metric(grid, metric)} for grid in bank["test"]
        ],
        "program_solution": program(chosen),
        "program_sha256": hashlib.sha256(program(chosen).encode("utf-8")).hexdigest(),
        "query_roles": bank["query_roles"],
    }
    episode["certificate"] = certify(episode)
    return copy.deepcopy(episode)


class RacketRunner:
    """One protected Racket bridge reused across a bounded evidence batch."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        _analyze(grid)
        wrapped = self.cache.setdefault(source, wrap_rule(source))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({wrapped} {literal})")

    def __exit__(self, *exc: Any) -> None:
        self.bridge.close()


def source_hashes() -> dict[str, str]:
    paths = [
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "canonical.rkt",
        HERE / "chebyshev.rkt",
        HERE / "euclidean_sq.rkt",
        HERE / "adversarial_probe.py",
        TASK_HOME / "generator.py",
    ]
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def _write_evidence(episodes: list[dict[str, Any]], destination: Path, runtime_identity: dict[str, Any]) -> None:
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    private = {
        "schema": "9ea9-distance-metric-evidence-v1",
        "status": "prototype_proposed",
        "training_admitted": False,
        "runtime_identity": runtime_identity,
        "source_sha256": source_hashes(),
        "episodes": episodes,
    }
    payload = json.dumps(private, sort_keys=True, separators=(",", ":")) + "\n"
    (destination / "episodes-private.json").write_text(payload, encoding="utf-8")
    manifest = {
        "schema": "9ea9-distance-metric-evidence-manifest-v1",
        "status": "prototype_proposed",
        "episodes": len(episodes),
        "racket_checked_pairs": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
        "files": {
            "episodes-private.json": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        },
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--metric", choices=METRICS, default="manhattan")
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    settings = SETTINGS if args.all_settings else ({"metric": args.metric},)
    episodes = []
    with RacketRunner() as execute:
        for setting in settings:
            for seed in args.seeds or [0, 17]:
                episode = generate(seed, setting, args.demos, args.queries)
                episode["certificate"] = certify(episode, execute)
                episodes.append(episode)
        _write_evidence(episodes, args.out, execute.identity)
    print(
        json.dumps(
            {
                "status": "prototype_proposed",
                "episodes": len(episodes),
                "racket_checked_pairs": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
