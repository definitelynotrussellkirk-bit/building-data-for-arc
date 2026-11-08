#!/usr/bin/env python3
"""Build sharded ARC-native JSONL episodes from ARC-GEN generators.

The output is meant for the ARC-native tensorizer, not the NVARC text
format. By default each row contains one query input/output. With
--group-query-pairs, one row can contain up to four query/test pairs so the
bottleneck model can share one inferred rule across all contest test slots.
"""

from __future__ import annotations

import argparse
import importlib
import json
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.neural.arc_native.dataset import episode_row_to_tensors  # noqa: E402
from src.neural.arc_native.bottleneck_dataset import bottleneck_row_to_tensors  # noqa: E402
from src.neural.arc_native.tensorize import validate_grid  # noqa: E402


DEFAULT_GENERATOR_ROOT = (
    Path("/home/user/Desktop/arc-agi-2-generators")
    if Path("/home/user/Desktop/arc-agi-2-generators").exists()
    else ROOT
)


def load_runner(generator_root: Path):
    sys.path.insert(0, str(generator_root.resolve()))
    return importlib.import_module("puzzle_generators.runner")


def discover_task_ids(generator_root: Path) -> list[str]:
    per_puzzle = generator_root / "puzzle_generators" / "per_puzzle"
    return sorted(
        path.parent.name
        for path in per_puzzle.glob("*/generator.py")
        if not path.parent.name.startswith((".", "_"))
    )


