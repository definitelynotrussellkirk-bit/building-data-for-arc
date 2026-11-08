#!/usr/bin/env python3
"""Build ARC-native JSONL episodes with multiple generator workers."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator-root", type=Path, default=Path("/home/user/Desktop/arc-agi-2-generators"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--target-rows", type=int, required=True)
    parser.add_argument("--episodes-per-task", type=int, default=30)
    parser.add_argument("--task-limit", type=int, default=0)
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
    parser.add_argument("--seed", type=int, default=270515)
    parser.add_argument("--context-pairs", type=int, default=5)
    parser.add_argument(
        "--context-pairs-mix",
        help="weighted demo-count mix like 2:0.2,3:0.55,4:0.2,5:0.05",
    )
    parser.add_argument("--query-pairs", type=int, default=1)
    parser.add_argument("--group-query-pairs", action="store_true")
    parser.add_argument("--canvas-size", type=int, default=30)
    parser.add_argument("--num-arc-colors", type=int, default=10)
    parser.add_argument("--shard-rows", type=int, default=1000)
    parser.add_argument("--sample-count", type=int, default=32)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"),
                        help="force one generator difficulty for every episode")
    parser.add_argument("--difficulty-mix",
                        help="weighted mix like easy:0.6,medium:0.3,hard:0.1")
    parser.add_argument("--progress-every", type=int, default=100)
    parser.add_argument("--poll-seconds", type=float, default=15.0)
    return parser.parse_args()


def read_summary(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


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


def link_or_copy(src: Path, dst: Path) -> None:
    if dst.exists():
        dst.unlink()
    try:
        dst.hardlink_to(src)
    except OSError:
        shutil.copy2(src, dst)


def merge_worker_outputs(output_dir: Path, worker_dirs: list[Path], args: argparse.Namespace, elapsed: float) -> int:
    summaries = [read_summary(path / "summary.json") for path in worker_dirs if (path / "summary.json").exists()]
    produced = sum(int(s.get("produced", 0)) for s in summaries)
    skipped = sum(int(s.get("skipped", 0)) for s in summaries)
    bounds_failures = sum(int(s.get("bounds_failures", 0)) for s in summaries)
    tensor_failures = sum(int(s.get("tensor_failures", 0)) for s in summaries)
    max_grid_height = max([int(s.get("max_grid_height", 0)) for s in summaries] or [0])
    max_grid_width = max([int(s.get("max_grid_width", 0)) for s in summaries] or [0])

    demo_hist: Counter[str] = Counter()
    same_shape_hist: Counter[str] = Counter()
    difficulty_hist: Counter[str] = Counter()
    task_id_hist: Counter[str] = Counter()
    token_hist: Counter[str] = Counter()
    shape_hist: Counter[str] = Counter()
    bounds_failure_hist: Counter[str] = Counter()
    task_failures: list[dict[str, Any]] = []
    shards: list[str] = []

    for worker_id, worker_dir in enumerate(worker_dirs):
        prefix = f"episodes-w{worker_id:02d}"
        for shard in sorted(worker_dir.glob(f"{prefix}-*.jsonl")):
            dst = output_dir / shard.name
            link_or_copy(shard, dst)
            shards.append(str(dst))

    for summary in summaries:
        demo_hist.update({str(k): int(v) for k, v in summary.get("demo_count_hist", {}).items()})
        same_shape_hist.update({str(k): int(v) for k, v in summary.get("same_shape_hist", {}).items()})
        difficulty_hist.update({str(k): int(v) for k, v in summary.get("difficulty_hist", {}).items()})
        task_id_hist.update({str(k): int(v) for k, v in summary.get("task_id_hist", {}).items()})
        token_hist.update({str(k): int(v) for k, v in summary.get("dense_token_hist", {}).items()})
        shape_hist.update({str(k): int(v) for k, v in summary.get("top_query_shape_transitions", [])})
        bounds_failure_hist.update({str(k): int(v) for k, v in summary.get("bounds_failure_hist", {}).items()})
        task_failures.extend(summary.get("task_failures_sample", []))

    sample_reports = []
    for worker_dir in worker_dirs:
        sample_path = worker_dir / "sample_report.md"
        if sample_path.exists():
            sample_reports.append(sample_path.read_text())
    (output_dir / "sample_report.md").write_text("\n\n---\n\n".join(sample_reports[: args.workers]))

    merged = {
        "format": "arc_native_episode_v1",
        "builder": "parallel",
        "generator_root": str(args.generator_root),
        "output_dir": str(output_dir),
        "workers": args.workers,
        "target_rows": args.target_rows,
        "episodes_per_task": args.episodes_per_task,
        "difficulty": args.difficulty,
        "difficulty_mix": args.difficulty or args.difficulty_mix,
        "task_id_file": str(args.task_id_file) if args.task_id_file else None,
        "task_id_filter": args.task_id,
        "task_limit": args.task_limit,
        "min_generator_version": args.min_generator_version,
        "require_rule": args.require_rule,
        "context_pairs": args.context_pairs,
        "context_pairs_mix": args.context_pairs_mix,
        "query_pairs": args.query_pairs,
        "canvas_size": args.canvas_size,
        "num_arc_colors": args.num_arc_colors,
        "seed": args.seed,
        "produced": produced,
        "skipped": skipped,
        "bounds_failures": bounds_failures,
        "tensor_failures": tensor_failures,
        "max_grid_height": max_grid_height,
        "max_grid_width": max_grid_width,
        "elapsed_seconds": elapsed,
        "rows_per_second": produced / max(elapsed, 1e-9),
        "shard_count": len(shards),
        "shards": shards,
        "demo_count_hist": dict(sorted(demo_hist.items())),
        "same_shape_hist": dict(sorted(same_shape_hist.items())),
        "difficulty_hist": dict(sorted(difficulty_hist.items())),
        "task_id_hist": dict(sorted(task_id_hist.items())),
        "dense_token_hist": dict(sorted(token_hist.items())),
        "bounds_failure_hist": dict(sorted(bounds_failure_hist.items())),
        "top_query_shape_transitions": shape_hist.most_common(25),
        "task_failures_sample": task_failures[:100],
        "worker_summaries": [str(path / "summary.json") for path in worker_dirs],
    }
    (output_dir / "summary.json").write_text(json.dumps(merged, indent=2, sort_keys=True))
    print(json.dumps(merged, indent=2, sort_keys=True))
    return produced


def main() -> int:
    args = parse_args()
    if args.workers < 1:
        raise ValueError("--workers must be >= 1")
    requested_task_ids = list(args.task_id or [])
    if args.task_id_file:
        requested_task_ids.extend(read_task_ids_file(args.task_id_file))
    requested_task_ids = dedupe_preserving_order(requested_task_ids)
    if requested_task_ids:
        args.workers = min(args.workers, len(requested_task_ids))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    worker_root = args.output_dir / "_workers"
    worker_root.mkdir(exist_ok=True)

    rows_per_worker = math.ceil(args.target_rows / args.workers)
    procs: list[tuple[int, Path, Path, subprocess.Popen]] = []
    start = time.time()
    for worker_id in range(args.workers):
        worker_dir = worker_root / f"worker-{worker_id:02d}"
        if worker_dir.exists():
            shutil.rmtree(worker_dir)
        worker_dir.mkdir(parents=True)
        log_path = args.output_dir / f"worker-{worker_id:02d}.log"
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "build_arc_native_dataset.py"),
            "--generator-root",
            str(args.generator_root),
            "--output-dir",
            str(worker_dir),
            "--target-rows",
            str(rows_per_worker),
            "--task-limit",
            str(args.task_limit),
            "--min-generator-version",
            str(args.min_generator_version or ""),
            "--episodes-per-task",
            str(args.episodes_per_task),
            "--context-pairs",
            str(args.context_pairs),
            "--query-pairs",
            str(args.query_pairs),
            "--canvas-size",
            str(args.canvas_size),
            "--num-arc-colors",
            str(args.num_arc_colors),
            "--seed",
            str(args.seed),
            "--shard-rows",
            str(args.shard_rows),
            "--sample-count",
            str(max(1, math.ceil(args.sample_count / args.workers))),
            "--progress-every",
            str(args.progress_every),
            "--task-offset",
            str(worker_id),
            "--task-stride",
            str(args.workers),
            "--shard-prefix",
            f"episodes-w{worker_id:02d}",
        ]
        if args.require_rule:
            cmd.append("--require-rule")
        if args.difficulty:
            cmd.extend(["--difficulty", args.difficulty])
        if args.difficulty_mix:
            cmd.extend(["--difficulty-mix", args.difficulty_mix])
        if args.context_pairs_mix:
            cmd.extend(["--context-pairs-mix", args.context_pairs_mix])
        if args.group_query_pairs:
            cmd.append("--group-query-pairs")
        for task_id in args.task_id:
            cmd.extend(["--task-id", task_id])
        if args.task_id_file:
            cmd.extend(["--task-id-file", str(args.task_id_file)])
        handle = log_path.open("w")
        proc = subprocess.Popen(cmd, stdout=handle, stderr=subprocess.STDOUT)
        procs.append((worker_id, worker_dir, log_path, proc))
        print(f"worker_start id={worker_id} pid={proc.pid} log={log_path}", flush=True)

    while True:
        alive = [proc for _, _, _, proc in procs if proc.poll() is None]
        produced = 0
        for _, worker_dir, _, _ in procs:
            for shard in worker_dir.glob("episodes-w*.jsonl"):
                try:
                    with shard.open("rb") as f:
                        produced += sum(1 for _ in f)
                except FileNotFoundError:
                    pass
        print(
            f"parallel_progress produced={produced} target={args.target_rows} "
            f"alive={len(alive)} elapsed={time.time() - start:.1f}s",
            flush=True,
        )
        if not alive:
            break
        time.sleep(args.poll_seconds)

    failed = [(worker_id, proc.returncode, log_path) for worker_id, _, log_path, proc in procs if proc.returncode != 0]
    if failed:
        for worker_id, returncode, log_path in failed:
            print(f"worker_failed id={worker_id} returncode={returncode} log={log_path}", file=sys.stderr)
        return 1

    elapsed = time.time() - start
    produced = merge_worker_outputs(args.output_dir, [worker_dir for _, worker_dir, _, _ in procs], args, elapsed)
    return 0 if produced else 1


if __name__ == "__main__":
    raise SystemExit(main())