def parse_version(value: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", value or "")
    return tuple(int(part) for part in parts) if parts else (0,)


def generator_version(generator_root: Path, task_id: str) -> str:
    path = generator_root / "puzzle_generators" / "per_puzzle" / task_id / "generator.py"
    try:
        text = path.read_text(errors="ignore")
    except OSError:
        return ""
    match = re.search(r"^\s*VERSION\s*=\s*['\"]([^'\"]+)['\"]", text, re.MULTILINE)
    return match.group(1) if match else ""


def filter_task_ids_by_version(generator_root: Path, task_ids: list[str], minimum: str | None) -> list[str]:
    if not minimum:
        return task_ids
    min_version = parse_version(minimum)
    return [
        task_id
        for task_id in task_ids
        if parse_version(generator_version(generator_root, task_id)) >= min_version
    ]


def discover_rule_task_ids(generator_root: Path) -> set[str]:
    """Return task IDs that have a usable output rule source.

    ARC-GEN per-puzzle generators emit inputs; outputs are produced by
    applying the matching rule. Filtering this once avoids repeatedly
    probing thousands of v2 generators that cannot yet emit pairs.
    """
    rule_ids: set[str] = set()
    solutions_dir = generator_root / "data" / "base" / "solutions"
    if solutions_dir.exists():
        for path in solutions_dir.rglob("*.json"):
            try:
                data = json.loads(path.read_text())
            except Exception:
                continue
            task_id = data.get("task_id")
            racket_target = data.get("racket_target") or {}
            source = (
                racket_target.get("target_code")
                or racket_target.get("raw_code")
                or ""
            )
            if task_id and source.strip() and not racket_target.get("needs_conversion"):
                rule_ids.add(str(task_id))

    sys.path.insert(0, str(generator_root.resolve()))
    try:
        from solvers.grounded_rules import GROUNDED_RULES  # type: ignore
    except Exception:
        GROUNDED_RULES = {}
    for task_id, rule in GROUNDED_RULES.items():
        if isinstance(rule, str) and rule.strip() and not rule.strip().startswith("NOT_GROUNDED"):
            rule_ids.add(str(task_id))
    return rule_ids


def read_task_ids_file(path: Path) -> list[str]:
    task_ids: list[str] = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if line:
            task_ids.append(line)
    return task_ids


def dedupe_preserving_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


class ShardWriter:
    def __init__(self, output_dir: Path, shard_rows: int, *, prefix: str = "episodes") -> None:
        self.output_dir = output_dir
        self.shard_rows = shard_rows
        self.prefix = prefix
        self.shard_index = 0
        self.rows_in_shard = 0
        self.handle = None
        self.paths: list[Path] = []

    def _open_next(self) -> None:
        if self.handle:
            self.handle.close()
        path = self.output_dir / f"{self.prefix}-{self.shard_index:05d}.jsonl"
        self.handle = path.open("w")
        self.paths.append(path)
        self.shard_index += 1
        self.rows_in_shard = 0

    def write(self, row: dict[str, Any]) -> None:
        if self.handle is None or self.rows_in_shard >= self.shard_rows:
            self._open_next()
        assert self.handle is not None
        self.handle.write(json.dumps(row, separators=(",", ":")) + "\n")
        self.rows_in_shard += 1

    def close(self) -> None:
        if self.handle:
            self.handle.close()
            self.handle = None


def _rows_in_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as f:
        return sum(1 for _ in f)


def shape(grid: list[list[int]]) -> list[int]:
    return [len(grid), len(grid[0]) if grid else 0]


def color_set(grid: list[list[int]]) -> list[int]:
    return sorted({int(cell) for row in grid for cell in row})


def validate_episode_grids(
    *,
    demo_pairs: list[dict],
    query_pair: dict,
    canvas_size: int,
    num_arc_colors: int,
) -> tuple[int, int]:
    max_height = 0
    max_width = 0
    grids = []
    for pair in demo_pairs:
        grids.append(pair["input"])
        grids.append(pair["output"])
    grids.append(query_pair["input"])
    grids.append(query_pair["output"])

    for grid in grids:
        height, width = validate_grid(
            grid,
            canvas_size=canvas_size,
            num_arc_colors=num_arc_colors,
        )
        max_height = max(max_height, height)
        max_width = max(max_width, width)
    return max_height, max_width


def validate_episode_query_pairs(
    *,
    demo_pairs: list[dict],
    query_pairs: list[dict],
    canvas_size: int,
    num_arc_colors: int,
) -> tuple[int, int]:
    max_height = 0
    max_width = 0
    for query_pair in query_pairs:
        height, width = validate_episode_grids(
            demo_pairs=demo_pairs,
            query_pair=query_pair,
            canvas_size=canvas_size,
            num_arc_colors=num_arc_colors,
        )
        max_height = max(max_height, height)
        max_width = max(max_width, width)
    return max_height, max_width


def grid_text(grid: list[list[int]], *, max_rows: int = 30, max_cols: int = 30) -> str:
    rows = grid[:max_rows]
    rendered = []
    for row in rows:
        text = "".join(str(int(v)) for v in row[:max_cols])
        if len(row) > max_cols:
            text += "..."
        rendered.append(text)
    if len(grid) > max_rows:
        rendered.append("...")
    return "\n".join(rendered)


def build_row(
    *,
    source: str,
    task_id: str,
    seed: int,
    difficulty: str | None,
    episode_index: int,
    query_index: int,
    demo_pairs: list[dict],
    query_pair: dict,
) -> dict[str, Any]:
    demo_shapes = [
        {
            "input": shape(pair["input"]),
            "output": shape(pair["output"]),
            "same_shape": shape(pair["input"]) == shape(pair["output"]),
        }
        for pair in demo_pairs
    ]
    query_shape = {
        "input": shape(query_pair["input"]),
        "output": shape(query_pair["output"]),
        "same_shape": shape(query_pair["input"]) == shape(query_pair["output"]),
    }
    return {
        "format": "arc_native_episode_v1",
        "source": source,
        "task_id": task_id,
        "seed": seed,
        "difficulty": difficulty,
        "episode_index": episode_index,
        "query_index": query_index,
        "demo_count": len(demo_pairs),
        "query_count": 1,
        "demo_pairs": demo_pairs,
        "query": {
            "input": query_pair["input"],
            "output": query_pair["output"],
        },
        "shapes": {
            "demo_pairs": demo_shapes,
            "query": query_shape,
        },
        "colors": {
            "query_input": color_set(query_pair["input"]),
            "query_output": color_set(query_pair["output"]),
        },
    }


def build_grouped_query_row(
    *,
    source: str,
    task_id: str,
    seed: int,
    difficulty: str | None,
    episode_index: int,
    demo_pairs: list[dict],
    query_pairs: list[dict],
) -> dict[str, Any]:
    demo_shapes = [
        {
            "input": shape(pair["input"]),
            "output": shape(pair["output"]),
            "same_shape": shape(pair["input"]) == shape(pair["output"]),
        }
        for pair in demo_pairs
    ]
    query_shapes = [
        {
            "input": shape(pair["input"]),
            "output": shape(pair["output"]),
            "same_shape": shape(pair["input"]) == shape(pair["output"]),
        }
        for pair in query_pairs
    ]
    return {
        "format": "arc_native_episode_v2",
        "source": source,
        "task_id": task_id,
        "seed": seed,
        "difficulty": difficulty,
        "episode_index": episode_index,
        "query_index": -1,
        "demo_count": len(demo_pairs),
        "query_count": len(query_pairs),
        "demo_pairs": demo_pairs,
        "queries": [
            {
                "input": pair["input"],
                "output": pair["output"],
            }
            for pair in query_pairs
        ],
        "shapes": {
            "demo_pairs": demo_shapes,
            "queries": query_shapes,
        },
        "colors": {
            "query_inputs": [color_set(pair["input"]) for pair in query_pairs],
            "query_outputs": [color_set(pair["output"]) for pair in query_pairs],
        },
    }
def build_sample_report(samples: list[dict[str, Any]]) -> str:
    lines = ["# ARC-Native Episode Samples", ""]
    for i, sample in enumerate(samples, start=1):
        queries = sample.get("queries") or [sample["query"]]
        q = queries[0]
        query_shape = sample["shapes"].get("query") or sample["shapes"]["queries"][0]
        lines.append(
            f"## {i}. task={sample['task_id']} seed={sample['seed']} "
            f"difficulty={sample.get('difficulty') or 'mixed'} "
            f"demo_count={sample['demo_count']} query_shape="
            f"{query_shape['input']}->{query_shape['output']} "
            f"query_count={sample.get('query_count', 1)}"
        )
        lines.append("")
        lines.append("Demo shape summary:")
        for j, pair_shape in enumerate(sample["shapes"]["demo_pairs"], start=1):
            lines.append(
                f"- demo {j}: {pair_shape['input']} -> {pair_shape['output']} "
                f"same={pair_shape['same_shape']}"
            )
        lines.append("")
        lines.append("Query input:")
        lines.append("```text")
        lines.append(grid_text(q["input"]))
        lines.append("```")
        lines.append("")
        lines.append("Query output:")
        lines.append("```text")
        lines.append(grid_text(q["output"]))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def parse_difficulty_mix(spec: str | None) -> list[tuple[str | None, float]]:
    if not spec:
        return [(None, 1.0)]
    allowed = {"easy", "medium", "hard"}
    parts: list[tuple[str | None, float]] = []
    for raw_item in spec.split(","):
        item = raw_item.strip()
        if not item:
            continue
        if ":" in item:
            name, weight_text = item.split(":", 1)
            name = name.strip()
            weight = float(weight_text.strip())
        else:
            name = item
            weight = 1.0
        if name not in allowed:
            raise ValueError(f"unknown difficulty {name!r}; expected easy, medium, or hard")
        if weight <= 0:
            raise ValueError(f"difficulty weight must be positive: {item!r}")
        parts.append((name, weight))
    if not parts:
        return [(None, 1.0)]
    return parts


def parse_context_pairs_mix(spec: str | None, *, fallback: int) -> list[tuple[int, float]]:
    if not spec:
        return [(fallback, 1.0)]
    parts: list[tuple[int, float]] = []
    for raw_item in spec.split(","):
        item = raw_item.strip()
        if not item:
            continue
        if ":" in item:
            value_text, weight_text = item.split(":", 1)
            value = int(value_text.strip())
            weight = float(weight_text.strip())
        else:
            value = int(item)
            weight = 1.0
        if value < 1:
            raise ValueError(f"context pair count must be positive: {item!r}")
        if weight <= 0:
            raise ValueError(f"context pair weight must be positive: {item!r}")
        parts.append((value, weight))
    if not parts:
        return [(fallback, 1.0)]
    return parts


def choose_difficulty(rng: random.Random, mix: list[tuple[str | None, float]]) -> str | None:
    if len(mix) == 1:
        return mix[0][0]
    total = sum(weight for _, weight in mix)
    roll = rng.random() * total
    acc = 0.0
    for name, weight in mix:
        acc += weight
        if roll <= acc:
            return name
    return mix[-1][0]


def choose_context_pairs(rng: random.Random, mix: list[tuple[int, float]]) -> int:
    if len(mix) == 1:
        return mix[0][0]
    total = sum(weight for _, weight in mix)
    roll = rng.random() * total
    acc = 0.0
    for count, weight in mix:
        acc += weight
        if roll <= acc:
            return count
    return mix[-1][0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator-root", type=Path, default=DEFAULT_GENERATOR_ROOT)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "tmp" / "arc_native_episodes")
    parser.add_argument("--episodes-per-task", type=int, default=1)
    parser.add_argument("--task-limit", type=int, default=100)
    parser.add_argument(
        "--min-generator-version",
        help="only include generators whose VERSION is at least this semantic-ish version, e.g. 2.0.0",
    )
    parser.add_argument(
        "--require-rule",
        action="store_true",
        help="only include generators that have a rule source available for output generation",
    )
    parser.add_argument(
        "--task-id",
        action="append",
        default=[],
        help="restrict generation to this task/generator id; may repeat",
    )
    parser.add_argument(
        "--task-id-file",
        type=Path,
        help="newline-delimited task/generator ids to include; # comments allowed",
    )
    parser.add_argument("--target-rows", type=int, default=None,
                        help="stop after this many successfully written query rows")
    parser.add_argument("--seed", type=int, default=260515)
    parser.add_argument("--seed-stride", type=int, default=1_000_000)
    parser.add_argument("--context-pairs", type=int, default=5)
    parser.add_argument(
        "--context-pairs-mix",
        help="weighted demo-count mix like 2:0.2,3:0.55,4:0.2,5:0.05",
    )
    parser.add_argument("--query-pairs", type=int, default=1)
    parser.add_argument(
        "--group-query-pairs",
        action="store_true",
        help="Keep all generated test/query pairs in one row. Use with --query-pairs up to 4.",
    )
    parser.add_argument("--canvas-size", type=int, default=30,
                        help="maximum accepted grid height/width")
    parser.add_argument("--num-arc-colors", type=int, default=10,
                        help="valid ARC colors are 0..N-1")
    parser.add_argument("--shard-rows", type=int, default=1000)
    parser.add_argument("--sample-count", type=int, default=32)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"),
                        help="force one generator difficulty for every episode")
    parser.add_argument("--difficulty-mix",
                        help="weighted mix like easy:0.6,medium:0.3,hard:0.1")
    parser.add_argument("--progress-every", type=int, default=25)
    parser.add_argument("--task-offset", type=int, default=0,
                        help="after shuffling/limiting tasks, start from this offset")
    parser.add_argument("--task-stride", type=int, default=1,
                        help="after task-offset, keep every Nth task; useful for parallel workers")
    parser.add_argument("--shard-prefix", default="episodes",
                        help="prefix for JSONL shards; workers should use distinct prefixes")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    difficulty_mix = parse_difficulty_mix(args.difficulty or args.difficulty_mix)
    context_pairs_mix = parse_context_pairs_mix(args.context_pairs_mix, fallback=args.context_pairs)

    runner = load_runner(args.generator_root)
    discovered_task_ids = discover_task_ids(args.generator_root)
    discovered_task_count = len(discovered_task_ids)
    discovered_task_ids = filter_task_ids_by_version(
        args.generator_root,
        discovered_task_ids,
        args.min_generator_version,
    )
    rule_backed_task_count: int | None = None
    if args.require_rule:
        rule_task_ids = discover_rule_task_ids(args.generator_root)
        discovered_task_ids = [
            task_id for task_id in discovered_task_ids if task_id in rule_task_ids
        ]
        rule_backed_task_count = len(discovered_task_ids)
    discovered = set(discovered_task_ids)
    requested_task_ids = list(args.task_id or [])
    if args.task_id_file:
        requested_task_ids.extend(read_task_ids_file(args.task_id_file))
    requested_task_ids = dedupe_preserving_order(requested_task_ids)

    if requested_task_ids:
        missing = [task_id for task_id in requested_task_ids if task_id not in discovered]
        if missing:
            raise ValueError(
                f"{len(missing)} requested task ids were not found under "
                f"{args.generator_root}: {missing[:10]}"
            )
        task_ids = list(requested_task_ids)
    else:
        task_ids = discovered_task_ids
    rng.shuffle(task_ids)
    if args.task_limit:
        task_ids = task_ids[: args.task_limit]
    total_tasks_after_limit = len(task_ids)
    if args.task_stride < 1:
        raise ValueError("--task-stride must be >= 1")
    task_ids = task_ids[args.task_offset :: args.task_stride]

    writer = ShardWriter(args.output_dir, args.shard_rows, prefix=args.shard_prefix)
    produced = 0
    skipped = 0
    bounds_failures = 0
    tensor_failures = 0
    task_failures: list[dict[str, str]] = []
    sampled_rows: list[dict[str, Any]] = []
    demo_hist: Counter[int] = Counter()
    query_shape_hist: Counter[str] = Counter()
    same_shape_hist: Counter[bool] = Counter()
    difficulty_hist: Counter[str] = Counter()
    task_id_hist: Counter[str] = Counter()
    token_hist: Counter[int] = Counter()
    bounds_failure_hist: Counter[str] = Counter()
    max_grid_height = 0
    max_grid_width = 0
    start = time.time()

    try:
        for task_index, task_id in enumerate(task_ids, start=1):
            if args.target_rows is not None and produced >= args.target_rows:
                break
            bridge = None
            try:
                bundle = runner._load_bundle(task_id)
                bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
                for episode_index in range(args.episodes_per_task):
                    if args.target_rows is not None and produced >= args.target_rows:
                        break
                    seed = args.seed + task_index * args.seed_stride + episode_index
                    difficulty = choose_difficulty(rng, difficulty_mix)
                    context_pairs = choose_context_pairs(rng, context_pairs_mix)
                    inst = runner.run_one(
                        task_id,
                        seed=seed,
                        sample_index=0,
                        n_train=context_pairs,
                        n_test=args.query_pairs,
                        bundle=bundle,
                        bridge=bridge,
                        fn_name=fn_name,
                        difficulty=difficulty,
                    )
                    demo_pairs = inst["train"]
                    if args.group_query_pairs:
                        query_pairs = list(inst["test"])
                        try:
                            row_max_height, row_max_width = validate_episode_query_pairs(
                                demo_pairs=demo_pairs,
                                query_pairs=query_pairs,
                                canvas_size=args.canvas_size,
                                num_arc_colors=args.num_arc_colors,
                            )
                        except Exception as exc:
                            bounds_failures += 1
                            bounds_failure_hist[type(exc).__name__] += 1
                            task_failures.append({
                                "task_id": task_id,
                                "exception": type(exc).__name__,
                                "message": f"grid validation failed: {str(exc)[:400]}",
                            })
                            continue
                        row = build_grouped_query_row(
                            source="arcgen",
                            task_id=task_id,
                            seed=seed,
                            difficulty=difficulty,
                            episode_index=episode_index,
                            demo_pairs=demo_pairs,
                            query_pairs=query_pairs,
                        )
                        try:
                            tensors = bottleneck_row_to_tensors(
                                row,
                                canvas_size=args.canvas_size,
                                max_context_pairs=max(context_pairs, args.context_pairs),
                                max_query_pairs=args.query_pairs,
                            )
                        except Exception as exc:
                            tensor_failures += 1
                            task_failures.append({
                                "task_id": task_id,
                                "exception": type(exc).__name__,
                                "message": f"bottleneck tensorize failed: {str(exc)[:400]}",
                            })
                            continue
                        row["dense_tokens_with_target"] = int(tensors["labels"].numel())
                        writer.write(row)
                        produced += 1
                        max_grid_height = max(max_grid_height, row_max_height)
                        max_grid_width = max(max_grid_width, row_max_width)
                        demo_hist[len(demo_pairs)] += 1
                        for query_shape in row["shapes"]["queries"]:
                            query_shape_hist[f"{query_shape['input']}->{query_shape['output']}"] += 1
                            same_shape_hist[bool(query_shape["same_shape"])] += 1
                        difficulty_hist[difficulty or "unrestricted"] += 1
                        task_id_hist[task_id] += 1
                        token_hist[int(row["dense_tokens_with_target"])] += 1

                        if len(sampled_rows) < args.sample_count:
                            sampled_rows.append(row)
                        else:
                            j = rng.randrange(produced)
                            if j < args.sample_count:
                                sampled_rows[j] = row
                        continue

                    for query_index, query_pair in enumerate(inst["test"]):
                        if args.target_rows is not None and produced >= args.target_rows:
                            break
                        try:
                            row_max_height, row_max_width = validate_episode_grids(
                                demo_pairs=demo_pairs,
                                query_pair=query_pair,
                                canvas_size=args.canvas_size,
                                num_arc_colors=args.num_arc_colors,
                            )
                        except Exception as exc:
                            bounds_failures += 1
                            bounds_failure_hist[type(exc).__name__] += 1
                            task_failures.append({
                                "task_id": task_id,
                                "exception": type(exc).__name__,
                                "message": f"grid validation failed: {str(exc)[:400]}",
                            })
                            continue
                        row = build_row(
                            source="arcgen",
                            task_id=task_id,
                            seed=seed,
                            difficulty=difficulty,
                            episode_index=episode_index,
                            query_index=query_index,
                            demo_pairs=demo_pairs,
                            query_pair=query_pair,
                        )
                        try:
                            tensors = episode_row_to_tensors(row, canvas_size=args.canvas_size)
                        except Exception as exc:
                            tensor_failures += 1
                            task_failures.append({
                                "task_id": task_id,
                                "exception": type(exc).__name__,
                                "message": f"tensorize failed: {str(exc)[:400]}",
                            })
                            continue
                        row["dense_tokens_with_target"] = int(tensors["cell_ids"].numel())
                        writer.write(row)
                        produced += 1
                        max_grid_height = max(max_grid_height, row_max_height)
                        max_grid_width = max(max_grid_width, row_max_width)
                        demo_hist[len(demo_pairs)] += 1
                        qshape = row["shapes"]["query"]
                        query_shape_hist[f"{qshape['input']}->{qshape['output']}"] += 1
                        same_shape_hist[bool(qshape["same_shape"])] += 1
                        difficulty_hist[difficulty or "unrestricted"] += 1
                        task_id_hist[task_id] += 1
                        token_hist[int(row["dense_tokens_with_target"])] += 1

                        if len(sampled_rows) < args.sample_count:
                            sampled_rows.append(row)
                        else:
                            j = rng.randrange(produced)
                            if j < args.sample_count:
                                sampled_rows[j] = row
            except Exception as exc:
                skipped += args.episodes_per_task
                task_failures.append({
                    "task_id": task_id,
                    "exception": type(exc).__name__,
                    "message": str(exc)[:500],
                })
            finally:
                if bridge is not None:
                    try:
                        bridge.shutdown()
                    except Exception:
                        pass

            if task_index % args.progress_every == 0:
                elapsed = time.time() - start
                print(
                    f"tasks={task_index}/{len(task_ids)} produced={produced} "
                    f"skipped={skipped} bounds_failures={bounds_failures} "
                    f"tensor_failures={tensor_failures} "
                    f"elapsed={elapsed:.1f}s",
                    flush=True,
                )
    finally:
        writer.close()

    summary = {
        "format": "arc_native_episode_v1",
        "generator_root": str(args.generator_root),
        "output_dir": str(args.output_dir),
        "tasks_requested": len(task_ids),
        "tasks_discovered": discovered_task_count,
        "min_generator_version": args.min_generator_version,
        "require_rule": args.require_rule,
        "rule_backed_tasks": rule_backed_task_count,
        "total_tasks_after_limit": total_tasks_after_limit,
        "task_offset": args.task_offset,
        "task_stride": args.task_stride,
        "task_id_file": str(args.task_id_file) if args.task_id_file else None,
        "task_id_filter": requested_task_ids,
        "shard_prefix": args.shard_prefix,
        "episodes_per_task": args.episodes_per_task,
        "difficulty": args.difficulty,
        "difficulty_mix": args.difficulty or args.difficulty_mix,
        "target_rows": args.target_rows,
        "context_pairs": args.context_pairs,
        "context_pairs_mix": args.context_pairs_mix,
        "query_pairs": args.query_pairs,
        "group_query_pairs": args.group_query_pairs,
        "canvas_size": args.canvas_size,
        "num_arc_colors": args.num_arc_colors,
        "produced": produced,
        "skipped": skipped,
        "bounds_failures": bounds_failures,
        "tensor_failures": tensor_failures,
        "max_grid_height": max_grid_height,
        "max_grid_width": max_grid_width,
        "elapsed_seconds": time.time() - start,
        "shards": [str(path) for path in writer.paths],
        "demo_count_hist": dict(sorted(demo_hist.items())),
        "same_shape_hist": {str(k): v for k, v in sorted(same_shape_hist.items())},
        "difficulty_hist": dict(sorted(difficulty_hist.items())),
        "task_id_hist": dict(sorted(task_id_hist.items())),
        "dense_token_hist": dict(sorted(token_hist.items())),
        "bounds_failure_hist": dict(sorted(bounds_failure_hist.items())),
        "top_query_shape_transitions": query_shape_hist.most_common(25),
        "task_failures_sample": task_failures[:100],
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (args.output_dir / "sample_report.md").write_text(build_sample_report(sampled_rows))
    print(json.dumps(summary, indent=2))
    return 0 if produced else 1


if __name__ == "__main__":
    raise SystemExit(main())
